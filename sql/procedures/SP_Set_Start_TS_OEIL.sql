-- =============================================================================
-- Stored Procedure : SP_Set_Start_TS_OEIL
-- =============================================================================
-- Description : Marque le début d'un run L'ŒIL en posant le start_ts.
--               Si le run n'existe pas encore dans vigie_ctrl, la SP le crée
--               avec un contrat minimal (ctrl_id, dataset, periodicity,
--               extraction_date, source_system, start_ts, status_global).
--
-- Logique :
--   1. Vérifie si le ctrl_id existe déjà dans vigie_ctrl.
--   2a. Si NON → INSERT d'une nouvelle ligne avec :
--       - start_ts = SYSUTCDATETIME()
--       - status_global = 'IN_PROGRESS'
--       - created_ts = SYSUTCDATETIME()
--   2b. Si OUI → UPDATE start_ts UNE SEULE FOIS (garde la première valeur).
--       La clause WHERE start_ts IS NULL garantit l'idempotence.
--
-- Idempotence :
--   Appeler cette SP plusieurs fois avec le même ctrl_id ne modifie PAS
--   le start_ts après le premier appel. C'est le comportement voulu pour
--   éviter que des re-runs écrasent le vrai début.
--
-- Paramètres :
--   @ctrl_id          nvarchar(200)  — Identifiant unique du run
--   @dataset          nvarchar(100)  — Nom du dataset
--   @periodicity      nvarchar(10)   — Fréquence (D/W/M/Q)
--   @extraction_date  date           — Date d'extraction
--   @source_system    nvarchar(50)   — Système source (optionnel)
--
-- Tables utilisées :
--   - dbo.vigie_ctrl  (lecture + insertion ou mise à jour)
--
-- Colonnes affectées :
--   INSERT : ctrl_id, dataset, periodicity, extraction_date, source_system,
--            start_ts, status_global, created_ts
--   UPDATE : start_ts (si NULL uniquement)
-- =============================================================================

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE   PROCEDURE [dbo].[SP_Set_Start_TS_OEIL]
    @ctrl_id          NVARCHAR(200),
    @dataset          NVARCHAR(100),
    @periodicity      NVARCHAR(10),
    @extraction_date  DATE,
    @source_system    NVARCHAR(50) = NULL
AS
BEGIN
    SET NOCOUNT ON;

    -- 1️⃣ Si la ligne n'existe PAS encore → on la crée (contrat minimal)
    IF NOT EXISTS (
        SELECT 1
        FROM dbo.vigie_ctrl
        WHERE ctrl_id = @ctrl_id
    )
    BEGIN
        INSERT INTO dbo.vigie_ctrl (
            ctrl_id,
            dataset,
            periodicity,
            extraction_date,
            source_system,
            start_ts,
            status_global,
            created_ts
        )
        VALUES (
            @ctrl_id,
            @dataset,
            @periodicity,
            @extraction_date,
            @source_system,
            SYSUTCDATETIME(),
            'IN_PROGRESS',
            SYSUTCDATETIME()
        );
    END
    ELSE
    BEGIN
        -- 2️⃣ Sinon → on pose start_ts UNE SEULE FOIS (idempotent)
        UPDATE dbo.vigie_ctrl
        SET start_ts = SYSUTCDATETIME()
        WHERE ctrl_id = @ctrl_id
          AND start_ts IS NULL;
    END
END;
GO
