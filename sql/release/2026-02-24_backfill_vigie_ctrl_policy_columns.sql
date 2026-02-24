SET NOCOUNT ON;

PRINT '=== Backfill start: vigie_ctrl.policy_dataset_id + policy_snapshot_json ===';

;WITH target AS (
    SELECT
        vc.ctrl_id,
        vc.dataset,
        picked.policy_dataset_id
    FROM dbo.vigie_ctrl vc
    OUTER APPLY (
        SELECT TOP 1 pd.policy_dataset_id
        FROM dbo.vigie_policy_dataset pd
        WHERE pd.dataset_name = vc.dataset
          AND pd.is_active = 1
        ORDER BY CASE WHEN UPPER(pd.environment) = 'DEV' THEN 0 ELSE 1 END, pd.policy_dataset_id
    ) picked
    WHERE vc.policy_dataset_id IS NULL
       OR vc.policy_snapshot_json IS NULL
), snapshot AS (
    SELECT
        t.ctrl_id,
        t.policy_dataset_id,
        CAST((
            SELECT
                pd.policy_dataset_id,
                pd.dataset_name,
                pd.environment,
                pd.synapse_allowed,
                pd.max_synapse_cost_usd,
                (
                    SELECT
                        tt.test_code,
                        pt.frequency,
                        pt.column_name,
                        pt.hash_algorithm,
                        pt.threshold_value
                    FROM dbo.vigie_policy_test pt
                    INNER JOIN dbo.vigie_policy_test_type tt
                        ON tt.test_type_id = pt.test_type_id
                    WHERE pt.policy_dataset_id = pd.policy_dataset_id
                      AND pt.is_enabled = 1
                    ORDER BY pt.policy_test_id
                    FOR JSON PATH
                ) AS tests
            FROM dbo.vigie_policy_dataset pd
            WHERE pd.policy_dataset_id = t.policy_dataset_id
            FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
        ) AS NVARCHAR(MAX)) AS policy_snapshot_json
    FROM target t
    WHERE t.policy_dataset_id IS NOT NULL
)
UPDATE vc
SET
    vc.policy_dataset_id = ISNULL(vc.policy_dataset_id, s.policy_dataset_id),
    vc.policy_snapshot_json = ISNULL(vc.policy_snapshot_json, s.policy_snapshot_json)
FROM dbo.vigie_ctrl vc
INNER JOIN snapshot s
    ON s.ctrl_id = vc.ctrl_id;

PRINT 'Rows still null (policy_dataset_id):';
SELECT COUNT(*) AS remaining_policy_dataset_id_null
FROM dbo.vigie_ctrl
WHERE policy_dataset_id IS NULL;

PRINT 'Rows still null (policy_snapshot_json):';
SELECT COUNT(*) AS remaining_policy_snapshot_json_null
FROM dbo.vigie_ctrl
WHERE policy_snapshot_json IS NULL;

PRINT '=== Backfill completed ===';
