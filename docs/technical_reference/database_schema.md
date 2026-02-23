# 🗄️ Database Schema

Le schéma SQL est le cœur du framework. Il stocke l'état, l'historique et la configuration.

## Marquage audit

- **[Implemented]** : confirmé dans les scripts/pipelines versionnés.
- **[Recommended]** : convention cible validée, à aligner selon environnement.

## Tables Principales

### `dbo.vigie_ctrl` (Run Metrics)

Une ligne par exécution de pipeline. Clé primaire : `ctrl_id`.

| Colonne | Type | Description |
|---|---|---|
| `ctrl_id` | VARCHAR(200) PK | Identifiant unique composite du run |
| `dataset` | VARCHAR(50) | Dataset métier |
| `periodicity` | VARCHAR(10) | Fréquence du run |
| `extraction_date` | DATE | Date de référence de l'extraction |
| `expected_rows` | INT | Volume attendu (si connu) |
| `source_system` | VARCHAR(50) | Système source métier |
| `created_ts` | DATETIME2(7) | Timestamp de création logique du run |
| `pipeline_run_id` | VARCHAR(100) | Run id ADF |
| `adf_pipeline_name` | VARCHAR(100) | Nom pipeline ADF |
| `adf_trigger_name` | VARCHAR(100) | Nom trigger ADF |
| `start_ts` | DATETIME2(7) | Début du lifecycle run |
| `status` | VARCHAR(20) | Statut technique du run |
| `inserted_ts` | DATETIME2(7) NOT NULL | Timestamp d'insertion SQL (default `SYSUTCDATETIME()`) |
| `bronze_rows` | INT | Nombre de lignes Bronze |
| `bronze_delta` | INT | Écart Bronze vs attendu |
| `bronze_status` | VARCHAR(10) | Statut volume Bronze |
| `parquet_rows` | INT | Nombre de lignes Parquet |
| `parquet_delta` | INT | Écart Parquet vs Bronze/attendu |
| `parquet_status` | VARCHAR(10) | Statut volume Parquet |
| `status_global` | VARCHAR(20) | Statut agrégé global |
| `quality_status_global` | NVARCHAR(20) | Statut agrégé des tests qualité (`PASS`/`WARNING`/`FAIL`) |
| `quality_tests_total` | INT | Nombre total de tests qualité exécutés pour le run |
| `quality_tests_pass` | INT | Nombre de tests qualité en `PASS` |
| `quality_tests_fail` | INT | Nombre de tests qualité en `FAIL` |
| `quality_tests_warning` | INT | Nombre de tests qualité en `WARNING` |
| `sla_expected_sec` | INT | SLA attendu global (sec) |
| `sla_threshold_sec` | INT | Seuil SLA global (sec) |
| `end_ts` | DATETIME2(7) | Fin du lifecycle run |
| `duration_sec` | INT | Durée totale run (sec) |
| `sla_sec` | INT | SLA observé global (sec) |
| `sla_status` | VARCHAR(20) | Verdict SLA global |
| `sla_reason` | VARCHAR(50) | Raison du verdict global |
| `volume_status` | VARCHAR(20) | Verdict qualité volume |
| `sla_bucket` | VARCHAR(10) | Bucket SLA (FAST/SLOW/FAIL...) |
| `row_count_adf_ingestion_copie_parquet` | INT | Row count reporté par copie ADF |
| `adf_start_ts` | DATETIME2(7) | Début ADF ingestion |
| `adf_end_ts` | DATETIME2(7) | Fin ADF ingestion |
| `adf_duration_sec` | INT | Durée ADF (sec) |
| `adf_sla_status` | VARCHAR(20) | Verdict SLA ADF |
| `adf_sla_reason` | VARCHAR(100) | Raison verdict SLA ADF |
| `adf_sla_sec` | INT | SLA observé ADF (sec) |
| `adf_sla_expected_sec` | INT | SLA attendu ADF (sec) |
| `adf_sla_threshold_sec` | INT | Seuil SLA ADF (sec) |
| `synapse_start_ts` | DATETIME2(7) | Début compute Synapse |
| `synapse_end_ts` | DATETIME2(7) | Fin compute Synapse |
| `synapse_duration_sec` | INT | Durée Synapse (sec) |
| `synapse_sla_sec` | INT | SLA observé Synapse (sec) |
| `synapse_sla_expected_sec` | INT | SLA attendu Synapse (sec) |
| `synapse_sla_threshold_sec` | INT | Seuil SLA Synapse (sec) |
| `synapse_sla_status` | VARCHAR(20) | Verdict SLA Synapse |
| `synapse_sla_reason` | VARCHAR(100) | Raison verdict SLA Synapse |
| `oeil_sla_sec` | INT | SLA observé OEIL (sec) |
| `oeil_sla_expected_sec` | INT | SLA attendu OEIL (sec) |
| `oeil_sla_threshold_sec` | INT | Seuil SLA OEIL (sec) |
| `oeil_sla_status` | VARCHAR(20) | Verdict SLA OEIL |
| `oeil_sla_reason` | VARCHAR(100) | Raison verdict SLA OEIL |
| `alert_flag` | BIT | Présence d'alerte |
| `alert_reason` | VARCHAR(100) | Raison de l'alerte |
| `alert_ts` | DATETIME2(7) | Timestamp de levée d'alerte |
| `alert_level` | VARCHAR(20) | Niveau d'alerte |
| `synapse_cost_estimated_cad` | DECIMAL(10,6) | Coût Synapse estimé (CAD) |
| `synapse_cost_rate_cad_per_min` | DECIMAL(10,6) | Taux CAD/min utilisé pour estimation |
| `policy_dataset_id` | INT | Policy dataset appliquée |
| `policy_snapshot_json` | NVARCHAR(MAX) | Snapshot JSON de policy au moment du run |
| `payload_canonical` | VARCHAR(500) | Payload CTRL canonicalisé |
| `payload_hash_sha256` | CHAR(64) | Hash SHA-256 du payload canonicalisé |
| `payload_hash_version` | TINYINT | Version de l'algorithme de hash |
| `payload_hash_match` | BIT | Résultat du contrôle d'intégrité hash |

