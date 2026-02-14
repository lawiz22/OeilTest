# 👁️ L'ŒIL — Data Quality & Integrity Framework

> **Un moteur de validation configurable, traçable et réutilisable — enterprise-wide.**

L'ŒIL est un framework de contrôle qualité des données conçu pour les environnements Azure. Il orchestre la validation de volumes, de SLA, d'intégrité et de coûts à travers Azure Data Factory, Synapse, Azure SQL et Log Analytics.

![Build](https://img.shields.io/badge/build-manual-lightgrey)
![Coverage](https://img.shields.io/badge/coverage-n/a-lightgrey)
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
