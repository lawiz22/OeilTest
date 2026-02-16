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

## 9) Gap Register (Recommended -> Implemented)

Suivi des conventions documentées comme **[Recommended]** pour passage en **[Implemented]**.

| Sujet | Statut actuel | Action pour clôture |
|---|---|---|
| Valeurs volume (`EMPTY` / `MISSING` / `EXPECTED_ZERO`) | Convention doc, dépend de l'implémentation SQL locale | Uniformiser `SC_Set_Volume_Check` + mapping BI |
| Applicabilité fréquence tests (SKIPPED vs MISSING) | Convention doc, non persistée explicitement partout | Ajouter statut explicite côté `vigie_integrity_result` ou table de synthèse |
| Réduction multi-tests (tous test_codes) | Implémenté pour `ROWCOUNT` via SP dédiée | Étendre règle de réduction standard à tous les tests dans les vues BI/SQL |
| Cohérence timestamps non-réécriture | Règle documentée | Vérifier/renforcer idempotence dans SP lifecycle (`start_ts`/`end_ts`) |
| `p_environment` transmis à Quality Engine | Paramètre par défaut utilisé depuis `PL_Ctrl_To_Vigie` | Passer `p_environment` explicitement dans `ExecutePipeline` |
| Secret Log Analytics | Secret hardcodé retiré, paramètre `secureString` ajouté | Migrer en Azure Key Vault linked service (recommandé prod) |

## 10) Issues GitHub (copier-coller)

### Issue 1 — Uniformiser les flags volume (`EMPTY` / `MISSING` / `EXPECTED_ZERO`)

**Title**
- `docs+sql: standardize volume_status values (EMPTY/MISSING/EXPECTED_ZERO)`

**Description**
- Aligner la logique SQL de `SC_Set_Volume_Check` avec les conventions documentées.
- Garantir le mapping BI unique pour éviter les ambiguïtés entre `UNKNOWN`, `WARNING`, `ANOMALY`, etc.

**Definition of Done**
- `volume_status` suit un dictionnaire stable documenté.
- Mapping BI validé.
- Docs mises à jour si nomenclature finale différente.

### Issue 2 — Fréquence policy: expliciter `SKIPPED` vs `MISSING`

**Title**
- `quality-engine: persist explicit test applicability status (SKIPPED/MISSING)`

**Description**
- Rendre explicite la différence entre test non applicable (fréquence/policy) et test manquant (incident).
- Éviter qu'un test non exécuté soit confondu avec un test échoué ou absent.

**Definition of Done**
- Statut d'applicabilité persistant dans SQL (ou vue dédiée).
- Règle documentée dans la policy.
- Vérification sur un run avec tests applicables + non applicables.

### Issue 3 — Réduction multi-tests généralisée

**Title**
- `sql: generalize latest-result reduction for integrity tests`

**Description**
- Étendre la règle de réduction déjà utilisée pour `ROWCOUNT` aux autres `test_code`.
- Standardiser la sélection du dernier résultat valide par (`ctrl_id`, `test_code`, `column_name`).

**Definition of Done**
- Règle SQL/vues unifiée.
- Pas de dépendance à l'ordre implicite d'insertion.
- Résultat vérifié sur jeux avec doublons de tests.

### Issue 4 — Idempotence timestamps lifecycle

**Title**
- `sql: enforce lifecycle timestamp idempotence (start_ts/end_ts)`

**Description**
- Empêcher la réécriture involontaire de timestamps déjà posés.
- Sécuriser les cas de rerun partiel et éviter les durées nulles ou incohérentes.

**Definition of Done**
- Guard clauses SQL présentes et testées.
- Cas rerun documenté.
- Durées OEIL/ADF/Synapse restent cohérentes.

### Issue 5 — Passer `p_environment` explicitement au pipeline qualité

**Title**
- `adf: pass p_environment from PL_Ctrl_To_Vigie to PL_Oeil_Quality_Engine`

**Description**
- Éviter la dépendance à la valeur par défaut du pipeline qualité.
- Garantir le même comportement entre environnements et déploiements.

**Definition of Done**
- Paramètre transmis explicitement dans `ExecutePipeline`.
- Validation sur au moins 2 environnements (ex: DEV/PROD).
- Documentation I/O contract ajustée.

### Issue 6 — Migrer le secret Log Analytics vers Key Vault

**Title**
- `security: replace runtime secret parameter with Azure Key Vault reference`

**Description**
- Remplacer l'injection `secureString` runtime par une référence Key Vault.
- Réduire le risque opérationnel et simplifier les rotations de secret.

**Definition of Done**
- Linked service Key Vault configuré.
- Pipeline ADF consomme le secret via référence sécurisée.
- Push Protection ne détecte plus de secret applicatif dans les JSON versionnés.
