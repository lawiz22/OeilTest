-- =====================================================
-- 👁️ L'ŒIL v2 — vigie_integrity_result
-- =====================================================
-- Résultats détaillés d'intégrité par run + type de test.
-- Un row par test exécuté, avec valeurs attendues vs réelles
-- et traçabilité du compute engine utilisé.
-- =====================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'vigie_integrity_result')
CREATE TABLE dbo.vigie_integrity_result (
    id                  BIGINT IDENTITY(1,1) PRIMARY KEY,
    ctrl_id             VARCHAR(200)    NOT NULL,
    dataset             VARCHAR(100)    NOT NULL,
    test_type           VARCHAR(30)     NOT NULL,       -- ROW_COUNT | MIN_MAX | CHECKSUM | NULL_COUNT | DELTA_PREV
    target_column       VARCHAR(128)    NULL,
    result_status       VARCHAR(20)     NOT NULL,       -- OK | FAIL | SKIPPED
    expected_value      VARCHAR(500)    NULL,
    actual_value        VARCHAR(500)    NULL,
    detail_json         NVARCHAR(MAX)   NULL,           -- Full detail payload (JSON)
    computed_ts         DATETIME2       DEFAULT SYSUTCDATETIME(),
    compute_engine      VARCHAR(20)     DEFAULT 'PYTHON',  -- PYTHON | SYNAPSE | ADF
    compute_cost_cad    DECIMAL(10,6)   NULL
);
GO

-- =====================================================
-- Index for fast lookup by ctrl_id
-- =====================================================
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_integrity_result_ctrl_id')
CREATE NONCLUSTERED INDEX IX_integrity_result_ctrl_id
    ON dbo.vigie_integrity_result (ctrl_id);
GO
