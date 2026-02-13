-- =============================================================================
-- Stored Procedure : SP_Compute_SLA_Vigie
-- =============================================================================
-- Description : Calcule le SLA global « vigie » par dataset. Contrairement
--               aux SP par moteur (ADF/OEIL/SYNAPSE) qui utilisent
--               sla_profile_execution_type, cette SP utilise la table
--               sla_profile qui définit un profil SLA propre à chaque dataset.
--
-- Logique :
--   1. Récupère le dataset, le row count ADF (parquet) et la durée totale
--      du run depuis vigie_ctrl.
--   2. Charge le profil SLA spécifique au dataset depuis sla_profile
--      (overhead fixe + coût variable par 1K rows + tolérance).
--   3. Calcule le SLA attendu avec la formule :
--        sla_expected  = base_overhead_sec + (rows / 1000) × sec_per_1k_rows
--        sla_threshold = sla_expected × (1 + tolerance_pct)
--   4. Compare la durée réelle au seuil et écrit le verdict :
--        OK   → raison OK_WITHIN_THRESHOLD
--        FAIL → raison EXCEEDED_THRESHOLD
--
-- Différence vs SP par moteur :
--   - Utilise sla_profile (par dataset) au lieu de
--     sla_profile_execution_type (par moteur).
--   - Écrit dans les champs sla_* globaux (pas oeil_sla_*, adf_sla_*, etc.)
--   - La raison du verdict est plus descriptive (OK_WITHIN_THRESHOLD /
--     EXCEEDED_THRESHOLD) vs simplement 'ADF_INGESTION' ou 'OEIL_EXECUTION'.
--   - Feature future : cette SP sera utilisée quand les profils SLA par
--     dataset seront activés en production.
--
-- Cas d'erreur :
--   - Si duration_sec ou row_count sont NULL → statut UNKNOWN,
--     raison NO_ADF_METRICS
--   - Si aucun profil SLA actif n'existe pour le dataset → statut UNKNOWN,
--     raison NO_SLA_PROFILE
--
-- Paramètres :
--   @p_ctrl_id  varchar(200)  — Identifiant du run dans vigie_ctrl
--
-- Tables utilisées :
--   - dbo.vigie_ctrl    (lecture + écriture)
--   - dbo.sla_profile   (lecture)
--
-- Colonnes mises à jour dans vigie_ctrl :
--   sla_sec, sla_expected_sec, sla_threshold_sec, sla_status, sla_reason
-- =============================================================================

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE PROCEDURE [dbo].[SP_Compute_SLA_Vigie]
    @p_ctrl_id varchar(200)
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE
        @dataset                varchar(50),
        @rows_total             int,
        @duration_sec           int,

        @base_overhead_sec      int,
        @sec_per_1k_rows        int,
        @tolerance_pct          decimal(5,2),

        @sla_expected_sec       int,
        @sla_threshold_sec      int;

    /* ===========================
       1. Récupérer données réelles
       =========================== */
    SELECT
        @dataset      = dataset,
        @rows_total   = row_count_adf_ingestion_copie_parquet,
        @duration_sec = duration_sec
    FROM dbo.vigie_ctrl
    WHERE ctrl_id = @p_ctrl_id;

    /* Protection minimale */
    IF @duration_sec IS NULL OR @rows_total IS NULL
    BEGIN
        UPDATE dbo.vigie_ctrl
        SET
            sla_status = 'UNKNOWN',
            sla_reason = 'NO_ADF_METRICS'
        WHERE ctrl_id = @p_ctrl_id;
        RETURN;
    END;

    /* ===========================
       2. Charger profil SLA par dataset
       Note : utilise sla_profile (pas sla_profile_execution_type)
       =========================== */
    SELECT
        @base_overhead_sec = base_overhead_sec,
        @sec_per_1k_rows   = sec_per_1k_rows,
        @tolerance_pct     = tolerance_pct
    FROM dbo.sla_profile
    WHERE dataset = @dataset
      AND active_flag = 1;

    IF @base_overhead_sec IS NULL
    BEGIN
        UPDATE dbo.vigie_ctrl
        SET
            sla_status = 'UNKNOWN',
            sla_reason = 'NO_SLA_PROFILE'
        WHERE ctrl_id = @p_ctrl_id;
        RETURN;
    END;

    /* ===========================
       3. Calcul SLA attendu
       Formule : expected  = overhead + (rows/1000) × cost_per_1k
                 threshold = expected × (1 + tolerance%)
       =========================== */
    SET @sla_expected_sec =
        @base_overhead_sec
        + CAST((@rows_total / 1000.0) * @sec_per_1k_rows AS int);

    SET @sla_threshold_sec =
        CAST(@sla_expected_sec * (1 + @tolerance_pct) AS int);

    /* ===========================
       4. Verdict SLA global
       OK   = durée <= seuil  → OK_WITHIN_THRESHOLD
       FAIL = durée >  seuil  → EXCEEDED_THRESHOLD
       =========================== */
    UPDATE dbo.vigie_ctrl
    SET
        sla_sec           = @duration_sec,
        sla_expected_sec  = @sla_expected_sec,
        sla_threshold_sec = @sla_threshold_sec,
        sla_status =
            CASE
                WHEN @duration_sec <= @sla_threshold_sec THEN 'OK'
                ELSE 'FAIL'
            END,
        sla_reason =
            CASE
                WHEN @duration_sec <= @sla_threshold_sec THEN 'OK_WITHIN_THRESHOLD'
                ELSE 'EXCEEDED_THRESHOLD'
            END
    WHERE ctrl_id = @p_ctrl_id;
END;
GO
