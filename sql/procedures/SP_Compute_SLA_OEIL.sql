-- =====================================================
-- 👁️ L'ŒIL — SP_Compute_SLA_OEIL
-- =====================================================
-- Calculates the overall OEIL SLA for a given ctrl_id.
-- Combines ADF + Synapse durations into a single SLA bucket.
--
-- PARAMETERS:
--   @p_ctrl_id VARCHAR(200) — The ctrl_id to compute SLA for
--
-- SLA BUCKETS:
--   FAST       ≤ 200s total   → OK
--   SLOW       ≤ 300s total   → OK
--   VERY_SLOW  > 300s total   → FAIL
-- =====================================================

CREATE OR ALTER PROCEDURE dbo.SP_Compute_SLA_OEIL
    @p_ctrl_id VARCHAR(200)
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE dbo.vigie_ctrl
    SET
        sla_bucket = CASE
            WHEN duration_sec <= 200 THEN 'FAST'
            WHEN duration_sec <= 300 THEN 'SLOW'
            ELSE 'VERY_SLOW'
        END,
        oeil_sla_status = CASE
            WHEN duration_sec <= 300 THEN 'OK'
            ELSE 'FAIL'
        END
    WHERE ctrl_id = @p_ctrl_id;
END;
GO
