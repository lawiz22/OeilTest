import sys
import shutil
import sqlite3
from pathlib import Path

# Ensure project root is on sys.path so "python.core.*" imports work
# when running this file directly (e.g. VS Code Run button)
_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from python.core.sqlite_schema import SCHEMA_SQL, DB_PATH

# ==========================================
# PATHS
# ==========================================
BRONZE_PATH = Path("output/bronze")

# ==========================================
# 1️⃣ FLUSH FILE SYSTEM (CSV + CTRL)
# ==========================================
def flush_bronze_files():
    if BRONZE_PATH.exists():
        shutil.rmtree(BRONZE_PATH)
        print(f"[OK] Bronze folder flushed: {BRONZE_PATH.resolve()}")
    else:
        print("[INFO] Bronze folder already empty")

# ==========================================
# 2️⃣ DROP SQLITE TABLES
# ==========================================
def drop_sqlite_tables():
    if not DB_PATH.exists():
        print("[INFO] SQLite DB does not exist, nothing to drop")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for table in SCHEMA_SQL.keys():
        cur.execute(f"DROP TABLE IF EXISTS {table}")
        print(f"[OK] Dropped table: {table}")

    conn.commit()
    conn.close()

# ==========================================
# 3️⃣ RECREATE SQLITE SCHEMA (CLEAN STATE)
# ==========================================
def recreate_schema():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for ddl in SCHEMA_SQL.values():
        cur.execute(ddl)

    conn.commit()
    conn.close()
    print("[OK] SQLite schema recreated cleanly")

# ==========================================
# MAIN
# ==========================================
def main():
    print("[START] RESETTING OEIL ENVIRONMENT")

    flush_bronze_files()
    drop_sqlite_tables()
    recreate_schema()

    print("[OK] Environment is clean and ready")

if __name__ == "__main__":
    main()
