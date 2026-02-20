SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

SET NOCOUNT ON;

PRINT '=== Release start: SP_Insert_VigieIntegrityResult ===';

IF OBJECT_ID('dbo.SP_Insert_VigieIntegrityResult', 'P') IS NULL
BEGIN
    RAISERROR('Procedure dbo.SP_Insert_VigieIntegrityResult introuvable.', 16, 1);
    RETURN;
END;

IF COL_LENGTH('dbo.vigie_integrity_result', 'observed_value_text') IS NULL
   OR COL_LENGTH('dbo.vigie_integrity_result', 'reference_value_text') IS NULL
BEGIN
    RAISERROR('Colonnes observed_value_text/reference_value_text absentes dans dbo.vigie_integrity_result.', 16, 1);
    RETURN;
END;
GO

ALTER PROCEDURE [dbo].[SP_Insert_VigieIntegrityResult]
    @ctrl_id NVARCHAR(150),
    @dataset_name NVARCHAR(150),
    @test_code NVARCHAR(50),
    @column_name NVARCHAR(150) = NULL,

    @bronze_value FLOAT = NULL,
    @bronze_aux_value FLOAT = NULL,
    @parquet_value FLOAT = NULL,
    @parquet_aux_value FLOAT = NULL,

    @status NVARCHAR(30),
    @execution_time_ms INT = NULL,

    @synapse_start_ts DATETIME2 = NULL,
    @synapse_end_ts DATETIME2 = NULL,

    @observed_value_text NVARCHAR(500) = NULL,
    @reference_value_text NVARCHAR(500) = NULL
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @delta FLOAT;

    SET @delta =
        CASE
            WHEN @bronze_value IS NOT NULL
             AND @parquet_value IS NOT NULL
            THEN ABS(@bronze_value - @parquet_value)
            ELSE NULL
        END;

    IF @synapse_start_ts IS NULL
        SET @synapse_start_ts = SYSUTCDATETIME();

    IF @synapse_end_ts IS NULL
        SET @synapse_end_ts = SYSUTCDATETIME();

    IF @synapse_end_ts < @synapse_start_ts
        SET @synapse_end_ts = @synapse_start_ts;

    INSERT INTO dbo.vigie_integrity_result
    (
        ctrl_id,
        dataset_name,
        test_code,
        column_name,

        observed_value_num,
        observed_value_aux_num,
        reference_value_num,
        reference_value_aux_num,

        observed_value_text,
        reference_value_text,

        delta_value,

        status,
        execution_time_ms,

        synapse_start_ts,
        synapse_end_ts,

        created_at
    )
    VALUES
    (
        @ctrl_id,
        @dataset_name,
        @test_code,
        @column_name,

        @bronze_value,
        @bronze_aux_value,
        @parquet_value,
        @parquet_aux_value,

        @observed_value_text,
        @reference_value_text,

        @delta,

        @status,
        @execution_time_ms,

        @synapse_start_ts,
        @synapse_end_ts,

        SYSUTCDATETIME()
    );
END;
GO

PRINT '=== Post-deploy smoke test (rollback) ===';

BEGIN TRY
    BEGIN TRANSACTION;

    DECLARE @ctrl_id NVARCHAR(150) = CONCAT('release_smoke_', REPLACE(CONVERT(VARCHAR(19), SYSUTCDATETIME(), 126), ':', '_'));

    EXEC dbo.SP_Insert_VigieIntegrityResult
        @ctrl_id = @ctrl_id,
        @dataset_name = N'release_dataset',
        @test_code = N'CHECKSUM',
        @column_name = N'client_id',
        @bronze_value = 1,
        @bronze_aux_value = NULL,
        @parquet_value = 1,
        @parquet_aux_value = NULL,
        @status = N'PASS',
        @execution_time_ms = 5,
        @synapse_start_ts = SYSUTCDATETIME(),
        @synapse_end_ts = SYSUTCDATETIME(),
        @observed_value_text = N'abc123',
        @reference_value_text = N'abc123';

    SELECT TOP 1
        ctrl_id,
        dataset_name,
        test_code,
        column_name,
        observed_value_num,
        reference_value_num,
        observed_value_text,
        reference_value_text,
        delta_value,
        status,
        execution_time_ms,
        synapse_start_ts,
        synapse_end_ts,
        created_at
    FROM dbo.vigie_integrity_result
    WHERE ctrl_id = @ctrl_id
    ORDER BY created_at DESC;

    ROLLBACK TRANSACTION;

    PRINT 'Smoke test OK (rollback effectif).';
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
        ROLLBACK TRANSACTION;

    DECLARE @ErrMsg NVARCHAR(4000) = ERROR_MESSAGE();
    DECLARE @ErrSeverity INT = ERROR_SEVERITY();
    DECLARE @ErrState INT = ERROR_STATE();

    RAISERROR('Post-deploy smoke test KO: %s', @ErrSeverity, @ErrState, @ErrMsg);
END CATCH;

PRINT '=== Release completed: SP_Insert_VigieIntegrityResult ===';
