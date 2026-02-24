# modules/policy_routes.py

import os
from decimal import Decimal
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .db import get_engine
from .layout import render
from ..policy_repository import PolicyRepository
from ..json_builder import PolicyJsonBuilder
from ..lake_writer import LakeWriter
from ..config import AZURE_SQL_CONN, AZCOPY_DEST

router = APIRouter()

DEFAULT_DISTRIBUTED_SIGNATURE_COMPONENTS = "COUNT|MIN|MAX|SUM"


def _policy_lake_path(dataset_name: str, environment: str) -> str:
    return f"standardized/_policies/{dataset_name}_{environment}.policy.json"


def _build_integrity_preview(tests):
    integrity = {}

    for test in tests:
        test_code = (test.get("test_code") or "").strip().upper()

        if test_code == "DISTRIBUTED_SIGNATURE":
            integrity["distributed_signature"] = {
                "column": test.get("column_name"),
                "algorithm": test.get("hash_algorithm") or "SHA256",
                "components": DEFAULT_DISTRIBUTED_SIGNATURE_COMPONENTS,
            }

        if test_code == "MIN_MAX":
            integrity["min_max"] = {
                "column": test.get("column_name"),
            }

    return integrity


def _serialize_policy_test(test):
    payload = {
        "test_code": test.get("test_code"),
    }

    if test.get("frequency"):
        payload["frequency"] = test.get("frequency")

    if test.get("column_name"):
        payload["column_name"] = test.get("column_name")

    threshold_value = test.get("threshold_value")
    if threshold_value is not None:
        payload["threshold_value"] = float(threshold_value)

    test_code = (test.get("test_code") or "").strip().upper()
    hash_algorithm = test.get("hash_algorithm")
    if hash_algorithm and test_code == "DISTRIBUTED_SIGNATURE":
        payload["hash_algorithm"] = hash_algorithm
        payload["components"] = DEFAULT_DISTRIBUTED_SIGNATURE_COMPONENTS

    return payload


def _load_dataset_for_export(dataset_id: int):
    if not AZURE_SQL_CONN:
        raise ValueError("OEIL_AZURE_SQL_CONN is not configured")

    repo = PolicyRepository(AZURE_SQL_CONN)
    datasets = repo.get_datasets()
    dataset = next((row for row in datasets if row.policy_dataset_id == dataset_id), None)
    return repo, dataset


def _load_policy_page_data(dataset_id: int):

    engine = get_engine()

    dataset_query = """
    SELECT policy_dataset_id,
           dataset_name,
           environment,
           synapse_allowed,
           max_synapse_cost_usd
    FROM vigie_policy_dataset
    WHERE policy_dataset_id = :dataset_id
    """

    tests_query = """
    SELECT t.policy_test_id,
           tt.test_code,
           t.column_name,
           t.frequency,
           t.hash_algorithm,
           t.threshold_value,
           t.is_enabled
    FROM vigie_policy_test t
    INNER JOIN vigie_policy_test_type tt
        ON t.test_type_id = tt.test_type_id
    WHERE t.policy_dataset_id = :dataset_id
    ORDER BY t.policy_test_id
    """

    with engine.connect() as conn:
        dataset = conn.execute(
            text(dataset_query),
            {"dataset_id": dataset_id}
        ).mappings().first()

        tests = conn.execute(
            text(tests_query),
            {"dataset_id": dataset_id}
        ).mappings().all()

        struct_dataset = conn.execute(
            text("""
                SELECT TOP 1 d.dataset_id
                FROM ctrl.dataset d
                INNER JOIN vigie_policy_dataset p
                    ON p.dataset_name = d.dataset_name
                WHERE p.policy_dataset_id = :dataset_id
                ORDER BY CASE WHEN p.environment = 'DEV' THEN 0 ELSE 1 END, d.dataset_id
            """),
            {"dataset_id": dataset_id}
        ).mappings().first()

    if not dataset:
        return None

    repo = PolicyRepository(AZURE_SQL_CONN) if AZURE_SQL_CONN else None
    test_types = repo.get_test_types() if repo else []
    available_columns = repo.get_available_columns_for_dataset(dataset["dataset_name"]) if repo else []

    return {
        "dataset": dataset,
        "tests": tests,
        "test_types": test_types,
        "available_columns": available_columns,
        "struct_dataset_id": struct_dataset["dataset_id"] if struct_dataset else None,
    }


def _resolve_policy_dataset_id(conn, dataset_name: str, environment: str):
    row = conn.execute(
        text("""
            SELECT TOP 1 policy_dataset_id
            FROM vigie_policy_dataset
            WHERE dataset_name = :dataset_name
              AND UPPER(environment) = UPPER(:environment)
            ORDER BY policy_dataset_id
        """),
        {
            "dataset_name": dataset_name,
            "environment": environment,
        }
    ).mappings().first()
    return row["policy_dataset_id"] if row else None


