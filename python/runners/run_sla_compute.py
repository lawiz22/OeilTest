import sys
from pathlib import Path

# Ensure project root is on sys.path so "python.core.*" imports work
# when running this file directly (e.g. VS Code Run button)
_project_root = str(Path(__file__).resolve().parents[2])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import pyodbc
from python.core.db_config import get_azure_sql_conn_str

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
    conn = pyodbc.connect(get_azure_sql_conn_str())
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
