from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from .home_service import get_dashboard_datasets
from .layout import render
from .db import ping_sql, reset_engine
from ..lake_writer import LakeWriter
from ..config import AZCOPY_DEST

router = APIRouter()


def _service_status_payload(force_reconnect: bool = False):
    if force_reconnect:
        reset_engine()

    sql_ok, sql_message = ping_sql()

    lake_ok = False
    lake_message = "OEIL_AZCOPY_DEST not configured"
    if AZCOPY_DEST:
        try:
            writer = LakeWriter(AZCOPY_DEST)
            lake_ok = writer.ping()
            lake_message = "Connected" if lake_ok else "Unavailable"
        except Exception as exc:
            lake_ok = False
            lake_message = str(exc)

    return {
        "azure_sql": {
            "ok": sql_ok,
            "message": sql_message,
        },
        "lake": {
            "ok": lake_ok,
            "message": lake_message,
        },
    }

@router.get("/")
def home(request: Request):
    dashboard = get_dashboard_datasets()
    return render(
        request,
        "home.html",
        context={
            "datasets": dashboard
        }
    )


@router.get("/service-status")
def service_status():
    return _service_status_payload(force_reconnect=False)


@router.post("/service-status/reconnect")
def reconnect_services():
    return JSONResponse(_service_status_payload(force_reconnect=True))