import pyodbc
from azure.identity import InteractiveBrowserCredential

TENANT_ID = "TON_TENANT_ID_ICI"  # Directory (tenant) ID
SERVER = "testbanque.database.windows.net"
DATABASE = "testbanque"

credential = InteractiveBrowserCredential(
    tenant_id='9efa3aee-91e4-46cb-a42d-157e10be0b3f'
)

token = credential.get_token(
    "https://database.windows.net/.default"
).token

conn = pyodbc.connect(
    f"Driver={{ODBC Driver 18 for SQL Server}};"
    f"Server=tcp:{SERVER},1433;"
    f"Database={DATABASE};"
    f"Encrypt=yes;"
    f"TrustServerCertificate=no;",
    attrs_before={1256: token}
)

print("✅ Connexion Azure SQL avec token OK")
conn.close()
