import csv
import json
import random
import sqlite3
import pyodbc
import hashlib
from pathlib import Path
from datetime import datetime
from faker import Faker

# =====================================================
# GLOBAL CONFIG
# =====================================================
fake = Faker("fr_CA")

BASE_BRONZE = Path("output/bronze")
SQLITE_DB = Path("oeil.db")

# =====================================================
# VARIANCE (CTRL MISMATCH)
# =====================================================
VARIANCE_MODE = "RANDOM"
VARIANCE_CHANCE = 0
VARIANCE_MAX_PCT = 0.22

# =====================================================
# HASH CONFIG (L’ŒIL — OFFICIEL)
# =====================================================
HASH_VERSION = 1

# =====================================================
# AZURE SQL CONFIG (CTRL INDEX)
# =====================================================
AZURE_SQL_CONN_STR = (
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=tcp:testbanque.database.windows.net,1433;"
    "Database=testbanque;"
    "Uid=oeil_ctrl_login;"
    "Pwd=Mabellefee!2222;"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
)

# =====================================================
# SQLITE HELPERS
# =====================================================
def insert_rows_sqlite(table, rows):
    if not rows:
        return

    conn = sqlite3.connect(SQLITE_DB)
    cur = conn.cursor()

    columns = list(rows[0].keys())
    placeholders = ",".join(["?"] * len(columns))
    col_list = ",".join(columns)

    sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"
    cur.executemany(
        sql,
        [tuple(row[col] for col in columns) for row in rows]
    )

    conn.commit()
    conn.close()

# =====================================================
# AZURE SQL CTRL INDEX
# =====================================================
def insert_ctrl_index_sql(ctrl_id, dataset, ctrl_path):
    conn = pyodbc.connect(AZURE_SQL_CONN_STR)
    cur = conn.cursor()

    cur.execute("""
        MERGE dbo.ctrl_file_index AS tgt
        USING (SELECT ? AS ctrl_id) src
        ON tgt.ctrl_id = src.ctrl_id
        WHEN NOT MATCHED THEN
            INSERT (
                ctrl_id,
                dataset,
                ctrl_path,
                created_ts,
                processed_flag
            )
            VALUES (
                ?, ?, ?, SYSUTCDATETIME(), 0
            );
    """, (
        ctrl_id,
        ctrl_id,
        dataset,
        ctrl_path
    ))

    conn.commit()
    conn.close()

# =====================================================
# PERIODICITY LOGIC
# =====================================================
def should_run(date, period, qs_days=None, weekly_day=None):
    if period == "Q":
        return True
    if period == "QS":
        return date.weekday() in qs_days
    if period == "H":
        return date.weekday() == weekly_day
    if period == "M":
        return date.day == 1
    return False

# =====================================================
# DATA GENERATORS
# =====================================================
def gen_clients(rows, eff_date):
    for _ in range(rows):
        yield {
            "client_id": random.randint(100000, 999999),
            "nom": fake.last_name(),
            "prenom": fake.first_name(),
            "pays": fake.country_code(),
            "date_eff": eff_date.isoformat()
        }

def gen_accounts(rows, eff_date):
    for _ in range(rows):
        yield {
            "account_id": random.randint(1_000_000, 9_999_999),
            "client_id": random.randint(100000, 999999),
            "account_type": random.choice(["CHEQUE", "EPARGNE"]),
            "currency": random.choice(["CAD", "USD"]),
            "date_eff": eff_date.isoformat()
        }

def gen_transactions(rows, eff_date):
    for _ in range(rows):
        yield {
            "transaction_id": random.randint(1_000_000, 9_999_999),
            "client_id": random.randint(100000, 999999),
            "account_id": random.randint(1_000_000, 9_999_999),
            "amount": round(random.uniform(-5000, 5000), 2),
            "currency": random.choice(["CAD", "USD"]),
            "transaction_ts": eff_date.isoformat()
        }

def gen_contracts(rows, eff_date):
    for _ in range(rows):
        yield {
            "contract_id": random.randint(10000, 99999),
            "client_id": random.randint(100000, 999999),
            "contract_type": random.choice(["PRET", "HYPOTHEQUE"]),
            "status": random.choice(["ACTIF", "FERME"]),
            "date_eff": eff_date.isoformat()
        }

