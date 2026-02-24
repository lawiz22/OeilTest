# modules/structural_routes.py

import hashlib
import json
import sqlite3
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from .db import get_engine
from .structural_service import preview_structural
from .layout import render
from python.core.sqlite_schema import DB_PATH

router = APIRouter()


CANONICAL_TYPE_PROFILE = {
    "clients": {
        "client_id": {"type_source": "INT", "type_sink": "INT", "normalization_rule": None},
        "nom": {"type_source": "VARCHAR(120)", "type_sink": "VARCHAR(120)", "normalization_rule": "TRIM"},
        "prenom": {"type_source": "VARCHAR(120)", "type_sink": "VARCHAR(120)", "normalization_rule": None},
        "client_type": {"type_source": "VARCHAR(50)", "type_sink": "VARCHAR(50)", "normalization_rule": None},
        "pays": {"type_source": "VARCHAR(50)", "type_sink": "VARCHAR(50)", "normalization_rule": None},
        "statut": {"type_source": "VARCHAR(50)", "type_sink": "VARCHAR(50)", "normalization_rule": None},
        "date_effet": {"type_source": "VARCHAR(10)", "type_sink": "DATE", "normalization_rule": None},
    },
    "accounts": {
        "account_id": {"type_source": "INT", "type_sink": "INT", "normalization_rule": None},
        "client_id": {"type_source": "INT", "type_sink": "INT", "normalization_rule": None},
        "account_type": {"type_source": "VARCHAR(20)", "type_sink": "VARCHAR(20)", "normalization_rule": None},
        "currency": {"type_source": "CHAR(3)", "type_sink": "CHAR(3)", "normalization_rule": None},
        "balance": {"type_source": "DECIMAL(18,2)", "type_sink": "DECIMAL(18,2)", "normalization_rule": None},
        "open_date": {"type_source": "DATE", "type_sink": "DATE", "normalization_rule": None},
    },
    "transactions": {
        "transaction_id": {"type_source": "BIGINT", "type_sink": "BIGINT", "normalization_rule": None},
        "account_id": {"type_source": "INT", "type_sink": "INT", "normalization_rule": None},
        "amount": {"type_source": "DECIMAL(18,2)", "type_sink": "DECIMAL(18,2)", "normalization_rule": None},
        "currency": {"type_source": "CHAR(3)", "type_sink": "CHAR(3)", "normalization_rule": None},
        "transaction_ts": {"type_source": "DATETIME2", "type_sink": "DATETIME2", "normalization_rule": None},
        "ingestion_date": {"type_source": "DATE", "type_sink": "DATE", "normalization_rule": None},
    },
    "contracts": {
        "contract_id": {"type_source": "INT", "type_sink": "INT", "normalization_rule": None},
        "client_id": {"type_source": "INT", "type_sink": "INT", "normalization_rule": None},
        "product_type": {"type_source": "VARCHAR(30)", "type_sink": "VARCHAR(30)", "normalization_rule": None},
        "start_date": {"type_source": "DATE", "type_sink": "DATE", "normalization_rule": None},
        "end_date": {"type_source": "DATE", "type_sink": "DATE", "normalization_rule": None},
        "statut": {"type_source": "VARCHAR(20)", "type_sink": "VARCHAR(20)", "normalization_rule": None},
    },
}


def _is_clients_dataset(dataset_name: str) -> bool:
    return (dataset_name or "").strip().lower() == "clients"


def _resolve_dataset_ref(conn, dataset_ref: int):
    dataset = conn.execute(
        text("""
            SELECT TOP 1
                   d.dataset_id,
                   d.dataset_name,
                   d.source_system,
                   d.mapping_version,
                   d.structural_hash
            FROM ctrl.dataset d
            INNER JOIN vigie_policy_dataset p
                ON p.dataset_name = d.dataset_name
            WHERE p.policy_dataset_id = :dataset_ref
            ORDER BY CASE WHEN p.environment = 'DEV' THEN 0 ELSE 1 END, p.policy_dataset_id
        """),
        {"dataset_ref": dataset_ref}
    ).mappings().first()

    if dataset:
        return dataset

    dataset = conn.execute(
        text("""
            SELECT dataset_id,
                   dataset_name,
                   source_system,
                   mapping_version,
                   structural_hash
            FROM ctrl.dataset
            WHERE dataset_id = :dataset_ref
        """),
        {"dataset_ref": dataset_ref}
    ).mappings().first()

    if dataset:
        return dataset
    return None


