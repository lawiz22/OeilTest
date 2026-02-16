-- Source: sql/synapse/procedures/SP_OEIL_ROWCOUNT.sql
-- Placeholders:
--   {{bronze_path}}  ex: bronze/clients/period=Q/year=2026/month=05/day=01/data/*.csv
--   {{parquet_path}} ex: standardized/clients/year=2026/month=05/day=01/*.parquet

WITH bronze_data AS (
    SELECT COUNT(*) AS bronze_count
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
    SELECT COUNT(*) AS parquet_count
    FROM OPENROWSET(
        BULK '{{parquet_path}}',
        DATA_SOURCE = 'ds_adls_standardized',
        FORMAT = 'PARQUET'
    ) AS rows
)
SELECT
    b.bronze_count,
    p.parquet_count,
    (b.bronze_count - p.parquet_count) AS delta_count,
    CASE
        WHEN b.bronze_count = p.parquet_count THEN 'PASS'
        ELSE 'FAIL'
    END AS integrity_status
FROM bronze_data b
CROSS JOIN parquet_data p;
