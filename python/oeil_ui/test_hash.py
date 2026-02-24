import sys
import os
from pathlib import Path
import hashlib

# Allow project imports
sys.path.append(str(Path(__file__).resolve().parents[2]))

from dotenv import load_dotenv
load_dotenv()

from python.oeil_ui.struct_repository import StructRepository


def main():

    conn_str = os.getenv("OEIL_AZURE_SQL_CONN")

    if not conn_str:
        raise ValueError("OEIL_AZURE_SQL_CONN not defined")

    repo = StructRepository(conn_str)

    # Get JSON exactly as SQL builds it
    sql_json = repo.get_sql_generated_json("clients")

    print("SQL JSON used for hash:")
    print(sql_json)

    # Hash exactly like SQL
    hash_hex = hashlib.sha256(
    sql_json.encode("utf-16le")
    ).hexdigest().upper()

    print("\nHash (HEX):")
    print(hash_hex)


if __name__ == "__main__":
    main()