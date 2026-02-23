CREATE   PROCEDURE ctrl.SP_OEIL_MIN_MAX_PQ
(
    @dataset_name NVARCHAR(150),
    @column_name NVARCHAR(128),
    @expected_min FLOAT,
    @expected_max FLOAT,
    @year NVARCHAR(4),
    @month NVARCHAR(2),
    @day NVARCHAR(2)
)
AS
BEGIN
    DECLARE @sql NVARCHAR(MAX);

    SET @sql = '
        SELECT
            MIN(TRY_CAST(' + QUOTENAME(@column_name) + ' AS FLOAT)) AS detected_min,
            MAX(TRY_CAST(' + QUOTENAME(@column_name) + ' AS FLOAT)) AS detected_max
        FROM OPENROWSET(
            BULK ''standardized/' + @dataset_name + 
            '/year=' + @year + 
            '/month=' + @month + 
            '/day=' + @day + 
            '/*.parquet'',
            DATA_SOURCE = ''ds_adls_standardized'',
            FORMAT = ''PARQUET''
        ) AS rows;
    ';

    CREATE TABLE #t (
        detected_min FLOAT,
        detected_max FLOAT
    );

    INSERT INTO #t
    EXEC(@sql);

    DECLARE @detected_min FLOAT;
    DECLARE @detected_max FLOAT;

    SELECT 
        @detected_min = detected_min,
        @detected_max = detected_max
    FROM #t;

    SELECT
        @detected_min AS parquet_min,
        @detected_max AS parquet_max,
        @expected_min AS contract_min,
        @expected_max AS contract_max,
        CASE 
            WHEN @detected_min = @expected_min
             AND @detected_max = @expected_max
            THEN 'OK'
            ELSE 'ANOMALY'
        END AS integrity_status;
END;