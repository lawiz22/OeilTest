-- =====================================================
-- 👁️ L'ŒIL — SP_Compute_SLA_Vigie
-- =====================================================
-- Master SLA procedure that orchestrates all SLA steps
-- for a single ctrl_id. Calls individual SLA procedures
-- and finalizes the overall SLA status.
--
-- PARAMETERS:
--   @p_ctrl_id VARCHAR(200)
-- =====================================================

CREATE OR ALTER PROCEDURE dbo.SP_Compute_SLA_Vigie
    @p_ctrl_id VARCHAR(200)
AS
BEGIN
    SET NOCOUNT ON;

    -- 1. Compute individual SLAs
    EXEC dbo.SP_Compute_SLA_ADF     @p_ctrl_id = @p_ctrl_id;
    EXEC dbo.SP_Compute_SLA_SYNAPSE @p_ctrl_id = @p_ctrl_id;
    EXEC dbo.SP_Compute_SLA_OEIL    @p_ctrl_id = @p_ctrl_id;

    -- 2. Sync global SLA from OEIL
    UPDATE dbo.vigie_ctrl
    SET sla_status = oeil_sla_status
    WHERE ctrl_id = @p_ctrl_id;
END;
GO
