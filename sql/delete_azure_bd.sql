IF  EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[synapse_rowcount_cache]') AND type in (N'U'))
DELETE [dbo].[synapse_rowcount_cache]
GO

IF  EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[synapse_rowcount_cache]') AND type in (N'U'))
DELETE [dbo].[vigie_ctrl]
GO

IF  EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[synapse_rowcount_cache]') AND type in (N'U'))
DELETE [dbo].[ctrl_file_index]
GO

