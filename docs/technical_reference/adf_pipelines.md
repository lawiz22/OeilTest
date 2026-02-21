# 🚀 ADF Pipelines

Les pipelines Azure Data Factory sont les moteurs d'ingestion et de transformation.

## Marquage audit

- **[Implemented]** : reflète le JSON pipeline actuel.
- **[Recommended]** : convention d'exploitation/documentation.

## Convention de vocabulaire (cross-docs)

Pour uniformiser la lecture entre ADF, SQL et reporting, les termes canoniques sont :

- `p_ctrl_id`
- `p_dataset`
- `p_periodicity`
- `p_extraction_date`

Quand le nom technique diffère dans un pipeline (ex: `p_table`, `p_period`), il est documenté avec l'équivalence canonique.

## Organisation (ordre d'exécution)

### Pipelines d’ingestion

1. `PL_Bronze_Event_Master`
2. `PL_Bronze_To_Standardized_Parquet`

### Pipelines ŒIL

3. `PL_Oeil_Guardian`
4. `PL_Oeil_Core`
5. `PL_Oeil_Quality_Engine`

## 1. `PL_Bronze_Event_Master`

### Rôle : Point d'entrée Event-Driven
Pipeline déclenché automatiquement lors de l'arrivée d'un fichier dans le lake Bronze. Parse le `folderPath` du blob trigger pour en extraire les métadonnées du dataset, puis délègue le traitement à `PL_Bronze_To_Standardized_Parquet`.

![Architecture Event-Driven](../screenshots/adf_pl_bronze_event_master.png)

### Paramètres

| Paramètre | Source | Description |
|---|---|---|
| `p_folderPath` | Trigger | Chemin complet du blob déclencheur |
| `p_fileName` | Trigger | Nom du fichier déposé |

### Logique de Parsing
Extraction des segments du `folderPath` pour déterminer :

-   `dataset` (canonique `p_dataset`, implémentation `p_table`) : le nom du dataset.
-   `period` (canonique `p_periodicity`, implémentation `p_period`), `year`, `month`, `day` : la date et la fréquence de l'extraction.
-   Génération du `ctrl_id` unique composite (`dataset_date_period`).

### Input / Output Contract (audit)

| Élément | Type | Contrat |
|---|---|---|
| `p_folderPath` | Input | Chemin blob déclencheur (source vérité de parsing) |
| `p_fileName` | Input | Nom du fichier trigger |
| `p_table` (`p_dataset`) | Derived | Extrait du `folderPath` |
| `p_period` (`p_periodicity`) | Derived | Extrait du `folderPath` |
| `p_year` / `p_month` / `p_day` | Derived | Extraits du `folderPath` |
| `p_ctrl_id` | Derived | Clé composite envoyée au pipeline enfant |
| `PL_Bronze_To_Standardized_Parquet` | Output | Exécution déléguée avec paramètres normalisés |

---

## 2. `PL_Bronze_To_Standardized_Parquet`

### Rôle : Transformation CSV → Parquet
Pipeline de transformation appelé par `PL_Bronze_Event_Master`. Convertit les CSV du lake Bronze en Parquet standardisé, puis écrit un fichier `.done` JSON contenant le `bronze_run_id` pour un pointage KQL robuste.

![Flux de transformation v2](../screenshots/adf_pl_bronze_to_standardized_parquet_v2_canvas.png)

### Flux

1.  **Build Done Payload** : `V_Payload_ID_Oeil` construit un JSON:
	 - `bronze_run_id = pipeline().RunId`
	 - `ctrl_id = pipeline().parameters.p_ctrl_id`
	 - `completed_ts = utcNow()`
2.  **Copy Data** : `Bronze To Standard` copie les CSV Bronze vers Parquet standardisé.
	 - `userProperties` transportés: `p_ctrl_id` et `p_pipeline_run_id`.
3.  **Create Done File** : `WEB_Create_DONE` crée `.../bronze/control/oeil_done/{ctrl_id}.done` (ADLS Gen2 REST, MSI).
4.  **Append Payload** : `WEB_Append_DONE` écrit le JSON dans le fichier `.done`.
5.  **Flush File** : `WEB_Flush_DONE` finalise le fichier avec la longueur exacte du payload.

