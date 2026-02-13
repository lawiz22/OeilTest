CREATE TABLE dbo.vigie_policy_dataset (
    policy_dataset_id INT IDENTITY PRIMARY KEY,
    dataset_name NVARCHAR(150) NOT NULL,
    environment NVARCHAR(20) NOT NULL, -- DEV / QA / PROD
    is_active BIT NOT NULL DEFAULT 1,
    synapse_allowed BIT NOT NULL DEFAULT 1,
    max_synapse_cost_usd DECIMAL(10,2) NULL,
    created_at DATETIME2 DEFAULT SYSUTCDATETIME(),
    updated_at DATETIME2 DEFAULT SYSUTCDATETIME()
);
