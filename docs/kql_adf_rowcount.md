# Requête KQL – ADF Activity Run Metrics

Requête utilisée dans le pipeline `PL_Ctrl_To_Vigie` (activité `WEB_ADF_RowCount_Copie_Parquet`)
pour récupérer les métriques d'ingestion ADF depuis **Log Analytics**.

## Requête

```kql
ADFActivityRun
| extend up = parse_json(UserProperties)
| where tostring(up.p_ctrl_id) == "clients_2025-12-07_H"
| where Status == "Succeeded"
| extend o = parse_json(Output)
| extend rc = tolong(o.rowsCopied)
| where isnotnull(rc)
| summarize
    row_count_adf_ingestion_copie_parquet = max(rc),
    adf_start_ts = min(Start),
    adf_end_ts   = max(End)
| extend adf_duration_sec = datetime_diff("second", adf_end_ts, adf_start_ts)
| project row_count_adf_ingestion_copie_parquet, adf_start_ts, adf_end_ts, adf_duration_sec
```

## Résultat exemple (14 février 2026)

| row_count_adf_ingestion_copie_parquet | adf_start_ts [UTC]       | adf_end_ts [UTC]         | adf_duration_sec |
|---------------------------------------|--------------------------|--------------------------|------------------|
| 1656                                  | 2026-02-14T16:23:52.000  | 2026-02-14T16:31:35.000  | 463              |

## Screenshot

![KQL Log Analytics – ADF RowCount](screenshots/kql_adf_rowcount.png)

## Notes

- La requête filtre sur `UserProperties.p_ctrl_id` pour cibler un ctrl_id spécifique.
- Seuls les runs `Succeeded` avec un `rowsCopied` non-null sont retenus.
- Le pipeline ADF injecte dynamiquement le `p_ctrl_id` via `@replace(...)`.
