-- =====================================================
-- 👁️ L'ŒIL v2 — vigie_policy_test
-- =====================================================
-- Tests activés par dataset.
-- Chaque ligne = 1 test (row_count, min_max, checksum, etc.)
-- configurable par fréquence, colonne cible, et environnement.
-- =====================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'vigie_policy_test')
CREATE TABLE dbo.vigie_policy_test (
    id                  INT IDENTITY(1,1) PRIMARY KEY,
    dataset             VARCHAR(100)    NOT NULL,
    test_type           VARCHAR(30)     NOT NULL,       -- ROW_COUNT | MIN_MAX | CHECKSUM | NULL_COUNT | DELTA_PREV
    enabled             BIT             NOT NULL DEFAULT 1,
    frequency           VARCHAR(10)     NOT NULL DEFAULT 'DAILY',  -- DAILY | WEEKLY | MONTHLY
    target_column       VARCHAR(128)    NULL,            -- Colonne cible (pour min_max, checksum, null_count)
    algorithm           VARCHAR(20)     NULL,            -- SHA256, MD5 (pour checksum)
    threshold_pct       DECIMAL(5,2)    NULL,            -- Seuil de tolérance en %
    environment         VARCHAR(10)     NOT NULL DEFAULT 'PROD',

    CONSTRAINT FK_policy_test_dataset
        FOREIGN KEY (dataset) REFERENCES dbo.vigie_policy_table(dataset)
);
GO

-- =====================================================
-- Seed example tests
-- =====================================================
-- INSERT INTO dbo.vigie_policy_test (dataset, test_type, enabled, frequency, target_column, algorithm)
-- VALUES
--     ('clients',      'ROW_COUNT', 1, 'DAILY',  NULL,          NULL),
--     ('clients',      'MIN_MAX',   1, 'DAILY',  'client_id',   NULL),
--     ('clients',      'CHECKSUM',  1, 'WEEKLY', 'client_id',   'SHA256'),
--     ('accounts',     'ROW_COUNT', 1, 'DAILY',  NULL,          NULL),
--     ('accounts',     'MIN_MAX',   1, 'DAILY',  'account_id',  NULL),
--     ('transactions', 'ROW_COUNT', 1, 'DAILY',  NULL,          NULL),
--     ('transactions', 'CHECKSUM',  1, 'DAILY',  'transaction_id', 'SHA256'),
--     ('transactions', 'NULL_COUNT',1, 'WEEKLY', 'amount',      NULL);
