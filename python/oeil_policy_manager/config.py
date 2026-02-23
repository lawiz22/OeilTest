import os
from dotenv import load_dotenv
from pathlib import Path

# Charge .env depuis la racine du projet
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

AZURE_SQL_CONN = os.getenv("OEIL_AZURE_SQL_CONN")
STORAGE_CONN = os.getenv("OEIL_STORAGE_CONN")
STORAGE_CONTAINER = os.getenv("OEIL_STORAGE_CONTAINER")


print("CONFIG LOADED")
print("AZURE_SQL_CONN =", AZURE_SQL_CONN)