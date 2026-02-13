"""
=====================================================
🔥 RUN VIGIE FINALIZER — SLA + ALERT (FINAL / POC SAFE)
=====================================================

✔ Calcule SLA OEIL / ADF / SYNAPSE
✔ Force status = RECEIVED
✔ Force SLA OEIL si manquant
✔ Synchronise SLA GLOBAL depuis OEIL
✔ Calcule volume_status
✔ Calcule alertes explicables
✔ Finalise les runs (COMPLETED)

Usage :
    python run_vigie_finalize.py
=====================================================
"""

import pyodbc

# =====================================================
# 🔐 CONNEXION SQL
# =====================================================

AZURE_SQL_CONN_STR = (
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=tcp:testbanque.database.windows.net,1433;"
    "Database=testbanque;"
    "Uid=oeil_ctrl_login;"
    "Pwd=Mabellefee!2222;"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
)

# =====================================================
# ⚙️ STORED PROCEDURES SLA
# =====================================================

SLA_PROCS = [
    "dbo.SP_Compute_SLA_OEIL",
    "dbo.SP_Compute_SLA_ADF",
    "dbo.SP_Compute_SLA_SYNAPSE"
]

# =====================================================
# 🔍 RUNS À FINALISER
# =====================================================

def fetch_ctrl_ids_to_finalize(cur):
    cur.execute("""
        SELECT ctrl_id
        FROM dbo.vigie_ctrl
        WHERE status_global IS NULL
           OR status_global <> 'COMPLETED'
    """)
    return [row[0] for row in cur.fetchall()]

# =====================================================
# 🧠 SLA (SP)
# =====================================================

def compute_all_sla(cur, ctrl_id):
    for proc in SLA_PROCS:
        cur.execute(f"EXEC {proc} @p_ctrl_id = ?", ctrl_id)

# =====================================================
# 🟢 STATUS = RECEIVED
# =====================================================

def ensure_status_received(cur, ctrl_id):
    cur.execute("""
        UPDATE dbo.vigie_ctrl
        SET status = 'RECEIVED'
        WHERE ctrl_id = ?
          AND status IS NULL
    """, ctrl_id)

# =====================================================
# 🛠️ SLA OEIL (FORCE SI MANQUANT)
# =====================================================

def ensure_oeil_sla(cur, ctrl_id):
    cur.execute("""
        UPDATE dbo.vigie_ctrl
        SET
            oeil_sla_sec = duration_sec,
            oeil_sla_expected_sec = COALESCE(oeil_sla_expected_sec, sla_expected_sec),
            oeil_sla_threshold_sec = COALESCE(oeil_sla_threshold_sec, sla_threshold_sec),
            oeil_sla_status =
                CASE
                    WHEN duration_sec <= COALESCE(oeil_sla_threshold_sec, sla_threshold_sec)
                        THEN 'OK'
                    ELSE 'FAIL'
                END,
            oeil_sla_reason = 'OEIL_EXECUTION'
        WHERE ctrl_id = ?
          AND oeil_sla_sec IS NULL
    """, ctrl_id)

# =====================================================
# 🔁 SLA GLOBAL = SLA OEIL
# =====================================================

def sync_global_sla_from_oeil(cur, ctrl_id):
    cur.execute("""
        UPDATE dbo.vigie_ctrl
        SET
            sla_sec           = oeil_sla_sec,
            sla_expected_sec  = oeil_sla_expected_sec,
            sla_threshold_sec = oeil_sla_threshold_sec,
            sla_status        = oeil_sla_status,
            sla_reason        = oeil_sla_reason
        WHERE ctrl_id = ?
          AND sla_sec IS NULL
    """, ctrl_id)

# =====================================================
# 📦 VOLUME STATUS (ADF ROWCOUNT)
# =====================================================

def compute_volume_status(cur, ctrl_id):
    cur.execute("""
        UPDATE dbo.vigie_ctrl
        SET volume_status =
            CASE
                WHEN row_count_adf_ingestion_copie_parquet IS NULL
                    THEN 'UNKNOWN'
                WHEN ABS(row_count_adf_ingestion_copie_parquet - expected_rows)
                        > expected_rows * 0.20
                    THEN 'ANOMALY'
                WHEN ABS(row_count_adf_ingestion_copie_parquet - expected_rows)
                        > expected_rows * 0.05
                    THEN 'LOW'
                ELSE 'OK'
            END
        WHERE ctrl_id = ?
    """, ctrl_id)

