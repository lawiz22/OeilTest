-- =====================================================
-- 👁️ L'ŒIL — SP_Compute_SLA_ADF
-- =====================================================
-- Calculates the ADF ingestion SLA for a given ctrl_id.
--
-- PARAMETERS:
--   @p_ctrl_id VARCHAR(200)
--
-- RULE:
--   adf_duration_sec < 30s → OK, else FAIL
-- =====================================================

CREATE OR ALTER PROCEDURE dbo.SP_Compute_SLA_ADF
    @p_ctrl_id VARCHAR(200)
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE dbo.vigie_ctrl
    SET adf_sla_status = CASE
            WHEN adf_duration_sec < 30 THEN 'OK'
            ELSE 'FAIL'
        END
    WHERE ctrl_id = @p_ctrl_id;
END;
GO
