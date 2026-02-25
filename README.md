
# 👁️ L'ŒIL — Data Quality & Integrity Framework

## Principaux outils visuels


### Dashboard Executive (SLA)
<img src="docs/screenshots/PowerBi_Main_Execv2.png" alt="Dashboard Executive" width="400" />

### Control Center (UI)
<img src="docs/screenshots/cc_home.png" alt="Control Center" width="350" />

### Synthèse Qualité
<img src="docs/screenshots/BI_Qualite_1.png" alt="Qualité" width="350" />

### Vue Structurelle
<img src="docs/screenshots/cc_structural.png" alt="Vue Structurelle" width="350" />


[![Build](https://github.com/lawiz22/OeilTest/actions/workflows/validate-sql-json.yml/badge.svg)](https://github.com/lawiz22/OeilTest/actions/workflows/validate-sql-json.yml)
![Tests](https://img.shields.io/badge/tests-e2e--demo-blue)
![Version](https://img.shields.io/badge/version-2.0-blue)
![License](https://img.shields.io/badge/license-Internal-red)
![Azure](https://img.shields.io/badge/platform-Azure-0078D4)
![Framework](https://img.shields.io/badge/type-Policy%20Driven%20Framework-purple)

> Moteur de validation configurable, traçable et réutilisable pour Azure (ADF + Synapse + Azure SQL + Log Analytics).

## 🎯 Ce que fait L’ŒIL

- Valide le contrat de données attendu vs exécution réelle.
- Calcule les SLA ADF, Synapse et global run.
- Pilote la qualité via des policies versionnées et exportables.
- Contrôle l’intégrité structurelle par hash (contract_hash vs detected_hash).
- Génère des traces d’audit exploitables pour runbook et reporting.

## 🧱 Architecture logique (6 blocs)

- Ingestion & orchestration: `PL_Bronze_*`, `PL_Oeil_Guardian`, `PL_Oeil_Core`.
- Contrat de run: Control File (CTRL) et tables `vigie_*`.
- Moteur policy: règles dataset/environnement + tests activables.
- Moteur SLA: calculs ADF / Synapse / OEIL.
- Gate structurel: comparaison hash contrat vs hash détecté.
- Observabilité: logs, indicateurs et dashboard.

## 🚀 Commandes rapides

- Environnement Python
  - `python -m venv .venv2`
  - `.venv2\Scripts\activate`
  - `pip install -r requirements.txt`
- Variables (PowerShell)
  - `$env:OEIL_AZURE_SQL_PASSWORD="YOUR_PASSWORD_HERE"`
- Run extraction
  - `python -m python.runners.run_extractions`
- Reset environnement
  - `python -m python.runners.reset_oeil_environment`
- UI Control Center
  - `python -m uvicorn python.oeil_ui.main:app --reload`

## 🧭 Parcours recommandé

- Démo courte (15–20 min)
  - [Documentation Hub](docs/index.md)
  - [Parcours guidé](docs/walkthrough/index.md)
  - [Control Center](docs/guides/control_center.md)
- Démo complète (45 min)
  - [Demo Run — End-to-End](docs/guides/demo_run_end_to_end.md)
  - [Release Checklist](docs/guides/release_checklist.md)
- Approfondissement technique
  - [Concepts](docs/concepts/index.md)
  - [Référence technique](docs/technical_reference/index.md)

## 📚 Documentation

- Entrée principale: [docs/index.md](docs/index.md)
- Concepts: [docs/concepts/index.md](docs/concepts/index.md)
- Référence technique: [docs/technical_reference/index.md](docs/technical_reference/index.md)
- Annexes: [docs/appendices/index.md](docs/appendices/index.md)

## 📜 License

Projet interne — L'ŒIL Framework © 2026
