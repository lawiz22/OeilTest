import os

AZURE_SQL_CONN_STR_ENV = "OEIL_AZURE_SQL_CONN_STR"
AZURE_SQL_PASSWORD_ENV = "OEIL_AZURE_SQL_PASSWORD"



def get_azure_sql_conn_str():
    conn_str_from_env = os.getenv(AZURE_SQL_CONN_STR_ENV)
    if conn_str_from_env:
        return conn_str_from_env

    password = os.getenv(AZURE_SQL_PASSWORD_ENV)
    if not password:
        raise RuntimeError(
            f"Missing environment variable '{AZURE_SQL_PASSWORD_ENV}' "
            "for Azure SQL authentication."
        )

    return (
        "Driver={ODBC Driver 18 for SQL Server};"
        "Server=tcp:testbanque.database.windows.net,1433;"
        "Database=testbanque;"
        "Uid=oeil_ctrl_login;"
        f"Pwd={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
    )
