INSERT INTO dbo.vigie_policy_test_type (test_code, description, requires_synapse)
VALUES
('ROW_COUNT',      'Validation du nombre de lignes',                     0),
('MIN_MAX',        'Validation min/max sur colonne clé',                  1),
('CHECKSUM',       'Checksum déterministique SHA256',                     1),
('NULL_COUNT',     'Validation du nombre de valeurs NULL',                1),
('RUN_COMPARISON', 'Comparaison avec le run précédent',                   0);


INSERT INTO dbo.vigie_policy_dataset
(dataset_name, environment, is_active, synapse_allowed, max_synapse_cost_usd)
VALUES
('clients',      'DEV',  1, 1, 5.00),
('clients',      'PROD', 1, 1, 2.00),

('accounts',     'DEV',  1, 1, 8.00),
('accounts',     'PROD', 1, 1, 3.00),

('transactions', 'DEV',  1, 1, 15.00),
('transactions', 'PROD', 1, 1, 6.00),

('contracts',    'DEV',  1, 0, NULL),
('contracts',    'PROD', 1, 0, NULL);

INSERT INTO dbo.vigie_policy_test
(policy_dataset_id, test_type_id, is_enabled, frequency, threshold_value, column_name)
SELECT d.policy_dataset_id, t.test_type_id, 1, 'DAILY', NULL, NULL
FROM dbo.vigie_policy_dataset d
JOIN dbo.vigie_policy_test_type t ON t.test_code = 'ROW_COUNT'
WHERE d.dataset_name = 'clients' AND d.environment = 'DEV';

INSERT INTO dbo.vigie_policy_test
(policy_dataset_id, test_type_id, is_enabled, frequency, threshold_value, column_name)
SELECT d.policy_dataset_id, t.test_type_id, 1, 'DAILY', NULL, 'client_id'
FROM dbo.vigie_policy_dataset d
JOIN dbo.vigie_policy_test_type t ON t.test_code IN ('MIN_MAX','NULL_COUNT')
WHERE d.dataset_name = 'clients' AND d.environment = 'DEV';

INSERT INTO dbo.vigie_policy_test
(policy_dataset_id, test_type_id, is_enabled, frequency, threshold_value, column_name)
SELECT d.policy_dataset_id, t.test_type_id, 1, 'WEEKLY', NULL, 'client_id'
FROM dbo.vigie_policy_dataset d
JOIN dbo.vigie_policy_test_type t ON t.test_code = 'CHECKSUM'
WHERE d.dataset_name = 'clients' AND d.environment = 'DEV';


INSERT INTO dbo.vigie_policy_test
(policy_dataset_id, test_type_id, is_enabled, frequency, threshold_value, column_name)
SELECT d.policy_dataset_id, t.test_type_id, 1, 'DAILY', NULL, NULL
FROM dbo.vigie_policy_dataset d
JOIN dbo.vigie_policy_test_type t ON t.test_code = 'ROW_COUNT'
WHERE d.dataset_name = 'clients' AND d.environment = 'PROD';

INSERT INTO dbo.vigie_policy_test
(policy_dataset_id, test_type_id, is_enabled, frequency, threshold_value, column_name)
SELECT d.policy_dataset_id, t.test_type_id, 1, 'WEEKLY', NULL, 'client_id'
FROM dbo.vigie_policy_dataset d
JOIN dbo.vigie_policy_test_type t ON t.test_code = 'MIN_MAX'
WHERE d.dataset_name = 'clients' AND d.environment = 'PROD';

INSERT INTO dbo.vigie_policy_test
(policy_dataset_id, test_type_id, is_enabled, frequency, threshold_value, column_name)
SELECT d.policy_dataset_id, t.test_type_id, 1, 'DAILY', NULL, NULL
FROM dbo.vigie_policy_dataset d
JOIN dbo.vigie_policy_test_type t ON t.test_code = 'ROW_COUNT'
WHERE d.dataset_name = 'transactions' AND d.environment = 'DEV';

INSERT INTO dbo.vigie_policy_test
(policy_dataset_id, test_type_id, is_enabled, frequency, threshold_value, column_name)
SELECT d.policy_dataset_id, t.test_type_id, 1, 'DAILY', NULL, 'transaction_id'
FROM dbo.vigie_policy_dataset d
JOIN dbo.vigie_policy_test_type t ON t.test_code IN ('MIN_MAX','NULL_COUNT')
WHERE d.dataset_name = 'transactions' AND d.environment = 'DEV';


