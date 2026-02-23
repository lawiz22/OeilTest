import os
from dotenv import load_dotenv

load_dotenv()

AZURE_SQL_CONN = os.getenv("OEIL_AZURE_SQL_CONN")
STORAGE_CONN = os.getenv("OEIL_STORAGE_CONN")
STORAGE_CONTAINER = os.getenv("OEIL_STORAGE_CONTAINER")

if not AZURE_SQL_CONN:
    raise ValueError("Missing OEIL_AZURE_SQL_CONN in .env")

if not STORAGE_CONN:
    raise ValueError("Missing OEIL_STORAGE_CONN in .env")

if not STORAGE_CONTAINER:
    raise ValueError("Missing OEIL_STORAGE_CONTAINER in .env")


