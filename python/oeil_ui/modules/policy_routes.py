# modules/policy_routes.py

import os
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

    if not dataset:
        return HTMLResponse("<h2>Policy dataset not found</h2>", status_code=404)

    return render(
        request,
        "policy.html",
        context={
            "dataset": dataset,
            "tests": tests
        },
        dataset_id=dataset_id,
        active_tab="policy"
    )


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