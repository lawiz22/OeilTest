import pyodbc

AZURE_SQL_CONN_STR = (
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=tcp:testbanque.database.windows.net,1433;"
    "Database=testbanque;"
    "Uid=oeil_ctrl_login;"
    "Pwd=Mabellefee!2222;"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
)

SLA_PROC_NAME = "dbo.SP_Compute_SLA_Vigie"

def fetch_ctrl_ids_without_sla(cur):
    """
    Récupère les ctrl_id qui n'ont pas encore de SLA calculé
    """
    cur.execute("""
        SELECT ctrl_id
        FROM dbo.vigie_ctrl
        WHERE sla_status IS NULL
    """)
    return [row[0] for row in cur.fetchall()]

def compute_sla_for_ctrl(cur, ctrl_id):
    """
    Appelle la stored procedure SLA pour UN ctrl_id
    """
    cur.execute(
        f"EXEC {SLA_PROC_NAME} @p_ctrl_id = ?",
        ctrl_id
    )

def main():
    conn = pyodbc.connect(AZURE_SQL_CONN_STR)
    cur = conn.cursor()

    ctrl_ids = fetch_ctrl_ids_without_sla(cur)

    if not ctrl_ids:
        print("[OK] Aucun SLA a calculer.")
        conn.close()
        return

    print(f"[START] {len(ctrl_ids)} runs a enrichir avec SLA")
    print("-" * 50)

    success = 0
    failed = 0

    for ctrl_id in ctrl_ids:
        try:
            compute_sla_for_ctrl(cur, ctrl_id)
            success += 1
            print(f"[OK] SLA calcule -> {ctrl_id}")
        except Exception as e:
            failed += 1
            print(f"[ERROR] ERREUR SLA -> {ctrl_id}")
            print(str(e))

    conn.commit()
    conn.close()

    print("-" * 50)
    print(f"SLA DONE - OK={success} | FAIL={failed}")

if __name__ == "__main__":
    main()
