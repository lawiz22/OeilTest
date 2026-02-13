-- =====================================================
-- 👁️ L'ŒIL v2 — vigie_policy_table
-- =====================================================
-- Policy de gouvernance par dataset.
-- Source de vérité pour activer/désactiver les contrôles
-- et adapter par environnement (DEV / PROD).
-- =====================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'vigie_policy_table')
CREATE TABLE dbo.vigie_policy_table (
    dataset             VARCHAR(100)    NOT NULL PRIMARY KEY,
    environment         VARCHAR(10)     NOT NULL DEFAULT 'PROD',   -- DEV | PROD
    enabled             BIT             NOT NULL DEFAULT 1,
    synapse_allowed     BIT             NOT NULL DEFAULT 1,
    description         VARCHAR(500)    NULL,
    created_ts          DATETIME2       DEFAULT SYSUTCDATETIME(),
    updated_ts          DATETIME2       DEFAULT SYSUTCDATETIME()
);
GO

-- =====================================================
-- Seed example policies
-- =====================================================
-- INSERT INTO dbo.vigie_policy_table (dataset, environment, enabled, synapse_allowed, description)
-- VALUES
--     ('clients',      'PROD', 1, 1, 'Client master data – monthly'),
--     ('accounts',     'PROD', 1, 1, 'Account data – weekly'),
--     ('transactions', 'PROD', 1, 1, 'Transaction data – daily'),
--     ('contracts',    'PROD', 1, 0, 'Contract data – monthly, no Synapse');
