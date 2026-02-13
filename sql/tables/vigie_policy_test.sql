CREATE TABLE dbo.vigie_policy_test (
    policy_test_id INT IDENTITY PRIMARY KEY,
    policy_dataset_id INT NOT NULL,
    test_type_id INT NOT NULL,

    is_enabled BIT NOT NULL DEFAULT 1,
    frequency NVARCHAR(20) NOT NULL, -- DAILY / WEEKLY / MONTHLY
    threshold_value FLOAT NULL,
    column_name NVARCHAR(150) NULL,

    created_at DATETIME2 DEFAULT SYSUTCDATETIME(),

    FOREIGN KEY (policy_dataset_id)
        REFERENCES dbo.vigie_policy_dataset(policy_dataset_id),

    FOREIGN KEY (test_type_id)
        REFERENCES dbo.vigie_policy_test_type(test_type_id)
);
