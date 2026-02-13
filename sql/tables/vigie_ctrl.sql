-- =====================================================
-- 👁️ L'ŒIL — vigie_ctrl (Run-Level Metrics)
-- =====================================================
-- Stores one row per extraction run with volume,
-- SLA, cost, and alert information.
-- =====================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'vigie_ctrl')
CREATE TABLE dbo.vigie_ctrl (
    ctrl_id                             VARCHAR(200)    NOT NULL PRIMARY KEY,
    dataset                             VARCHAR(100)    NOT NULL,
    periodicity                         VARCHAR(5)      NOT NULL,
    extraction_date                     DATE            NOT NULL,
    expected_rows                       INT             NULL,
    source_system                       VARCHAR(50)     DEFAULT 'LEGACY_DS',

    created_ts                          DATETIME2       DEFAULT SYSUTCDATETIME(),
    pipeline_run_id                     VARCHAR(200)    NULL,
    adf_pipeline_name                   VARCHAR(200)    NULL,
    adf_trigger_name                    VARCHAR(200)    NULL,

    -- Timestamps
    start_ts                            DATETIME2       NULL,
    end_ts                              DATETIME2       NULL,
    duration_sec                        INT             NULL,

    -- Bronze volume
    bronze_rows                         INT             NULL,
    bronze_delta                        INT             NULL,
    bronze_status                       VARCHAR(20)     NULL,

    -- Parquet volume
    parquet_rows                        INT             NULL,
    parquet_delta                       INT             NULL,
    parquet_status                      VARCHAR(20)     NULL,

    -- ADF ingestion
    row_count_adf_ingestion_copie_parquet INT           NULL,
    adf_start_ts                        DATETIME2       NULL,
    adf_end_ts                          DATETIME2       NULL,
    adf_duration_sec                    INT             NULL,
    adf_sla_status                      VARCHAR(20)     NULL,

    -- Synapse compute
    synapse_start_ts                    DATETIME2       NULL,
    synapse_end_ts                      DATETIME2       NULL,
    synapse_duration_sec                INT             NULL,
    synapse_sla_status                  VARCHAR(20)     NULL,
    synapse_cost_estimated_cad          DECIMAL(10,6)   NULL,
    synapse_cost_rate_cad_per_min       DECIMAL(10,6)   NULL,

    -- SLA
    sla_bucket                          VARCHAR(20)     NULL,
    oeil_sla_status                     VARCHAR(20)     NULL,
    sla_status                          VARCHAR(20)     NULL,

    -- Alerts
    alert_flag                          BIT             DEFAULT 0,
    alert_level                         VARCHAR(20)     DEFAULT 'NO_ALERT',
    alert_reason                        VARCHAR(500)    NULL,
    alert_ts                            DATETIME2       NULL,

    -- Status
    status                              VARCHAR(20)     DEFAULT 'PENDING',
    completed_ts                        DATETIME2       NULL,

    -- Volume status
    volume_status                       VARCHAR(20)     NULL
);
GO
