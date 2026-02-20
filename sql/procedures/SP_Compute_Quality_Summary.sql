SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

CREATE OR ALTER PROCEDURE dbo.SP_Compute_Quality_Summary
    @ctrl_id NVARCHAR(150)
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE
        @total INT,
        @pass INT,
        @fail INT,
        @warning INT,
        @global_status NVARCHAR(20);

    SELECT
        @total = COUNT(*),
        @pass = SUM(CASE WHEN status = 'PASS' THEN 1 ELSE 0 END),
        @fail = SUM(CASE WHEN status = 'FAIL' THEN 1 ELSE 0 END),
        @warning = SUM(CASE WHEN status = 'WARNING' THEN 1 ELSE 0 END)
    FROM dbo.vigie_integrity_result
    WHERE ctrl_id = @ctrl_id;

    IF @total IS NULL OR @total = 0
        SET @global_status = 'UNKNOWN';
    ELSE IF @fail > 0
        SET @global_status = 'FAIL';
    ELSE IF @warning > 0
        SET @global_status = 'WARNING';
    ELSE
        SET @global_status = 'PASS';

    UPDATE dbo.vigie_ctrl
    SET
        quality_tests_total = @total,
        quality_tests_pass = @pass,
        quality_tests_fail = @fail,
        quality_tests_warning = @warning,
        quality_status_global = @global_status
    WHERE ctrl_id = @ctrl_id;
END;
GO