Résultat clé: le `p_pipeline_run_id` déposé dans `.done` permet d'interroger Log Analytics sur le run exact (`ADFActivityRun`) même en cas de retry/fail intermédiaire.

### Activités Clés

-   `V_Payload_ID_Oeil` : Compose le payload JSON `.done`.
-   `Bronze To Standard` : Activité de copie principale CSV → Parquet (`CopyBehavior = MergeFiles`).
-   `WEB_Create_DONE` : Crée le fichier `.done` via API ADLS (`PUT`, MSI).
-   `WEB_Append_DONE` : Append le payload JSON (`PATCH action=append`).
-   `WEB_Flush_DONE` : Flush le payload (`PATCH action=flush`).

### Input / Output Contract (audit)

| Élément | Type | Contrat |
|---|---|---|
| `p_table` (`p_dataset`), `p_period` (`p_periodicity`), `p_year`, `p_month`, `p_day` | Input | Identité partition source Bronze |
| `p_ctrl_id` | Input | Identifiant run propagé |
| `enable_synapse_validation` | Input | Paramètre booléen présent (non utilisé dans ce pipeline) |
| `DS_Bronze_CSV` | Input | Source CSV Bronze partitionnée |
| `DS_Standardized_Parquet` | Output | Données standardisées en Parquet |
| `p_pipeline_run_id` (userProperty) | Derived | `pipeline().RunId` pour corrélation KQL |
| `v_done_payload` | Derived | JSON `.done` avec `bronze_run_id`, `ctrl_id`, `completed_ts` |
| `{ctrl_id}.done` | Output | Fichier JSON en `bronze/control/oeil_done/` |

### Screenshots recommandés (ce pipeline)

1. Canvas pipeline (ordre des activités)
	- `docs/screenshots/adf_pl_bronze_to_standardized_parquet_v2_canvas.png`
2. Activité `Bronze To Standard` (onglet `User properties` montrant `p_ctrl_id` + `p_pipeline_run_id`)
	- `docs/screenshots/adf_pl_bronze_to_standardized_parquet_v2_userprops.png`

![Bronze To Standard — User properties (p_ctrl_id, p_pipeline_run_id)](../screenshots/adf_pl_bronze_to_standardized_parquet_v2_userprops.png)
3. Activités `.done` (`WEB_Create_DONE` → `WEB_Append_DONE` → `WEB_Flush_DONE`) avec statuts `Succeeded`
	- `docs/screenshots/adf_pl_bronze_to_standardized_parquet_v2_done_web_chain.png`

![Chaîne .done — WEB_Create_DONE, WEB_Append_DONE, WEB_Flush_DONE](../screenshots/adf_pl_bronze_to_standardized_parquet_v2_done_web_chain.png)

### Exemple réel de payload `.done`

```json
{"bronze_run_id":"6048574b-da8f-4dff-a305-8ff6b4899659","ctrl_id":"transactions_2026-08-04_Q","completed_ts":"2026-02-18T19:13:02.6002697Z"}
```

Ce payload est la source de corrélation entre le run Bronze et la requête KQL (`p_pipeline_run_id`).

---

## 3. `PL_Oeil_Guardian`

### Rôle : Préparation run + garde d’intégrité CTRL

Pipeline d’entrée qui lit le CTRL JSON, alimente `dbo.vigie_ctrl` avec les métadonnées et métriques ADF, puis applique une garde hash canonique avant d’autoriser le cœur métier.

### Dépendances ADF / Log Analytics (polling) [Implemented]

Pour fiabiliser la récupération des métriques d'ingestion :