def _resolve_policy_dataset_id(conn, dataset_name: str):
    row = conn.execute(
        text("""
            SELECT TOP 1 policy_dataset_id
            FROM vigie_policy_dataset
            WHERE dataset_name = :dataset_name
            ORDER BY CASE WHEN environment = 'DEV' THEN 0 ELSE 1 END, policy_dataset_id
        """),
        {"dataset_name": dataset_name}
    ).mappings().first()
    return row["policy_dataset_id"] if row else None


def _resolve_policy_dataset_id_by_env(conn, dataset_name: str, environment: str):
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


def _sqlite_columns(table_name: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def _suggest_sink_type(column_name: str, sqlite_type: str) -> str:
    name = (column_name or "").strip().lower()
    sql_type = (sqlite_type or "").strip().upper()

    if name.endswith("_id"):
        return "BIGINT"
    if name.endswith("_date"):
        return "DATE"
    if name.endswith("_ts") or name.endswith("_timestamp"):
        return "DATETIME2"
    if any(token in name for token in ["amount", "balance", "cost", "price", "rate"]):
        return "DECIMAL(18,2)"
    if name in {"currency"}:
        return "CHAR(3)"
    if name in {"status", "statut", "client_type", "account_type", "product_type", "pays"}:
        return "NVARCHAR(50)"

    if "INT" in sql_type:
        return "INT"
    if any(token in sql_type for token in ["REAL", "NUM", "DEC", "FLOAT", "DOUBLE"]):
        return "DECIMAL(18,2)"
    if any(token in sql_type for token in ["DATE", "TIME"]):
        return "DATETIME2"

    return "NVARCHAR(255)"


def _suggest_source_type(column_name: str, sqlite_type: str) -> str:
    name = (column_name or "").strip().lower()
    sql_type = (sqlite_type or "").strip().upper()

    if name.endswith("_id"):
        return "INT"
    if name.endswith("_date"):
        return "DATE"
    if name.endswith("_ts") or name.endswith("_timestamp"):
        return "DATETIME2"
    if any(token in name for token in ["amount", "balance", "cost", "price", "rate"]):
        return "DECIMAL(18,2)"
    if name in {"currency"}:
        return "CHAR(3)"
    if name in {"status", "statut", "client_type", "account_type", "product_type", "pays"}:
        return "VARCHAR(50)"

    if "INT" in sql_type:
        return "INT"
    if any(token in sql_type for token in ["REAL", "NUM", "DEC", "FLOAT", "DOUBLE"]):
        return "DECIMAL(18,2)"
    if any(token in sql_type for token in ["DATE", "TIME"]):
        return "DATETIME2"

    return "VARCHAR(255)"


def _canonical_types(dataset_name: str, column_name: str, sqlite_type: str):
    dataset_key = (dataset_name or "").strip().lower()
    column_key = (column_name or "").strip().lower()

    profile = CANONICAL_TYPE_PROFILE.get(dataset_key, {}).get(column_key)
    if profile:
        return {
            "type_source": profile["type_source"],
            "type_sink": profile["type_sink"],
            "normalization_rule": profile.get("normalization_rule"),
        }

    return {
        "type_source": _suggest_source_type(column_name, sqlite_type),
        "type_sink": _suggest_sink_type(column_name, sqlite_type),
        "normalization_rule": None,
    }


def _build_canonical_contract(conn, dataset_id: int):
    dataset = conn.execute(
        text("""
            SELECT dataset_id,
                   dataset_name,
                   source_system,
                   mapping_version
            FROM ctrl.dataset
            WHERE dataset_id = :dataset_id
        """),
        {"dataset_id": dataset_id}
    ).mappings().first()

    if not dataset:
        return None

    columns = conn.execute(
        text("""
            SELECT
                ordinal,
                column_name,
                type_source,
                type_sink,
                nullable,
                is_key,
                key_ordinal,
                is_tokenized,
                normalization_rule,
                is_control_excluded
            FROM ctrl.dataset_column
            WHERE dataset_id = :dataset_id
            ORDER BY ordinal
        """),
        {"dataset_id": dataset_id}
    ).mappings().all()

    contract = {
        "dataset": dataset["dataset_name"],
        "source_system": dataset["source_system"],
        "mapping_version": dataset["mapping_version"],
        "columns": [],
    }

    for col in columns:
        contract["columns"].append(
            {
                "ordinal": int(col["ordinal"]),
                "name": col["column_name"],
                "type_source": col["type_source"],
                "type_sink": col["type_sink"],
                "nullable": bool(col["nullable"]),
                "is_key": bool(col["is_key"]),
                "key_ordinal": int(col["key_ordinal"]) if col["key_ordinal"] is not None else None,
                "is_tokenized": bool(col["is_tokenized"]),
                "normalization_rule": col["normalization_rule"],
                "is_control_excluded": bool(col["is_control_excluded"]),
            }
        )

    canonical_json = json.dumps(contract, ensure_ascii=False, separators=(",", ":"))
    canonical_hash = hashlib.sha256(canonical_json.encode("utf-16le")).hexdigest().upper()

    return {
        "contract": contract,
        "canonical_json": canonical_json,
        "canonical_hash": canonical_hash,
    }


def _build_synapse_gate_contract(conn, dataset_name: str):
    row = conn.execute(
        text("""
            DECLARE @json NVARCHAR(MAX);

            SELECT @json =
            (
                SELECT
                    c.ordinal,
                    c.column_name AS [name],
                    CASE
                        WHEN c.type_sink = 'INT' THEN 'int'
                        WHEN c.type_sink = 'BIGINT' THEN 'bigint'
                        WHEN c.type_sink = 'DATE' THEN 'date'
                        WHEN c.type_sink IN ('DATETIME','DATETIME2') THEN 'datetime2'
                        WHEN c.type_sink LIKE 'VARCHAR%' THEN 'varchar'
                        WHEN c.type_sink LIKE 'CHAR%' THEN 'char'
                        WHEN c.type_sink LIKE 'DECIMAL%' THEN 'decimal'
                        ELSE LOWER(c.type_sink)
                    END AS type_detected
                FROM ctrl.dataset_column c
                JOIN ctrl.dataset d
                    ON c.dataset_id = d.dataset_id
                WHERE d.dataset_name = :dataset_name
                ORDER BY c.ordinal
                FOR JSON PATH
            );

            SELECT
                @json AS synapse_contract_json,
                CONVERT(VARCHAR(64), HASHBYTES('SHA2_256', @json), 2) AS synapse_contract_hash;
        """),
        {"dataset_name": dataset_name}
    ).mappings().first()

    return {
        "synapse_contract_json": row["synapse_contract_json"],
        "synapse_contract_hash": row["synapse_contract_hash"],
    }


def _refresh_structural_hash(conn, dataset_id: int, dataset_name: str):
    try:
        conn.execute(
            text("EXEC ctrl.SP_REFRESH_STRUCTURAL_HASH @dataset_name = :dataset_name"),
            {"dataset_name": dataset_name}
        )
        return "SP"
    except ProgrammingError as exc:
        message = str(exc).lower()
        if "execute permission was denied" not in message:
            raise

    conn.execute(
        text("""
            DECLARE @json NVARCHAR(MAX);

            SELECT @json =
            (
                SELECT
                    d.dataset_name AS [dataset],
                    d.source_system,
                    d.mapping_version,
                    (
                        SELECT
                            c.ordinal,
                            c.column_name AS [name],
                            c.type_source,
                            c.type_sink,
                            c.nullable,
                            c.is_key,
                            c.key_ordinal,
                            c.is_tokenized,
                            c.normalization_rule,
                            c.is_control_excluded
                        FROM ctrl.dataset_column c
                        WHERE c.dataset_id = d.dataset_id
                        ORDER BY c.ordinal
                        FOR JSON PATH
                    ) AS columns
                FROM ctrl.dataset d
                WHERE d.dataset_id = :dataset_id
                FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
            );

            UPDATE ctrl.dataset
            SET structural_hash = HASHBYTES('SHA2_256', @json)
            WHERE dataset_id = :dataset_id;
        """),
        {
            "dataset_id": dataset_id,
        }
    )
    return "INLINE"


# ==========================================================
# STRUCTURAL PAGE (HTML)
# ==========================================================

@router.get("/struct/{dataset_id}", response_class=HTMLResponse)
def structural_page(request: Request, dataset_id: int):

    engine = get_engine()

    with engine.connect() as conn:
        dataset = _resolve_dataset_ref(conn, dataset_id)
        policy_dataset_id = _resolve_policy_dataset_id(conn, dataset["dataset_name"]) if dataset else None
        policy_dataset = conn.execute(
            text("""
                SELECT environment
                FROM vigie_policy_dataset
                WHERE policy_dataset_id = :policy_dataset_id
            """),
            {"policy_dataset_id": policy_dataset_id}
        ).mappings().first() if policy_dataset_id else None

    if not dataset:
        return HTMLResponse("<h2>Dataset not found</h2>", status_code=404)

    return render(
        request,
        "structural.html",
        context={
            "dataset": dataset,
            "is_clients_locked": _is_clients_dataset(dataset["dataset_name"]),
        },
        dataset_id=dataset["dataset_id"],
        policy_dataset_id=policy_dataset_id,
        struct_dataset_id=dataset["dataset_id"],
        route_dataset_name=dataset["dataset_name"],
        route_environment=policy_dataset["environment"] if policy_dataset else None,
        active_tab="structural"
    )


# ==========================================================
# STRUCTURAL PREVIEW API
# ==========================================================

@router.get("/struct/{dataset_id}/preview")
def structural_preview(dataset_id: int):
    engine = get_engine()

    with engine.connect() as conn:
        dataset = _resolve_dataset_ref(conn, dataset_id)

    if not dataset:
        return JSONResponse({"error": "Dataset not found"}, status_code=404)

    return preview_structural(dataset["dataset_id"])


@router.get("/struct/{dataset_id}/canonical-preview")
def structural_canonical_preview(dataset_id: int):
    engine = get_engine()

    with engine.connect() as conn:
        dataset = _resolve_dataset_ref(conn, dataset_id)
        if not dataset:
            return JSONResponse({"error": "Dataset not found"}, status_code=404)

        payload = _build_canonical_contract(conn, dataset["dataset_id"])
        synapse_gate = _build_synapse_gate_contract(conn, dataset["dataset_name"])

    if payload is None:
        return JSONResponse({"error": "Dataset not found"}, status_code=404)

    return {
        "dataset_id": dataset["dataset_id"],
        "dataset_name": dataset["dataset_name"],
        "canonical_hash": payload["canonical_hash"],
        "synapse_contract_json": synapse_gate["synapse_contract_json"],
        "synapse_contract_hash": synapse_gate["synapse_contract_hash"],
        "contract": payload["contract"],
    }


# ==========================================================
# STRUCTURAL UPDATE API
# ==========================================================

@router.post("/struct/{dataset_id}/update")
def structural_update(dataset_id: int):

    engine = get_engine()

    with engine.connect() as conn:
        dataset = _resolve_dataset_ref(conn, dataset_id)

    if not dataset:
        return JSONResponse({"error": "Dataset not found"}, status_code=404)

    if _is_clients_dataset(dataset["dataset_name"]):
        return JSONResponse({"error": "clients dataset is locked from structural updates"}, status_code=403)

    preview = preview_structural(dataset["dataset_id"])

    if preview["status"] == "MATCH":
        return {
            "status": "NO_CHANGE",
            "message": "Structural hash already up to date",
            "hash": preview["new_hash"]
        }

    with engine.begin() as conn:
        _refresh_structural_hash(conn, dataset["dataset_id"], dataset["dataset_name"])

    refreshed = preview_structural(dataset["dataset_id"])

    return {
        "status": "UPDATED",
        "new_hash": refreshed["new_hash"]
    }


@router.get("/struct/sqlite-tables")
def list_sqlite_tables():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    rows = cur.fetchall()
    conn.close()

    return {"tables": [r["name"] for r in rows]}


@router.get("/struct/{dataset_id}/sqlite-detect")
def detect_sqlite_structure(dataset_id: int):

    engine = get_engine()
    with engine.connect() as conn:
        dataset = _resolve_dataset_ref(conn, dataset_id)

    if not dataset:
        return JSONResponse({"error": "Dataset not found"}, status_code=404)

    columns = _sqlite_columns(dataset["dataset_name"])
    if not columns:
        return JSONResponse({"error": f"No SQLite table found for {dataset['dataset_name']}"}, status_code=404)

    return {
        "dataset_id": dataset["dataset_id"],
        "dataset_name": dataset["dataset_name"],
        "columns": columns,
    }


@router.post("/struct/{dataset_id}/import-sqlite")
def import_sqlite_structure(dataset_id: int):

    engine = get_engine()

    with engine.connect() as conn:
        dataset = _resolve_dataset_ref(conn, dataset_id)

    if not dataset:
        return JSONResponse({"error": "Dataset not found"}, status_code=404)

    if _is_clients_dataset(dataset["dataset_name"]):
        return JSONResponse({"error": "clients dataset is locked from structural writes"}, status_code=403)

    sqlite_columns = _sqlite_columns(dataset["dataset_name"])
    if not sqlite_columns:
        return JSONResponse({"error": f"No SQLite table found for {dataset['dataset_name']}"}, status_code=404)

    with engine.begin() as conn:
        existing = conn.execute(
            text("SELECT column_name FROM ctrl.dataset_column WHERE dataset_id = :dataset_id"),
            {"dataset_id": dataset["dataset_id"]}
        ).mappings().all()

        existing_names = {r["column_name"].lower() for r in existing}

        inserted = 0
        for col in sqlite_columns:
            col_name = (col.get("name") or "").strip()
            if not col_name or col_name.lower() in existing_names:
                continue

            canonical = _canonical_types(dataset["dataset_name"], col_name, (col.get("type") or "TEXT"))

            conn.execute(
                text("""
                    INSERT INTO ctrl.dataset_column
                    (
                        dataset_id,
                        ordinal,
                        column_name,
                        type_source,
                        type_sink,
                        nullable,
                        is_key,
                        key_ordinal,
                        is_tokenized,
                        normalization_rule,
                        is_control_excluded
                    )
                    VALUES
                    (
                        :dataset_id,
                        :ordinal,
                        :column_name,
                        :type_source,
                        :type_sink,
                        :nullable,
                        :is_key,
                        :key_ordinal,
                        0,
                        :normalization_rule,
                        0
                    )
                """),
                {
                    "dataset_id": dataset["dataset_id"],
                    "ordinal": int(col.get("cid", 0)) + 1,
                    "column_name": col_name,
                    "type_source": canonical["type_source"],
                    "type_sink": canonical["type_sink"],
                    "nullable": 0 if int(col.get("notnull", 0)) == 1 else 1,
                    "is_key": 1 if int(col.get("pk", 0)) > 0 else 0,
                    "key_ordinal": int(col.get("pk", 0)) if int(col.get("pk", 0)) > 0 else None,
                    "normalization_rule": canonical["normalization_rule"],
                }
            )
            inserted += 1

        _refresh_structural_hash(conn, dataset["dataset_id"], dataset["dataset_name"])

    return {
        "status": "IMPORTED",
        "dataset_name": dataset["dataset_name"],
        "inserted_columns": inserted,
    }


@router.post("/struct/{dataset_id}/columns/add")
async def add_structural_column(dataset_id: int, request: Request):

    payload = await request.json()

    column_name = (payload.get("column_name") or "").strip()
    type_source = (payload.get("type_source") or "TEXT").strip()
    type_sink = (payload.get("type_sink") or type_source).strip()
    nullable = 1 if payload.get("nullable", True) else 0
    is_key = 1 if payload.get("is_key", False) else 0
    key_ordinal = payload.get("key_ordinal")
    is_tokenized = 1 if payload.get("is_tokenized", False) else 0
    normalization_rule = (payload.get("normalization_rule") or "").strip() or None
    is_control_excluded = 1 if payload.get("is_control_excluded", False) else 0

    if not column_name:
        return JSONResponse({"error": "column_name is required"}, status_code=400)

    engine = get_engine()

    with engine.connect() as conn:
        dataset = _resolve_dataset_ref(conn, dataset_id)

    if not dataset:
        return JSONResponse({"error": "Dataset not found"}, status_code=404)

    if _is_clients_dataset(dataset["dataset_name"]):
        return JSONResponse({"error": "clients dataset is locked from structural writes"}, status_code=403)

    with engine.begin() as conn:
        exists = conn.execute(
            text("""
                SELECT TOP 1 1
                FROM ctrl.dataset_column
                WHERE dataset_id = :dataset_id
                  AND LOWER(column_name) = LOWER(:column_name)
            """),
            {"dataset_id": dataset_id, "column_name": column_name}
        ).first()

        if exists:
            return JSONResponse({"error": "Column already exists for this dataset"}, status_code=409)

        max_ordinal = conn.execute(
            text("SELECT ISNULL(MAX(ordinal), 0) FROM ctrl.dataset_column WHERE dataset_id = :dataset_id"),
            {"dataset_id": dataset["dataset_id"]}
        ).scalar_one()

        conn.execute(
            text("""
                INSERT INTO ctrl.dataset_column
                (
                    dataset_id,
                    ordinal,
                    column_name,
                    type_source,
                    type_sink,
                    nullable,
                    is_key,
                    key_ordinal,
                    is_tokenized,
                    normalization_rule,
                    is_control_excluded
                )
                VALUES
                (
                    :dataset_id,
                    :ordinal,
                    :column_name,
                    :type_source,
                    :type_sink,
                    :nullable,
                    :is_key,
                    :key_ordinal,
                    :is_tokenized,
                    :normalization_rule,
                    :is_control_excluded
                )
            """),
            {
                "dataset_id": dataset["dataset_id"],
                "ordinal": int(max_ordinal) + 1,
                "column_name": column_name,
                "type_source": type_source,
                "type_sink": type_sink,
                "nullable": nullable,
                "is_key": is_key,
                "key_ordinal": key_ordinal if is_key else None,
                "is_tokenized": is_tokenized,
                "normalization_rule": normalization_rule,
                "is_control_excluded": is_control_excluded,
            }
        )

        _refresh_structural_hash(conn, dataset["dataset_id"], dataset["dataset_name"])

    return {"status": "COLUMN_ADDED", "column_name": column_name}


@router.post("/struct/{dataset_id}/apply-type-suggestions")
def apply_type_suggestions(dataset_id: int):

    engine = get_engine()

    with engine.connect() as conn:
        dataset = _resolve_dataset_ref(conn, dataset_id)

    if not dataset:
        return JSONResponse({"error": "Dataset not found"}, status_code=404)

    if _is_clients_dataset(dataset["dataset_name"]):
        return JSONResponse({"error": "clients dataset is locked from structural writes"}, status_code=403)

    sqlite_columns = _sqlite_columns(dataset["dataset_name"])
    sqlite_by_name = {
        (c.get("name") or "").strip().lower(): c
        for c in sqlite_columns
        if (c.get("name") or "").strip()
    }

    with engine.begin() as conn:
        db_columns = conn.execute(
            text("""
                SELECT column_name, type_source, type_sink, normalization_rule
                FROM ctrl.dataset_column
                WHERE dataset_id = :dataset_id
            """),
            {"dataset_id": dataset["dataset_id"]}
        ).mappings().all()

        updated = 0
        for db_col in db_columns:
            col_name = (db_col["column_name"] or "").strip()
            if not col_name:
                continue

            sqlite_meta = sqlite_by_name.get(col_name.lower())
            sqlite_type = (sqlite_meta.get("type") if sqlite_meta else db_col["type_source"] or "TEXT")
            canonical = _canonical_types(dataset["dataset_name"], col_name, sqlite_type)
            suggested_source = canonical["type_source"]
            suggested_sink = canonical["type_sink"]
            suggested_norm = canonical["normalization_rule"]

            same_source = (db_col["type_source"] or "").strip().upper() == suggested_source.upper()
            same_sink = (db_col["type_sink"] or "").strip().upper() == suggested_sink.upper()
            same_norm = (db_col["normalization_rule"] or "") == (suggested_norm or "")

            if same_source and same_sink and same_norm:
                continue

            conn.execute(
                text("""
                    UPDATE ctrl.dataset_column
                    SET type_source = :type_source,
                        type_sink = :type_sink,
                        normalization_rule = :normalization_rule
                    WHERE dataset_id = :dataset_id
                      AND column_name = :column_name
                """),
                {
                    "type_source": suggested_source,
                    "type_sink": suggested_sink,
                    "normalization_rule": suggested_norm,
                    "dataset_id": dataset["dataset_id"],
                    "column_name": col_name,
                }
            )
            updated += 1

        _refresh_structural_hash(conn, dataset["dataset_id"], dataset["dataset_name"])

    return {
        "status": "TYPE_SUGGESTIONS_APPLIED",
        "dataset_name": dataset["dataset_name"],
        "updated_columns": updated,
    }


@router.post("/struct/tables/create-from-sqlite")
async def create_structural_dataset_from_sqlite(request: Request):

    payload = await request.json()
    dataset_name = (payload.get("dataset_name") or "").strip()

    if not dataset_name:
        return JSONResponse({"error": "dataset_name is required"}, status_code=400)

    if _is_clients_dataset(dataset_name):
        return JSONResponse({"error": "clients dataset is locked from structural writes"}, status_code=403)

    sqlite_columns = _sqlite_columns(dataset_name)
    if not sqlite_columns:
        return JSONResponse({"error": f"No SQLite table found for {dataset_name}"}, status_code=404)

    engine = get_engine()

    with engine.begin() as conn:
        dataset = conn.execute(
            text("SELECT dataset_id, dataset_name FROM ctrl.dataset WHERE dataset_name = :dataset_name"),
            {"dataset_name": dataset_name}
        ).mappings().first()

        if dataset is None:
            inserted_row = conn.execute(
                text("""
                    INSERT INTO ctrl.dataset
                    (
                        dataset_name,
                        source_system,
                        mapping_version,
                        is_active
                    )
                    OUTPUT INSERTED.dataset_id
                    VALUES
                    (
                        :dataset_name,
                        'SQLITE',
                        '1.0.0',
                        1
                    );
                """),
                {"dataset_name": dataset_name}
            ).first()

            if inserted_row is None:
                return JSONResponse({"error": "Failed to create dataset"}, status_code=500)

            dataset_id = inserted_row[0]
        else:
            dataset_id = dataset["dataset_id"]

        existing = conn.execute(
            text("SELECT column_name FROM ctrl.dataset_column WHERE dataset_id = :dataset_id"),
            {"dataset_id": dataset_id}
        ).mappings().all()
        existing_names = {r["column_name"].lower() for r in existing}

        inserted = 0
        for col in sqlite_columns:
            col_name = (col.get("name") or "").strip()
            if not col_name or col_name.lower() in existing_names:
                continue

            canonical = _canonical_types(dataset_name, col_name, (col.get("type") or "TEXT"))

            conn.execute(
                text("""
                    INSERT INTO ctrl.dataset_column
                    (
                        dataset_id,
                        ordinal,
                        column_name,
                        type_source,
                        type_sink,
                        nullable,
                        is_key,
                        key_ordinal,
                        is_tokenized,
                        normalization_rule,
                        is_control_excluded
                    )
                    VALUES
                    (
                        :dataset_id,
                        :ordinal,
                        :column_name,
                        :type_source,
                        :type_sink,
                        :nullable,
                        :is_key,
                        :key_ordinal,
                        0,
                        :normalization_rule,
                        0
                    )
                """),
                {
                    "dataset_id": dataset_id,
                    "ordinal": int(col.get("cid", 0)) + 1,
                    "column_name": col_name,
                    "type_source": canonical["type_source"],
                    "type_sink": canonical["type_sink"],
                    "nullable": 0 if int(col.get("notnull", 0)) == 1 else 1,
                    "is_key": 1 if int(col.get("pk", 0)) > 0 else 0,
                    "key_ordinal": int(col.get("pk", 0)) if int(col.get("pk", 0)) > 0 else None,
                    "normalization_rule": canonical["normalization_rule"],
                }
            )
            inserted += 1

        _refresh_structural_hash(conn, dataset_id, dataset_name)

    return {
        "status": "DATASET_READY",
        "dataset_name": dataset_name,
        "dataset_id": dataset_id,
        "inserted_columns": inserted,
    }


@router.get("/struct/{dataset_name}/{environment}", response_class=HTMLResponse)
def structural_page_by_dataset_env(request: Request, dataset_name: str, environment: str):

    engine = get_engine()
    with engine.connect() as conn:
        policy_dataset_id = _resolve_policy_dataset_id_by_env(conn, dataset_name, environment)

    if policy_dataset_id is None:
        return HTMLResponse("<h2>Structural dataset not found for dataset/environment</h2>", status_code=404)

    return structural_page(request, policy_dataset_id)