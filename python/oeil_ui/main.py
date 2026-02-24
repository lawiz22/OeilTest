from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .modules.home import router as home_router
from .modules.structural_routes import router as structural_router
from .modules.policy_routes import router as policy_router

app = FastAPI()
app.mount("/static", StaticFiles(directory="python/oeil_ui/static"), name="static")

app.include_router(home_router)
app.include_router(structural_router)
app.include_router(policy_router)