-- =====================================================
-- 👁️ L'ŒIL — SP_Compute_SLA_SYNAPSE
-- =====================================================
-- Calculates the Synapse compute SLA for a given ctrl_id.
--
-- PARAMETERS:
--   @p_ctrl_id VARCHAR(200)
--
-- RULE:
--   synapse_duration_sec < 160s → OK, else FAIL
-- =====================================================

CREATE OR ALTER PROCEDURE dbo.SP_Compute_SLA_SYNAPSE
    @p_ctrl_id VARCHAR(200)
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE dbo.vigie_ctrl
    SET synapse_sla_status = CASE
            WHEN synapse_duration_sec < 160 THEN 'OK'
            ELSE 'FAIL'
        END
    WHERE ctrl_id = @p_ctrl_id;
END;
GO
