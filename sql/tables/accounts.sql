-- =====================================================
-- 👁️ L'ŒIL — accounts
-- =====================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'accounts')
CREATE TABLE dbo.accounts (
    account_id      INT,
    client_id       INT,
    account_type    VARCHAR(20),
    currency        CHAR(3),
    balance         DECIMAL(18,2),
    open_date       DATE
);
GO
