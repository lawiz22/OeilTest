import os
import hashlib
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

app = FastAPI()

# =========================
# DATABASE CONNECTION
# =========================

def get_engine():

    conn_str = os.getenv("OEIL_AZURE_SQL_CONN")

    if not conn_str:
        raise ValueError("OEIL_AZURE_SQL_CONN not defined")

    params = {
        item.split("=", 1)[0]: item.split("=", 1)[1]
        for item in conn_str.strip(";").split(";")
        if "=" in item
    }

    driver = params.get("Driver", "").replace("{", "").replace("}", "")
    server_raw = params.get("Server", "")
    database = params.get("Database", "")
    uid = params.get("Uid", "")
    pwd = params.get("Pwd", "")

    if server_raw.startswith("tcp:"):
        server_raw = server_raw.replace("tcp:", "")

    if "," in server_raw:
        host, port = server_raw.split(",", 1)
        server = f"{host}:{port}"
    else:
        server = server_raw

    url = (
        f"mssql+pyodbc://{uid}:{pwd}@{server}/{database}"
        f"?driver={driver.replace(' ', '+')}"
    )

    return create_engine(url)


# =========================
# HOME PAGE
# =========================

@app.get("/", response_class=HTMLResponse)
def home():

    engine = get_engine()

    query = """
    SELECT dataset_id, dataset_name, source_system, mapping_version
    FROM ctrl.dataset
    WHERE is_active = 1
    ORDER BY dataset_name
    """

    with engine.connect() as conn:
        rows = conn.execute(text(query)).mappings().all()

    table_rows = ""

    for r in rows:
        table_rows += f"""
        <tr>
            <td>{r['dataset_name']}</td>
            <td>{r['source_system']}</td>
            <td>{r['mapping_version']}</td>
            <td><a href="/dataset/{r['dataset_id']}">Open</a></td>
        </tr>
        """

    return f"""
    <html>
    <head>
        <style>
            body {{
                background:#0f172a;
                color:white;
                font-family:Arial;
                padding:40px;
            }}
            table {{
                width:100%;
                border-collapse:collapse;
            }}
            th, td {{
                padding:12px;
                border-bottom:1px solid #334155;
            }}
            a {{
                color:#38bdf8;
                text-decoration:none;
            }}
        </style>
    </head>
    <body>
        <h1>👁 OEIL Control Center</h1>
        <table>
            <tr>
                <th>Dataset</th>
                <th>Source</th>
                <th>Version</th>
                <th>Action</th>
            </tr>
            {table_rows}
        </table>
    </body>
    </html>
    """


# =========================
# DATASET PAGE
# =========================

@app.get("/dataset/{dataset_id}", response_class=HTMLResponse)
def dataset_page(dataset_id: int):

    return f"""
    <html>
    <head>
        <style>
            body {{
                background:#0f172a;
                color:white;
                font-family:Arial;
                padding:40px;
            }}
            button {{
                padding:10px 20px;
                margin-right:10px;
                border:none;
                border-radius:6px;
                cursor:pointer;
            }}
            .struct {{ background:#7c3aed; color:white; }}
            .back {{ background:#334155; color:white; }}
        </style>
    </head>
    <body>

        <h1>Dataset {dataset_id}</h1>

        <button class="struct" onclick="location.href='/struct/{dataset_id}'">
            🧬 Structural Mapping
        </button>

        <button class="back" onclick="location.href='/'">
            ⬅ Back
        </button>

    </body>
    </html>
    """


# =========================
# STRUCTURAL PAGE
# =========================

