CREATE TABLE dbo.vigie_integrity_result (
    integrity_result_id BIGINT IDENTITY PRIMARY KEY,

    ctrl_id NVARCHAR(150) NOT NULL,
    dataset_name NVARCHAR(150) NOT NULL,

    test_code NVARCHAR(50) NOT NULL,
    column_name NVARCHAR(150) NULL,

    numeric_value FLOAT NULL,
    text_value NVARCHAR(500) NULL,

    min_value FLOAT NULL,
    max_value FLOAT NULL,

    expected_value FLOAT NULL,
    delta_value FLOAT NULL,

    status NVARCHAR(30) NOT NULL, -- PASS / WARNING / FAIL
    execution_time_ms INT NULL,
    synapse_cost_usd DECIMAL(10,4) NULL,

    created_at DATETIME2 DEFAULT SYSUTCDATETIME()
);
