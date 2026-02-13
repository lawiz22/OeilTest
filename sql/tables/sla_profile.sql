-- =============================================================================
-- Table : sla_profile
-- Description : Profil SLA générique par dataset. Permet de calculer des SLA
--               de base en combinant un overhead fixe (base_overhead_sec),
--               un coût variable (sec_per_1k_rows) et une tolérance en %.
--               Clé primaire sur dataset : un profil SLA par dataset.
-- =============================================================================

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[sla_profile](
	[dataset] [nvarchar](200) NOT NULL,
	[base_overhead_sec] [int] NOT NULL,
	[sec_per_1k_rows] [int] NOT NULL,
	[tolerance_pct] [decimal](5, 2) NOT NULL,
	[active_flag] [bit] NOT NULL,
	[created_ts] [datetime2](3) NOT NULL
) ON [PRIMARY]
GO

-- Primary Key
SET ANSI_PADDING ON
GO
ALTER TABLE [dbo].[sla_profile] ADD  CONSTRAINT [PK_sla_profile] PRIMARY KEY CLUSTERED 
(
	[dataset] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

-- Defaults
ALTER TABLE [dbo].[sla_profile] ADD  DEFAULT ((1)) FOR [active_flag]
GO
ALTER TABLE [dbo].[sla_profile] ADD  DEFAULT (sysutcdatetime()) FOR [created_ts]
GO
