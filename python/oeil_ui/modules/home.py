from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from .home_service import get_dashboard_datasets

router = APIRouter()
templates = Jinja2Templates(directory="python/oeil_ui/templates")

@router.get("/")
def home(request: Request):
    dashboard = get_dashboard_datasets()
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "datasets": dashboard
        }
    )