Indexes / contraintes notables :

- `PK_vigie_ctrl (ctrl_id)`
- `IX_vigie_ctrl_dataset_date (dataset, periodicity, extraction_date)`

#### Sémantique des statuts (consommation BI / PM / Ingénierie) [Implemented]

| Colonne | Signification | Source |
|---|---|---|
| `status` (`vigie_ctrl`) | Lifecycle run state (`RECEIVED`, `PROCESSING`, `COMPLETED`, `FAILED`) | Orchestration ADF/SQL |
| `status` (`vigie_integrity_result`) | Résultat d'un test d'intégrité individuel (`OK`/`ANOMALY` pour volume, `PASS`/`FAIL` pour hash/signature, `WARNING` possible) | Integrity engine |
| `status_global` | État global d'orchestration du pipeline | Orchestration ADF/SQL |
| `quality_status_global` | État global qualité agrégé du run | Quality Engine + `SP_Compute_Quality_Summary` |
| `quality_tests_total`, `quality_tests_pass`, `quality_tests_fail`, `quality_tests_warning` | Compteurs de synthèse qualité par run | Quality Engine + `SP_Compute_Quality_Summary` |
| `adf_sla_status` | Verdict SLA ingestion | Métriques ADF (Log Analytics) |
| `oeil_sla_status` | Verdict SLA orchestration OEIL | Compute SLA OEIL |
| `synapse_sla_status` | Verdict SLA compute Synapse | Quality Engine + compute SLA Synapse |
| `alert_flag`, `alert_level` | Synthèse d'alerte métier | Règles d'alerting SQL |

#### Conventions volume / valeurs par défaut (doc de référence) [Recommended]

| Cas | Valeur recommandée | Interprétation |
|---|---|---|
| Rowcount = `0` | `volume_status = EMPTY` | Run valide mais dataset vide |
| Rowcount = `NULL` | `volume_status = MISSING` | Mesure absente/non récupérée |
| `expected_rows = 0` | Statut exceptionnel (`EXPECTED_ZERO`) | Cas métier explicite, hors comparaison standard |

Note : si un environnement conserve encore les buckets historiques (`OK`, `WARNING`, `ANOMALY`, `UNKNOWN`), documenter localement le mapping vers les conventions ci-dessus.

