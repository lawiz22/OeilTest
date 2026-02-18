# Requête KQL – ADF Activity Run Metrics

Requête utilisée dans le pipeline `PL_Oeil_Guardian` (activité `WEB_ADF_RowCount_Copie_Parquet`)
pour récupérer les métriques d'ingestion ADF depuis **Log Analytics**.

Le filtrage principal se fait maintenant sur `UserProperties.p_pipeline_run_id` (run id ADF déposé dans le fichier `.done`) afin de cibler le run exact et d'éviter les ambiguïtés liées aux retries.

Source versionnée du script : [queries/kql/adf_activity_run_rowcount_main.kql](../queries/kql/adf_activity_run_rowcount_main.kql)

## Requête

```kql
ADFActivityRun
| where TimeGenerated > ago(6h)
| where PipelineName == "PL_Bronze_To_Standardized_Parquet"
| where ActivityType == "Copy"
| where Status == "Succeeded"
| extend up = parse_json(UserProperties)
| where tostring(up.p_pipeline_run_id) == "0c99edd1-772b-455e-a182-61f1f54af376"
| extend o = parse_json(Output)
| extend rc = tolong(o.rowsCopied)
| where isnotnull(rc)
| summarize
    row_count_adf_ingestion_copie_parquet = max(rc),
    adf_start_ts = min(Start),
    adf_end_ts   = max(End)
| extend adf_duration_sec = datetime_diff("second", adf_end_ts, adf_start_ts)
| project
    row_count_adf_ingestion_copie_parquet,
    adf_start_ts,
    adf_end_ts,
    adf_duration_sec
```

## Résultat exemple (14 février 2026)

| row_count_adf_ingestion_copie_parquet | adf_start_ts [UTC]       | adf_end_ts [UTC]         | adf_duration_sec |
|---------------------------------------|--------------------------|--------------------------|------------------|
| 1656                                  | 2026-02-14T16:23:52.000  | 2026-02-14T16:31:35.000  | 463              |

## Screenshot

![KQL Log Analytics – ADF RowCount](screenshots/kql_adf_rowcount.png)

## Notes

- La requête filtre sur `UserProperties.p_pipeline_run_id` pour cibler un run ADF unique.
- Le `p_pipeline_run_id` est déposé dans le `.done`, ce qui permet un pointage fiable même en cas de retries.
- Le scope est restreint au pipeline `PL_Bronze_To_Standardized_Parquet`, à `ActivityType == Copy`, et à une fenêtre récente (`ago(6h)`).
- Seuls les runs `Succeeded` avec `rowsCopied` non null sont retenus.
