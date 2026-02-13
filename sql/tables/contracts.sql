-- =====================================================
-- 👁️ L'ŒIL — contracts
-- =====================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'contracts')
CREATE TABLE dbo.contracts (
    contract_id     INT,
    client_id       INT,
    product_type    VARCHAR(30),
    start_date      DATE,
    end_date        DATE,
    statut          VARCHAR(20)
);
GO
