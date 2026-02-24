import os
from sqlalchemy import create_engine
from sqlalchemy import text
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

        _engine = create_engine(
            sqlalchemy_url,
            pool_pre_ping=True,
            pool_recycle=1800,
        )

    return _engine


def reset_engine():
    global _engine

    if _engine is not None:
        try:
            _engine.dispose()
        except Exception:
            pass

    _engine = None


def ping_sql() -> tuple[bool, str]:
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "Connected"
    except Exception as exc:
        return False, str(exc)