# ==========================================================
# POLICY PAGE (HTML)
# ==========================================================

@router.get("/policy/{dataset_id}", response_class=HTMLResponse)
def policy_page(request: Request, dataset_id: int):
    page_data = _load_policy_page_data(dataset_id)
    if not page_data:
        return HTMLResponse("<h2>Policy dataset not found</h2>", status_code=404)

    dataset = page_data["dataset"]

    return render(
        request,
        "policy.html",
        context={
            "dataset": dataset,
            "tests": page_data["tests"],
            "test_types": page_data["test_types"],
            "available_columns": page_data["available_columns"],
        },
        dataset_id=dataset_id,
        policy_dataset_id=dataset_id,
        struct_dataset_id=page_data["struct_dataset_id"],
        route_dataset_name=dataset["dataset_name"],
        route_environment=dataset["environment"],
        active_tab="policy"
    )


@router.post("/policy/{dataset_id}/tests/add")
async def add_policy_test(dataset_id: int, request: Request):

    if not AZURE_SQL_CONN:
        return JSONResponse({"error": "OEIL_AZURE_SQL_CONN is not configured"}, status_code=500)

    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON payload"}, status_code=400)

    test_type_id = payload.get("test_type_id")
    frequency = (payload.get("frequency") or "DAILY").strip().upper()
    column_name = (payload.get("column_name") or "").strip() or None
    hash_algorithm = (payload.get("hash_algorithm") or "").strip() or None
    threshold_raw = payload.get("threshold_value")

    if not test_type_id:
        return JSONResponse({"error": "test_type_id is required"}, status_code=400)

    try:
        test_type_id = int(test_type_id)
    except (TypeError, ValueError):
        return JSONResponse({"error": "test_type_id must be numeric"}, status_code=400)

    if frequency not in {"DAILY", "WEEKLY", "MONTHLY"}:
        return JSONResponse({"error": "frequency must be DAILY, WEEKLY or MONTHLY"}, status_code=400)

    threshold_value = None
    if threshold_raw not in (None, ""):
        try:
            threshold_value = Decimal(str(threshold_raw))
        except Exception:
            return JSONResponse({"error": "threshold_value must be numeric"}, status_code=400)

    repo = PolicyRepository(AZURE_SQL_CONN)

    dataset = repo.get_dataset_by_id(dataset_id)
    if dataset is None:
        return JSONResponse({"error": "Policy dataset not found"}, status_code=404)

    test_type = repo.find_test_type_by_id(test_type_id)
    if test_type is None:
        return JSONResponse({"error": "Test type not found"}, status_code=404)

    if test_type["requires_synapse"] and not dataset["synapse_allowed"]:
        return JSONResponse(
            {"error": f"{test_type['test_code']} requires Synapse but this dataset does not allow Synapse."},
            status_code=400
        )

    if repo.policy_test_exists(dataset_id, test_type_id, column_name, frequency):
        return JSONResponse(
            {"error": "This policy test already exists for same type/column/frequency."},
            status_code=409
        )

    if test_type["test_code"] == "DISTRIBUTED_SIGNATURE" and not hash_algorithm:
        hash_algorithm = "SHA256"

    if test_type["test_code"] == "DISTRIBUTED_SIGNATURE" and not column_name:
        return JSONResponse({"error": "DISTRIBUTED_SIGNATURE requires a column_name"}, status_code=400)

    if test_type["test_code"] == "MIN_MAX" and not column_name:
        return JSONResponse({"error": "MIN_MAX requires a column_name"}, status_code=400)

    try:
        new_id = repo.add_policy_test(
            dataset_id=dataset_id,
            test_type_id=test_type_id,
            column_name=column_name,
            frequency=frequency,
            hash_algorithm=hash_algorithm,
            threshold_value=threshold_value,
        )
    except SQLAlchemyError as exc:
        db_message = str(getattr(exc, "orig", exc) or "").strip()
        db_message_lower = db_message.lower()

        if "duplicate" in db_message_lower or "unique" in db_message_lower:
            return JSONResponse(
                {"error": "This policy test already exists (database uniqueness rule)."},
                status_code=409,
            )

        return JSONResponse(
            {"error": f"Database error while adding policy test: {db_message or 'unknown database error'}"},
            status_code=500,
        )
    except Exception as exc:
        return JSONResponse(
            {"error": f"Unexpected error while adding policy test: {str(exc)}"},
            status_code=500,
        )

    return {
        "status": "CREATED",
        "policy_test_id": new_id,
    }


