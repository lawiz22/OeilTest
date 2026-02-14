import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "oeil.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def insert_rows(table, rows):
    if not rows:
        return

    conn = get_connection()
    cur = conn.cursor()

    columns = rows[0].keys()
    col_list = ",".join(columns)
    placeholders = ",".join(["?"] * len(columns))

    sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})"

    cur.executemany(
        sql,
        [tuple(row.values()) for row in rows]
    )

    conn.commit()
    conn.close()
