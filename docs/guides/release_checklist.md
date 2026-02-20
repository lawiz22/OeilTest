# Release Checklist (Demo / Runbook)

Checklist opérationnelle pour exécuter une passe complète sans oublier d'étape.

Ce checklist sert autant pour une **démo exécutive** que pour un **run technique complet**.

## Demo Mode

- **[Demo Required]** : étape minimale pour une démo réussie.
- **[Optional]** : étape recommandée mais non bloquante pour une démo.

## 1) Pré-flight (5 min) [Demo Required]

- Vérifier que l'environnement Python est actif :
  - `\.venv2\Scripts\activate`
- Vérifier la variable SQL :
  - `echo $env:OEIL_AZURE_SQL_PASSWORD`
- Vérifier la validité du SAS dans [azcopy_uploader.py](../../azcopy_uploader.py) :
  - heure de début/fin (`st`, `se`)
  - scope correct (`banquelaw` vs `banquelaw/bronze`)

## 2) Nettoyage (optionnel mais recommandé) [Optional]
WARNING: **Ne jamais exécuter `delete_azure_bd.sql` en PROD.**

- Local (fichiers + SQLite) :
  - `python -m python.runners.reset_oeil_environment`
- Azure SQL (si besoin de repartir propre) :
  - exécuter [sql/delete_azure_bd.sql](../../sql/delete_azure_bd.sql)

## 3) Génération des données [Demo Required]

- Extraction locale (CTRL + CSV + SQLite) :
  - `python -m python.runners.run_extractions`
- Données vigie simulées (dashboard volumétrique / SLA) :
  - `python -m python.runners.run_vigie_faker`

## 4) Upload Lake [Demo Required]

- Copier Bronze vers ADLS :
  - `python azcopy_uploader.py`

## 5) Calculs SLA / Finalisation [Demo Required]

- Calcul SLA :
  - `python -m python.runners.run_sla_compute`
- Finalisation SLA + alertes :
  - `python -m python.runners.run_vigie_sla_finalize`

## 6) Vérification rapide SQL (sanity checks) [Demo Required]

### 6a) Déploiement SP_Insert_VigieIntegrityResult (script versionné)

- Exécuter le script de release : [sql/release/2026-02-20_release_sp_insert_vigie_integrity_result.sql](../../sql/release/2026-02-20_release_sp_insert_vigie_integrity_result.sql)
- Le script inclut :
  - pré-checks (procédure cible + colonnes texte dans `vigie_integrity_result`)
  - `ALTER PROCEDURE`
  - smoke test post-déploiement avec `ROLLBACK` (aucune pollution de données)

Attendu en sortie SQL:

- message `Smoke test OK (rollback effectif).`
- une ligne de résultat contenant `observed_value_text` et `reference_value_text` non nulles pendant le smoke test.

```sql
SELECT TOP 20 ctrl_id,
       expected_rows,
       row_count_adf_ingestion_copie_parquet,
       bronze_delta,
       parquet_delta,
       quality_status_global,
       quality_tests_total,
       quality_tests_pass,
       quality_tests_fail,
       quality_tests_warning,
       created_ts
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

### 6b) Vérification hash canonique CTRL (3 requêtes) [Demo Required]

```sql
SELECT TOP 20
  ctrl_id,
  payload_hash_version,
  payload_hash_sha256,
  payload_canonical,
  payload_hash_match,
  alert_flag,
  alert_reason,
  inserted_ts
FROM dbo.vigie_ctrl
ORDER BY inserted_ts DESC;
```

```sql
SELECT
  COUNT(*) AS total_runs,
  SUM(CASE WHEN payload_hash_match = 1 THEN 1 ELSE 0 END) AS hash_ok_runs,
  SUM(CASE WHEN payload_hash_match = 0 THEN 1 ELSE 0 END) AS hash_mismatch_runs,
  SUM(CASE WHEN alert_reason = 'MISSING_HASH' THEN 1 ELSE 0 END) AS missing_hash_runs
FROM dbo.vigie_ctrl;
```

```sql
DECLARE @ctrl_id NVARCHAR(200) = 'clients_2026-07-01_Q';

SELECT
  v.ctrl_id,
  v.payload_hash_sha256 AS stored_hash,
  LOWER(CONVERT(VARCHAR(64), HASHBYTES('SHA2_256', CAST(
    v.dataset + '|' +
    v.periodicity + '|' +
    CONVERT(VARCHAR(10), v.extraction_date, 23) + '|' +
    CAST(v.expected_rows AS VARCHAR(20))
  AS VARCHAR(MAX))), 2)) AS computed_hash,
  v.payload_hash_match,
  v.alert_reason