@router.post("/policy/{dataset_id}/tests/{policy_test_id}/delete")
def delete_policy_test(dataset_id: int, policy_test_id: int):

    if not AZURE_SQL_CONN:
        return JSONResponse({"error": "OEIL_AZURE_SQL_CONN is not configured"}, status_code=500)

    repo = PolicyRepository(AZURE_SQL_CONN)
    deleted = repo.delete_policy_test(dataset_id=dataset_id, policy_test_id=policy_test_id)

    if deleted == 0:
        return JSONResponse({"error": "Policy test not found"}, status_code=404)

    return {"status": "DELETED", "policy_test_id": policy_test_id}


@router.post("/policy/{dataset_id}/tests/{policy_test_id}/update")
async def update_policy_test(dataset_id: int, policy_test_id: int, request: Request):

    if not AZURE_SQL_CONN:
        return JSONResponse({"error": "OEIL_AZURE_SQL_CONN is not configured"}, status_code=500)

    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON payload"}, status_code=400)

    frequency = (payload.get("frequency") or "DAILY").strip().upper()
    column_name = (payload.get("column_name") or "").strip() or None
    hash_algorithm = (payload.get("hash_algorithm") or "").strip() or None
    threshold_raw = payload.get("threshold_value")

    if frequency not in {"DAILY", "WEEKLY", "MONTHLY"}:
        return JSONResponse({"error": "frequency must be DAILY, WEEKLY or MONTHLY"}, status_code=400)

    threshold_value = None
    if threshold_raw not in (None, ""):
        try:
            threshold_value = Decimal(str(threshold_raw))
        except Exception:
            return JSONResponse({"error": "threshold_value must be numeric"}, status_code=400)

    repo = PolicyRepository(AZURE_SQL_CONN)

    dataset = repo.get_dataset_by_id(dataset_id)
    if dataset is None:
        return JSONResponse({"error": "Policy dataset not found"}, status_code=404)

    current_test = repo.get_policy_test_by_id(dataset_id=dataset_id, policy_test_id=policy_test_id)
    if current_test is None:
        return JSONResponse({"error": "Policy test not found"}, status_code=404)

    test_code = (current_test.get("test_code") or "").strip().upper()

    if test_code == "DISTRIBUTED_SIGNATURE" and not column_name:
        return JSONResponse({"error": "DISTRIBUTED_SIGNATURE requires a column_name"}, status_code=400)

    if test_code == "MIN_MAX" and not column_name:
        return JSONResponse({"error": "MIN_MAX requires a column_name"}, status_code=400)

    if test_code == "DISTRIBUTED_SIGNATURE" and not hash_algorithm:
        hash_algorithm = "SHA256"

    if test_code != "DISTRIBUTED_SIGNATURE":
        hash_algorithm = None

    if repo.policy_test_exists(
        dataset_id=dataset_id,
        test_type_id=current_test["test_type_id"],
        column_name=column_name,
        frequency=frequency,
        exclude_policy_test_id=policy_test_id,
    ):
        return JSONResponse(
            {"error": "Another active policy test already exists for same type/column/frequency."},
            status_code=409,
        )

    try:
        updated = repo.update_policy_test(
            dataset_id=dataset_id,
            policy_test_id=policy_test_id,
            column_name=column_name,
            frequency=frequency,
            hash_algorithm=hash_algorithm,
            threshold_value=threshold_value,
        )
    except SQLAlchemyError as exc:
        db_message = str(getattr(exc, "orig", exc) or "").strip()
        return JSONResponse(
            {"error": f"Database error while updating policy test: {db_message or 'unknown database error'}"},
            status_code=500,
        )

    if updated == 0:
        return JSONResponse({"error": "Policy test not found"}, status_code=404)

    return {
        "status": "UPDATED",
        "policy_test_id": policy_test_id,
    }


@router.post("/policy/{dataset_id}/synapse-allowed")
async def set_synapse_allowed(dataset_id: int, request: Request):

    payload = await request.json()
    value = payload.get("synapse_allowed")

    if value in (True, 1, "1", "true", "TRUE", "True"):
        synapse_allowed = 1
    elif value in (False, 0, "0", "false", "FALSE", "False"):
        synapse_allowed = 0
    else:
        return JSONResponse({"error": "synapse_allowed must be boolean"}, status_code=400)

    engine = get_engine()

    with engine.begin() as conn:
        result = conn.execute(
            text("""
                UPDATE vigie_policy_dataset
                SET synapse_allowed = :synapse_allowed
                WHERE policy_dataset_id = :dataset_id
            """),
            {
                "synapse_allowed": synapse_allowed,
                "dataset_id": dataset_id,
            }
        )

    if result.rowcount == 0:
        return JSONResponse({"error": "Policy dataset not found"}, status_code=404)

    return {
        "status": "UPDATED",
        "dataset_id": dataset_id,
        "synapse_allowed": bool(synapse_allowed),
    }


