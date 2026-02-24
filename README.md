# 👁️ L'ŒIL — Data Quality & Integrity Framework

> **Un moteur de validation configurable, traçable et réutilisable — enterprise-wide.**

> **A lightweight Data Reliability Platform for Azure-native architectures.**

L'ŒIL est un framework de contrôle qualité des données conçu pour les environnements Azure. Il orchestre la validation de volumes, de SLA, d'intégrité et de coûts à travers Azure Data Factory, Synapse, Azure SQL et Log Analytics.

## TL;DR — L’ŒIL en 30 secondes

L’ŒIL est un framework de qualité des données **piloté par politiques** pour Azure qui :

- valide le contrat de données vs l’exécution réelle,
- calcule les SLA et les coûts,
- génère des snapshots d’audit immuables,
- sépare l’ingestion de la gouvernance.

> **Mise à jour architecture** : l'orchestration est scindée entre `PL_Oeil_Guardian` (ingestion CTRL + garde hash) et `PL_Oeil_Core` (qualité/SLA/alertes). La validation Synapse reste centralisée dans `PL_Oeil_Quality_Engine` (appelé par `PL_Oeil_Core`).

## 🎯 Pourquoi L’ŒIL existe

Dans un environnement data moderne, les pipelines assurent le transport des données,
mais très peu garantissent :

- La cohérence entre couches (bronze → parquet → modèle)
- La traçabilité SLA complète (ADF + Synapse + global)
- La détection automatique d’anomalies volumétriques
- La gouvernance par politiques réutilisables

L’ŒIL apporte cette couche de contrôle transversale.

## 👁️ Modèle conceptuel

- Œil gauche : ce qui est attendu (Control File, contrat)
- Œil droit : ce qui est exécuté (ADF, Synapse, SLA, volumes)

L’ŒIL compare les deux.
- `status` : statut technique du dernier test d'intégrité
- `status_global` : statut global du run (`IN_PROGRESS`, `COMPLETED`)

## 🧩 Vision

L’ŒIL n’est pas un pipeline.
C’est une couche de gouvernance qualité transverse,
conçue pour devenir un standard interne.

## 🧾 Glossaire canonique (rapide)

Pour uniformiser ADF + SQL + reporting, on utilise les clés canoniques suivantes :

- `p_ctrl_id` : identifiant unique du run (`ctrl_id` en base)
- `p_dataset` : dataset métier (`p_table` dans certains pipelines, `dataset_name` dans les résultats d'intégrité)
- `p_periodicity` : fréquence (`p_period` dans certains pipelines)
- `p_extraction_date` : date de référence de la partition

Voir convention complète :
- [ADF Pipelines](docs/technical_reference/adf_pipelines.md)
- [Stored Procedures](docs/technical_reference/stored_procedures.md)

[![Build](https://github.com/lawiz22/OeilTest/actions/workflows/validate-sql-json.yml/badge.svg)](https://github.com/lawiz22/OeilTest/actions/workflows/validate-sql-json.yml)
![Tests](https://img.shields.io/badge/tests-e2e--demo-blue)
![Version](https://img.shields.io/badge/version-2.0-blue)
![License](https://img.shields.io/badge/license-Internal-red)
![Azure](https://img.shields.io/badge/platform-Azure-0078D4)
![Framework](https://img.shields.io/badge/type-Policy%20Driven%20Framework-purple)

---

## 📚 Documentation Complète

La documentation complète du projet est disponible dans le dossier [`docs/`](docs/index.md).

### 🚀 [Getting Started](docs/getting_started.md)
Prérequis, installation, et comment lancer votre première extraction.

### 🏗️ [Architecture](docs/architecture.md)
Vue d'ensemble des composants (ADF, SQL, Synapse) et flux de données.

### 🧠 Concepts
- **[Framework Capabilities](docs/concepts/framework_capabilities.md)**: Fonctionnalités v1 vs v2.
- **[Control File (CTRL)](docs/concepts/control_file.md)**: Structure du fichier JSON de contrôle.
- **[Policy Engine](docs/concepts/policy_engine.md)**: Modèle de gouvernance et règles.
- **[SLA Management](docs/concepts/sla_management.md)**: Logique de calcul des SLA.

### ⚙️ Référence Technique
- **[Database Schema](docs/technical_reference/database_schema.md)**: Définitions des tables SQL.
- **[Stored Procedures](docs/technical_reference/stored_procedures.md)**: Logique des procédures stockées.
- **[ADF Pipelines](docs/technical_reference/adf_pipelines.md)**: Pipelines d'ingestion et transformation.

### 📖 Guides
- **[Tableau de Bord Power BI](docs/guides/powerbi_dashboard.md)**: Comprendre les métriques.
- **[Choix de Design](docs/guides/design_decisions.md)**: Raisons derrière l'architecture.
- **[FAQ stratégique — Pourquoi pas un module Azure existant ?](docs/guides/design_decisions.md#9-faq-stratégique--pourquoi-ne-pas-utiliser-un-module-azure-existant)**: Réponse courte pour comités d’architecture.
- **[Oeil Control Center](docs/guides/control_center.md)**: Guide opérationnel complet de l’UI Home / Policy / Structural.
- **[Release Checklist](docs/guides/release_checklist.md)**: Runbook rapide pour les démos et exécutions complètes.
- **[Demo Run End-to-End](docs/guides/demo_run_end_to_end.md)**: Parcours pas à pas documenté avec screenshots.

---

## 🖥️ Control Center (outil central du workflow)

Le **Control Center** est devenu le point d’entrée principal pour opérer L’ŒIL:

- supervision globale (Home),
- gouvernance des tests (Policy),
- validation du contrat structurel et comparaison Synapse (Structural).

➡️ Documentation dédiée: **[docs/guides/control_center.md](docs/guides/control_center.md)**

---

## ⚡ Commandes Rapides

### Installation
```bash
python -m venv .venv2
.venv2\Scripts\activate
pip install -r requirements.txt
```

### Variables d'environnement (Azure SQL)
```bash
# PowerShell (session courante)
$env:OEIL_AZURE_SQL_PASSWORD="YOUR_PASSWORD_HERE"
```

Ou copie [.env.example](.env.example) vers `.env` puis remplace les valeurs.

### Configuration run_extractions
```bash
# Créer une config locale (non versionnée)
copy config\run_extractions.example.json config\run_extractions.json

# Exécuter avec config locale
python -m python.runners.run_extractions

# Ou exécuter avec un fichier explicite
python -m python.runners.run_extractions --config config\run_extractions.example.json
```

### Exécuter une simulation
```bash
python -m python.runners.run_extractions
```

### Reset complet
```bash
python -m python.runners.reset_oeil_environment
```

---

## 📜 License

Projet interne — L'ŒIL Framework © 2026
