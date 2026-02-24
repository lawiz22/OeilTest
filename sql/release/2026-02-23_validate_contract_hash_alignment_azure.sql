SET NOCOUNT ON;

PRINT '=== Validation start: contract hash alignment (Azure SQL) ===';

DECLARE @dataset_name NVARCHAR(150) = N'clients'; -- change if needed

DECLARE @sp TABLE
(
    contract_structure_json NVARCHAR(MAX),
    contract_structural_hash VARCHAR(64)
);

INSERT INTO @sp (contract_structure_json, contract_structural_hash)
EXEC ctrl.SP_GET_CONTRACT_STRUCTURE_HASH @dataset_name = @dataset_name;

IF NOT EXISTS (SELECT 1 FROM @sp)
BEGIN
    THROW 50031, 'Validation failed: SP_GET_CONTRACT_STRUCTURE_HASH returned no rows.', 1;
END;

DECLARE @inline_json NVARCHAR(MAX);
DECLARE @inline_hash VARCHAR(64);

SELECT @inline_json =
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

SET @inline_hash = CONVERT(VARCHAR(64), HASHBYTES('SHA2_256', @inline_json), 2);

SELECT
    @dataset_name AS dataset_name,
    (SELECT TOP 1 contract_structural_hash FROM @sp) AS sp_contract_hash,
    @inline_hash AS inline_contract_hash,
    CASE
        WHEN (SELECT TOP 1 contract_structural_hash FROM @sp) = @inline_hash THEN 'PASS'
        ELSE 'FAIL'
    END AS status;

IF (SELECT TOP 1 contract_structural_hash FROM @sp) <> @inline_hash
BEGIN
    THROW 50032, 'Validation failed: SP contract hash differs from inline normalized hash.', 1;
END;

PRINT 'Validation OK: SP contract hash matches normalized contract formula.';
PRINT '=== Validation completed: contract hash alignment (Azure SQL) ===';