- Le flux actif fait un `Wait` (60s), récupère un token (`WEB_Get_LogAnalytics_Token`), puis lance la requête KQL (`WEB_ADF_RowCount_Copie_Parquet`).
- `If_Has_RowCount_copy1` échoue explicitement si la métrique n'est pas disponible (fail-fast).
- La boucle `Until_Get_ADF_Metrics` est toujours présente dans le JSON mais marquée `Inactive` (fallback non utilisé).
- Critère de métrique ADF valide : `row_count_adf_ingestion_copie_parquet` non nul (avec `adf_start_ts`, `adf_end_ts`, `adf_duration_sec` issus de la même requête KQL).
- La requête KQL cible désormais `UserProperties.p_pipeline_run_id` (run id déposé dans le `.done`) pour pointer le run exact et éviter les collisions en cas de retry.

### Activités clés (vue simplifiée)

- `SP_Try_Start_OEIL`
- `Set Control_Path` → `LK_Read_CtrlJson`
- `LK_Read_DONE`
- `SP_Set_Start_TS_OEIL`
- `v_bronze_path` + `v_parquet_path` + `Wait`
- `WEB_Get_LogAnalytics_Token` + `WEB_ADF_RowCount_Copie_Parquet` + `If_Has_RowCount_copy1`
- `SP_Upsert_VigieCtrl`
- `SP_Verify_Ctrl_Hash_V1`
- `LK_Check_Hash_Result`
- `If le HASH du CTRL est OK`
	- vrai → `Execute Pipeline OEIL CORE` (`PL_Oeil_Core`) avec `p_ctrl_id`, `p_dataset`, `p_periodicity`, `p_extraction_date`, `p_environment=DEV`
	- faux → `Fail CTRL_HASH_MISMATCH`

### Hash canonique CTRL [Implemented]

- Le pipeline appelle `SP_Verify_Ctrl_Hash_V1`.
- La décision d’orchestration est basée sur `payload_hash_match` dans `dbo.vigie_ctrl`.
- Si `payload_hash_match = false`, le pipeline échoue volontairement avec `CTRL_HASH_MISMATCH`.
- Le canonical V1 vérifié est `dataset|periodicity|YYYY-MM-DD|expected_rows`.
- Le hash recalculé utilise `SHA2_256` (hex lowercase, sans `0x`).
- Le contrôle alimente aussi `alert_flag` et `alert_reason` (`HASH_OK`, `MISSING_HASH`, `CTRL_HASH_MISMATCH`).

### Diagramme Mermaid (flow)

```mermaid
flowchart TD
	A[Inputs: p_control_path, p_ctrl_id, p_done_path] --> B[SP_Try_Start_OEIL]
	B --> C[Set Control_Path]
	C --> D[LK_Read_CtrlJson]
	D --> E[LK_Read_DONE]
	E --> F[SP_Set_Start_TS_OEIL]
	F --> G[Set v_bronze_path / v_parquet_path]
	G --> H[Wait + WEB_Get_LogAnalytics_Token]
	H --> I[WEB_ADF_RowCount_Copie_Parquet]
	I --> J{row_count non nul ?}
	J -->|non| K[Fail ADF LOG TROP LONG]
	J -->|oui| L[SP_Upsert_VigieCtrl]
	L --> M[SP_Verify_Ctrl_Hash_V1]
	M --> N[LK_Check_Hash_Result]
	N --> O{payload_hash_match ?}
	O -->|true| P[ExecutePipeline: PL_Oeil_Core]
	O -->|false| Q[Fail: CTRL_HASH_MISMATCH]
	H --> I[SP_Verify_Ctrl_Hash_V1]

	P --> R[(Output: dbo.vigie_ctrl)]
```

### Input / Output Contract (audit)

