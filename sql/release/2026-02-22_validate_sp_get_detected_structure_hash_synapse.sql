SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

SET NOCOUNT ON;

PRINT '=== Validation start: ctrl.SP_GET_DETECTED_STRUCTURE_HASH (Synapse) ===';

DECLARE @dataset_name NVARCHAR(150) = N'clients'; -- TODO: adapter au dataset à tester
DECLARE @target_object NVARCHAR(300) = N'ext.' + @dataset_name + N'_pq';

IF OBJECT_ID('ctrl.SP_GET_DETECTED_STRUCTURE_HASH', 'P') IS NULL
BEGIN
    RAISERROR('Procédure ctrl.SP_GET_DETECTED_STRUCTURE_HASH introuvable.', 16, 1);
    RETURN;
END;

IF NOT EXISTS
(
    SELECT 1
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'ext'
      AND TABLE_NAME = @dataset_name + '_pq'
)
BEGIN
    RAISERROR('Aucune colonne trouvée pour %s (objet absent ou vide dans INFORMATION_SCHEMA.COLUMNS).', 16, 1, @target_object);
    RETURN;
END;

DECLARE @result TABLE
(
    detected_structure_json NVARCHAR(MAX),
    detected_structural_hash VARCHAR(64)
);

INSERT INTO @result (detected_structure_json, detected_structural_hash)
EXEC ctrl.SP_GET_DETECTED_STRUCTURE_HASH @dataset_name = @dataset_name;

IF NOT EXISTS (SELECT 1 FROM @result)
BEGIN
    RAISERROR('La procédure n''a retourné aucune ligne.', 16, 1);
    RETURN;
END;

IF EXISTS
(
    SELECT 1
    FROM @result
    WHERE detected_structure_json IS NULL
       OR detected_structural_hash IS NULL
       OR LEN(detected_structural_hash) <> 64
)
BEGIN
    RAISERROR('Résultat invalide: JSON ou hash manquant, ou hash non conforme (64 caractères attendus).', 16, 1);
    RETURN;
END;

SELECT
    @dataset_name AS dataset_name,
    @target_object AS synapse_object,
    detected_structure_json,
    detected_structural_hash
FROM @result;

PRINT 'Validation OK: JSON et hash détecté conformes.';
PRINT '=== Validation completed: ctrl.SP_GET_DETECTED_STRUCTURE_HASH (Synapse) ===';
