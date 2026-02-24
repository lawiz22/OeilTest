import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()


_engine = None


def get_engine():
    global _engine

    if _engine is None:
        conn_str = os.getenv("OEIL_AZURE_SQL_CONN")

        if not conn_str:
            raise Exception("OEIL_AZURE_SQL_CONN not found in environment variables")

        # Important pour SQL Server
        sqlalchemy_url = (
            "mssql+pyodbc:///?odbc_connect=" + conn_str
        )

        _engine = create_engine(sqlalchemy_url)

    return _engine