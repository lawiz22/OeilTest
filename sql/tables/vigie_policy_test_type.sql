CREATE TABLE dbo.vigie_policy_test_type (
    test_type_id INT IDENTITY PRIMARY KEY,
    test_code NVARCHAR(50) UNIQUE NOT NULL,
    description NVARCHAR(255),
    requires_synapse BIT NOT NULL DEFAULT 0
);
