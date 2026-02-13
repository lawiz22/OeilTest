-- =============================================================================
-- Stored Procedure : SP_Compute_SLA_OEIL
-- =============================================================================
-- Description : Calcule le SLA pour le moteur L'ŒIL lui-même, c'est-à-dire
--               la durée totale du run d'extraction de bout en bout
--               (start_ts → end_ts).
--
-- Logique :
--   1. Récupère start_ts, end_ts et duration_sec du run depuis vigie_ctrl.
--   2. Charge le profil SLA du type d'exécution 'OEIL' depuis
--      sla_profile_execution_type (overhead fixe uniquement).
--   3. Calcule le SLA attendu :
--        sla_expected  = base_overhead_sec          (fixe, pas de coût/row)
--        sla_threshold = sla_expected × (1 + tolerance_pct)
--   4. Compare la durée réelle au seuil et écrit le verdict (OK / FAIL).
--
-- Différence vs ADF :
--   L'ŒIL n'utilise PAS sec_per_1k_rows — le SLA est un overhead fixe
--   (360s par défaut) car il mesure le temps total du run, pas le volume
--   de données transférées.
--
-- Cas d'erreur :
--   - Si start_ts ou end_ts sont NULL → statut UNKNOWN,
--     raison MISSING_TIMESTAMPS
--   - Si aucun profil SLA actif n'existe pour OEIL → statut UNKNOWN,
--     raison NO_SLA_PROFILE
--
-- Paramètres :
--   @p_ctrl_id  varchar(200)  — Identifiant du run dans vigie_ctrl
--
-- Tables utilisées :
--   - dbo.vigie_ctrl                   (lecture + écriture)
--   - dbo.sla_profile_execution_type   (lecture)
--
-- Colonnes mises à jour dans vigie_ctrl :
--   oeil_sla_sec, oeil_sla_expected_sec, oeil_sla_threshold_sec,
--   oeil_sla_status, oeil_sla_reason
-- =============================================================================

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE PROCEDURE [dbo].[SP_Compute_SLA_OEIL]
    @p_ctrl_id varchar(200)
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE
        @start_ts datetime2,
        @end_ts datetime2,
        @duration_sec int,

        @base_overhead_sec int,
        @tolerance_pct decimal(5,2),

        @sla_expected_sec int,
        @sla_threshold_sec int;

    /* ============================
       1. Récupérer timestamps du run
       ============================ */
    SELECT
        @start_ts     = start_ts,
        @end_ts       = end_ts,
        @duration_sec = duration_sec
    FROM dbo.vigie_ctrl
    WHERE ctrl_id = @p_ctrl_id;

    IF @start_ts IS NULL OR @end_ts IS NULL
    BEGIN
        UPDATE dbo.vigie_ctrl
        SET
            oeil_sla_status = 'UNKNOWN',
            oeil_sla_reason = 'MISSING_TIMESTAMPS'
        WHERE ctrl_id = @p_ctrl_id;
        RETURN;
    END;

    /* ============================
       2. Charger profil SLA OEIL
       ============================ */
    SELECT
        @base_overhead_sec = base_overhead_sec,
        @tolerance_pct     = tolerance_pct
    FROM dbo.sla_profile_execution_type
    WHERE execution_type = 'OEIL'
      AND active_flag = 1;

    IF @base_overhead_sec IS NULL
    BEGIN
        UPDATE dbo.vigie_ctrl
        SET
            oeil_sla_status = 'UNKNOWN',
            oeil_sla_reason = 'NO_SLA_PROFILE'
        WHERE ctrl_id = @p_ctrl_id;
        RETURN;
    END;

    /* ============================
       3. Calcul SLA attendu
       Formule : expected  = base_overhead (fixe, pas de coût/row)
                 threshold = expected × (1 + tolerance%)
       ============================ */
    SET @sla_expected_sec  = @base_overhead_sec;
    SET @sla_threshold_sec = CAST(@sla_expected_sec * (1 + @tolerance_pct) AS int);

    /* ============================
       4. Verdict SLA OEIL
       OK   = durée <= seuil
       FAIL = durée >  seuil
       ============================ */
    UPDATE dbo.vigie_ctrl
    SET
        oeil_sla_sec           = @duration_sec,
        oeil_sla_expected_sec  = @sla_expected_sec,
        oeil_sla_threshold_sec = @sla_threshold_sec,
        oeil_sla_status =
            CASE
                WHEN @duration_sec <= @sla_threshold_sec THEN 'OK'
                ELSE 'FAIL'
            END,
        oeil_sla_reason = 'OEIL_EXECUTION'
    WHERE ctrl_id = @p_ctrl_id;
END;
GO
