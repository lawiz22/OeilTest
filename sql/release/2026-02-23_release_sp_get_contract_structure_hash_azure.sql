SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

SET NOCOUNT ON;

PRINT '=== Release start: ctrl.SP_GET_CONTRACT_STRUCTURE_HASH (Azure SQL) ===';

IF OBJECT_ID('ctrl.SP_GET_CONTRACT_STRUCTURE_HASH', 'P') IS NULL
BEGIN
    PRINT 'Procedure ctrl.SP_GET_CONTRACT_STRUCTURE_HASH does not exist yet. It will be created.';
END
ELSE
BEGIN
    PRINT 'Existing procedure found. Replacing definition with Synapse-gate aligned computation.';
END;
GO

CREATE OR ALTER PROCEDURE [ctrl].[SP_GET_CONTRACT_STRUCTURE_HASH]
(
    @dataset_name NVARCHAR(150)
)
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @json_contract NVARCHAR(MAX);

    SELECT @json_contract =
    (
        SELECT
            c.ordinal,
            c.column_name AS [name],
            CASE
                WHEN c.type_sink = 'INT' THEN 'int'
                WHEN c.type_sink = 'BIGINT' THEN 'bigint'
                WHEN c.type_sink = 'DATE' THEN 'date'
                WHEN c.type_sink IN ('DATETIME', 'DATETIME2') THEN 'datetime2'
                WHEN c.type_sink LIKE 'VARCHAR%' THEN 'varchar'
                WHEN c.type_sink LIKE 'CHAR%' THEN 'char'
                WHEN c.type_sink LIKE 'DECIMAL%' THEN 'decimal'
                ELSE LOWER(c.type_sink)
            END AS type_detected
        FROM ctrl.dataset_column c
        INNER JOIN ctrl.dataset d
            ON c.dataset_id = d.dataset_id
        WHERE d.dataset_name = @dataset_name
        ORDER BY c.ordinal
        FOR JSON PATH
    );

    IF @json_contract IS NULL
    BEGIN
        THROW 50011, 'No contract structure found in ctrl.dataset_column for provided dataset_name.', 1;
    END;

    SELECT
        @json_contract AS contract_structure_json,
        CONVERT(VARCHAR(64), HASHBYTES('SHA2_256', @json_contract), 2) AS contract_structural_hash;
END;
GO

PRINT '=== Release completed: ctrl.SP_GET_CONTRACT_STRUCTURE_HASH (Azure SQL) ===';
