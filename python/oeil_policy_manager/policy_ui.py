import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from .policy_repository import PolicyRepository
from .json_builder import PolicyJsonBuilder
from .lake_writer import LakeWriter

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="python/oeil_policy_manager/templates")

repo = PolicyRepository(os.getenv("OEIL_AZURE_SQL_CONN"))


# ======================================================
# LIST DATASETS
# ======================================================
@app.get("/", response_class=HTMLResponse)
def list_datasets(request: Request):
    datasets = repo.get_datasets()
    return templates.TemplateResponse(
        "datasets.html",
        {"request": request, "datasets": datasets},
    )


# ======================================================
# VIEW DATASET
# ======================================================
@app.get("/dataset/{dataset_id}", response_class=HTMLResponse)
def view_dataset(request: Request, dataset_id: int):
    datasets = repo.get_datasets()
    dataset = next(d for d in datasets if d.policy_dataset_id == dataset_id)
    tests = repo.get_tests_for_dataset(dataset_id)

    return templates.TemplateResponse(
        "dataset_detail.html",
        {
            "request": request,
            "dataset": dataset,
            "tests": tests,
        },
    )


# ======================================================
# EXPORT POLICY
# ======================================================
@app.post("/dataset/{dataset_id}/export")
def export_policy(dataset_id: int):

    datasets = repo.get_datasets()
    dataset = next(d for d in datasets if d.policy_dataset_id == dataset_id)
    tests = repo.get_tests_for_dataset(dataset_id)

    policy_dict = PolicyJsonBuilder.build(dataset, tests)
    json_content = PolicyJsonBuilder.to_json(policy_dict)

    writer = LakeWriter(os.getenv("OEIL_AZCOPY_DEST"))

    path = (
        f"standardized/_policies/"
        f"{dataset.dataset_name}_{dataset.environment}.policy.json"
    )

    writer.write_policy(path=path, content=json_content)

    return RedirectResponse(f"/dataset/{dataset_id}", status_code=303)


# ======================================================
# DOWNLOAD JSON
# ======================================================
@app.get("/dataset/{dataset_id}/download")
def download_policy(dataset_id: int):

    datasets = repo.get_datasets()
    dataset = next(d for d in datasets if d.policy_dataset_id == dataset_id)
    tests = repo.get_tests_for_dataset(dataset_id)

    policy_dict = PolicyJsonBuilder.build(dataset, tests)
    json_content = PolicyJsonBuilder.to_json(policy_dict)

    return JSONResponse(content=policy_dict)