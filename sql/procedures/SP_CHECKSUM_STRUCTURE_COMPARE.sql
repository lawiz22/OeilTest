CREATE OR ALTER PROCEDURE ctrl.SP_CHECKSUM_STRUCTURE_COMPARE
(
    @ctrl_id        NVARCHAR(150),
    @dataset_name   NVARCHAR(150),
    @contract_hash  VARBINARY(32),
    @detected_hash  VARBINARY(32)
)
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @status NVARCHAR(30);

    ---------------------------------------------------------
    -- 1️⃣ Comparaison des hash
    ---------------------------------------------------------
    SET @status =
        CASE 
            WHEN @contract_hash = @detected_hash THEN 'PASS'
            ELSE 'FAIL'
        END;

    ---------------------------------------------------------
    -- 2️⃣ Insertion dans vigie_integrity_result
    ---------------------------------------------------------
    INSERT INTO dbo.vigie_integrity_result
    (
        ctrl_id,
        dataset_name,
        test_code,
        observed_value_text,
        reference_value_text,
        status
    )
    VALUES
    (
        @ctrl_id,
        @dataset_name,
        'CHECKSUM_STRUCTURE',
        CONVERT(NVARCHAR(66), @detected_hash, 1),
        CONVERT(NVARCHAR(66), @contract_hash, 1),
        @status
    );

    ---------------------------------------------------------
    -- 3️⃣ Si FAIL → on bloque le pipeline
    ---------------------------------------------------------
    IF @status = 'FAIL'
    BEGIN
        DECLARE @msg NVARCHAR(500);

        SET @msg =
            'CHECKSUM_STRUCTURE FAILED for dataset [' 
            + @dataset_name 
            + '] - Contract hash: '
            + CONVERT(NVARCHAR(66), @contract_hash, 1)
            + ' | Detected hash: '
            + CONVERT(NVARCHAR(66), @detected_hash, 1);

        THROW 50001, @msg, 1;
    END;

    ---------------------------------------------------------
    -- 4️⃣ Retour propre si PASS
    ---------------------------------------------------------
    SELECT 
        @dataset_name AS dataset_name,
        CONVERT(NVARCHAR(66), @contract_hash, 1) AS contract_hash,
        CONVERT(NVARCHAR(66), @detected_hash, 1) AS detected_hash,
        @status AS status;

END;
