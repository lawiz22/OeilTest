CREATE OR ALTER PROCEDURE ctrl.SP_OEIL_CHECKSUM
(
    @bronze_path NVARCHAR(500),
    @parquet_path NVARCHAR(500),
    @column_name NVARCHAR(150)
)
AS
BEGIN

    SET NOCOUNT ON;

    DECLARE @sql NVARCHAR(MAX);

    SET @sql = '
    WITH bronze_data AS (
        SELECT CAST(' + @column_name + ' AS NVARCHAR(100)) AS val
        FROM OPENROWSET(
            BULK ''' + @bronze_path + ''',
            DATA_SOURCE = ''DS_BRONZE'',
            FORMAT = ''CSV'',
            PARSER_VERSION = ''2.0''
        ) AS rows
    ),
    parquet_data AS (
        SELECT CAST(' + @column_name + ' AS NVARCHAR(100)) AS val
        FROM OPENROWSET(
            BULK ''' + @parquet_path + ''',
            DATA_SOURCE = ''DS_STANDARDIZED'',
            FORMAT = ''PARQUET''
        ) AS rows
    ),
    bronze_hash AS (
        SELECT 
            LOWER(CONVERT(VARCHAR(64),
                HASHBYTES(''SHA2_256'',
                    STRING_AGG(val, ''|'') 
                    WITHIN GROUP (ORDER BY val)
                ), 2)
            ) AS checksum_value
        FROM bronze_data
    ),
    parquet_hash AS (
        SELECT 
            LOWER(CONVERT(VARCHAR(64),
                HASHBYTES(''SHA2_256'',
                    STRING_AGG(val, ''|'') 
                    WITHIN GROUP (ORDER BY val)
                ), 2)
            ) AS checksum_value
        FROM parquet_data
    )
    SELECT 
        b.checksum_value AS bronze_checksum,
        p.checksum_value AS parquet_checksum,
        CASE 
            WHEN b.checksum_value = p.checksum_value THEN ''PASS''
            ELSE ''FAIL''
        END AS integrity_status
    FROM bronze_hash b
    CROSS JOIN parquet_hash p;
    ';

    EXEC sp_executesql @sql;

END;
GO

