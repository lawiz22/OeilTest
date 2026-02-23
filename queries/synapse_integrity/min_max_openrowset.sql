-- Source: sql/synapse/procedures/SP_OEIL_MIN_MAX.sql (proc: ctrl.SP_OEIL_MIN_MAX_PQ)
-- Placeholders:
--   {{dataset_name}} ex: clients
--   {{year}}         ex: 2026
--   {{month}}        ex: 05
--   {{day}}          ex: 01
--   {{column_name}}  ex: client_id

SELECT
    MIN(TRY_CAST({{column_name}} AS FLOAT)) AS detected_min,
    MAX(TRY_CAST({{column_name}} AS FLOAT)) AS detected_max
FROM OPENROWSET(
    BULK 'standardized/{{dataset_name}}/year={{year}}/month={{month}}/day={{day}}/*.parquet',
    DATA_SOURCE = 'ds_adls_standardized',
    FORMAT = 'PARQUET'
) AS rows;
