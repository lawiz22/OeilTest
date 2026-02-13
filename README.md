# 👁️ L'ŒIL — Data Quality & Integrity Framework

> **Un moteur de validation configurable, traçable et réutilisable — enterprise-wide.**

L'ŒIL est un framework de contrôle qualité des données conçu pour les environnements Azure. Il orchestre la validation de volumes, de SLA, d'intégrité et de coûts à travers Azure Data Factory, Synapse, Azure SQL et Log Analytics.

---

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Azure Data  │────▶│  Azure SQL   │◀────│   Log Analytics  │
│   Factory    │     │  (vigie_ctrl │     │   (KQL Logs)     │
│  (Pipelines) │     │   + policy)  │     └─────────────────┘
└──────┬───────┘     └──────┬───────┘
       │                    │
       ▼                    ▼
┌─────────────┐     ┌──────────────┐
│   ADLS Gen2  │     │   Synapse    │
│  (Bronze CSV │     │  (Compute    │
│   + CTRL)    │     │   avancé)    │
└─────────────┘     └──────────────┘
```

| Composant         | Rôle                                          |
|-------------------|-----------------------------------------------|
| **ADF**           | Orchestration des pipelines d'ingestion        |
| **Azure SQL**     | Source de vérité (vigie_ctrl, policies)         |
| **Synapse**       | Compute ponctuel pour validations avancées     |
| **Log Analytics** | KQL pour logs ADF / SLA                        |
| **ADLS Gen2**     | Stockage Bronze (CSV + fichiers CTRL JSON)     |
| **Python**        | Génération de données, extraction, SLA compute |

---

## 📁 Structure du Projet

```
OeilTest/
├── python/
│   ├── core/                      # Modules de base
│   │   ├── extractor.py           # Extraction + CTRL + SHA256
│   │   ├── schemas.py             # Data generators (faker)
│   │   ├── sqlite_schema.py       # SQLite local schema
│   │   ├── sql_writer.py          # SQLite data writer
│   │   └── vigie_faker.py         # Générateur de faux runs vigie
│   ├── runners/                   # Scripts d'exécution
│   │   ├── run_extractions.py     # Génère CSV + CTRL bronze
│   │   ├── run_vigie_faker.py     # Injecte des runs vigie simulés
│   │   ├── run_sla_compute.py     # Calcul SLA via SP
│   │   ├── run_vigie_sla_finalize.py  # Finalisation SLA + alertes
│   │   ├── reset_oeil_environment.py  # Reset complet (DB + fichiers)
│   │   ├── create_schema.py       # Création schéma Azure/SQLite
│   │   └── ok_ctrl.py             # Insert CTRL manuel
│   └── generators/                # Générateurs standalone
│       ├── generate_fake_data.py
│       ├── fake_data_generator.py
│       └── ctrl_generator.py
├── sql/
│   ├── tables/                    # DDL (CREATE TABLE)
│   │   ├── vigie_ctrl.sql         # Table principale des runs
│   │   ├── vigie_policy_table.sql # Policy par dataset (v2)
│   │   ├── vigie_policy_test.sql  # Tests par policy (v2)
│   │   ├── vigie_integrity_result.sql # Résultats intégrité (v2)
│   │   ├── ctrl_file_index.sql    # Index fichiers ingérés (re-runs)
│   │   ├── sla_profile.sql        # Profil SLA par dataset (futur)
│   │   ├── sla_profile_execution_type.sql # Profil SLA par type exec (actif)
│   │   ├── synapse_rowcount_cache.sql # Cache row count Synapse (tampon)
│   │   ├── clients.sql
│   │   ├── accounts.sql
│   │   ├── transactions.sql
│   │   └── contracts.sql
│   └── procedures/                # Stored Procedures
│       ├── SP_Compute_SLA_OEIL.sql
│       ├── SP_Compute_SLA_ADF.sql
│       ├── SP_Compute_SLA_SYNAPSE.sql
│       └── SP_Compute_SLA_Vigie.sql
├── adf/                           # Pipeline JSON ADF
├── config/
│   ├── dataset_schedule.json      # Schedule par dataset
│   └── sample_ctrl.json           # Exemple fichier CTRL v2
├── azcopy_uploader.py             # Upload Bronze → ADLS
├── requirements.txt
└── README.md
```

---

## 🎯 Capacités

### v1 — En production
| Contrôle              | Description                                          |
|-----------------------|------------------------------------------------------|
| **Row Count**         | Comparaison expected vs actual (ADF ingestion)       |
| **SLA OEIL/ADF/Synapse** | Calcul automatique des buckets (FAST/SLOW/VERY_SLOW) |
| **Volume Status**     | OK / LOW / ANOMALY                                   |
| **Alert Level**       | NO_ALERT / INFO / WARNING / CRITICAL                 |
| **Coût Synapse**      | Estimation en CAD basée sur la durée                 |
| **Hash SHA256**       | Hash canonique déterministique du payload             |

### v2 — Intégrité configurable (en cours)
| Contrôle              | Description                                          |
|-----------------------|------------------------------------------------------|
| **Min/Max**           | Validation min/max sur colonne configurée             |
| **Checksum**          | SHA256/MD5 sur colonne configurée                     |
| **Null Count**        | Validation de nullabilité                             |
| **Delta Previous**    | Comparaison avec le run précédent                     |
| **Policy Engine**     | Activation/désactivation dynamique par dataset        |

---

## 📋 Fichier CTRL (v2)

Chaque run produit un fichier JSON CTRL stocké dans le lac :

```json
{
  "ctrl_id": "accounts_2026-10-08_Q",
  "dataset": "accounts",
  "periodicity": "Q",
  "extraction_date": "2026-10-08",
  "volume": {
    "expected_rows": 1261,
    "actual_rows": 1261,
    "delta": 0
  },
  "integrity": {
    "min_max": {
      "column": "account_id",
      "min": 100001,
      "max": 198772
    },
    "checksum": {
      "column": "account_id",
      "algorithm": "SHA256",
      "value": "ab3290c9..."
    }
  }
}
```

---

## 🏛️ Modèle de Policy (v2)

La source de vérité des policies est SQL. Elles sont exportables en JSON vers le lac.

```
vigie_policy_table          vigie_policy_test
┌──────────────────┐        ┌──────────────────────────┐
│ dataset (PK)     │───────▶│ dataset (FK)             │
│ environment      │        │ test_type                │
│ enabled          │        │ enabled                  │
│ synapse_allowed  │        │ frequency (DAILY/WEEKLY)  │
└──────────────────┘        │ target_column            │
                            │ algorithm                │
                            └──────────────────────────┘
                                       │
                                       ▼
                            ┌──────────────────────────┐
                            │ vigie_integrity_result    │
                            │ ctrl_id + test_type       │
                            │ result_status (OK/FAIL)   │
                            │ expected vs actual        │
                            │ compute_engine            │
                            │ compute_cost              │
                            └──────────────────────────┘
