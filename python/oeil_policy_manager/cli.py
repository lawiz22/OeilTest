import os
from pathlib import Path

from dotenv import load_dotenv

# Charge le .env à la racine du projet pour exécution depuis n'importe quel cwd.
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

AZURE_SQL_CONN = os.getenv("OEIL_AZURE_SQL_CONN")
STORAGE_CONN = os.getenv("OEIL_STORAGE_CONN")
STORAGE_CONTAINER = os.getenv("OEIL_STORAGE_CONTAINER")
AZCOPY_DEST = os.getenv("OEIL_AZCOPY_DEST")

if not AZURE_SQL_CONN:
    raise ValueError("Missing OEIL_AZURE_SQL_CONN in .env")

if not STORAGE_CONN:
    raise ValueError("Missing OEIL_STORAGE_CONN in .env")

if not STORAGE_CONTAINER:
    raise ValueError("Missing OEIL_STORAGE_CONTAINER in .env")

if not AZCOPY_DEST:
    raise ValueError("Missing OEIL_AZCOPY_DEST in .env")


