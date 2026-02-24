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
--            start_ts, status_global, created_ts, policy_dataset_id,
--            policy_snapshot_json
--   UPDATE : start_ts (si NULL uniquement), policy_dataset_id,
--            policy_snapshot_json (si NULL)
-- =============================================================================

SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

IF OBJECT_ID('[dbo].[SP_Set_Start_TS_OEIL]', 'P') IS NOT NULL
    DROP PROCEDURE [dbo].[SP_Set_Start_TS_OEIL];
GO

CREATE PROCEDURE [dbo].[SP_Set_Start_TS_OEIL]
    @ctrl_id          NVARCHAR(200),
    @dataset          NVARCHAR(100),
    @periodicity      NVARCHAR(10),
    @extraction_date  DATE,
    @source_system    NVARCHAR(50) = NULL
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @policy_dataset_id INT = NULL;
    DECLARE @policy_snapshot_json NVARCHAR(MAX) = NULL;

    SELECT TOP 1
        @policy_dataset_id = pd.policy_dataset_id
    FROM dbo.vigie_policy_dataset pd
    WHERE pd.dataset_name = @dataset
      AND pd.is_active = 1
    ORDER BY CASE WHEN UPPER(pd.environment) = 'DEV' THEN 0 ELSE 1 END, pd.policy_dataset_id;

    IF @policy_dataset_id IS NOT NULL
    BEGIN
        SELECT
            @policy_snapshot_json = (
                SELECT
                    pd.policy_dataset_id,
                    pd.dataset_name,
                    pd.environment,
                    pd.synapse_allowed,
                    pd.max_synapse_cost_usd,
                    (
                        SELECT
                            tt.test_code,
                            t.frequency,
                            t.column_name,
                            t.hash_algorithm,
                            t.threshold_value
                        FROM dbo.vigie_policy_test t
                        INNER JOIN dbo.vigie_policy_test_type tt
                            ON tt.test_type_id = t.test_type_id
                        WHERE t.policy_dataset_id = pd.policy_dataset_id
                          AND t.is_enabled = 1
                        ORDER BY t.policy_test_id
                        FOR JSON PATH
                    ) AS tests
                FROM dbo.vigie_policy_dataset pd
                WHERE pd.policy_dataset_id = @policy_dataset_id
                FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
            );
    END

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
            created_ts,
            policy_dataset_id,
            policy_snapshot_json
        )
        VALUES (
            @ctrl_id,
            @dataset,
            @periodicity,
            @extraction_date,
            @source_system,
            SYSUTCDATETIME(),
            'IN_PROGRESS',
            SYSUTCDATETIME(),
            @policy_dataset_id,
            @policy_snapshot_json
        );
    END
    ELSE
    BEGIN
        -- 2️⃣ Sinon → on complète les champs manquants sans écraser l'existant
        UPDATE dbo.vigie_ctrl
        SET start_ts = CASE WHEN start_ts IS NULL THEN SYSUTCDATETIME() ELSE start_ts END,
            policy_dataset_id = ISNULL(policy_dataset_id, @policy_dataset_id),
            policy_snapshot_json = ISNULL(policy_snapshot_json, @policy_snapshot_json)
        WHERE ctrl_id = @ctrl_id
          AND (
                start_ts IS NULL
                OR policy_dataset_id IS NULL
                OR policy_snapshot_json IS NULL
          );
    END
END;
GO