FROM dbo.vigie_ctrl v
WHERE v.ctrl_id = @ctrl_id;
```

Lecture rapide attendue:

- `payload_hash_match = 1` et `alert_reason = HASH_OK` => contrôle hash validé.
- `payload_hash_match = 0` et `alert_reason = CTRL_HASH_MISMATCH` => fichier CTRL potentiellement altéré.
- `alert_reason = MISSING_HASH` => hash absent côté payload CTRL.

## 7) Vérification Power BI [Demo Required]

- Refresh dataset/model
- Vérifier filtres (mois/dataset)
- Confirmer les onglets volumétriques :
  - Volume Watch ADF
  - Volume Watch SYNAPSE

## 8) Commande de secours (timeout Azure SQL sur extraction) [Optional]

Si `run_extractions` échoue sur l'insert SQL de `ctrl_file_index`, lancer en mode tolérant :

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
| `p_environment` transmis à Quality Engine | Implémenté (propagé `Guardian` -> `Core` -> `Quality`) | Clôturé |
| Secret Log Analytics | Secret hardcodé retiré, paramètre `secureString` ajouté | Migrer en Azure Key Vault linked service (recommandé prod) |

## 10) Issues GitHub (copier-coller)

Statut rapide: Issues `1,2,3,4,6` = **OPEN** ; Issue `5` = **CLOSED**.

### Ouvertes

### Issue 1 [OPEN] - Uniformiser les flags volume (`EMPTY` / `MISSING` / `EXPECTED_ZERO`)

**Title**
- `docs+sql: standardize volume_status values (EMPTY/MISSING/EXPECTED_ZERO)`

**Description**
- Aligner la logique SQL de `SC_Set_Volume_Check` avec les conventions documentées.
- Garantir le mapping BI unique pour éviter les ambiguïtés entre `UNKNOWN`, `WARNING`, `ANOMALY`, etc.

**Definition of Done**
- `volume_status` suit un dictionnaire stable documenté.
- Mapping BI validé.
- Docs mises à jour si nomenclature finale différente.

### Issue 2 [OPEN] - Fréquence policy: expliciter `SKIPPED` vs `MISSING`

**Title**
- `quality-engine: persist explicit test applicability status (SKIPPED/MISSING)`

**Description**
- Rendre explicite la différence entre test non applicable (fréquence/policy) et test manquant (incident).
- Éviter qu'un test non exécuté soit confondu avec un test échoué ou absent.

**Definition of Done**
- Statut d'applicabilité persistant dans SQL (ou vue dédiée).
- Règle documentée dans la policy.
- Vérification sur un run avec tests applicables + non applicables.

### Issue 3 [OPEN] - Réduction multi-tests généralisée

**Title**
- `sql: generalize latest-result reduction for integrity tests`

**Description**
- Étendre la règle de réduction déjà utilisée pour `ROWCOUNT` aux autres `test_code`.
- Standardiser la sélection du dernier résultat valide par (`ctrl_id`, `test_code`, `column_name`).

**Definition of Done**
- Règle SQL/vues unifiée.
- Pas de dépendance à l'ordre implicite d'insertion.
- Résultat vérifié sur jeux avec doublons de tests.

### Issue 4 [OPEN] - Idempotence timestamps lifecycle

**Title**
- `sql: enforce lifecycle timestamp idempotence (start_ts/end_ts)`

**Description**
- Empêcher la réécriture involontaire de timestamps déjà posés.
- Sécuriser les cas de rerun partiel et éviter les durées nulles ou incohérentes.

**Definition of Done**
- Guard clauses SQL présentes et testées.
- Cas rerun documenté.
- Durées OEIL/ADF/Synapse restent cohérentes.

### Issue 6 [OPEN] - Migrer le secret Log Analytics vers Key Vault

**Title**
- `security: replace runtime secret parameter with Azure Key Vault reference`

**Description**
- Remplacer l'injection `secureString` runtime par une référence Key Vault.
- Réduire le risque opérationnel et simplifier les rotations de secret.

**Definition of Done**
- Linked service Key Vault configuré.
- Pipeline ADF consomme le secret via référence sécurisée.
- Push Protection ne détecte plus de secret applicatif dans les JSON versionnés.

### Clôturées

### Issue 5 [CLOSED] - Passer `p_environment` explicitement au pipeline qualité

**Title**
- `[CLOSED] adf: pass p_environment from PL_Oeil_Core to PL_Oeil_Quality_Engine`

**Description**
- Implémenté: `p_environment` est propagé explicitement de `PL_Oeil_Guardian` vers `PL_Oeil_Core`, puis vers `PL_Oeil_Quality_Engine`.
- Le comportement n'est plus dépendant d'une valeur par défaut implicite.

**Definition of Done**
- Paramètre transmis explicitement dans `ExecutePipeline`.
- Documentation I/O contract ajustée.
- Validation multi-environnements à conserver en check de release (DEV/PROD).