| Élément | Type | Contrat |
|---|---|---|
| `p_control_path` | Input | Paramètre déclaré (chemin effectif reconstruit depuis `p_ctrl_id`) |
| `p_ctrl_id` | Input | Clé de run à enrichir et valider |
| `p_done_path` | Input | Chemin du `.done` utilisé par `LK_Read_DONE` pour lire `bronze_run_id` |
| `p_bronze_run_id` | Input | Paramètre déclaré (non utilisé dans le flux implémenté) |
| `v_control_path`, `v_bronze_path`, `v_parquet_path` | Derived | Chemins techniques normalisés |
| `row_count_adf_ingestion_copie_parquet` | Derived | Métrique ingestion issue de KQL |
| `payload_canonical`, `payload_hash_sha256`, `payload_hash_version` | Input (CTRL) | Valeurs lues du CTRL JSON |
| `payload_hash_match` | Output | Résultat booléen de validation hash canonique |
| `PL_Oeil_Core` | Output | Exécution autorisée si hash valide, avec paramètres métier (`dataset`, `periodicity`, `extraction_date`, `environment`) |
| `dbo.vigie_ctrl` | Output | Run enrichi (ADF + hash + lifecycle) |

---

## 4. `PL_Oeil_Core`

### Rôle : Cœur qualité / SLA / alertes

Sous-pipeline appelé par `PL_Oeil_Guardian` après validation hash. Il enchaîne les calculs volumétriques, l’exécution qualité, les SLA et la consolidation des alertes.

Le pipeline reçoit désormais des paramètres enrichis (`p_dataset`, `p_periodicity`, `p_extraction_date`, `p_environment`) en plus de `p_ctrl_id`.

### Activités clés (vue simplifiée)

- `LK_Read_CtrlJson`
- `SC_Set_Volume_Check`
- `Pipeline Qualite` → `PL_Oeil_Quality_Engine`
- `SC_Update_In_Progress`
- `SP_SLA_Compute_ADF`
- `SP_Set_End_TS_OEIL`
- `SP_SLA_Compute_OEIL`
- `SC_Set_OEIL_Bucket`
- `SC_Set_Intelligent_Alert`
- `SC_Ajuste Alert FLAG`
- `SC_Mark_OEIL_Completed`
- `SC_Mark_Processed_Ctrl_Index`

### Diagramme Mermaid (flow)

```mermaid
flowchart TD
	A[Input: p_ctrl_id + contexte métier] --> B[Set Control_Path]
	B --> C[LK_Read_CtrlJson]
	C --> D[SC_Set_Volume_Check]
	D --> E[Pipeline Qualite: PL_Oeil_Quality_Engine]
	E --> F[SC_Update_In_Progress]
	E --> F[SP_SLA_Compute_ADF]
	F --> G[SP_Set_End_TS_OEIL]
	G --> H[SP_SLA_Compute_OEIL]
	H --> I[SC_Set_OEIL_Bucket]
	I --> J[SC_Set_Intelligent_Alert]
	J --> K[SC_Ajuste Alert FLAG]
	K --> L[SC_Mark_OEIL_Completed]
	L --> M[SC_Mark_Processed_Ctrl_Index]

	M --> N[(Output: dbo.vigie_ctrl)]
	M --> O[(Output: dbo.ctrl_file_index)]
```

### Input / Output Contract (audit)

| Élément | Type | Contrat |
|---|---|---|
| `p_ctrl_id` | Input | Clé de run à finaliser |
| `p_dataset`, `p_periodicity`, `p_extraction_date`, `p_environment` | Input | Paramètres déclarés et fournis par `PL_Oeil_Guardian` |
| `LK_Read_CtrlJson` | Derived | Dataset/periodicity/extraction_date utilisés pour exécuter la qualité |
| `PL_Oeil_Quality_Engine` | Output | Exécution qualité Synapse pilotée par policy |
| `dbo.vigie_ctrl` | Output | Run enrichi (volume status, SLA, bucket, alert, status_global, quality_status_global, quality_tests_*) |
| `dbo.ctrl_file_index` | Output | Flag `processed_flag=1`, `processed_ts` |

---

## 5. `PL_Oeil_Quality_Engine`

### Rôle : Exécuter les policies d'intégrité (Synapse + Azure SQL)

Pipeline de contrôle qualité piloté par policy SQL. Il lit les tests actifs pour un dataset/environnement, exécute les contrôles via Synapse, puis persiste les résultats dans `dbo.vigie_integrity_result`.

![Pipeline qualité OEIL](../screenshots/adf_pl_oeil_quality_engine.png)

### Paramètres

