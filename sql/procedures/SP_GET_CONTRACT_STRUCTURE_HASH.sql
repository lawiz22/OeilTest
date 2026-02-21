SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE OR ALTER PROCEDURE [ctrl].[SP_GET_CONTRACT_STRUCTURE_HASH]
(
    @dataset_name VARCHAR(100)
)
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @json_contract NVARCHAR(MAX);
    DECLARE @hash_contract VARBINARY(32);

    SELECT @json_contract =
    (
        SELECT
            c.ordinal,
            c.column_name AS [name],
            CASE 
                WHEN c.type_sink = 'INT' THEN 'int'
                WHEN c.type_sink = 'BIGINT' THEN 'bigint'
                WHEN c.type_sink = 'DATE' THEN 'date'
                WHEN c.type_sink IN ('DATETIME','DATETIME2') THEN 'datetime2'
                WHEN c.type_sink LIKE 'VARCHAR%' THEN 'varchar'
                WHEN c.type_sink LIKE 'CHAR%' THEN 'char'
                WHEN c.type_sink LIKE 'DECIMAL%' THEN 'decimal'
                ELSE LOWER(c.type_sink)
            END AS type_detected
        FROM ctrl.dataset_column c
        JOIN ctrl.dataset d
            ON c.dataset_id = d.dataset_id
        WHERE d.dataset_name = @dataset_name
        ORDER BY c.ordinal
        FOR JSON PATH
    );

    SET @hash_contract = HASHBYTES('SHA2_256', @json_contract);

    SELECT 
        @json_contract AS contract_structure_json,
        @hash_contract AS contract_structural_hash;
END;
GO