#### Tables de référence (dictionnaires) [Recommended]

##### `frequency`

| Valeur | Signification |
|---|---|
| `DAILY` | Test à chaque jour d'extraction |
| `WEEKLY` | Test hebdomadaire |
| `MONTHLY` | Test mensuel |

##### `volume_status`

| Valeur | Signification |
|---|---|
| `OK` | Volume conforme |
| `EMPTY` | Run valide mais dataset vide |
| `MISSING` | Mesure absente/non disponible |
| `WARNING` | Écart modéré |
| `ANOMALY` | Écart critique |
| `EXPECTED_ZERO` | Cas métier attendu (`expected_rows = 0`) |

##### `sla_status`

| Valeur | Signification |
|---|---|
| `FAST` | Durée <= attendu |
| `SLOW` | Durée entre attendu et seuil |
| `VERY_SLOW` | Durée > seuil |
| `FAIL` | Échec technique/fonctionnel |

### `dbo.vigie_policy_dataset` (Policy Dataset v2)

| Colonne | Type | Description |
|---|---|---|
| `policy_dataset_id` | INT IDENTITY PK | Identifiant technique de policy dataset |
| `dataset_name` | NVARCHAR(150) NOT NULL | Nom dataset |
| `environment` | NVARCHAR(20) NOT NULL | Environnement (`DEV` / `QA` / `PROD`) |
| `is_active` | BIT NOT NULL DEFAULT 1 | Activation policy dataset |
| `synapse_allowed` | BIT NOT NULL DEFAULT 1 | Autorise exécution Synapse |
| `max_synapse_cost_usd` | DECIMAL(10,2) NULL | Budget max Synapse (USD) |
| `created_at` | DATETIME2 DEFAULT SYSUTCDATETIME() | Création |
| `updated_at` | DATETIME2 DEFAULT SYSUTCDATETIME() | Dernière mise à jour |

### `dbo.vigie_policy_test_type` (Catalogue des tests)

| Colonne | Type | Description |
|---|---|---|
| `test_type_id` | INT IDENTITY PK | Identifiant type de test |
| `test_code` | NVARCHAR(50) UNIQUE NOT NULL | Code test (`ROW_COUNT`, `MIN_MAX`, ...) |
| `description` | NVARCHAR(255) NULL | Description test |
| `requires_synapse` | BIT NOT NULL DEFAULT 0 | Le test requiert Synapse |

### `dbo.vigie_policy_test` (Activation des tests)

| Colonne | Type | Description |
|---|---|---|
| `policy_test_id` | INT IDENTITY PK | Identifiant de la règle de test |
| `policy_dataset_id` | INT NOT NULL FK | Référence `vigie_policy_dataset(policy_dataset_id)` |
| `test_type_id` | INT NOT NULL FK | Référence `vigie_policy_test_type(test_type_id)` |
| `is_enabled` | BIT NOT NULL DEFAULT 1 | Activation du test |
| `frequency` | NVARCHAR(20) NOT NULL | Fréquence (`DAILY`/`WEEKLY`/`MONTHLY`) |
| `threshold_value` | FLOAT NULL | Seuil paramétrable |
| `column_name` | NVARCHAR(150) NULL | Colonne ciblée (si test colonne) |
| `checksum_level` | TINYINT NULL | Niveau de stratégie hash (colonne legacy conservée pour compatibilité) |
| `hash_algorithm` | NVARCHAR(50) NULL | Algorithme de hash (ex: `SHA256`) |
| `column_list` | NVARCHAR(1000) NULL | Liste de colonnes pour signature/hash déterministe |
| `order_by_column` | NVARCHAR(150) NULL | Colonne d’ordre déterministe pour signature/hash |
| `created_at` | DATETIME2 DEFAULT SYSUTCDATETIME() | Création |

FK notables :

- `vigie_policy_test.policy_dataset_id` -> `vigie_policy_dataset.policy_dataset_id`
- `vigie_policy_test.test_type_id` -> `vigie_policy_test_type.test_type_id`

### `dbo.vigie_policy_table` (Policy legacy/simple)

Table de gouvernance historique (coexistence avec le modèle v2 ci-dessus selon pipelines).