| Paramètre | Type | Description |
|---|---|---|
| `p_ctrl_id` | string | Identifiant run (ex: `clients_2026-05-01_Q`) |
| `p_dataset` | string | Dataset ciblé |
| `p_environment` | string | Environnement policy (`DEV`/`PROD`) |
| `p_periodicity` | string | Périodicité (`Q`, `H`, `M`, etc.) |
| `p_extraction_date` | string | Date d'extraction (`YYYY-MM-DD`) |

### Variables calculées

| Variable | Description |
|---|---|
| `v_bronze_path` | Pattern CSV Bronze (`bronze/<dataset>/period=<p>/year=.../data/*.csv`) |
| `v_parquet_path` | Pattern Parquet standardized (`standardized/<dataset>/year=.../*.parquet`) |
| `v_synapse_start_ts` | Horodatage de début de la phase Synapse (capturé avant `ForEach_Policy`) |

### Flux d'exécution

1. **Lookup Policy**
	 - Requête SQL sur `vigie_policy_dataset`, `vigie_policy_test`, `vigie_policy_test_type`
	 - Filtre: dataset + environment + tests actifs
2. **Set `v_bronze_path`**
3. **Set `v_parquet_path`**
4. **Set `v_synapse_start_ts`**
5. **LK_Get_Contract_Hash** (`ctrl.SP_GET_CONTRACT_STRUCTURE_HASH`)
6. **SC_Get_Detected_Hash** (`ctrl.SP_GET_DETECTED_STRUCTURE_HASH`)
7. **SP_Compare_Structure** (`ctrl.SP_CHECKSUM_STRUCTURE_COMPARE`)
	 - Bloque le pipeline immédiatement si `CHECKSUM_STRUCTURE` en `FAIL`
8. **ForEach_Policy** sur les tests actifs
9. **Switch_Policy** par `test_code`
	 - Cas `MIN_MAX`
		 - `SC_SYNAPSE_MIN_MAX` → `EXEC ctrl.SP_OEIL_MIN_MAX ...`
		 - `SP_Insert_Vigie` → `EXEC dbo.SP_Insert_VigieIntegrityResult ...`
	 - Cas `ROW_COUNT`
		 - `SC_SYNAPSE_ROWCOUNT` → `EXEC ctrl.SP_OEIL_ROWCOUNT ...`
		 - `SP_Insert_Vigie_ROWCOUNT` → `EXEC dbo.SP_Insert_VigieIntegrityResult ...`
		 - `synapse_start_ts` / `synapse_end_ts` sont persistés au moment de l'insert `ROW_COUNT`
	 - Cas `CHECKSUM`
		 - `SC_SYNAPSE_CHECKSUM` → `EXEC ctrl.SP_OEIL_CHECKSUM ...`
		 - `SP_Insert_Vigie_CHECKSUM` → persiste `observed_value_text` / `reference_value_text`
10. **`SP_Update_VigieCtrl_FromIntegrity`**
	 - Synchronise les résultats `ROW_COUNT` d'intégrité vers `dbo.vigie_ctrl`
	 - Alimente `synapse_start_ts`, `synapse_end_ts`, `synapse_duration_sec`, `row_count_adf_ingestion_copie_parquet`, `status`
11. **`SP_Compute_Quality_Summary`**
	 - Agrège les résultats qualité et met à jour `quality_status_global` + `quality_tests_*`
12. **`SP_Compute_SLA_SYNAPSE`**
	 - Calcule le SLA Synapse à partir de la durée consolidée
13. **`SC_Compute_Synapse_Cost_CAD_copy1`**
	 - Estime le coût Synapse et met à jour `synapse_cost_estimated_cad`

### Diagramme Mermaid (flow)

