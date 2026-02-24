# modules/policy_routes.py

import os
from decimal import Decimal
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import text

from .db import get_engine
from .layout import render
from ..policy_repository import PolicyRepository
from ..json_builder import PolicyJsonBuilder
from ..lake_writer import LakeWriter
from ..config import AZURE_SQL_CONN, AZCOPY_DEST

router = APIRouter()


def _policy_lake_path(dataset_name: str, environment: str) -> str:
    return f"standardized/_policies/{dataset_name}_{environment}.policy.json"


def _load_dataset_for_export(dataset_id: int):
    if not AZURE_SQL_CONN:
        raise ValueError("OEIL_AZURE_SQL_CONN is not configured")

    repo = PolicyRepository(AZURE_SQL_CONN)
    datasets = repo.get_datasets()
    dataset = next((row for row in datasets if row.policy_dataset_id == dataset_id), None)
    return repo, dataset


# ==========================================================
# POLICY PAGE (HTML)
# ==========================================================

@router.get("/policy/{dataset_id}", response_class=HTMLResponse)
def policy_page(request: Request, dataset_id: int):

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

    repo = PolicyRepository(AZURE_SQL_CONN) if AZURE_SQL_CONN else None
    test_types = repo.get_test_types() if repo else []
    available_columns = repo.get_available_columns_for_dataset(dataset["dataset_name"]) if repo else []

    if not dataset:
        return HTMLResponse("<h2>Policy dataset not found</h2>", status_code=404)

    return render(
        request,
        "policy.html",
        context={
            "dataset": dataset,
            "tests": tests,
            "test_types": test_types,
            "available_columns": available_columns,
        },
        dataset_id=dataset_id,
        active_tab="policy"
    )


@router.post("/policy/{dataset_id}/tests/add")
async def add_policy_test(dataset_id: int, request: Request):

    if not AZURE_SQL_CONN:
        return JSONResponse({"error": "OEIL_AZURE_SQL_CONN is not configured"}, status_code=500)

    payload = await request.json()

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

    if test_type["test_code"] == "MIN_MAX" and not column_name:
        return JSONResponse({"error": "MIN_MAX requires a column_name"}, status_code=400)

    new_id = repo.add_policy_test(
        dataset_id=dataset_id,
        test_type_id=test_type_id,
        column_name=column_name,
        frequency=frequency,
        hash_algorithm=hash_algorithm,
        threshold_value=threshold_value,
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
        "tests": [
            {
                "test_code": t["test_code"],
                "column_name": t["column_name"],
                "hash_algorithm": t["hash_algorithm"],
                "frequency": t["frequency"],
                "threshold_value": float(t["threshold_value"]) if t["threshold_value"] else None
            }
            for t in tests
        ]
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