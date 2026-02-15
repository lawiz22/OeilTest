CREATE OR ALTER PROCEDURE ctrl.SP_OEIL_MIN_MAX
    @ctrl_id NVARCHAR(150),
    @dataset_name NVARCHAR(150),
    @test_code NVARCHAR(50),
    @bronze_path NVARCHAR(500),
    @parquet_path NVARCHAR(500),
    @column_name NVARCHAR(128)
AS
BEGIN

    DECLARE @sql NVARCHAR(MAX);

    DECLARE @bronze_min FLOAT;
    DECLARE @bronze_max FLOAT;
    DECLARE @parquet_min FLOAT;
    DECLARE @parquet_max FLOAT;

    SET @sql = '
    WITH bronze_data AS (
        SELECT
            MIN(' + QUOTENAME(@column_name) + ') AS bronze_min,
            MAX(' + QUOTENAME(@column_name) + ') AS bronze_max
        FROM OPENROWSET(
            BULK ''' + @bronze_path + ''',
            DATA_SOURCE = ''ds_adls_bronze'',
            FORMAT = ''CSV'',
            FIRSTROW = 2
        )
        WITH (
            client_id INT,
            nom VARCHAR(100),
            prenom VARCHAR(100),
            pays VARCHAR(10),
            date_eff DATE
        ) AS rows
    ),
    parquet_data AS (
        SELECT
            MIN(' + QUOTENAME(@column_name) + ') AS parquet_min,
            MAX(' + QUOTENAME(@column_name) + ') AS parquet_max
        FROM OPENROWSET(
            BULK ''' + @parquet_path + ''',
            DATA_SOURCE = ''ds_adls_standardized'',
            FORMAT = ''PARQUET''
        ) AS rows
    )
    SELECT
        @bronze_min_out = b.bronze_min,
        @bronze_max_out = b.bronze_max,
        @parquet_min_out = p.parquet_min,
        @parquet_max_out = p.parquet_max
    FROM bronze_data b
    CROSS JOIN parquet_data p;
    ';

    EXEC sp_executesql
        @sql,
        N'@bronze_min_out FLOAT OUTPUT,
          @bronze_max_out FLOAT OUTPUT,
          @parquet_min_out FLOAT OUTPUT,
          @parquet_max_out FLOAT OUTPUT',
        @bronze_min OUTPUT,
        @bronze_max OUTPUT,
        @parquet_min OUTPUT,
        @parquet_max OUTPUT;

    DECLARE @status NVARCHAR(30);

    IF @bronze_min = @parquet_min
       AND @bronze_max = @parquet_max
        SET @status = 'PASS';
    ELSE
        SET @status = 'FAIL';

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
        ABS(@bronze_max - @parquet_max),
        @status,
        SYSUTCDATETIME()
    );

    SELECT
        @bronze_min AS bronze_min,
        @bronze_max AS bronze_max,
        @parquet_min AS parquet_min,
        @parquet_max AS parquet_max,
        @status AS integrity_status;

END;
