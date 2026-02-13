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
