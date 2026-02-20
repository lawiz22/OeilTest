# 📎 Annexe — Snapshot complet `vigie_ctrl` (tous les champs)

Cette annexe contient la vue exhaustive du snapshot `vigie_ctrl` pour le run de démo v2.

- Orientation: **verticale** (un champ par ligne)
- Colonnes: les 6 `ctrl_id` du run
- Objectif: audit complet sans alourdir la page principale

## Snapshot vertical complet

| Champ | clients_2026-03-01_Q | clients_2026-03-02_Q | clients_2026-03-03_Q | transactions_2026-03-01_Q | transactions_2026-03-02_Q | transactions_2026-03-03_Q |
|---|---|---|---|---|---|---|
| `ctrl_id` | `clients_2026-03-01_Q` | `clients_2026-03-02_Q` | `clients_2026-03-03_Q` | `transactions_2026-03-01_Q` | `transactions_2026-03-02_Q` | `transactions_2026-03-03_Q` |
| `dataset` | `clients` | `clients` | `clients` | `transactions` | `transactions` | `transactions` |
| `periodicity` | `Q` | `Q` | `Q` | `Q` | `Q` | `Q` |
| `extraction_date` | `2026-03-01` | `2026-03-02` | `2026-03-03` | `2026-03-01` | `2026-03-02` | `2026-03-03` |
| `expected_rows` | `1147` | `921` | `1178` | `1176` | `873` | `1567` |
| `source_system` | `LEGACY_DS` | `LEGACY_DS` | `LEGACY_DS` | `LEGACY_DS` | `LEGACY_DS` | `LEGACY_DS` |
| `created_ts` | `2026-02-19 13:24:21.0800000` | `2026-02-19 13:24:22.1566667` | `2026-02-19 15:27:37.6633333` | `2026-02-19 13:24:19.7800000` | `2026-02-19 13:24:21.7500000` | `2026-02-19 15:27:36.3633333` |
| `pipeline_run_id` | `af8cf1a1-669d-4898-8326-f54eab96a5c3` | `49d3fcb2-3eb1-49d0-8bed-14b7a7b4a26c` | `25bfc2ea-afd1-4e57-bde5-41e64abed7fc` | `6f33f2ce-a5d2-4f37-b392-aaafc4e9331f` | `bf27812b-3622-449b-af6c-6933b4606e02` | `5aac118a-aaad-46cb-8ecc-fff8e30e58ab` |
| `adf_pipeline_name` | `PL_Oeil_Guardian` | `PL_Oeil_Guardian` | `PL_Oeil_Guardian` | `PL_Oeil_Guardian` | `PL_Oeil_Guardian` | `PL_Oeil_Guardian` |
| `adf_trigger_name` | `TR_Oeil_Done` | `TR_Oeil_Done` | `TR_Oeil_Done` | `TR_Oeil_Done` | `TR_Oeil_Done` | `Manual` |
| `start_ts` | `2026-02-19 13:26:45.8999251` | `2026-02-19 13:26:56.1051413` | `2026-02-19 15:30:35.6868503` | `2026-02-19 13:26:37.9299689` | `2026-02-19 13:26:46.9003044` | `2026-02-19 15:29:51.2861508` |
| `status` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` | `PASS` |
| `inserted_ts` | `2026-02-19 13:26:45.8999251` | `2026-02-19 13:26:56.1051413` | `2026-02-19 15:30:35.6868503` | `2026-02-19 13:26:37.9299689` | `2026-02-19 13:26:46.9003044` | `2026-02-19 15:29:51.2861508` |
| `bronze_rows` | `1147` | `921` | `1178` | `1176` | `873` | `1515` |
| `bronze_delta` | `0` | `0` | `0` | `0` | `0` | `-52` |
| `bronze_status` | `OK` | `OK` | `OK` | `OK` | `OK` | `MISMATCH` |
| `parquet_rows` | `1147` | `921` | `1178` | `1176` | `873` | `1515` |
| `parquet_delta` | `0` | `0` | `0` | `0` | `0` | `-52` |
| `parquet_status` | `OK` | `OK` | `OK` | `OK` | `OK` | `MISMATCH` |
| `status_global` | `COMPLETED` | `COMPLETED` | `COMPLETED` | `COMPLETED` | `COMPLETED` | `COMPLETED` |
| `quality_status_global` | `NULL` | `NULL` | `NULL` | `NULL` | `NULL` | `NULL` |
| `quality_tests_total` | `NULL` | `NULL` | `NULL` | `NULL` | `NULL` | `NULL` |
| `quality_tests_pass` | `NULL` | `NULL` | `NULL` | `NULL` | `NULL` | `NULL` |
| `quality_tests_fail` | `NULL` | `NULL` | `NULL` | `NULL` | `NULL` | `NULL` |
| `quality_tests_warning` | `NULL` | `NULL` | `NULL` | `NULL` | `NULL` | `NULL` |
| `sla_expected_sec` | `360` | `360` | `360` | `360` | `360` | `360` |
| `sla_threshold_sec` | `439` | `439` | `439` | `439` | `439` | `439` |
| `end_ts` | `2026-02-19 13:31:15.1774683` | `2026-02-19 13:31:21.8352372` | `2026-02-19 15:34:41.8066756` | `2026-02-19 13:41:01.1972102` | `2026-02-19 13:31:21.9446142` | `2026-02-19 16:40:34.8080811` |
| `duration_sec` | `270` | `265` | `246` | `864` | `275` | `4243` |
| `sla_sec` | `270` | `265` | `246` | `864` | `275` | `4243` |
| `sla_status` | `OK` | `OK` | `OK` | `FAIL` | `OK` | `FAIL` |
| `sla_reason` | `OEIL` | `OEIL` | `OEIL` | `OEIL` | `OEIL` | `OEIL` |
| `volume_status` | `OK` | `OK` | `OK` | `OK` | `OK` | `ANOMALY` |
| `sla_bucket` | `FAST` | `FAST` | `FAST` | `VERY_SLOW` | `FAST` | `VERY_SLOW` |
| `row_count_adf_ingestion_copie_parquet` | `1147` | `921` | `1178` | `1176` | `873` | `1515` |
| `adf_start_ts` | `2026-02-19 13:25:39.0000000` | `2026-02-19 13:25:34.0000000` | `2026-02-19 15:27:58.0000000` | `2026-02-19 13:25:25.0000000` | `2026-02-19 13:25:29.0000000` | `2026-02-19 15:27:57.0000000` |
| `adf_end_ts` | `2026-02-19 13:25:56.0000000` | `2026-02-19 13:25:50.0000000` | `2026-02-19 15:28:13.0000000` | `2026-02-19 13:25:43.0000000` | `2026-02-19 13:25:46.0000000` | `2026-02-19 15:28:14.0000000` |
| `adf_duration_sec` | `17` | `16` | `15` | `18` | `17` | `17` |
| `adf_sla_status` | `OK` | `OK` | `OK` | `OK` | `OK` | `OK` |
| `adf_sla_reason` | `ADF_INGESTION` | `ADF_INGESTION` | `ADF_INGESTION` | `ADF_INGESTION` | `ADF_INGESTION` | `ADF_INGESTION` |
| `synapse_start_ts` | `2026-02-19 13:29:21.7733333` | `2026-02-19 13:29:40.6866667` | `2026-02-19 15:33:08.3066667` | `2026-02-19 13:39:44.8766667` | `2026-02-19 13:29:39.3133333` | `2026-02-19 16:39:05.9800000` |
| `synapse_end_ts` | `2026-02-19 13:29:50.8500000` | `2026-02-19 13:29:56.8400000` | `2026-02-19 15:33:31.1266667` | `2026-02-19 13:39:58.1566667` | `2026-02-19 13:29:53.3400000` | `2026-02-19 16:39:24.7133333` |
| `synapse_duration_sec` | `29` | `16` | `23` | `14` | `14` | `19` |
| `oeil_sla_sec` | `270` | `265` | `246` | `864` | `275` | `4243` |
| `oeil_sla_expected_sec` | `360` | `360` | `360` | `360` | `360` | `360` |
| `oeil_sla_threshold_sec` | `439` | `439` | `439` | `439` | `439` | `439` |
| `oeil_sla_status` | `OK` | `OK` | `OK` | `FAIL` | `OK` | `FAIL` |
| `oeil_sla_reason` | `OEIL_EXECUTION` | `OEIL_EXECUTION` | `OEIL_EXECUTION` | `OEIL_EXECUTION` | `OEIL_EXECUTION` | `OEIL_EXECUTION` |
| `adf_sla_sec` | `17` | `16` | `15` | `18` | `17` | `17` |
| `adf_sla_expected_sec` | `35` | `34` | `35` | `35` | `34` | `37` |
| `adf_sla_threshold_sec` | `43` | `42` | `43` | `43` | `42` | `46` |
| `synapse_sla_sec` | `29` | `16` | `23` | `14` | `14` | `19` |
| `synapse_sla_expected_sec` | `120` | `120` | `120` | `120` | `120` | `120` |
| `synapse_sla_threshold_sec` | `156` | `156` | `156` | `156` | `156` | `156` |
| `synapse_sla_status` | `OK` | `OK` | `OK` | `OK` | `OK` | `OK` |
| `synapse_sla_reason` | `SYNAPSE_COMPUTE` | `SYNAPSE_COMPUTE` | `SYNAPSE_COMPUTE` | `SYNAPSE_COMPUTE` | `SYNAPSE_COMPUTE` | `SYNAPSE_COMPUTE` |
| `alert_flag` | `0` | `0` | `0` | `1` | `0` | `1` |
| `alert_reason` | `NO_ALERT` | `NO_ALERT` | `NO_ALERT` | `OEIL=FAIL \| BUCKET=VERY_SLOW \| VOLUME=OK \| ADF=OK \| SYNAPSE=OK` | `NO_ALERT` | `OEIL=FAIL \| BUCKET=VERY_SLOW \| VOLUME=ANOMALY \| ADF=OK \| SYNAPSE=OK` |
| `alert_ts` | `NULL` | `NULL` | `NULL` | `2026-02-19 13:41:28.3271235` | `NULL` | `2026-02-19 16:41:15.3150989` |
| `synapse_cost_estimated_cad` | `0.000967` | `0.000533` | `0.000767` | `0.000467` | `0.000467` | `0.000633` |
| `synapse_cost_rate_cad_per_min` | `0.002000` | `0.002000` | `0.002000` | `0.002000` | `0.002000` | `0.002000` |
| `alert_level` | `NO_ALERT` | `NO_ALERT` | `NO_ALERT` | `CRITICAL` | `NO_ALERT` | `CRITICAL` |
| `payload_canonical` | `clients\|Q\|2026-03-01\|1147` | `clients\|Q\|2026-03-02\|921` | `clients\|Q\|2026-03-03\|1178` | `transactions\|Q\|2026-03-01\|1176` | `transactions\|Q\|2026-03-02\|873` | `transactions\|Q\|2026-03-03\|1567` |
| `payload_hash_sha256` | `ea2aee4415bcc27134d0faba08dee83537362e2f35d5154b2e566a1971d20609` | `8883fe9c9a570e16c0ab9edd43eeab4eacc08a4cad5c61c4849f4ba40a60ecc3` | `66f58142c062a7a0953b01065266df95b6ebf2cac9a76df6dcb97d82c9be36c6` | `6ce360c40d99ca516b25b833bc0a7015ef0bf5329f1d2ce2fdb405e9d19173a3` | `3f0a30c8cc898fcd16cc0cf63baed8f479bf94d12dc25420c59e5ea5f9e1091b` | `bc7baa3e5b8d682a407fcb8dbf338a65c2dfd5800416e9e7ff586a4d22448637` |
| `payload_hash_version` | `1` | `1` | `1` | `1` | `1` | `1` |
| `payload_hash_match` | `1` | `1` | `1` | `1` | `1` | `1` |
| `policy_dataset_id` | `NULL` | `NULL` | `NULL` | `NULL` | `NULL` | `NULL` |
| `policy_snapshot_json` | `NULL` | `NULL` | `NULL` | `NULL` | `NULL` | `NULL` |

## Note d’utilisation

- Cette annexe reprend les valeurs brutes du snapshot final, prêtes pour audit.
- Les définitions métier des champs restent dans le guide principal: `demo_run_end_to_end.md`.
