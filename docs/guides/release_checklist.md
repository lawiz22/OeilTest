# ✅ Release Checklist (Demo / Runbook)

Checklist opérationnelle pour exécuter une passe complète sans oublier d’étape.

## 1) Pré-flight (5 min)

- Vérifier que l’environnement Python est actif :
  - `\.venv2\Scripts\activate`
- Vérifier la variable SQL :
  - `echo $env:OEIL_AZURE_SQL_PASSWORD`
- Vérifier la validité du SAS dans [azcopy_uploader.py](../../azcopy_uploader.py) :
  - heure de début/fin (`st`, `se`)
  - scope correct (`banquelaw` vs `banquelaw/bronze`)

## 2) Nettoyage (optionnel mais recommandé)

- Local (fichiers + SQLite) :
  - `python -m python.runners.reset_oeil_environment`
- Azure SQL (si besoin de repartir propre) :
  - exécuter [sql/delete_azure_bd.sql](../../sql/delete_azure_bd.sql)

## 3) Génération des données

- Extraction locale (CTRL + CSV + SQLite) :
  - `python -m python.runners.run_extractions`
- Données vigie simulées (dashboard volumétrique / SLA) :
  - `python -m python.runners.run_vigie_faker`

## 4) Upload Lake

- Copier Bronze vers ADLS :
  - `python azcopy_uploader.py`

## 5) Calculs SLA / Finalisation

- Calcul SLA :
  - `python -m python.runners.run_sla_compute`
- Finalisation SLA + alertes :
  - `python -m python.runners.run_vigie_sla_finalize`

## 6) Vérification rapide SQL (sanity checks)

```sql
SELECT TOP 20 ctrl_id, expected_rows, row_count_adf_ingestion_copie_parquet, bronze_delta, parquet_delta, created_ts
FROM dbo.vigie_ctrl
ORDER BY created_ts DESC;
```

```sql
SELECT dataset,
       COUNT(*) AS runs,
       SUM(CASE WHEN COALESCE(bronze_delta,0) <> 0 OR COALESCE(parquet_delta,0) <> 0 THEN 1 ELSE 0 END) AS runs_with_delta
FROM dbo.vigie_ctrl
GROUP BY dataset;
```

## 7) Vérification Power BI

- Refresh dataset/model
- Vérifier filtres (mois/dataset)
- Confirmer les onglets volumétriques :
  - Volume Watch ADF
  - Volume Watch SYNAPSE

## 8) Commande de secours (timeout Azure SQL sur extraction)

Si `run_extractions` échoue sur l’insert SQL de `ctrl_file_index`, lancer en mode tolérant :

- PowerShell :
  - `$env:OEIL_CTRL_INDEX_MODE="best_effort"`
  - `python -m python.runners.run_extractions`

Modes disponibles : `required` (défaut), `best_effort`, `disabled`.
