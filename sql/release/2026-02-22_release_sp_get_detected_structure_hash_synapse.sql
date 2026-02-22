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

    SELECT @json =
    (
        SELECT
            ORDINAL_POSITION AS ordinal,
            COLUMN_NAME AS name,
            DATA_TYPE AS type_detected
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'ext'
          AND TABLE_NAME = @dataset_name + '_pq'
        ORDER BY ORDINAL_POSITION
        FOR JSON PATH
    );

    SELECT
        @json AS detected_structure_json,
        CONVERT(VARCHAR(64), HASHBYTES('SHA2_256', @json), 2) AS detected_structural_hash;
END;
GO

PRINT '=== Release completed: ctrl.SP_GET_DETECTED_STRUCTURE_HASH (Synapse) ===';