| Colonne | Type | Description |
|---|---|---|
| `dataset` | VARCHAR(100) PK | Dataset |
| `environment` | VARCHAR(10) NOT NULL DEFAULT `PROD` | Environnement (`DEV`/`PROD`) |
| `enabled` | BIT NOT NULL DEFAULT 1 | Activation policy |
| `synapse_allowed` | BIT NOT NULL DEFAULT 1 | Autorisation Synapse |
| `description` | VARCHAR(500) NULL | Description libre |
| `created_ts` | DATETIME2 DEFAULT SYSUTCDATETIME() | Création |
| `updated_ts` | DATETIME2 DEFAULT SYSUTCDATETIME() | Dernière mise à jour |

### `dbo.vigie_integrity_result` (Résultats Tests)

| Colonne | Type | Description |
|---|---|---|
| `integrity_result_id` | BIGINT IDENTITY PK | ID du résultat |
| `ctrl_id` | NVARCHAR(150) NOT NULL | Lien vers le run |
| `dataset_name` | NVARCHAR(150) NOT NULL | Dataset évalué |
| `test_code` | NVARCHAR(50) NOT NULL | Code du test exécuté |
| `column_name` | NVARCHAR(150) NULL | Colonne ciblée par le test |
| `observed_value_num` | FLOAT NULL | Valeur observée principale (numérique) |
| `observed_value_aux_num` | FLOAT NULL | Valeur observée secondaire (numérique) |
| `reference_value_num` | FLOAT NULL | Valeur de référence principale (numérique) |
| `reference_value_aux_num` | FLOAT NULL | Valeur de référence secondaire (numérique) |
| `observed_value_text` | NVARCHAR(500) NULL | Valeur observée textuelle (ex: signature) |
| `reference_value_text` | NVARCHAR(500) NULL | Valeur de référence textuelle |
| `delta_value` | FLOAT | Écart observé |
| `status` | NVARCHAR(30) NOT NULL | `OK` / `ANOMALY` / `PASS` / `FAIL` / `WARNING` |
| `execution_time_ms` | INT | Durée d'exécution du test |
| `synapse_start_ts` | DATETIME2(7) NULL | Début du segment Synapse pour le test |
| `synapse_end_ts` | DATETIME2(7) NULL | Fin du segment Synapse pour le test |
| `created_at` | DATETIME2 DEFAULT SYSUTCDATETIME() | Timestamp UTC d'insertion |

### `dbo.ctrl_file_index` (Index d'ingestion)

| Colonne | Type | Description |
|---|---|---|
| `ctrl_id` | NVARCHAR(200) PK | Identifiant contrôle |
| `dataset` | NVARCHAR(200) NOT NULL | Dataset |
| `ctrl_path` | NVARCHAR(1024) NOT NULL | Chemin du fichier CTRL |
| `processed_flag` | BIT NOT NULL DEFAULT 0 | Fichier traité par le pipeline de consolidation |
| `processed_ts` | DATETIME2(3) NULL | Horodatage de traitement |
| `created_ts` | DATETIME2(3) NOT NULL DEFAULT SYSUTCDATETIME() | Horodatage d'indexation |
| `ctrl_path_hash` | Computed PERSISTED (BINARY(32)) | SHA-256 de `ctrl_path` |

Indexes / contraintes notables :

- `PK_ctrl_file_index (ctrl_id)`
- `UX_ctrl_file_index_ctrl_path_hash` (unique sur hash du chemin)

### `dbo.synapse_rowcount_cache` (Cache row counts)

| Colonne | Type | Description |
|---|---|---|
| `dataset` | VARCHAR(50) PK(1) | Dataset |
| `periodicity` | VARCHAR(10) PK(2) | Fréquence |
| `extraction_date` | DATE PK(3) | Date d'extraction |
| `layer` | VARCHAR(10) PK(4) | Couche (`BRONZE`/`PARQUET`) |
| `row_count` | INT NOT NULL | Nombre de lignes calculé |
| `computed_ts` | DATETIME2(7) NOT NULL DEFAULT SYSUTCDATETIME() | Timestamp de calcul |

Indexes / contraintes notables :

- `PK_synapse_rowcount_cache (dataset, periodicity, extraction_date, layer)`

### `dbo.sla_profile_execution_type` (SLA par moteur)

