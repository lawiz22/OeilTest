import random
import pyodbc
from datetime import datetime, timedelta
from python.core.db_config import get_azure_sql_conn_str

# =====================================================
# ✍️ MAIN WRITER
# =====================================================
def write_fake_vigie_run(
    ctrl_id,
    dataset,
    periodicity,
    extraction_date,
    expected_rows,
    chaos_level=50,
    source_system="LEGACY_DS"
):
    run_day = datetime.fromisoformat(extraction_date)

    # =================================================
    # 📦 VOLUME FAKE (BRONZE / PARQUET)
    # =================================================
    actual_rows = expected_rows
    if random.random() < chaos_level / 100:
        actual_rows += random.randint(-expected_rows // 3, expected_rows // 3)

    bronze_rows = actual_rows

    parquet_rows = bronze_rows
    if random.random() < chaos_level / 100:
        parquet_rows += random.randint(-bronze_rows // 10, bronze_rows // 10)

    bronze_delta = bronze_rows - expected_rows
    parquet_delta = parquet_rows - expected_rows

    bronze_status = "OK" if bronze_delta == 0 else "MISMATCH"
    parquet_status = "OK" if parquet_delta == 0 else "KO"

    # =================================================
    # ⏱️ ADF (INGESTION)
    # =================================================
    adf_duration = random.randint(12, 25)
    adf_end_ts = run_day + timedelta(
        hours=random.randint(1, 6),
        minutes=random.randint(0, 59)
    )
    adf_start_ts = adf_end_ts - timedelta(seconds=adf_duration)

    adf_sla_status = "OK" if adf_duration < 30 else "FAIL"

    # =================================================
    # ⚙️ SYNAPSE (COMPUTE BRUT)
    # =================================================
    synapse_duration = random.randint(60, 180)
    synapse_start_ts = adf_end_ts + timedelta(seconds=5)
    synapse_end_ts = synapse_start_ts + timedelta(seconds=synapse_duration)

    synapse_sla_status = "OK" if synapse_duration < 160 else "FAIL"

    synapse_rate = 0.002
    synapse_cost = round((synapse_duration / 60) * synapse_rate, 6)

    # =================================================
    # 👁️ OEIL (ORCHESTRATION)
    # =================================================
    start_ts = adf_start_ts
    end_ts = synapse_end_ts
    duration_sec = int((end_ts - start_ts).total_seconds())

    if duration_sec <= 200:
        sla_bucket = "FAST"
        oeil_sla_status = "OK"
    elif duration_sec <= 300:
        sla_bucket = "SLOW"
        oeil_sla_status = "OK"
    else:
        sla_bucket = "VERY_SLOW"
        oeil_sla_status = "FAIL"

    # =================================================
    # 🚨 ALERTES (POC)
    # =================================================
    if (
        oeil_sla_status == "FAIL"
        or adf_sla_status != "OK"
        or synapse_sla_status != "OK"
        or parquet_status != "OK"
    ):
        alert_level = "CRITICAL"
        alert_flag = 1
    elif sla_bucket == "VERY_SLOW":
        alert_level = "WARNING"
        alert_flag = 1
    elif sla_bucket == "SLOW":
        alert_level = "INFO"
        alert_flag = 1
    else:
        alert_level = "NO_ALERT"
        alert_flag = 0

    alert_reason = (
        f"OEIL={oeil_sla_status} | "
        f"BUCKET={sla_bucket} | "
        f"BRONZE={bronze_status} | "
        f"PARQUET={parquet_status} | "
        f"ADF={adf_sla_status} | "
        f"SYNAPSE={synapse_sla_status}"
        if alert_flag else "NO_ALERT"
    )

    alert_ts = end_ts if alert_flag else None

    # =================================================
    # 💾 INSERT
    # =================================================
    conn = pyodbc.connect(get_azure_sql_conn_str())
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO dbo.vigie_ctrl (
            ctrl_id,
            dataset,
            periodicity,
            extraction_date,
            expected_rows,
            source_system,

            created_ts,
            pipeline_run_id,
            adf_pipeline_name,
            adf_trigger_name,

            start_ts,
            end_ts,
            duration_sec,

            bronze_rows,
            bronze_delta,
            bronze_status,
            parquet_rows,
            parquet_delta,
            parquet_status,

            row_count_adf_ingestion_copie_parquet,
            adf_start_ts,
            adf_end_ts,
            adf_duration_sec,
            adf_sla_status,

            synapse_start_ts,
            synapse_end_ts,
            synapse_duration_sec,
            synapse_sla_status,
            synapse_cost_estimated_cad,
            synapse_cost_rate_cad_per_min,

            sla_bucket,
            oeil_sla_status,

            alert_flag,
            alert_level,
            alert_reason,
            alert_ts
        )
        VALUES (?, ?, ?, ?, ?, ?, SYSUTCDATETIME(),
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?)
    """, (
        ctrl_id,
        dataset,
        periodicity,
        extraction_date,
        expected_rows,
        source_system,

        f"fake-{ctrl_id}",
        "PL_Ctrl_To_Vigie",
        "FAKER",

        start_ts,
        end_ts,
        duration_sec,

        bronze_rows,
        bronze_delta,
        bronze_status,
        parquet_rows,
        parquet_delta,
        parquet_status,

        parquet_rows,
        adf_start_ts,
        adf_end_ts,
        adf_duration,
        adf_sla_status,

        synapse_start_ts,
        synapse_end_ts,
        synapse_duration,
        synapse_sla_status,
        synapse_cost,
        synapse_rate,

        sla_bucket,
        oeil_sla_status,

        alert_flag,
        alert_level,
        alert_reason,
        alert_ts
    ))

    conn.commit()
    conn.close()

    print(f"[RUN] {ctrl_id} | bucket={sla_bucket} | alert={alert_level}")
