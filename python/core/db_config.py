import os
from pathlib import Path

AZURE_SQL_CONN_STR_ENV = "OEIL_AZURE_SQL_CONN_STR"
AZURE_SQL_CONN_ENV = "OEIL_AZURE_SQL_CONN"
AZURE_SQL_PASSWORD_ENV = "OEIL_AZURE_SQL_PASSWORD"
AZURE_SQL_SERVER_ENV = "OEIL_AZURE_SQL_SERVER"
AZURE_SQL_DATABASE_ENV = "OEIL_AZURE_SQL_DATABASE"
AZURE_SQL_USER_ENV = "OEIL_AZURE_SQL_USER"


def _load_dotenv() -> None:
    dotenv_path = Path(__file__).resolve().parents[1] / ".env"
    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if key and key not in os.environ:
            os.environ[key] = value



def get_azure_sql_conn_str():
    _load_dotenv()

    conn_str_from_env = os.getenv(AZURE_SQL_CONN_ENV) or os.getenv(AZURE_SQL_CONN_STR_ENV)
    if conn_str_from_env:
        return conn_str_from_env

    password = os.getenv(AZURE_SQL_PASSWORD_ENV)
    server = os.getenv(AZURE_SQL_SERVER_ENV)
    database = os.getenv(AZURE_SQL_DATABASE_ENV)
    user = os.getenv(AZURE_SQL_USER_ENV)

    if not all([password, server, database, user]):
        raise RuntimeError(
            "Missing Azure SQL config in environment/.env. "
            f"Provide '{AZURE_SQL_CONN_ENV}' (or '{AZURE_SQL_CONN_STR_ENV}') "
            f"OR provide '{AZURE_SQL_SERVER_ENV}', '{AZURE_SQL_DATABASE_ENV}', "
            f"'{AZURE_SQL_USER_ENV}', '{AZURE_SQL_PASSWORD_ENV}'."
        )

    return (
        "Driver={ODBC Driver 18 for SQL Server};"
        f"Server=tcp:{server},1433;"
        f"Database={database};"
        f"Uid={user};"
        f"Pwd={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
    )
