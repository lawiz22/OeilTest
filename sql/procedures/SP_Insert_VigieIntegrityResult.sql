SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
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
    @synapse_end_ts DATETIME2 = NULL
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @delta FLOAT;
    DECLARE @duration_sec INT;

    /* =========================================
       1️⃣ Delta générique (observed vs reference)
       ========================================= */
    SET @delta =
        CASE
            WHEN @bronze_value IS NOT NULL
             AND @parquet_value IS NOT NULL
            THEN ABS(@bronze_value - @parquet_value)
            ELSE NULL
        END;

    /* =========================================
       2️⃣ Sécurisation timestamps Synapse
       ========================================= */
    IF @synapse_start_ts IS NULL
        SET @synapse_start_ts = SYSUTCDATETIME();

    IF @synapse_end_ts IS NULL
        SET @synapse_end_ts = SYSUTCDATETIME();

    IF @synapse_end_ts < @synapse_start_ts
        SET @synapse_end_ts = @synapse_start_ts;

    SET @duration_sec =
        DATEDIFF(SECOND, @synapse_start_ts, @synapse_end_ts);

    /* =========================================
       3️⃣ Insert Integrity Result (nouvelle structure)
       ========================================= */
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

        @delta,

        @status,
        @execution_time_ms,

        @synapse_start_ts,
        @synapse_end_ts,

        SYSUTCDATETIME()
    );
END;
GO
