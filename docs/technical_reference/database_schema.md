# 🗄️ Database Schema

Le schéma SQL est le cœur du framework. Il stocke l'état, l'historique et la configuration.

## Tables Principales

### `dbo.vigie_ctrl` (Run Metrics)

Une ligne par exécution de pipeline. Clé primaire : `ctrl_id`.

| Colonne | Type | Description |
|---|---|---|
| `ctrl_id` | PK | Identifiant unique composite (`dataset` + `date` + `period`) |
| `status_global` | VARCHAR(20) | Statut agrégé (IN_PROGRESS, SUCCEEDED, FAILED) |
| `bronze_rows` | INT | Nombre de lignes chargées en Bronze |
| `parquet_rows` | INT | Nombre de lignes converties en Parquet |
| `sla_status` | VARCHAR(20) | Verdict SLA global (FAST, SLOW, FAIL) |
| `synapse_cost_estimated_cad` | DECIMAL | Coût estimé du compute Synapse |
| `payload_hash_match` | BIT | Intégrité du fichier CTRL original |

### `dbo.vigie_policy_table` (Configuration Dataset)

| Colonne | Type | Description |
|---|---|---|
| `dataset_name` | PK | Nom du dataset |
| `environment` | VARCHAR(20) | DEV / PROD |
| `synapse_allowed` | BIT | Autorisation d'utiliser Synapse |
| `max_synapse_cost_usd` | DECIMAL | Budget maximum |

### `dbo.vigie_policy_test` (Tests Activés)

| Colonne | Type | Description |
|---|---|---|
| `policy_test_id` | PK | ID unique du test |
| `dataset_name` | FK | Dataset concerné |
| `test_type` | FK | Type de test (ROW_COUNT, CHECKSUM, etc.) |
| `frequency` | VARCHAR(20) | DAILY, WEEKLY, MONTHLY |
| `threshold` | FLOAT | Seuil de tolérance |

### `dbo.vigie_integrity_result` (Résultats Tests)

| Colonne | Type | Description |
|---|---|---|
| `integrity_result_id` | PK | ID du résultat |
| `ctrl_id` | FK | Lien vers le run |
| `dataset_name` | VARCHAR(150) | Dataset évalué |
| `test_code` | VARCHAR(50) | Code du test exécuté |
| `column_name` | VARCHAR(150) | Colonne ciblée par le test |
| `status` | VARCHAR(30) | PASS / WARNING / FAIL |
| `numeric_value` | FLOAT | Valeur mesurée |
| `text_value` | VARCHAR(500) | Valeur texte mesurée (si applicable) |
| `min_value` | FLOAT | Min observé |
| `max_value` | FLOAT | Max observé |
| `expected_value` | FLOAT | Valeur attendue (si applicable) |
| `delta_value` | FLOAT | Écart observé |
| `execution_time_ms` | INT | Durée d'exécution du test |
| `synapse_cost_usd` | DECIMAL(10,4) | Coût Synapse estimé pour ce test |
| `created_at` | DATETIME2 | Timestamp UTC d'insertion |

### TABLES ANNEXES

-   `dbo.ctrl_file_index` : Index des fichiers ingérés pour éviter les doublons.
-   `dbo.sla_profile_execution_type` : Seuils SLA par moteur (ADF, Synapse, OEIL).
-   `dbo.synapse_rowcount_cache` : Cache des row counts pour éviter les requêtes coûteuses.
