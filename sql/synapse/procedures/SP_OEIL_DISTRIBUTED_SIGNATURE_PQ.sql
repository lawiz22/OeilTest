CREATE OR ALTER PROCEDURE ctrl.SP_OEIL_DISTRIBUTED_SIGNATURE_PQ
    @dataset_name        NVARCHAR(100),
    @column_name         NVARCHAR(128),
    @expected_signature  NVARCHAR(64),
    @year                NVARCHAR(4),
    @month               NVARCHAR(2),
    @day                 NVARCHAR(2)
AS
BEGIN

    DECLARE @sql NVARCHAR(MAX);

    SET @sql = '
    WITH dataset_stats AS (
        SELECT
            COUNT(*) AS row_count,
            MIN(' + QUOTENAME(@column_name) + ') AS min_val,
            MAX(' + QUOTENAME(@column_name) + ') AS max_val,
            SUM(CAST(' + QUOTENAME(@column_name) + ' AS BIGINT)) AS sum_val,
            SUM(CHECKSUM(' + QUOTENAME(@column_name) + ')) AS sum_checksum_val,
            SUM(BINARY_CHECKSUM(' + QUOTENAME(@column_name) + ')) AS sum_binary_checksum_val
        FROM OPENROWSET(
            BULK ''standardized/' + @dataset_name + '/year=' + @year + '/month=' + @month + '/day=' + @day + '/*.parquet'',
            DATA_SOURCE = ''ds_adls_standardized'',
            FORMAT = ''PARQUET''
        ) AS rows
    )
    SELECT
        row_count,
        min_val,
        max_val,
        sum_val,
        sum_checksum_val,
        sum_binary_checksum_val,

        CONCAT(
            row_count,''|'',
            min_val,''|'',
            max_val,''|'',
            sum_val,''|'',
            sum_checksum_val,''|'',
            sum_binary_checksum_val
        ) AS signature_input_string,

        LOWER(CONVERT(VARCHAR(64),
            HASHBYTES(
                ''SHA2_256'',
                CONCAT(
                    row_count,''|'',
                    min_val,''|'',
                    max_val,''|'',
                    sum_val,''|'',
                    sum_checksum_val,''|'',
                    sum_binary_checksum_val
                )
            ), 2
        )) AS parquet_signature,

        LOWER(@expected_signature) AS contract_signature,

        CASE
            WHEN LOWER(CONVERT(VARCHAR(64),
                HASHBYTES(
                    ''SHA2_256'',
                    CONCAT(
                        row_count,''|'',
                        min_val,''|'',
                        max_val,''|'',
                        sum_val,''|'',
                        sum_checksum_val,''|'',
                        sum_binary_checksum_val
                    )
                ), 2
            )) = LOWER(@expected_signature)
            THEN ''PASS''
            ELSE ''FAIL''
        END AS integrity_status

    FROM dataset_stats;
    ';

    EXEC sp_executesql
        @sql,
        N'@expected_signature NVARCHAR(64)',
        @expected_signature = @expected_signature;

END;
