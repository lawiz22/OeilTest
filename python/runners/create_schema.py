import argparse
import sqlite3
from pathlib import Path

try:
    import pyodbc
except ModuleNotFoundError:
    pyodbc = None

SQLSERVER_DRIVER_CANDIDATES = (
    "ODBC Driver 18 for SQL Server",
    "ODBC Driver 17 for SQL Server",
)

CONN_STR_TEMPLATE = (
    "Driver={{{driver}}};"
    "Server=tcp:testbanque.database.windows.net;"
    "Database=testbanque;"
    "Authentication=ActiveDirectoryInteractive;"
    "Encrypt=True;"
    "TrustServerCertificate=True;"
    "Connection Timeout=30;"
)

DDL_STATEMENTS_SQLSERVER = [
    # Table de vigie
    """
    IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'vigie_runs')
    CREATE TABLE dbo.vigie_runs (
        run_id BIGINT IDENTITY(1,1) PRIMARY KEY,
        dataset_name VARCHAR(100) NOT NULL,
        frequency VARCHAR(5) NOT NULL,
        mode VARCHAR(20) NOT NULL,
        date_debut_eff DATE NULL,
        date_fin_eff DATE NULL,
        expected_rows_min INT,
        expected_rows_max INT,
        actual_rows INT,
        status VARCHAR(20),
        message VARCHAR(500),
        run_ts DATETIME2 DEFAULT SYSDATETIME()
    );
    """,
    # CLIENTS (Mensuel)
    """
    IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'clients')
    CREATE TABLE dbo.clients (
        client_id INT,
        client_type VARCHAR(20),
        pays VARCHAR(50),
        statut VARCHAR(20),
        date_effet DATE
    );
    """,
    # ACCOUNTS (Hebdo)
    """
    IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'accounts')
    CREATE TABLE dbo.accounts (
        account_id INT,
        client_id INT,
        account_type VARCHAR(20),
        currency CHAR(3),
        balance DECIMAL(18,2),
        open_date DATE
    );
    """,
    # TRANSACTIONS (Quotidien)
    """
    IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'transactions')
    CREATE TABLE dbo.transactions (
        transaction_id BIGINT,
        account_id INT,
        amount DECIMAL(18,2),
        currency CHAR(3),
        transaction_ts DATETIME2,
        ingestion_date DATE
    );
    """,
    # CONTRACTS (Mensuel)
    """
    IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'contracts')
    CREATE TABLE dbo.contracts (
        contract_id INT,
        client_id INT,
        product_type VARCHAR(30),
        start_date DATE,
        end_date DATE,
        statut VARCHAR(20)
    );
    """,
]

DDL_STATEMENTS_SQLITE = [
    """
    CREATE TABLE IF NOT EXISTS vigie_runs (
        run_id INTEGER PRIMARY KEY AUTOINCREMENT,
        dataset_name TEXT NOT NULL,
        frequency TEXT NOT NULL,
        mode TEXT NOT NULL,
        date_debut_eff DATE,
        date_fin_eff DATE,
        expected_rows_min INTEGER,
        expected_rows_max INTEGER,
        actual_rows INTEGER,
        status TEXT,
        message TEXT,
        run_ts TEXT DEFAULT (datetime('now'))
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS clients (
        client_id INTEGER,
        client_type TEXT,
        pays TEXT,
        statut TEXT,
        date_effet DATE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS accounts (
        account_id INTEGER,
        client_id INTEGER,
        account_type TEXT,
        currency TEXT,
        balance REAL,
        open_date DATE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS transactions (
        transaction_id INTEGER,
        account_id INTEGER,
        amount REAL,
        currency TEXT,
        transaction_ts TEXT,
        ingestion_date DATE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS contracts (
        contract_id INTEGER,
        client_id INTEGER,
        product_type TEXT,
        start_date DATE,
        end_date DATE,
        statut TEXT
    );
    """,
]


def main():
    parser = argparse.ArgumentParser(description="Create schema in Azure SQL or SQLite.")
    parser.add_argument(
        "--backend",
        choices=("azure", "sqlite"),
        default="azure",
        help="Target backend. Defaults to azure if pyodbc is available, else sqlite.",
    )
    args = parser.parse_args()

    use_azure = args.backend == "azure"
    if use_azure and pyodbc is None:
        print("pyodbc not available; falling back to SQLite.")
        use_azure = False

    if use_azure:
        available_drivers = set(pyodbc.drivers())
        driver = next(
            (name for name in SQLSERVER_DRIVER_CANDIDATES if name in available_drivers),
            None,
        )
        if driver is None:
            print(
                "No compatible SQL Server ODBC driver found; falling back to SQLite."
            )
            use_azure = False
        else:
            conn_str = CONN_STR_TEMPLATE.format(driver=driver)
            print(f"Connecting to Azure SQL / Synapse using {driver}...")
            try:
                conn = pyodbc.connect(conn_str)
            except pyodbc.InterfaceError as exc:
                print(f"ODBC connection failed ({exc}); falling back to SQLite.")
                use_azure = False

    if use_azure:
        cursor = conn.cursor()

        for ddl in DDL_STATEMENTS_SQLSERVER:
            cursor.execute(ddl)

        conn.commit()
        cursor.close()
        conn.close()

        print("All tables created successfully.")
        return

    # Fallback: create a local SQLite schema for development/testing.
    db_path = Path("schema.db")
    print(f"pyodbc not available; creating local SQLite schema at {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for ddl in DDL_STATEMENTS_SQLITE:
        cursor.execute(ddl)

    conn.commit()
    cursor.close()
    conn.close()
    print("SQLite tables created successfully.")


if __name__ == "__main__":
    main()
