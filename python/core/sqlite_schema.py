import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "oeil.db"

SCHEMA_SQL = {
    "clients": """
        CREATE TABLE IF NOT EXISTS clients (
            client_id INTEGER,
            nom TEXT,
            prenom TEXT,
            pays TEXT,
            date_eff TEXT
        );
    """,
    "accounts": """
        CREATE TABLE IF NOT EXISTS accounts (
            account_id INTEGER,
            client_id INTEGER,
            account_type TEXT,
            currency TEXT,
            date_eff TEXT
        );
    """,
    "transactions": """
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER,
            client_id INTEGER,
            account_id INTEGER,
            amount REAL,
            currency TEXT,
            transaction_ts TEXT
        );
    """,
    "contracts": """
        CREATE TABLE IF NOT EXISTS contracts (
            contract_id INTEGER,
            client_id INTEGER,
            contract_type TEXT,
            status TEXT,
            date_eff TEXT
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

    print(f"✅ SQLite schema ensured at {DB_PATH}")
