# Synapse Integrity Queries

Ce dossier est réservé aux requêtes d'intégrité Synapse (ex: `MIN_MAX_PQ`, `ROW_COUNT`, `NULL_COUNT`, `DISTRIBUTED_SIGNATURE_PQ`).

Ajoutez ici les scripts au fur et à mesure (un fichier par test ou par use-case).

## Requêtes déjà extraites depuis les SP Synapse

- `rowcount_openrowset.sql` (source: `sql/synapse/procedures/SP_OEIL_ROWCOUNT.sql`)
- `min_max_openrowset.sql` (source: `sql/synapse/procedures/SP_OEIL_MIN_MAX.sql` / procédure `ctrl.SP_OEIL_MIN_MAX_PQ`)
- `distributed_signature_openrowset.sql` (source: `sql/synapse/procedures/SP_OEIL_DISTRIBUTED_SIGNATURE_PQ.sql`)