```mermaid
flowchart TD
		A[Inputs: p_ctrl_id, p_dataset, p_environment, p_periodicity, p_extraction_date] --> B[Lookup Policy Azure SQL]
		B --> C[Derived: v_bronze_path]
		C --> D[Derived: v_parquet_path]
		D --> E[Set v_synapse_start_ts]
		E --> F[LK_Get_Contract_Hash]
		F --> G[SC_Get_Detected_Hash]
		G --> H[SP_Compare_Structure]
		H --> I[ForEach_Policy]
		I --> J{Switch test_code}

		J -->|MIN_MAX| K[SC_SYNAPSE_MIN_MAX\nEXEC ctrl.SP_OEIL_MIN_MAX]
		K --> L[SP_Insert_Vigie\nEXEC dbo.SP_Insert_VigieIntegrityResult]

		J -->|ROW_COUNT| M[SC_SYNAPSE_ROWCOUNT\nEXEC ctrl.SP_OEIL_ROWCOUNT]
		M --> N[SP_Insert_Vigie_ROWCOUNT\nEXEC dbo.SP_Insert_VigieIntegrityResult]

		J -->|CHECKSUM| O[SC_SYNAPSE_CHECKSUM\nEXEC ctrl.SP_OEIL_CHECKSUM]
		O --> P[SP_Insert_Vigie_CHECKSUM\nEXEC dbo.SP_Insert_VigieIntegrityResult]

		L --> Q[SP_Update_VigieCtrl_FromIntegrity]
		N --> Q
		P --> Q
		Q --> R[SP_Compute_Quality_Summary]
		R --> S[SP_Compute_SLA_SYNAPSE]
		S --> T[SC_Compute_Synapse_Cost_CAD]

		T --> U[(Output: dbo.vigie_ctrl Synapse SLA/Cost)]
		L --> V[(Output: dbo.vigie_integrity_result)]
		N --> V
		P --> V
```

### Résultat attendu

- Une ligne par test exécuté dans `dbo.vigie_integrity_result`.
- Colonnes clés alimentées: `ctrl_id` (`p_ctrl_id`), `dataset_name` (`p_dataset`), `test_code`, `column_name`, `observed_value_num`, `observed_value_aux_num`, `reference_value_num`, `reference_value_aux_num`, `observed_value_text`, `reference_value_text`, `delta_value`, `status`, `execution_time_ms`, `created_at`.

### Input / Output Contract (audit)

| Élément | Type | Contrat |
|---|---|---|
| `p_ctrl_id` | Input | ID unique du run de contrôle |
| `p_dataset` | Input | Dataset cible des tests |
| `p_environment` | Input | Scope des policies actives |
| `p_periodicity` | Input | Fréquence logique du run |
| `p_extraction_date` | Input | Date de référence pour construire les paths Bronze/Parquet |
| `v_bronze_path` | Derived | Pattern source CSV Bronze |
| `v_parquet_path` | Derived | Pattern source Parquet Standardized |
| `v_synapse_start_ts` | Derived | Start timestamp de la phase Synapse |
| `Lookup Policy` | Derived | Liste des tests actifs (`ROW_COUNT`, `MIN_MAX`, `CHECKSUM`, etc.) |
| `LK_Get_Contract_Hash` | Derived | Hash structure contractuelle (Azure SQL) |
| `SC_Get_Detected_Hash` | Derived | Hash structure détectée (Synapse) |
| `SP_Compare_Structure` | Output | Gate structurel (`CHECKSUM_STRUCTURE`) avant exécution des tests |
| `dbo.vigie_integrity_result` | Output | Une ligne persistée par test exécuté |
| `SP_Update_VigieCtrl_FromIntegrity` | Output | Synchronisation des métriques d'intégrité vers `vigie_ctrl` |
| `SP_Compute_Quality_Summary` | Output | Agrégation des statuts de qualité (`quality_status_global`, `quality_tests_*`) |
| `dbo.vigie_ctrl` | Output | Colonnes Synapse enrichies (`synapse_*`, `status`, rowcount) + synthèse qualité |
| `synapse_cost_estimated_cad` | Output | Coût Synapse estimé sur le run |
| `status` | Output | `PASS` / `FAIL` (retour Synapse) |
| `delta_value` | Output | Écart calculé (0 attendu sur run nominal) |
| `execution_time_ms` | Output | Durée mesurée de l'exécution du test |
