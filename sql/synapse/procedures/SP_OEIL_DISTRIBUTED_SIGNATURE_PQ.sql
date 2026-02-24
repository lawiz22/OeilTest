CREATE OR ALTER PROCEDURE ctrl.SP_OEIL_DISTRIBUTED_SIGNATURE_PQ
    @dataset_name        NVARCHAR(100),
    @column_name         NVARCHAR(128),
    @expected_signature  NVARCHAR(64),
    @year                NVARCHAR(4),
    @month               NVARCHAR(2),
    @day                 NVARCHAR(2)
AS
BEGIN

    IF @dataset_name IS NULL OR LTRIM(RTRIM(@dataset_name)) = ''
        THROW 50001, 'SP_OEIL_DISTRIBUTED_SIGNATURE_PQ: @dataset_name is required.', 1;

    IF @column_name IS NULL OR LTRIM(RTRIM(@column_name)) = ''
        THROW 50002, 'SP_OEIL_DISTRIBUTED_SIGNATURE_PQ: @column_name is required and cannot be empty.', 1;

    IF @expected_signature IS NULL OR LTRIM(RTRIM(@expected_signature)) = ''
        THROW 50003, 'SP_OEIL_DISTRIBUTED_SIGNATURE_PQ: @expected_signature is required.', 1;

    SET @dataset_name = LTRIM(RTRIM(@dataset_name));
    SET @column_name = LTRIM(RTRIM(@column_name));
    SET @expected_signature = LTRIM(RTRIM(@expected_signature));

    DECLARE @sql NVARCHAR(MAX);

    SET @sql = '
    WITH dataset_stats AS (
        SELECT
            COUNT_BIG(*) AS row_count,
            MIN(' + QUOTENAME(@column_name) + ') AS min_val,
            MAX(' + QUOTENAME(@column_name) + ') AS max_val,
            SUM(CAST(' + QUOTENAME(@column_name) + ' AS BIGINT)) AS sum_val,
            SUM(CAST(CHECKSUM(' + QUOTENAME(@column_name) + ') AS BIGINT)) AS sum_checksum_val,
            SUM(CAST(BINARY_CHECKSUM(' + QUOTENAME(@column_name) + ') AS BIGINT)) AS sum_binary_checksum_val
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
