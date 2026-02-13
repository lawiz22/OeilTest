-- =============================================================================
-- Stored Procedure : SP_Compute_SLA_SYNAPSE
-- =============================================================================
-- Description : Calcule le SLA pour les exécutions Synapse (compute avancé).
--               Synapse est le moteur le plus coûteux — il est déclenché
--               uniquement quand la policy l'autorise (synapse_allowed = 1).
--
-- Logique :
--   1. Récupère synapse_duration_sec du run depuis vigie_ctrl.
--   2. Charge le profil SLA du type d'exécution 'SYNAPSE' depuis
--      sla_profile_execution_type (overhead fixe uniquement).
--   3. Calcule le SLA attendu :
--        sla_expected  = base_overhead_sec          (fixe, pas de coût/row)
--        sla_threshold = sla_expected × (1 + tolerance_pct)
--   4. Compare la durée réelle au seuil et écrit le verdict (OK / FAIL).
--
-- Similaire à OEIL :
--   Pas de sec_per_1k_rows — SLA fixe (120s par défaut, tolérance 30%).
--   Les deux moteurs (OEIL et SYNAPSE) ont un overhead constant car ils
--   mesurent le temps d'exécution de compute, pas de data movement.
--
-- Différence vs OEIL :
--   - Lookup sur synapse_duration_sec (pas duration_sec global)
--   - Écrit dans les champs synapse_sla_* (pas oeil_sla_*)
--   - Profil SLA plus court (120s vs 360s) mais tolérance plus large (30% vs 22%)
--
-- Cas d'erreur :
--   - Si synapse_duration_sec est NULL → statut UNKNOWN,
--     raison NO_SYNAPSE_METRICS
--   - Si aucun profil SLA actif n'existe pour SYNAPSE → statut UNKNOWN,
--     raison NO_SYNAPSE_SLA_PROFILE
--
-- Paramètres :
--   @p_ctrl_id  varchar(200)  — Identifiant du run dans vigie_ctrl
--
-- Tables utilisées :
--   - dbo.vigie_ctrl                   (lecture + écriture)
--   - dbo.sla_profile_execution_type   (lecture)
--
-- Colonnes mises à jour dans vigie_ctrl :
--   synapse_sla_sec, synapse_sla_expected_sec, synapse_sla_threshold_sec,
--   synapse_sla_status, synapse_sla_reason
-- =============================================================================

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE PROCEDURE [dbo].[SP_Compute_SLA_SYNAPSE]
    @p_ctrl_id varchar(200)
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE
        @duration_sec int,
        @base_overhead_sec int,
        @tolerance_pct decimal(5,2),
        @sla_expected_sec int,
        @sla_threshold_sec int;

    /* ============================
       1. Récupérer la durée Synapse
       ============================ */
    SELECT
        @duration_sec = synapse_duration_sec
    FROM dbo.vigie_ctrl
    WHERE ctrl_id = @p_ctrl_id;

    IF @duration_sec IS NULL
    BEGIN
        UPDATE dbo.vigie_ctrl
        SET
            synapse_sla_status = 'UNKNOWN',
            synapse_sla_reason = 'NO_SYNAPSE_METRICS'
        WHERE ctrl_id = @p_ctrl_id;
        RETURN;
    END;

    /* ============================
       2. Charger profil SLA Synapse
       ============================ */
    SELECT
        @base_overhead_sec = base_overhead_sec,
        @tolerance_pct     = tolerance_pct
    FROM dbo.sla_profile_execution_type
    WHERE execution_type = 'SYNAPSE'
      AND active_flag = 1;

    IF @base_overhead_sec IS NULL
    BEGIN
        UPDATE dbo.vigie_ctrl
        SET
            synapse_sla_status = 'UNKNOWN',
            synapse_sla_reason = 'NO_SYNAPSE_SLA_PROFILE'
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
       4. Verdict SLA Synapse
       OK   = durée <= seuil
       FAIL = durée >  seuil
       ============================ */
    UPDATE dbo.vigie_ctrl
    SET
        synapse_sla_sec           = @duration_sec,
        synapse_sla_expected_sec  = @sla_expected_sec,
        synapse_sla_threshold_sec = @sla_threshold_sec,
        synapse_sla_status =
            CASE
                WHEN @duration_sec <= @sla_threshold_sec THEN 'OK'
                ELSE 'FAIL'
            END,
        synapse_sla_reason = 'SYNAPSE_COMPUTE'
    WHERE ctrl_id = @p_ctrl_id;
END;
GO
