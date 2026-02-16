-- Source: sql/synapse/procedures/SP_OEIL_MIN_MAX.sql
-- Placeholders:
--   {{bronze_path}}  ex: bronze/clients/period=Q/year=2026/month=05/day=01/data/*.csv
--   {{parquet_path}} ex: standardized/clients/year=2026/month=05/day=01/*.parquet
--   {{column_name}}  ex: client_id

WITH bronze_data AS (
    SELECT
        MIN({{column_name}}) AS bronze_min,
        MAX({{column_name}}) AS bronze_max
    FROM OPENROWSET(
        BULK '{{bronze_path}}',
        DATA_SOURCE = 'ds_adls_bronze',
        FORMAT = 'CSV',
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
        MIN({{column_name}}) AS parquet_min,
        MAX({{column_name}}) AS parquet_max
    FROM OPENROWSET(
        BULK '{{parquet_path}}',
        DATA_SOURCE = 'ds_adls_standardized',
        FORMAT = 'PARQUET'
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
        THEN 'PASS'
        ELSE 'FAIL'
    END AS integrity_status
FROM bronze_data b
CROSS JOIN parquet_data p;