@app.get("/struct/{dataset_id}", response_class=HTMLResponse)
def struct_page(dataset_id: int):

    return f"""
    <html>
    <head>
        <style>
            body {{
                background:#0f172a;
                color:white;
                font-family:Arial;
                padding:40px;
            }}
            .box {{
                background:#1e293b;
                padding:20px;
                border-radius:10px;
                margin-bottom:20px;
            }}
            button {{
                padding:10px 20px;
                border:none;
                border-radius:6px;
                cursor:pointer;
                margin-right:10px;
            }}
            .preview {{ background:#2563eb; color:white; }}
            .update {{ background:#16a34a; color:white; }}
            pre {{
                background:black;
                padding:15px;
                border-radius:6px;
                overflow-x:auto;
            }}
        </style>
    </head>
    <body>

        <h1>Structural Manager – Dataset {dataset_id}</h1>

        <div class="box">
            <button class="preview" onclick="preview()">Preview Recalculate</button>
            <button class="update" id="updateBtn" onclick="update()">Confirm Update</button>
        </div>

        <div class="box">
            <h3>Status</h3>
            <div id="status"></div>
        </div>

        <div class="box">
            <h3>JSON Used For Hash</h3>
            <pre id="json"></pre>
        </div>

        <script>
            async function preview() {{
                const response = await fetch("/struct/{dataset_id}/preview");
                const data = await response.json();

                document.getElementById("json").textContent = data.json;

                let color = data.status === "MATCH" ? "#16a34a" : "#dc2626";

                document.getElementById("status").innerHTML =
                    "<b>DB Hash:</b> " + data.db_hash + "<br>" +
                    "<b>New Hash:</b> " + data.new_hash + "<br>" +
                    "<b>Status:</b> <span style='color:" + color + "'>" + data.status + "</span>";

                document.getElementById("updateBtn").disabled = (data.status === "MATCH");
            }}

            async function update() {{
                const response = await fetch("/struct/{dataset_id}/update", {{
                    method: "POST"
                }});
                const data = await response.json();
                alert("Updated to: " + data.new_hash);
                preview();
            }}

            window.onload = preview;
        </script>

    </body>
    </html>
    """


# =========================
# PREVIEW ROUTE
# =========================

@app.get("/struct/{dataset_id}/preview")
def preview_struct(dataset_id: int):

    engine = get_engine()

    dataset_query = """
    SELECT *
    FROM ctrl.dataset
    WHERE dataset_id = :dataset_id
    """

    columns_query = """
    SELECT *
    FROM ctrl.dataset_column
    WHERE dataset_id = :dataset_id
    ORDER BY ordinal
    """

    with engine.connect() as conn:
        dataset = conn.execute(text(dataset_query), {"dataset_id": dataset_id}).mappings().first()
        columns = conn.execute(text(columns_query), {"dataset_id": dataset_id}).mappings().all()

    payload = {
        "dataset": dataset["dataset_name"],
        "source_system": dataset["source_system"],
        "mapping_version": dataset["mapping_version"],
        "columns": []
    }

    for col in columns:
        payload["columns"].append({
            "ordinal": col["ordinal"],
            "name": col["column_name"],
            "type_source": col["type_source"],
            "type_sink": col["type_sink"],
            "nullable": bool(col["nullable"]),
            "is_key": bool(col["is_key"]),
            "key_ordinal": col["key_ordinal"],
            "is_tokenized": bool(col["is_tokenized"]),
            "normalization_rule": col["normalization_rule"],
            "is_control_excluded": bool(col["is_control_excluded"])
        })

    import json
    json_string = json.dumps(payload, separators=(",", ":"))

    new_hash = hashlib.sha256(json_string.encode("utf-16le")).hexdigest().upper()

    db_hash = dataset["structural_hash"]
    db_hash_hex = db_hash.hex().upper() if db_hash else None

    status = "MATCH" if db_hash_hex == new_hash else "DRIFT"

    return {
        "json": json_string,
        "new_hash": new_hash,
        "db_hash": db_hash_hex,
        "status": status
    }


# =========================
# UPDATE ROUTE
# =========================

@app.post("/struct/{dataset_id}/update")
def update_struct(dataset_id: int):

    preview = preview_struct(dataset_id)

    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(
            text("UPDATE ctrl.dataset SET structural_hash = :h WHERE dataset_id = :id"),
            {"h": bytes.fromhex(preview["new_hash"]), "id": dataset_id}
        )

    return {"new_hash": preview["new_hash"]}