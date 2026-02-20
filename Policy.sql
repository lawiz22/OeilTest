BEGIN TRANSACTION;

-- 1️⃣ Supprimer les tests (table enfant)
DELETE FROM dbo.vigie_policy_test;

DBCC CHECKIDENT ('dbo.vigie_policy_test', RESEED, 0);

-- 2️⃣ Supprimer les datasets (table parent)
DELETE FROM dbo.vigie_policy_dataset;

DBCC CHECKIDENT ('dbo.vigie_policy_dataset', RESEED, 0);

COMMIT;


INSERT INTO dbo.vigie_policy_dataset
(
    dataset_name,
    environment,
    is_active,
    synapse_allowed,
    max_synapse_cost_usd
)
VALUES
-- CLIENTS
('clients', 'DEV', 1, 1, 5.00),
('clients', 'PROD', 1, 1, 2.00),

-- ACCOUNTS
('accounts', 'DEV', 1, 1, 8.00),
('accounts', 'PROD', 1, 1, 3.00),

-- TRANSACTIONS
('transactions', 'DEV', 1, 1, 15.00),
('transactions', 'PROD', 1, 1, 6.00),

-- CONTRACTS
('contracts', 'DEV', 1, 0, NULL),
('contracts', 'PROD', 1, 0, NULL);




INSERT INTO dbo.vigie_policy_test
(
    policy_dataset_id,
    test_type_id,
    is_enabled,
    frequency,
    threshold_value,
    column_name
)
SELECT
    d.policy_dataset_id,
    tt.test_type_id,
    1,              -- is_enabled
    'DAILY',        -- frequency
    NULL,           -- threshold_value (pas utile pour row_count)
    NULL            -- column_name pour row_count
FROM dbo.vigie_policy_dataset d
JOIN dbo.vigie_policy_test_type tt
    ON tt.test_code = 'ROW_COUNT'
WHERE d.environment = 'DEV';


-- MIN_MAX

INSERT INTO dbo.vigie_policy_test
(
    policy_dataset_id,
    test_type_id,
    is_enabled,
    frequency,
    threshold_value,
    column_name
)
SELECT
    d.policy_dataset_id,
    tt.test_type_id,
    1,
    'DAILY',
    NULL,
    CASE 
        WHEN d.dataset_name = 'clients' THEN 'client_id'
        WHEN d.dataset_name = 'accounts' THEN 'account_id'
        WHEN d.dataset_name = 'transactions' THEN 'transaction_id'
        WHEN d.dataset_name = 'contracts' THEN 'contract_id'
    END
FROM dbo.vigie_policy_dataset d
JOIN dbo.vigie_policy_test_type tt
    ON tt.test_code = 'MIN_MAX'
WHERE d.environment = 'DEV';





SELECT 
    d.dataset_name,
    d.environment,
    tt.test_code,
    t.column_name
FROM dbo.vigie_policy_test t
JOIN dbo.vigie_policy_dataset d 
    ON t.policy_dataset_id = d.policy_dataset_id
JOIN dbo.vigie_policy_test_type tt
    ON t.test_type_id = tt.test_type_id
ORDER BY d.dataset_name;



BEGIN TRANSACTION;

-- 1️⃣ Supprimer les tests liés
DELETE FROM dbo.vigie_policy_test;
DBCC CHECKIDENT ('dbo.vigie_policy_test', RESEED, 0);

-- 2️⃣ Supprimer les types de test
DELETE FROM dbo.vigie_policy_test_type;
DBCC CHECKIDENT ('dbo.vigie_policy_test_type', RESEED, 0);

COMMIT;


INSERT INTO dbo.vigie_policy_test_type
(
    test_code,
    description,
    requires_synapse
)
VALUES
('ROW_COUNT',      'Validation stricte du nombre de lignes (0% tolérance)', 0),
('MIN_MAX',        'Validation min/max sur colonne clé',                     1),
('CHECKSUM',       'Checksum déterministique SHA256',                        1),
('NULL_COUNT',     'Validation du nombre de valeurs NULL',                   1),
('RUN_COMPARISON', 'Comparaison avec le run précédent',                      0);




BEGIN TRANSACTION;

-- 1️⃣ Niveau de checksum (1,2,3)
IF COL_LENGTH('dbo.vigie_policy_test', 'checksum_level') IS NULL
BEGIN
    ALTER TABLE dbo.vigie_policy_test
    ADD checksum_level TINYINT NULL;
END

-- 2️⃣ Algorithme utilisé
IF COL_LENGTH('dbo.vigie_policy_test', 'hash_algorithm') IS NULL
BEGIN
    ALTER TABLE dbo.vigie_policy_test
    ADD hash_algorithm NVARCHAR(50) NULL;
END

-- 3️⃣ Liste de colonnes (pour row-level hash)
IF COL_LENGTH('dbo.vigie_policy_test', 'column_list') IS NULL
BEGIN
    ALTER TABLE dbo.vigie_policy_test
    ADD column_list NVARCHAR(1000) NULL;
END

-- 4️⃣ Colonne pour ORDER BY déterministe (niveau 2/3)
IF COL_LENGTH('dbo.vigie_policy_test', 'order_by_column') IS NULL
BEGIN
    ALTER TABLE dbo.vigie_policy_test
    ADD order_by_column NVARCHAR(150) NULL;
END

COMMIT;


INSERT INTO dbo.vigie_policy_test
(
    policy_dataset_id,
    test_type_id,
    is_enabled,
    frequency,
    threshold_value,
    column_name,
    checksum_level,
    hash_algorithm,
    column_list,
    order_by_column
)
SELECT
    d.policy_dataset_id,
    tt.test_type_id,
    1,
    'DAILY',
    NULL,
    CASE 
        WHEN d.dataset_name = 'clients' THEN 'client_id'
        WHEN d.dataset_name = 'accounts' THEN 'account_id'
        WHEN d.dataset_name = 'transactions' THEN 'transaction_id'
        WHEN d.dataset_name = 'contracts' THEN 'contract_id'
    END,
    1,
    'SHA256',
    NULL,
    NULL
FROM dbo.vigie_policy_dataset d
JOIN dbo.vigie_policy_test_type tt
    ON tt.test_code = 'CHECKSUM'
WHERE d.environment = 'DEV';

