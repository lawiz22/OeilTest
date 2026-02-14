import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "oeil.db"

SCHEMA_SQL = {
    "clients": """
        CREATE TABLE IF NOT EXISTS clients (
            client_id INTEGER,
            nom TEXT,
            prenom TEXT,
            client_type TEXT,
            pays TEXT,
            statut TEXT,
            date_effet TEXT
        );
    """,
    "accounts": """
        CREATE TABLE IF NOT EXISTS accounts (
            account_id INTEGER,
            client_id INTEGER,
            account_type TEXT,
            currency TEXT,
            balance REAL,
            open_date TEXT
        );
    """,
    "transactions": """
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER,
            account_id INTEGER,
            amount REAL,
            currency TEXT,
            transaction_ts TEXT,
            ingestion_date TEXT
        );
    """,
    "contracts": """
        CREATE TABLE IF NOT EXISTS contracts (
            contract_id INTEGER,
            client_id INTEGER,
            product_type TEXT,
            start_date TEXT,
            end_date TEXT,
            statut TEXT
        );
    """
}

def ensure_schema():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for ddl in SCHEMA_SQL.values():
        cur.execute(ddl)

    conn.commit()
    conn.close()

    print(f"[OK] SQLite schema ensured at {DB_PATH}")
