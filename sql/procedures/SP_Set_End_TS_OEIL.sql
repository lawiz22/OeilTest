-- =============================================================================
-- Stored Procedure : SP_Set_End_TS_OEIL
-- =============================================================================
-- Description : Marque la fin d'un run L'ŒIL et calcule le SLA inline.
--               Contrairement à SP_Compute_SLA_OEIL (qui ne fait que le calcul),
--               cette SP pose le end_ts, calcule la durée, ET évalue le SLA
--               en une seule opération atomique.
--
-- Logique :
--   1. Capture end_ts = SYSUTCDATETIME() (une seule fois, variable locale).
--   2. Récupère start_ts du run depuis vigie_ctrl.
--   3. Si start_ts est NULL → marque sla_status UNKNOWN avec raison
--      MISSING_START_TS (le chrono n'a jamais été démarré).
--   4. Calcule duration_sec = DATEDIFF(SECOND, start_ts, end_ts).
--   5. Charge le profil SLA 'OEIL' depuis sla_profile_execution_type.
--   6. Si aucun profil actif → écrit les métriques de durée mais marque
--      le SLA UNKNOWN avec raison NO_SLA_PROFILE (fallback gracieux).
--   7. Calcule le SLA :
--        sla_expected  = base_overhead_sec (fixe)
--        sla_threshold = sla_expected × (1 + tolerance_pct)
--   8. Écrit le verdict final (OK / FAIL) dans vigie_ctrl.
--
-- Différence vs SP_Compute_SLA_OEIL :
--   SP_Compute_SLA_OEIL      → calcul SLA pur (suppose que end_ts existe déjà)
--   SP_Set_End_TS_OEIL       → pose end_ts + calcule durée + calcul SLA
--   Cette SP est le point d'entrée opérationnel appelé par le runner Python.
--
-- Relation avec SP_Set_Start_TS_OEIL :
--   Les deux SP forment le lifecycle complet d'un run :
--     SP_Set_Start_TS_OEIL → crée la ligne + start_ts
--     SP_Set_End_TS_OEIL   → end_ts + durée + SLA
--
-- Paramètres :
--   @ctrl_id  nvarchar(200)  — Identifiant du run dans vigie_ctrl
--
-- Tables utilisées :
--   - dbo.vigie_ctrl                   (lecture + écriture)
--   - dbo.sla_profile_execution_type   (lecture)
--
-- Colonnes mises à jour dans vigie_ctrl :
--   end_ts, duration_sec, sla_sec, sla_expected_sec, sla_threshold_sec,
--   sla_status, sla_reason
-- =============================================================================

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE   PROCEDURE [dbo].[SP_Set_End_TS_OEIL]
    @ctrl_id NVARCHAR(200)
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @start_ts datetime2;
    DECLARE @end_ts   datetime2;
    DECLARE @duration_sec int;

    DECLARE @base_overhead_sec int;
    DECLARE @tolerance_pct decimal(5,2);

    DECLARE @sla_expected_sec  int;
    DECLARE @sla_threshold_sec int;

    /* =========================
       Capture du end_ts (UNE fois)
       ========================= */
    SET @end_ts = SYSUTCDATETIME();

    /* =========================
       Lecture du start_ts
       ========================= */
    SELECT
        @start_ts = start_ts
    FROM dbo.vigie_ctrl
    WHERE ctrl_id = @ctrl_id;

    /* =========================
       Protection : start_ts manquant
       ========================= */
    IF @start_ts IS NULL
    BEGIN
        UPDATE dbo.vigie_ctrl
        SET
            end_ts     = @end_ts,
            sla_status = 'UNKNOWN',
            sla_reason = 'MISSING_START_TS'
        WHERE ctrl_id = @ctrl_id;

        RETURN;
    END;

    /* =========================
       Calcul durée L'ŒIL
       ========================= */
    SET @duration_sec = DATEDIFF(SECOND, @start_ts, @end_ts);

    /* =========================
       Chargement profil SLA ŒIL
       ========================= */
    SELECT
        @base_overhead_sec = base_overhead_sec,
        @tolerance_pct     = tolerance_pct
    FROM dbo.sla_profile_execution_type
    WHERE execution_type = 'OEIL'
      AND active_flag = 1;

    /* =========================
       Fallback : profil SLA absent
       On écrit quand même les métriques de durée
       ========================= */
    IF @base_overhead_sec IS NULL
    BEGIN
        UPDATE dbo.vigie_ctrl
        SET
            end_ts       = @end_ts,
            duration_sec = @duration_sec,
            sla_sec      = @duration_sec,
            sla_status   = 'UNKNOWN',
            sla_reason   = 'NO_SLA_PROFILE'
        WHERE ctrl_id = @ctrl_id;

        RETURN;
    END;

    /* =========================
       Calcul SLA ŒIL
       Formule : expected  = base_overhead (fixe)
                 threshold = expected × (1 + tolerance%)
       ========================= */
    SET @sla_expected_sec  = @base_overhead_sec;
    SET @sla_threshold_sec = CAST(@sla_expected_sec * (1 + @tolerance_pct) AS int);

    /* =========================
       Update final ŒIL
       Pose end_ts + durée + verdict SLA en une seule écriture
       ========================= */
    UPDATE dbo.vigie_ctrl
    SET
        end_ts            = @end_ts,
        duration_sec      = @duration_sec,
        sla_sec           = @duration_sec,
        sla_expected_sec  = @sla_expected_sec,
        sla_threshold_sec = @sla_threshold_sec,
        sla_status =
            CASE
                WHEN @duration_sec <= @sla_threshold_sec THEN 'OK'
                ELSE 'FAIL'
            END,
        sla_reason = 'OEIL'
    WHERE ctrl_id = @ctrl_id;
END;
GO
