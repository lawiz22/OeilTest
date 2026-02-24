SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

SET NOCOUNT ON;

PRINT '=== Release start: ctrl.SP_GET_DETECTED_STRUCTURE_HASH (Synapse) ===';
GO

CREATE OR ALTER PROCEDURE ctrl.SP_GET_DETECTED_STRUCTURE_HASH
(
    @dataset_name NVARCHAR(150)
)
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @json NVARCHAR(MAX);
    DECLARE @target_object NVARCHAR(300) = N'ext.' + @dataset_name + N'_pq';

    SELECT @json =
    (
        SELECT
            ORDINAL_POSITION AS ordinal,
            COLUMN_NAME AS name,
            LOWER(DATA_TYPE) AS type_detected
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'ext'
          AND TABLE_NAME = @dataset_name + '_pq'
        ORDER BY ORDINAL_POSITION
        FOR JSON PATH
    );

    IF @json IS NULL OR @json = '[]'
    BEGIN
        DECLARE @msg NVARCHAR(500) =
            N'SP_GET_DETECTED_STRUCTURE_HASH: no columns found for object [' + @target_object + N'] in INFORMATION_SCHEMA.COLUMNS.';
        THROW 50021, @msg, 1;
    END;

    SELECT
        @json AS detected_structure_json,
        CONVERT(VARCHAR(64), HASHBYTES('SHA2_256', @json), 2) AS detected_structural_hash;
END;
GO

PRINT '=== Release completed: ctrl.SP_GET_DETECTED_STRUCTURE_HASH (Synapse) ===';
