CREATE OR ALTER PROCEDURE ctrl.SP_REFRESH_STRUCTURAL_HASH
(
    @dataset_name VARCHAR(100) = NULL  -- NULL = tous les datasets
)
AS
BEGIN

    SET NOCOUNT ON;

    DECLARE @dataset_id INT;
    DECLARE @json NVARCHAR(MAX);
    DECLARE @hash VARBINARY(32);

    DECLARE dataset_cursor CURSOR FOR
    SELECT dataset_id
    FROM ctrl.dataset
    WHERE (@dataset_name IS NULL OR dataset_name = @dataset_name)
      AND is_active = 1;

    OPEN dataset_cursor;

    FETCH NEXT FROM dataset_cursor INTO @dataset_id;

    WHILE @@FETCH_STATUS = 0
    BEGIN

        -- Générer JSON déterministe
        SELECT @json =
        (
            SELECT
                d.dataset_name AS [dataset],
                d.source_system,
                d.mapping_version,
                (
                    SELECT
                        c.ordinal,
                        c.column_name AS [name],
                        c.type_source,
                        c.type_sink,
                        c.nullable,
                        c.is_key,
                        c.key_ordinal,
                        c.is_tokenized,
                        c.normalization_rule,
                        c.is_control_excluded
                    FROM ctrl.dataset_column c
                    WHERE c.dataset_id = d.dataset_id
                    ORDER BY c.ordinal
                    FOR JSON PATH
                ) AS columns
            FROM ctrl.dataset d
            WHERE d.dataset_id = @dataset_id
            FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
        );

        -- Calcul SHA256
        SET @hash = HASHBYTES('SHA2_256', @json);

        -- Mise à jour
        UPDATE ctrl.dataset
        SET structural_hash = @hash
        WHERE dataset_id = @dataset_id;

        FETCH NEXT FROM dataset_cursor INTO @dataset_id;

    END

    CLOSE dataset_cursor;
    DEALLOCATE dataset_cursor;

END;
