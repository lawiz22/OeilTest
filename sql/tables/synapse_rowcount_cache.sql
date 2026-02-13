-- =============================================================================
-- Table : synapse_rowcount_cache
-- Description : Table tampon (row cache) pour Synapse. Stocke les row counts
--               par dataset/periodicité/date/layer pour éviter des requêtes
--               Synapse coûteuses et répétitives.
--               Première ébauche fonctionnelle — la logique d'agrégation
--               complète reste à programmer.
-- =============================================================================

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[synapse_rowcount_cache](
	[dataset] [varchar](50) NOT NULL,
	[periodicity] [varchar](10) NOT NULL,
	[extraction_date] [date] NOT NULL,
	[layer] [varchar](10) NOT NULL,
	[row_count] [int] NOT NULL,
	[computed_ts] [datetime2](7) NOT NULL
) ON [PRIMARY]
GO

-- Primary Key (composite : dataset + periodicity + extraction_date + layer)
SET ANSI_PADDING ON
GO
ALTER TABLE [dbo].[synapse_rowcount_cache] ADD  CONSTRAINT [PK_synapse_rowcount_cache] PRIMARY KEY CLUSTERED 
(
	[dataset] ASC,
	[periodicity] ASC,
	[extraction_date] ASC,
	[layer] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

-- Defaults
ALTER TABLE [dbo].[synapse_rowcount_cache] ADD  DEFAULT (sysutcdatetime()) FOR [computed_ts]
GO