@router.post("/policy/{dataset_id}/toggle-active")
def toggle_policy_active(dataset_id: int):

    engine = get_engine()

    with engine.begin() as conn:
        current = conn.execute(
            text("""
                SELECT is_active
                FROM vigie_policy_dataset
                WHERE policy_dataset_id = :dataset_id
            """),
            {"dataset_id": dataset_id}
        ).mappings().first()

        if not current:
            return JSONResponse({"error": "Policy dataset not found"}, status_code=404)

        next_value = 0 if bool(current["is_active"]) else 1

        conn.execute(
            text("""
                UPDATE vigie_policy_dataset
                SET is_active = :is_active
                WHERE policy_dataset_id = :dataset_id
            """),
            {
                "is_active": next_value,
                "dataset_id": dataset_id,
            }
        )

    return {
        "status": "UPDATED",
        "dataset_id": dataset_id,
        "is_active": bool(next_value),
    }


# ==========================================================
# POLICY EXPORT (JSON API)
# ==========================================================

@router.get("/policy/{dataset_id}/export")
def export_policy(dataset_id: int):

    engine = get_engine()

    dataset_query = """
    SELECT dataset_name,
           environment,
           synapse_allowed,
           max_synapse_cost_usd
    FROM vigie_policy_dataset
    WHERE policy_dataset_id = :dataset_id
    """

    tests_query = """
    SELECT tt.test_code,
           t.column_name,
           t.hash_algorithm,
           t.frequency,
           t.threshold_value,
           t.is_enabled
    FROM vigie_policy_test t
    INNER JOIN vigie_policy_test_type tt
        ON t.test_type_id = tt.test_type_id
    WHERE t.policy_dataset_id = :dataset_id
      AND t.is_enabled = 1
    """

    with engine.connect() as conn:
        dataset = conn.execute(
            text(dataset_query),
            {"dataset_id": dataset_id}
        ).mappings().first()

        tests = conn.execute(
            text(tests_query),
            {"dataset_id": dataset_id}
        ).mappings().all()

    if not dataset:
        return JSONResponse({"error": "Policy not found"}, status_code=404)

    policy_json = {
        "dataset_name": dataset["dataset_name"],
        "environment": dataset["environment"],
        "synapse_allowed": dataset["synapse_allowed"],
        "max_synapse_cost_usd": float(dataset["max_synapse_cost_usd"]) if dataset["max_synapse_cost_usd"] else None,
        "integrity": _build_integrity_preview(tests),
        "tests": [_serialize_policy_test(t) for t in tests]
    }

    return policy_json


@router.get("/policy/{dataset_id}/lake-status")
def policy_lake_status(dataset_id: int):
    try:
        repo, dataset = _load_dataset_for_export(dataset_id)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)

    if dataset is None:
        return JSONResponse({"error": "Policy not found"}, status_code=404)

    if not AZCOPY_DEST:
        return JSONResponse({"error": "OEIL_AZCOPY_DEST is not configured"}, status_code=500)

    path = _policy_lake_path(dataset.dataset_name, dataset.environment)

    try:
        writer = LakeWriter(AZCOPY_DEST)
        exists = writer.policy_exists(path)
    except Exception as exc:
        return JSONResponse({"error": f"Lake access failed: {exc}"}, status_code=500)

    return {
        "dataset_id": dataset_id,
        "path": path,
        "exists": exists,
    }


@router.post("/policy/{dataset_id}/export-lake")
def export_policy_to_lake(dataset_id: int):
    try:
        repo, dataset = _load_dataset_for_export(dataset_id)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)

    if dataset is None:
        return JSONResponse({"error": "Policy not found"}, status_code=404)

    if not AZCOPY_DEST:
        return JSONResponse({"error": "OEIL_AZCOPY_DEST is not configured"}, status_code=500)

    tests = repo.get_tests_for_dataset(dataset_id)
    policy_dict = PolicyJsonBuilder.build(dataset, tests)
    json_content = PolicyJsonBuilder.to_json(policy_dict)

    path = _policy_lake_path(dataset.dataset_name, dataset.environment)

    try:
        writer = LakeWriter(AZCOPY_DEST)
        existed_before = writer.policy_exists(path)
        writer.write_policy(path=path, content=json_content)
    except Exception as exc:
        return JSONResponse({"error": f"Lake export failed: {exc}"}, status_code=500)

    return {
        "status": "EXPORTED",
        "path": path,
        "already_existed": existed_before,
    }


@router.get("/policy/{dataset_name}/{environment}", response_class=HTMLResponse)
def policy_page_by_dataset_env(request: Request, dataset_name: str, environment: str):

    engine = get_engine()
    with engine.connect() as conn:
        dataset_id = _resolve_policy_dataset_id(conn, dataset_name, environment)

    if dataset_id is None:
        return HTMLResponse("<h2>Policy dataset not found for dataset/environment</h2>", status_code=404)

    return policy_page(request, dataset_id)