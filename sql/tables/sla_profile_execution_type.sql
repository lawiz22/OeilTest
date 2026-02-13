-- =============================================================================
-- Table : sla_profile_execution_type
-- Description : Profil SLA par type d'exécution (ADF, SYNAPSE, OEIL).
--               Version actuellement en production — le profil par dataset
--               (sla_profile) est prévu pour une feature future.
--               Même logique de calcul : overhead fixe + coût variable + tolérance.
-- =============================================================================

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[sla_profile_execution_type](
	[execution_type] [varchar](30) NOT NULL,
	[base_overhead_sec] [int] NOT NULL,
	[sec_per_1k_rows] [int] NULL,
	[tolerance_pct] [decimal](5, 2) NOT NULL,
	[active_flag] [bit] NOT NULL,
	[created_ts] [datetime2](3) NOT NULL
) ON [PRIMARY]
GO

-- Primary Key
SET ANSI_PADDING ON
GO
ALTER TABLE [dbo].[sla_profile_execution_type] ADD  CONSTRAINT [PK_sla_profile_execution_type] PRIMARY KEY CLUSTERED 
(
	[execution_type] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

-- Defaults
ALTER TABLE [dbo].[sla_profile_execution_type] ADD  CONSTRAINT [DF_sla_exec_active]  DEFAULT ((1)) FOR [active_flag]
GO
ALTER TABLE [dbo].[sla_profile_execution_type] ADD  CONSTRAINT [DF_sla_exec_created]  DEFAULT (sysutcdatetime()) FOR [created_ts]
GO

-- =============================================================================
-- Données de base
-- =============================================================================
INSERT INTO [dbo].[sla_profile_execution_type]
    ([execution_type], [base_overhead_sec], [sec_per_1k_rows], [tolerance_pct], [active_flag], [created_ts])
VALUES
    ('ADF',     30,   5,    0.25, 1, '2026-02-08 23:38:46.140'),
    ('OEIL',    360,  NULL, 0.22, 1, '2026-02-08 23:38:07.116'),
    ('SYNAPSE', 120,  NULL, 0.30, 1, '2026-02-09 03:06:51.128');
GO
