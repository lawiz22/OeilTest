CREATE OR ALTER PROCEDURE dbo.SP_Insert_VigieIntegrityResult
    @ctrl_id NVARCHAR(150),
    @dataset_name NVARCHAR(150),
    @test_code NVARCHAR(50),
    @column_name NVARCHAR(150),
    @bronze_min FLOAT,
    @bronze_max FLOAT,
    @parquet_min FLOAT,
    @parquet_max FLOAT,
    @status NVARCHAR(30),
    @execution_time_ms INT = NULL
AS
BEGIN

    SET NOCOUNT ON;

    DECLARE @delta FLOAT;

    SET @delta = ABS(ISNULL(@bronze_max,0) - ISNULL(@parquet_max,0));

    INSERT INTO dbo.vigie_integrity_result
    (
        ctrl_id,
        dataset_name,
        test_code,
        column_name,
        min_value,
        max_value,
        expected_value,
        delta_value,
        status,
        execution_time_ms,
        created_at
    )
    VALUES
    (
        @ctrl_id,
        @dataset_name,
        @test_code,
        @column_name,
        @bronze_min,
        @bronze_max,
        @parquet_min,
        @delta,
        @status,
        @execution_time_ms,
        SYSUTCDATETIME()
    );

END;
