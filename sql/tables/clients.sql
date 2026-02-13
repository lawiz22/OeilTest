-- =====================================================
-- 👁️ L'ŒIL — clients
-- =====================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name = 'clients')
CREATE TABLE dbo.clients (
    client_id       INT,
    client_type     VARCHAR(20),
    pays            VARCHAR(50),
    statut          VARCHAR(20),
    date_effet      DATE
);
GO
