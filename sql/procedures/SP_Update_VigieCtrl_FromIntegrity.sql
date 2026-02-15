CREATE OR ALTER PROCEDURE dbo.SP_Update_VigieCtrl_FromIntegrity
    @ctrl_id NVARCHAR(150)
AS
BEGIN

    SET NOCOUNT ON;

    DECLARE 
        @synapse_start_ts DATETIME2,
        @synapse_end_ts   DATETIME2,
        @synapse_duration_sec INT,
        @rowcount INT,
        @status NVARCHAR(30);

    -- On prend le dernier ROWCOUNT pour ce ctrl_id
    SELECT TOP 1
        @synapse_start_ts = synapse_start_ts,
        @synapse_end_ts   = synapse_end_ts,
        @synapse_duration_sec = 
            DATEDIFF(SECOND, synapse_start_ts, synapse_end_ts),
        @rowcount = CAST(min_value AS INT),
        @status = status
    FROM dbo.vigie_integrity_result
    WHERE ctrl_id = @ctrl_id
      AND test_code = 'ROWCOUNT'
    ORDER BY integrity_result_id DESC;

    UPDATE dbo.vigie_ctrl
    SET
        synapse_start_ts     = @synapse_start_ts,
        synapse_end_ts       = @synapse_end_ts,
        synapse_duration_sec = @synapse_duration_sec,
        row_count_adf_ingestion_copie_parquet = @rowcount,
        status = @status
    WHERE ctrl_id = @ctrl_id;

END;
