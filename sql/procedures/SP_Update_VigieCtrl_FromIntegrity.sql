SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

ALTER PROCEDURE [dbo].[SP_Update_VigieCtrl_FromIntegrity]
    @ctrl_id NVARCHAR(150)
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE 
        @bronze INT,
        @parquet INT,
        @expected INT,
        @status NVARCHAR(30),
        @synapse_start_ts DATETIME2,
        @synapse_end_ts DATETIME2,
        @synapse_duration_sec INT;

    /* =========================================
       1️⃣ Récupération ROW_COUNT depuis integrity
       ========================================= */
    SELECT TOP 1
        @bronze = CAST(observed_value_num AS INT),
        @parquet = CAST(reference_value_num AS INT),
        @status = status,
        @synapse_start_ts = synapse_start_ts,
        @synapse_end_ts = synapse_end_ts,
        @synapse_duration_sec =
            DATEDIFF(SECOND, synapse_start_ts, synapse_end_ts)
    FROM dbo.vigie_integrity_result
    WHERE ctrl_id = @ctrl_id
      AND test_code = 'ROW_COUNT'
    ORDER BY integrity_result_id DESC;

    /* =========================================
       2️⃣ Récupération expected_rows depuis ctrl
       ========================================= */
    SELECT @expected = expected_rows
    FROM dbo.vigie_ctrl
    WHERE ctrl_id = @ctrl_id;

    /* =========================================
       3️⃣ Mise à jour vigie_ctrl
       ========================================= */
    UPDATE dbo.vigie_ctrl
    SET
        bronze_rows  = @bronze,
        bronze_delta = @bronze - @expected,
        bronze_status =
            CASE
                WHEN @bronze IS NULL THEN 'MISSING'
                WHEN @bronze = @expected THEN 'OK'
                ELSE 'MISMATCH'
            END,

        parquet_rows  = @parquet,
        parquet_delta = @parquet - @expected,
        parquet_status =
            CASE
                WHEN @parquet IS NULL THEN 'MISSING'
                WHEN @parquet = @expected THEN 'OK'
                ELSE 'MISMATCH'
            END,

        synapse_start_ts     = @synapse_start_ts,
        synapse_end_ts       = @synapse_end_ts,
        synapse_duration_sec = @synapse_duration_sec,

        status = @status
    WHERE ctrl_id = @ctrl_id;
END;
GO
