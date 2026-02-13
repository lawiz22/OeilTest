-- =============================================================================
-- Table : vigie_ctrl
-- Description : Table principale de L'ŒIL — un enregistrement par run
--               d'extraction. Contient les métriques de volume (bronze/parquet),
--               les SLA par moteur (OEIL/ADF/SYNAPSE), les coûts Synapse,
--               les alertes et le hash SHA-256 déterministique du payload.
-- =============================================================================

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[vigie_ctrl](
	[ctrl_id] [varchar](200) NOT NULL,
	[dataset] [varchar](50) NOT NULL,
	[periodicity] [varchar](10) NOT NULL,
	[extraction_date] [date] NOT NULL,
	[expected_rows] [int] NULL,
	[source_system] [varchar](50) NULL,
	[created_ts] [datetime2](7) NULL,
	[pipeline_run_id] [varchar](100) NULL,
	[adf_pipeline_name] [varchar](100) NULL,
	[adf_trigger_name] [varchar](100) NULL,
	[start_ts] [datetime2](7) NULL,
	[status] [varchar](20) NULL,
	[inserted_ts] [datetime2](7) NOT NULL,

	-- Volume Bronze
	[bronze_rows] [int] NULL,
	[bronze_delta] [int] NULL,
	[bronze_status] [varchar](10) NULL,

	-- Volume Parquet
	[parquet_rows] [int] NULL,
	[parquet_delta] [int] NULL,
	[parquet_status] [varchar](10) NULL,

	-- Status global
	[status_global] [varchar](20) NULL,

	-- SLA global
	[sla_expected_sec] [int] NULL,
	[sla_threshold_sec] [int] NULL,
	[end_ts] [datetime2](7) NULL,
	[duration_sec] [int] NULL,
	[sla_sec] [int] NULL,
	[sla_status] [varchar](20) NULL,
	[sla_reason] [varchar](50) NULL,
	[volume_status] [varchar](20) NULL,
	[sla_bucket] [varchar](10) NULL,

	-- ADF ingestion
	[row_count_adf_ingestion_copie_parquet] [int] NULL,
	[adf_start_ts] [datetime2](7) NULL,
	[adf_end_ts] [datetime2](7) NULL,
	[adf_duration_sec] [int] NULL,
	[adf_sla_status] [varchar](20) NULL,
	[adf_sla_reason] [varchar](100) NULL,

	-- SLA ADF détaillé
	[adf_sla_sec] [int] NULL,
	[adf_sla_expected_sec] [int] NULL,
	[adf_sla_threshold_sec] [int] NULL,

	-- Synapse compute
	[synapse_start_ts] [datetime2](7) NULL,
	[synapse_end_ts] [datetime2](7) NULL,
	[synapse_duration_sec] [int] NULL,

	-- SLA Synapse détaillé
	[synapse_sla_sec] [int] NULL,
	[synapse_sla_expected_sec] [int] NULL,
	[synapse_sla_threshold_sec] [int] NULL,
	[synapse_sla_status] [varchar](20) NULL,
	[synapse_sla_reason] [varchar](100) NULL,

	-- SLA OEIL détaillé
	[oeil_sla_sec] [int] NULL,
	[oeil_sla_expected_sec] [int] NULL,
	[oeil_sla_threshold_sec] [int] NULL,
	[oeil_sla_status] [varchar](20) NULL,
	[oeil_sla_reason] [varchar](100) NULL,

	-- Alertes
	[alert_flag] [bit] NULL,
	[alert_reason] [varchar](100) NULL,
	[alert_ts] [datetime2](7) NULL,
	[alert_level] [varchar](20) NULL,

	-- Coût Synapse
	[synapse_cost_estimated_cad] [decimal](10, 6) NULL,
	[synapse_cost_rate_cad_per_min] [decimal](10, 6) NULL,

	-- Hash payload (intégrité)
	[payload_canonical] [varchar](500) NULL,
	[payload_hash_sha256] [char](64) NULL,
	[payload_hash_version] [tinyint] NULL,
	[payload_hash_match] [bit] NULL
) ON [PRIMARY]
GO

-- Primary Key
SET ANSI_PADDING ON
GO
ALTER TABLE [dbo].[vigie_ctrl] ADD  CONSTRAINT [PK_vigie_ctrl] PRIMARY KEY CLUSTERED 
(
	[ctrl_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

-- Index composite pour recherche par dataset + periodicité + date
SET ANSI_PADDING ON
GO
CREATE NONCLUSTERED INDEX [IX_vigie_ctrl_dataset_date] ON [dbo].[vigie_ctrl]
(
	[dataset] ASC,
	[periodicity] ASC,
	[extraction_date] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

-- Defaults
ALTER TABLE [dbo].[vigie_ctrl] ADD  CONSTRAINT [DF_vigie_ctrl_inserted_ts]  DEFAULT (sysutcdatetime()) FOR [inserted_ts]
GO
