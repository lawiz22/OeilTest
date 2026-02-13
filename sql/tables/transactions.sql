-- =====================================================
-- 👁️ L'ŒIL — transactions
-- =====================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'transactions')
CREATE TABLE dbo.transactions (
    transaction_id  BIGINT,
    account_id      INT,
    amount          DECIMAL(18,2),
    currency        CHAR(3),
    transaction_ts  DATETIME2,
    ingestion_date  DATE
);
GO
