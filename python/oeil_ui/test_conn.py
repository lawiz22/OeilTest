import os
from pathlib import Path

import pyodbc
from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[2] / ".env")

conn_str = os.getenv("OEIL_AZURE_SQL_CONN", "")
if not conn_str:
    raise RuntimeError("Missing OEIL_AZURE_SQL_CONN in project .env")

conn = pyodbc.connect(conn_str)
print("Connected OK")
conn.close()