CREATE OR ALTER PROCEDURE ctrl.SP_OEIL_ROWCOUNT
    @bronze_path NVARCHAR(500),
    @parquet_path NVARCHAR(500)
AS
BEGIN

    DECLARE @sql NVARCHAR(MAX);

    SET @sql = '
    WITH bronze_data AS (
        SELECT COUNT(*) AS bronze_count
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
        SELECT COUNT(*) AS parquet_count
        FROM OPENROWSET(
            BULK ''' + @parquet_path + ''',
            DATA_SOURCE = ''ds_adls_standardized'',
            FORMAT = ''PARQUET''
        ) AS rows
    )
    SELECT
        b.bronze_count,
        p.parquet_count,
        (b.bronze_count - p.parquet_count) AS delta_count,
        CASE 
            WHEN b.bronze_count = p.parquet_count
            THEN ''PASS''
            ELSE ''FAIL''
        END AS integrity_status
    FROM bronze_data b
    CROSS JOIN parquet_data p;
    ';

    EXEC sp_executesql @sql;

END;
