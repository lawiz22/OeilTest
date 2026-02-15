CREATE OR ALTER PROCEDURE ctrl.SP_OEIL_MIN_MAX
    @bronze_path NVARCHAR(500),
    @parquet_path NVARCHAR(500),
    @column_name NVARCHAR(128)
AS
BEGIN

    DECLARE @sql NVARCHAR(MAX);

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
        b.bronze_min,
        b.bronze_max,
        p.parquet_min,
        p.parquet_max,
        CASE 
            WHEN b.bronze_min = p.parquet_min
             AND b.bronze_max = p.parquet_max
            THEN ''PASS''
            ELSE ''FAIL''
        END AS integrity_status
    FROM bronze_data b
    CROSS JOIN parquet_data p;
    ';

    EXEC sp_executesql @sql;

END;