```

---

## 🚀 Quick Start

### Prérequis
- Python 3.12+
- ODBC Driver 18 for SQL Server
- Azure SQL Database
- AzCopy (pour upload ADLS)

### Installation

```bash
python -m venv .venv2
.venv2\Scripts\activate
pip install -r requirements.txt
```

### Exécuter une extraction (fake data)

```bash
python -m python.runners.run_extractions
```

### Injecter des runs vigie simulés

```bash
python -m python.runners.run_vigie_faker
```

### Calculer les SLA

```bash
python -m python.runners.run_sla_compute
```

### Finaliser SLA + Alertes

```bash
python -m python.runners.run_vigie_sla_finalize
```

### Upload Bronze → ADLS

```bash
python azcopy_uploader.py
```

### Reset complet de l'environnement

```bash
python -m python.runners.reset_oeil_environment
```

---

## ⚡ Contraintes de Design

| Contrainte                          | Approche                                            |
|-------------------------------------|-----------------------------------------------------|
| Synapse = coûteux                   | Déclenché **uniquement** si policy active             |
| DEV peut être plus strict que PROD  | Champ `environment` dans vigie_policy_table           |
| Tests activables dynamiquement      | Table vigie_policy_test avec champ `enabled`          |
| Compute traçable                    | Champs `compute_engine` + `compute_cost` dans résultats |
| Aucune modification pipeline        | La policy SQL contrôle tout dynamiquement             |

---

## 📊 Tables SQL

| Table                        | Rôle                                 |
|------------------------------|--------------------------------------|
| `dbo.vigie_ctrl`             | Métriques run-level (volume, SLA, alertes) |
| `dbo.vigie_policy_table`     | Policy de gouvernance par dataset     |
| `dbo.vigie_policy_test`      | Tests activés par type et fréquence   |
| `dbo.vigie_integrity_result` | Résultats détaillés d'intégrité       |
| `dbo.ctrl_file_index`        | Index des fichiers ingérés (re-runs)  |
| `dbo.sla_profile`            | Profil SLA par dataset (feature future) |
| `dbo.sla_profile_execution_type` | Profil SLA par type d'exécution (actif) |
| `dbo.synapse_rowcount_cache`     | Cache row count Synapse (table tampon)  |

### 👁️ `vigie_ctrl` — Table principale (run-level metrics)

Un enregistrement par run d'extraction. Contient toutes les métriques de volume, SLA, coûts et alertes.

**Identité du run :**

| Colonne | Type | Rôle |
|---|---|---|
| `ctrl_id` | varchar(200) | **PK** — identifiant unique du run |
| `dataset` | varchar(50) | Nom du dataset |
| `periodicity` | varchar(10) | Fréquence (D/W/M/Q) |
| `extraction_date` | date | Date d'extraction |
| `expected_rows` | int | Lignes attendues |
| `source_system` | varchar(50) | Système source |
| `created_ts` | datetime2(7) | Timestamp de création |
| `pipeline_run_id` | varchar(100) | ID du pipeline ADF |
| `adf_pipeline_name` | varchar(100) | Nom du pipeline ADF |
| `adf_trigger_name` | varchar(100) | Nom du trigger ADF |
| `start_ts` / `end_ts` | datetime2(7) | Début / fin du run |
| `duration_sec` | int | Durée totale (sec) |
| `status` | varchar(20) | Statut du run |
| `status_global` | varchar(20) | Statut agrégé global |
| `inserted_ts` | datetime2(7) | Auto : date d'insertion (UTC) |

**Volume (Bronze / Parquet) :**

| Colonne | Type | Rôle |
|---|---|---|
| `bronze_rows` / `parquet_rows` | int | Row count par couche |
| `bronze_delta` / `parquet_delta` | int | Delta vs expected |
| `bronze_status` / `parquet_status` | varchar | OK / LOW / ANOMALY |
| `volume_status` | varchar(20) | Statut volume agrégé |
| `row_count_adf_ingestion_copie_parquet` | int | Rows copiées par ADF vers parquet |

**SLA par moteur :**

| Préfixe | Colonnes | Description |
|---|---|---|
| `sla_*` | `sla_sec`, `sla_expected_sec`, `sla_threshold_sec`, `sla_status`, `sla_reason`, `sla_bucket` | SLA global |
| `oeil_sla_*` | `oeil_sla_sec`, `oeil_sla_expected_sec`, `oeil_sla_threshold_sec`, `oeil_sla_status`, `oeil_sla_reason` | SLA L'ŒIL |
| `adf_sla_*` | `adf_sla_sec`, `adf_sla_expected_sec`, `adf_sla_threshold_sec`, `adf_sla_status`, `adf_sla_reason` | SLA ADF |
| `synapse_sla_*` | `synapse_sla_sec`, `synapse_sla_expected_sec`, `synapse_sla_threshold_sec`, `synapse_sla_status`, `synapse_sla_reason` | SLA Synapse |

**Alertes & Coûts :**

| Colonne | Type | Rôle |
|---|---|---|
| `alert_flag` | bit | Alerte déclenchée ? |
| `alert_level` | varchar(20) | NO_ALERT / INFO / WARNING / CRITICAL |
| `alert_reason` | varchar(100) | Raison de l'alerte |
| `alert_ts` | datetime2(7) | Timestamp de l'alerte |
| `synapse_cost_estimated_cad` | decimal(10,6) | Coût estimé Synapse (CAD) |
| `synapse_cost_rate_cad_per_min` | decimal(10,6) | Taux $/min Synapse |

**Intégrité payload :**

| Colonne | Type | Rôle |
|---|---|---|
| `payload_canonical` | varchar(500) | Forme canonique du payload |
| `payload_hash_sha256` | char(64) | Hash SHA-256 déterministique |
| `payload_hash_version` | tinyint | Version de l'algorithme de hash |
| `payload_hash_match` | bit | Hash correspond ? |

> **Index** : `IX_vigie_ctrl_dataset_date` sur (`dataset`, `periodicity`, `extraction_date`) pour les lookups rapides.

### 📂 `ctrl_file_index` — Index des fichiers ingérés

Insérée lors de l'upload réussi d'un fichier sur le lake bronze. Essentielle pour les re-runs.

| Colonne | Type | Rôle |
|---|---|---|
| `ctrl_id` | nvarchar(200) | **PK** — identifiant unique du contrôle |
| `dataset` | nvarchar(200) | Nom du dataset |
| `ctrl_path` | nvarchar(1024) | Chemin logique complet du fichier |
| `processed_flag` | bit | Re-run : `0` = à traiter, `1` = déjà traité |
| `processed_ts` | datetime2(3) | Timestamp du traitement |
| `created_ts` | datetime2(3) | Auto : date de création (UTC) |
| `ctrl_path_hash` | binary(32) | **Computed + Unique Index** — SHA-256 du chemin (dédoublonnage) |

### 📈 `sla_profile` — Profil SLA par dataset (feature future)

Calcul de SLA de base par dataset : `SLA = base_overhead_sec + (rows / 1000) × sec_per_1k_rows` avec marge de tolérance.

| Colonne | Type | Rôle |
|---|---|---|
| `dataset` | nvarchar(200) | **PK** — un profil SLA par dataset |
| `base_overhead_sec` | int | Overhead fixe de base (secondes) |
| `sec_per_1k_rows` | int | Coût variable par tranche de 1K lignes |
| `tolerance_pct` | decimal(5,2) | Tolérance en % avant alerte SLA |
| `active_flag` | bit | Actif/inactif (default `1`) |
| `created_ts` | datetime2(3) | Auto : date de création (UTC) |

### ⚡ `sla_profile_execution_type` — Profil SLA par type d'exécution (actif)

Version en production — profils SLA par type d'exécution (ADF / SYNAPSE / OEIL).

| Colonne | Type | Rôle |
|---|---|---|
| `execution_type` | varchar(30) | **PK** — type d'exécution |
| `base_overhead_sec` | int | Overhead fixe (secondes) |
| `sec_per_1k_rows` | int (nullable) | Coût variable par 1K lignes |
| `tolerance_pct` | decimal(5,2) | Tolérance en % |
| `active_flag` | bit | Actif (default `1`) |
| `created_ts` | datetime2(3) | Date de création (UTC) |

**Données de base :**

| execution_type | overhead | /1K rows | tolérance |
|---|---|---|---|
| **ADF** | 30s | 5s | 25% |
| **OEIL** | 360s (6 min) | — | 22% |
| **SYNAPSE** | 120s (2 min) | — | 30% |

### 🗄️ `synapse_rowcount_cache` — Cache row count Synapse

Table tampon pour éviter les requêtes Synapse coûteuses et répétitives. Stocke les row counts par dataset/periodicité/date/layer. Première ébauche fonctionnelle — la logique d'agrégation complète reste à programmer.

| Colonne | Type | Rôle |
|---|---|---|
| `dataset` | varchar(50) | **PK (1/4)** — nom du dataset |
| `periodicity` | varchar(10) | **PK (2/4)** — fréquence (D/W/M/Q) |
| `extraction_date` | date | **PK (3/4)** — date d'extraction |
| `layer` | varchar(10) | **PK (4/4)** — couche (bronze/silver/gold) |
| `row_count` | int | Nombre de lignes comptées |
| `computed_ts` | datetime2(7) | Auto : timestamp du calcul (UTC) |

> **Design** : PK composite à 4 colonnes = un row count unique par combinaison dataset + periodicité + date + layer. Pas de surrogate key — la clé naturelle suffit pour le cache.

---

## 🔮 Roadmap

- [ ] Orchestration conditionnelle Synapse via policy SQL
- [ ] Export policy → JSON dans le lac
- [ ] Dashboard Power BI connecté à vigie_ctrl
- [ ] Notification Teams / Email sur CRITICAL
- [ ] Support multi-environnement (DEV / UAT / PROD)
- [ ] Intégration Log Analytics KQL pour audit trail

---

## 📜 License

Projet interne — L'ŒIL Framework © 2026
