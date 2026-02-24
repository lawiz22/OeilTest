# modules/structural_routes.py

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import text

from .db import get_engine
from .structural_service import preview_structural
from .layout import render

router = APIRouter()


# ==========================================================
# STRUCTURAL PAGE (HTML)
# ==========================================================

@router.get("/struct/{dataset_id}", response_class=HTMLResponse)
def structural_page(request: Request, dataset_id: int):

    engine = get_engine()

    query = """
    SELECT dataset_id,
           dataset_name,
           source_system,
           mapping_version
    FROM ctrl.dataset
    WHERE dataset_id = :dataset_id
    """

    with engine.connect() as conn:
        dataset = conn.execute(
            text(query),
            {"dataset_id": dataset_id}
        ).mappings().first()

    if not dataset:
        return HTMLResponse("<h2>Dataset not found</h2>", status_code=404)

    return render(
        request,
        "structural.html",
        context={
            "dataset": dataset
        },
        dataset_id=dataset_id,
        active_tab="structural"
    )


# ==========================================================
# STRUCTURAL PREVIEW API
# ==========================================================

@router.get("/struct/{dataset_id}/preview")
def structural_preview(dataset_id: int):

    return preview_structural(dataset_id)


# ==========================================================
# STRUCTURAL UPDATE API
# ==========================================================

@router.post("/struct/{dataset_id}/update")
def structural_update(dataset_id: int):

    preview = preview_structural(dataset_id)

    if preview["status"] == "MATCH":
        return {
            "status": "NO_CHANGE",
            "message": "Structural hash already up to date",
            "hash": preview["new_hash"]
        }

    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE ctrl.dataset
                SET structural_hash = :hash_value
                WHERE dataset_id = :dataset_id
            """),
            {
                "hash_value": bytes.fromhex(preview["new_hash"]),
                "dataset_id": dataset_id
            }
        )

    return {
        "status": "UPDATED",
        "new_hash": preview["new_hash"]
    }