CREATE OR ALTER PROCEDURE ctrl.SP_GET_DETECTED_STRUCTURE_HASH
(
    @dataset_name VARCHAR(100)
)
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @table_name SYSNAME;
    DECLARE @json_detected NVARCHAR(MAX);
    DECLARE @hash_detected VARBINARY(32);

    SET @table_name = @dataset_name + '_std';

    DECLARE @sql NVARCHAR(MAX);

    SET @sql = '
    SELECT @json_out =
    (
        SELECT
            ORDINAL_POSITION AS ordinal,
            COLUMN_NAME AS name,
            DATA_TYPE AS type_detected
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = ''ext''
          AND TABLE_NAME = ''' + @table_name + '''
        ORDER BY ORDINAL_POSITION
        FOR JSON PATH
    );';

    EXEC sp_executesql 
        @sql,
        N'@json_out NVARCHAR(MAX) OUTPUT',
        @json_out = @json_detected OUTPUT;

    SET @hash_detected = HASHBYTES('SHA2_256', @json_detected);

    SELECT 
        @json_detected AS detected_structure_json,
        @hash_detected AS detected_structural_hash;
END;