# =====================================================
# SCHEMA REGISTRY
# =====================================================
SCHEMAS = {
    "clients": {
        "fields": ["client_id", "nom", "prenom", "pays", "date_eff"],
        "generator": gen_clients
    },
    "accounts": {
        "fields": ["account_id", "client_id", "account_type", "currency", "date_eff"],
        "generator": gen_accounts
    },
    "transactions": {
        "fields": [
            "transaction_id", "client_id", "account_id",
            "amount", "currency", "transaction_ts"
        ],
        "generator": gen_transactions
    },
    "contracts": {
        "fields": ["contract_id", "client_id", "contract_type", "status", "date_eff"],
        "generator": gen_contracts
    }
}

# =====================================================
# CORE EXTRACTION FUNCTION
# =====================================================
def extract_dataset(
    table,
    extraction_date,
    period,
    rows,
    qs_days=None,
    weekly_day=None,
    source_system="LEGACY_DS"
):
    if table not in SCHEMAS:
        raise ValueError(f"Unknown table: {table}")

    if not should_run(extraction_date, period, qs_days, weekly_day):
        return

    schema = SCHEMAS[table]
    fields = schema["fields"]
    generator = schema["generator"]

    base_path = (
        BASE_BRONZE
        / table
        / f"period={period}"
        / f"year={extraction_date.year}"
        / f"month={extraction_date.month:02d}"
        / f"day={extraction_date.day:02d}"
    )

    data_dir = base_path / "data"
    ctrl_dir = base_path / "ctrl"
    data_dir.mkdir(parents=True, exist_ok=True)
    ctrl_dir.mkdir(parents=True, exist_ok=True)

    date_str = extraction_date.date().isoformat()
    csv_file = data_dir / f"{table}_{date_str}_{period}.csv"
    ctrl_file = ctrl_dir / f"{table}_{date_str}_{period}.ctrl.json"

    generated_rows = []

    with open(csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in generator(rows, extraction_date):
            writer.writerow(row)
            generated_rows.append(row)

    insert_rows_sqlite(table, generated_rows)

    # =================================================
    # VARIANCE
    # =================================================
    actual_rows = len(generated_rows)
    expected_rows = actual_rows
    variance_applied = False

    if VARIANCE_MODE == "RANDOM" and random.random() < VARIANCE_CHANCE:
        sign = random.choice([-1, 1])
        delta_pct = random.uniform(0, VARIANCE_MAX_PCT)
        delta = int(actual_rows * delta_pct * sign)
        expected_rows = max(0, actual_rows + delta)
        variance_applied = True

    # =================================================
    # CANONICAL PAYLOAD + HASH
    # =================================================
    canonical_payload = f"{table}|{period}|{date_str}|{expected_rows}"
    payload_hash = hashlib.sha256(
        canonical_payload.encode("utf-8")
    ).hexdigest()

    # =================================================
    # CTRL FILE
    # =================================================
    ctrl = {
        "ctrl_id": f"{table}_{date_str}_{period}",
        "dataset": table,
        "periodicity": period,
        "extraction_date": date_str,

        "expected_rows": expected_rows,
        "actual_rows": actual_rows,
        "variance_applied": variance_applied,
        "variance_delta": expected_rows - actual_rows,

        "payload_canonical": canonical_payload,
        "payload_hash_sha256": payload_hash,
        "payload_hash_version": HASH_VERSION,

        "source_system": source_system,
        "created_ts": datetime.utcnow().isoformat(),

        "pipeline_name": None,
        "trigger_name": None,
        "pipeline_run_id": None,

        "status": "CREATED",
        "start_ts": None,
        "end_ts": None
    }

    with open(ctrl_file, "w", encoding="utf-8") as f:
        json.dump(ctrl, f, indent=2)

    ctrl_path = (
        f"{table}/period={period}/"
        f"year={extraction_date.year}/"
        f"month={extraction_date.month:02d}/"
        f"day={extraction_date.day:02d}/"
        f"ctrl/{ctrl_file.name}"
    )

    insert_ctrl_index_sql(
        ctrl_id=ctrl["ctrl_id"],
        dataset=table,
        ctrl_path=ctrl_path
    )

    print(
        f"✅ {table} | {date_str} | {period} | "
        f"actual={actual_rows} expected={expected_rows} "
        f"{'⚠️ VARIANCE' if variance_applied else 'OK'}"
    )
