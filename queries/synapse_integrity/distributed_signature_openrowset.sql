-- Source: sql/synapse/procedures/SP_OEIL_DISTRIBUTED_SIGNATURE_PQ.sql
-- Placeholders:
--   {{dataset_name}} ex: clients
--   {{year}}         ex: 2026
--   {{month}}        ex: 05
--   {{day}}          ex: 01
--   {{column_name}}  ex: client_id

WITH dataset_stats AS (
    SELECT
        COUNT(*) AS row_count,
        MIN({{column_name}}) AS min_val,
        MAX({{column_name}}) AS max_val,
        SUM(CAST({{column_name}} AS BIGINT)) AS sum_val,
        SUM(CHECKSUM({{column_name}})) AS sum_checksum_val,
        SUM(BINARY_CHECKSUM({{column_name}})) AS sum_binary_checksum_val
    FROM OPENROWSET(
        BULK 'standardized/{{dataset_name}}/year={{year}}/month={{month}}/day={{day}}/*.parquet',
        DATA_SOURCE = 'ds_adls_standardized',
        FORMAT = 'PARQUET'
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
        row_count, '|',
        min_val, '|',
        max_val, '|',
        sum_val, '|',
        sum_checksum_val, '|',
        sum_binary_checksum_val
    ) AS signature_input_string,
    LOWER(CONVERT(VARCHAR(64), HASHBYTES('SHA2_256', CONCAT(
        row_count, '|',
        min_val, '|',
        max_val, '|',
        sum_val, '|',
        sum_checksum_val, '|',
        sum_binary_checksum_val
    )), 2)) AS parquet_signature
FROM dataset_stats;