# =====================================================
# 🚨 ALERTES
# =====================================================

def compute_alert(cur, ctrl_id):
    cur.execute("""
        UPDATE dbo.vigie_ctrl
        SET
            alert_level =
                CASE
                    WHEN
                        oeil_sla_status = 'FAIL'
                        OR volume_status IN ('ANOMALY', 'LOW')
                        OR adf_sla_status <> 'OK'
                        OR synapse_sla_status <> 'OK'
                    THEN 'CRITICAL'

                    WHEN
                        sla_bucket = 'VERY_SLOW'
                        OR volume_status IN ('ANOMALY', 'LOW')
                    THEN 'WARNING'

                    WHEN
                        sla_bucket = 'SLOW'
                    THEN 'INFO'

                    ELSE 'NO_ALERT'
                END,

            alert_flag =
                CASE
                    WHEN
                        oeil_sla_status = 'FAIL'
                        OR volume_status IN ('ANOMALY', 'LOW')
                        OR adf_sla_status <> 'OK'
                        OR synapse_sla_status <> 'OK'
                        OR sla_bucket IN ('SLOW', 'VERY_SLOW')
                    THEN 1
                    ELSE 0
                END,

            alert_reason =
                CASE
                    WHEN
                        oeil_sla_status = 'FAIL'
                        OR volume_status IN ('ANOMALY', 'LOW')
                        OR adf_sla_status <> 'OK'
                        OR synapse_sla_status <> 'OK'
                    THEN
                        CONCAT(
                            'OEIL=', oeil_sla_status,
                            ' | BUCKET=', sla_bucket,
                            ' | VOLUME=', COALESCE(volume_status, 'NA'),
                            ' | ADF=', COALESCE(adf_sla_status, 'NA'),
                            ' | SYNAPSE=', COALESCE(synapse_sla_status, 'NA')
                        )

                    WHEN
                        sla_bucket IN ('SLOW', 'VERY_SLOW')
                    THEN
                        CONCAT(
                            'OEIL=', oeil_sla_status,
                            ' | BUCKET=', sla_bucket,
                            ' | VOLUME=', COALESCE(volume_status, 'OK')
                        )

                    ELSE 'NO_ALERT'
                END,

            alert_ts =
                CASE
                    WHEN
                        oeil_sla_status = 'FAIL'
                        OR volume_status IN ('ANOMALY', 'LOW')
                        OR adf_sla_status <> 'OK'
                        OR synapse_sla_status <> 'OK'
                        OR sla_bucket IN ('SLOW', 'VERY_SLOW')
                    THEN SYSUTCDATETIME()
                    ELSE NULL
                END
        WHERE ctrl_id = ?
    """, ctrl_id)

# =====================================================
# ✅ FINALISATION
# =====================================================

def mark_completed(cur, ctrl_id):
    cur.execute("""
        UPDATE dbo.vigie_ctrl
        SET status_global = 'COMPLETED'
        WHERE ctrl_id = ?
    """, ctrl_id)

# =====================================================
# 🚀 MAIN
# =====================================================

def main():
    conn = pyodbc.connect(AZURE_SQL_CONN_STR)
    cur = conn.cursor()

    ctrl_ids = fetch_ctrl_ids_to_finalize(cur)

    if not ctrl_ids:
        print("✅ Aucun run à finaliser.")
        conn.close()
        return

    print("🔥 VIGIE FINALIZER")
    print(f"📦 Runs à traiter : {len(ctrl_ids)}")
    print("-" * 60)

    ok = 0
    fail = 0

    for ctrl_id in ctrl_ids:
        try:
            compute_all_sla(cur, ctrl_id)
            ensure_status_received(cur, ctrl_id)
            ensure_oeil_sla(cur, ctrl_id)
            sync_global_sla_from_oeil(cur, ctrl_id)
            compute_volume_status(cur, ctrl_id)
            compute_alert(cur, ctrl_id)
            mark_completed(cur, ctrl_id)

            ok += 1
            print(f"✅ COMPLETED → {ctrl_id}")

        except Exception as e:
            fail += 1
            print(f"❌ ERREUR → {ctrl_id}")
            print(str(e))

    conn.commit()
    conn.close()

    print("-" * 60)
    print(f"🍖 DONE — OK={ok} | FAIL={fail}")

# =====================================================
# ENTRY POINT
# =====================================================

if __name__ == "__main__":
    main()
