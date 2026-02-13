-- =============================================================================
-- Table : ctrl_file_index
-- Description : Index de contrôle des fichiers ingérés dans le lake.
--               Chaque enregistrement est créé lors de l'upload réussi d'un
--               fichier sur le premier lake (bronze).
--               Le flag processed_flag et le hash SHA-256 du chemin permettent
--               de gérer les re-runs et d'éviter les doublons.
-- =============================================================================

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[ctrl_file_index](
	[ctrl_id] [nvarchar](200) NOT NULL,
	[dataset] [nvarchar](200) NOT NULL,
	[ctrl_path] [nvarchar](1024) NOT NULL,
	[processed_flag] [bit] NOT NULL,
	[processed_ts] [datetime2](3) NULL,
	[created_ts] [datetime2](3) NOT NULL,
	[ctrl_path_hash]  AS (CONVERT([binary](32),hashbytes('SHA2_256',[ctrl_path]))) PERSISTED
) ON [PRIMARY]
GO

-- Primary Key
ALTER TABLE [dbo].[ctrl_file_index] ADD  CONSTRAINT [PK_ctrl_file_index] PRIMARY KEY CLUSTERED 
(
	[ctrl_id] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

-- Index unique sur le hash du chemin (évite les doublons de fichiers)
SET ARITHABORT ON
SET CONCAT_NULL_YIELDS_NULL ON
SET QUOTED_IDENTIFIER ON
SET ANSI_NULLS ON
SET ANSI_PADDING ON
SET ANSI_WARNINGS ON
SET NUMERIC_ROUNDABORT OFF
GO
CREATE UNIQUE NONCLUSTERED INDEX [UX_ctrl_file_index_ctrl_path_hash] ON [dbo].[ctrl_file_index]
(
	[ctrl_path_hash] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

-- Defaults
ALTER TABLE [dbo].[ctrl_file_index] ADD  DEFAULT ((0)) FOR [processed_flag]
GO
ALTER TABLE [dbo].[ctrl_file_index] ADD  DEFAULT (sysutcdatetime()) FOR [created_ts]
GO
