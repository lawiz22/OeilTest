-- =============================================================================
-- Stored Procedure : SP_Compute_SLA_ADF
-- =============================================================================
-- Description : Calcule le SLA pour les pipelines Azure Data Factory (ADF).
--
-- Logique :
--   1. Récupère les métriques ADF du run (row count copié, durée) depuis
--      vigie_ctrl.
--   2. Charge le profil SLA du type d'exécution 'ADF' depuis
--      sla_profile_execution_type (overhead fixe + coût variable par 1K rows).
--   3. Calcule le SLA attendu avec la formule :
--        sla_expected = base_overhead_sec + (rows / 1000) × sec_per_1k_rows
--        sla_threshold = sla_expected × (1 + tolerance_pct)
--   4. Compare la durée réelle au seuil et écrit le verdict (OK / FAIL)
--      dans vigie_ctrl.
--
-- Particularité ADF :
--   Seul moteur qui utilise sec_per_1k_rows car le temps d'ingestion ADF
--   est directement proportionnel au volume de données transférées.
--
-- Cas d'erreur :
--   - Si adf_duration_sec ou row_count sont NULL → statut UNKNOWN,
--     raison NO_ADF_METRICS
--   - Si aucun profil SLA actif n'existe pour ADF → statut UNKNOWN,
--     raison NO_ADF_SLA_PROFILE
--
-- Paramètres :
--   @p_ctrl_id  varchar(200)  — Identifiant du run dans vigie_ctrl
--
-- Tables utilisées :
--   - dbo.vigie_ctrl                   (lecture + écriture)
--   - dbo.sla_profile_execution_type   (lecture)
--
-- Colonnes mises à jour dans vigie_ctrl :
--   adf_sla_sec, adf_sla_expected_sec, adf_sla_threshold_sec,
--   adf_sla_status, adf_sla_reason
-- =============================================================================

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE PROCEDURE [dbo].[SP_Compute_SLA_ADF]
    @p_ctrl_id varchar(200)
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE
        @rows_total             int,
        @duration_sec           int,

        @base_overhead_sec      int,
        @sec_per_1k_rows        int,
        @tolerance_pct          decimal(5,2),

        @sla_expected_sec       int,
        @sla_threshold_sec      int;

    /* ============================
       1. Récupérer métriques ADF
       ============================ */
    SELECT
        @rows_total   = row_count_adf_ingestion_copie_parquet,
        @duration_sec = adf_duration_sec
    FROM dbo.vigie_ctrl
    WHERE ctrl_id = @p_ctrl_id;

    IF @duration_sec IS NULL OR @rows_total IS NULL
    BEGIN
        UPDATE dbo.vigie_ctrl
        SET
            adf_sla_status = 'UNKNOWN',
            adf_sla_reason = 'NO_ADF_METRICS'
        WHERE ctrl_id = @p_ctrl_id;
        RETURN;
    END;

    /* ============================
       2. Charger profil SLA ADF
       ============================ */
    SELECT
        @base_overhead_sec = base_overhead_sec,
        @sec_per_1k_rows   = sec_per_1k_rows,
        @tolerance_pct     = tolerance_pct
    FROM dbo.sla_profile_execution_type
    WHERE execution_type = 'ADF'
      AND active_flag = 1;

    IF @base_overhead_sec IS NULL
    BEGIN
        UPDATE dbo.vigie_ctrl
        SET
            adf_sla_status = 'UNKNOWN',
            adf_sla_reason = 'NO_ADF_SLA_PROFILE'
        WHERE ctrl_id = @p_ctrl_id;
        RETURN;
    END;

    /* ============================
       3. Calcul SLA attendu
       Formule : expected = overhead + (rows/1000) × cost_per_1k
                 threshold = expected × (1 + tolerance%)
       ============================ */
    SET @sla_expected_sec =
        @base_overhead_sec
        + CAST((@rows_total / 1000.0) * @sec_per_1k_rows AS int);

    SET @sla_threshold_sec =
        CAST(@sla_expected_sec * (1 + @tolerance_pct) AS int);

    /* ============================
       4. Verdict SLA ADF
       OK   = durée <= seuil
       FAIL = durée >  seuil
       ============================ */
    UPDATE dbo.vigie_ctrl
    SET
        adf_sla_sec           = @duration_sec,
        adf_sla_expected_sec  = @sla_expected_sec,
        adf_sla_threshold_sec = @sla_threshold_sec,
        adf_sla_status =
            CASE
                WHEN @duration_sec <= @sla_threshold_sec THEN 'OK'
                ELSE 'FAIL'
            END,
        adf_sla_reason = 'ADF_INGESTION'
    WHERE ctrl_id = @p_ctrl_id;
END;
GO