| Colonne | Type | Description |
|---|---|---|
| `execution_type` | VARCHAR(30) PK | Type (`ADF`, `SYNAPSE`, `OEIL`) |
| `base_overhead_sec` | INT NOT NULL | Overhead fixe |
| `sec_per_1k_rows` | INT NULL | Coût variable par 1000 lignes |
| `tolerance_pct` | DECIMAL(5,2) NOT NULL | Tolérance (%) |
| `active_flag` | BIT NOT NULL DEFAULT 1 | Profil actif |
| `created_ts` | DATETIME2(3) NOT NULL DEFAULT SYSUTCDATETIME() | Création |

### `dbo.sla_profile` (SLA par dataset)

| Colonne | Type | Description |
|---|---|---|
| `dataset` | NVARCHAR(200) PK | Dataset |
| `base_overhead_sec` | INT NOT NULL | Overhead fixe |
| `sec_per_1k_rows` | INT NOT NULL | Coût variable par 1000 lignes |
| `tolerance_pct` | DECIMAL(5,2) NOT NULL | Tolérance (%) |
| `active_flag` | BIT NOT NULL DEFAULT 1 | Profil actif |
| `created_ts` | DATETIME2(3) NOT NULL DEFAULT SYSUTCDATETIME() | Création |

## Tables métiers (données de démo)

### `dbo.clients`

| Colonne | Type | Description |
|---|---|---|
| `client_id` | INT | Identifiant client |
| `nom` | VARCHAR(120) | Nom client |
| `prenom` | VARCHAR(120) | Prénom client |
| `client_type` | VARCHAR(20) | Type (segment client) |
| `pays` | VARCHAR(50) | Pays |
| `statut` | VARCHAR(20) | Statut client |
| `date_effet` | DATE | Date d'effet |

### `dbo.accounts`

| Colonne | Type | Description |
|---|---|---|
| `account_id` | INT | Identifiant compte |
| `client_id` | INT | Référence client |
| `account_type` | VARCHAR(20) | Type de compte |
| `currency` | CHAR(3) | Devise ISO |
| `balance` | DECIMAL(18,2) | Solde |
| `open_date` | DATE | Date d'ouverture |

### `dbo.transactions`

| Colonne | Type | Description |
|---|---|---|
| `transaction_id` | BIGINT | Identifiant transaction |
| `account_id` | INT | Référence compte |
| `amount` | DECIMAL(18,2) | Montant |
| `currency` | CHAR(3) | Devise ISO |
| `transaction_ts` | DATETIME2 | Timestamp transaction |
| `ingestion_date` | DATE | Date d'ingestion |

### `dbo.contracts`

| Colonne | Type | Description |
|---|---|---|
| `contract_id` | INT | Identifiant contrat |
| `client_id` | INT | Référence client |
| `product_type` | VARCHAR(30) | Type de produit |
| `start_date` | DATE | Date de début |
| `end_date` | DATE | Date de fin |
| `statut` | VARCHAR(20) | Statut contrat |

### TABLES ANNEXES

-   Les tables métiers ci-dessus sont volontairement simples (sans PK/FK explicites dans les scripts de démo).

## Archivage & rétention [Recommended]

- Rétention opérationnelle en table chaude (`vigie_ctrl`, `vigie_integrity_result`) à définir par environnement (ex: 90-180 jours).
- Archivage long terme dans ADLS via artefacts immuables (`CTRL JSON` + snapshots de policy).
- Purge planifiée hors PROD business hours, avec contrôle de volumétrie avant/après purge.
- Toujours tracer la fenêtre purgée (`extraction_date`, `dataset`, `rows_deleted`) dans un journal d'exploitation.

## Concurrency & Idempotence [Implemented + Recommended]

- **[Implemented]** : `PK_vigie_ctrl (ctrl_id)` protège l'unicité d'un run logique.
- **[Implemented]** : procédures lifecycle idempotentes (`start_ts`/`end_ts` protégés) pour limiter les doubles écritures.
- **[Recommended]** : sérialiser les mises à jour critiques par `ctrl_id` quand plusieurs orchestrations concurrentes sont possibles.
- **[Recommended]** : considérer une stratégie de verrou applicatif (ou `sp_getapplock`) si contention fréquente observée.
