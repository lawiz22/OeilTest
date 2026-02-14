SET NOCOUNT ON;
SET XACT_ABORT ON;

IF DB_NAME() <> N'testbanque'
BEGIN
	THROW 50001, 'Wrong database context. Switch to [testbanque] before running this script.', 1;
END;

PRINT CONCAT('[INFO] Running cleanup in DB: ', DB_NAME());

SELECT 'before' AS phase, 'synapse_rowcount_cache' AS table_name, COUNT(*) AS row_count FROM dbo.synapse_rowcount_cache
UNION ALL
SELECT 'before', 'vigie_ctrl', COUNT(*) FROM dbo.vigie_ctrl
UNION ALL
SELECT 'before', 'ctrl_file_index', COUNT(*) FROM dbo.ctrl_file_index;

BEGIN TRY
	BEGIN TRAN;

	IF OBJECT_ID(N'dbo.synapse_rowcount_cache', N'U') IS NOT NULL
	BEGIN
		DELETE FROM dbo.synapse_rowcount_cache;
		PRINT CONCAT('[OK] dbo.synapse_rowcount_cache deleted rows: ', @@ROWCOUNT);
	END
	ELSE
	BEGIN
		PRINT '[INFO] dbo.synapse_rowcount_cache does not exist';
	END;

	IF OBJECT_ID(N'dbo.vigie_ctrl', N'U') IS NOT NULL
	BEGIN
		DELETE FROM dbo.vigie_ctrl;
		PRINT CONCAT('[OK] dbo.vigie_ctrl deleted rows: ', @@ROWCOUNT);
	END
	ELSE
	BEGIN
		PRINT '[INFO] dbo.vigie_ctrl does not exist';
	END;

	IF OBJECT_ID(N'dbo.ctrl_file_index', N'U') IS NOT NULL
	BEGIN
		DELETE FROM dbo.ctrl_file_index;
		PRINT CONCAT('[OK] dbo.ctrl_file_index deleted rows: ', @@ROWCOUNT);
	END
	ELSE
	BEGIN
		PRINT '[INFO] dbo.ctrl_file_index does not exist';
	END;

	COMMIT TRAN;
	PRINT '[OK] Cleanup completed successfully';
END TRY
BEGIN CATCH
	IF @@TRANCOUNT > 0
		ROLLBACK TRAN;

	PRINT CONCAT('[ERROR] ', ERROR_MESSAGE());
	THROW;
END CATCH;

SELECT 'after' AS phase, 'synapse_rowcount_cache' AS table_name, COUNT(*) AS row_count FROM dbo.synapse_rowcount_cache
UNION ALL
SELECT 'after', 'vigie_ctrl', COUNT(*) FROM dbo.vigie_ctrl
UNION ALL
SELECT 'after', 'ctrl_file_index', COUNT(*) FROM dbo.ctrl_file_index;

