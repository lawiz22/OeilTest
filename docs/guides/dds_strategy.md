# 🧩 DDS Strategy — Distributed Dataset Signature

## Décision retenue

La stratégie **hash classique** n’est pas retenue comme mécanisme principal en PROD.

La stratégie retenue est la **DDS (Distributed Dataset Signature)**, en priorité pour les environnements DEV et pour les cas où un contrôle distribué est pertinent sous Synapse Serverless.

## Pourquoi ce choix

Contexte Synapse Serverless:

- Le compute est éphémère et sensible au coût de scan.
- Les contrôles hash complets ligne-à-ligne sont coûteux et difficiles à stabiliser à grande échelle.
- Les comparaisons doivent rester robustes, rapides et exploitables dans ADF.

DDS répond à ces contraintes en calculant une signature compacte à partir d’agrégats distribuables.

## Agrégats DDS utilisés

Pour une colonne clé (ex: `client_id`), DDS calcule:

- `COUNT(*)`
- `MIN(id)`
- `MAX(id)`
- `SUM(id)`
- `SUM(CHECKSUM(id))`
- `SUM(BINARY_CHECKSUM(id))`

Ces composantes sont concaténées puis hashées en SHA-256 pour produire la signature finale comparée au contrat.

## Procédure Synapse associée

- Procédure: `ctrl.SP_OEIL_DISTRIBUTED_SIGNATURE_PQ`
- Localisation: `sql/synapse/procedures/SP_OEIL_DISTRIBUTED_SIGNATURE_PQ.sql`
- Sorties principales:
  - `signature_input_string`
  - `parquet_signature`
  - `contract_signature`
  - `integrity_status` (`PASS` / `FAIL`)

## Positionnement DEV vs PROD

### DEV

- DDS activée fréquemment pour détecter rapidement les régressions.
- Utilisée avec `ROW_COUNT` et `MIN_MAX` pour renforcer la couverture qualité.

### PROD

- Hash historique retiré de la stratégie principale.
- `ROW_COUNT` + `MIN_MAX` + validation structurelle restent la base.
- DDS activée de façon ciblée selon criticité dataset, coût et policy.

## Limites connues DDS

- DDS ne remplace pas un hash ligne-complet déterministe pour tous les scénarios.
- Deux jeux de données différents peuvent théoriquement partager certains agrégats (risque faible mais non nul).
- Les colonnes non numériques exigent une stratégie dédiée (normalisation/casting explicite).

## Recommandation opérationnelle

Utiliser DDS comme compromis coût/robustesse dans Synapse Serverless:

1. Gate structurel (`SP_GET_CONTRACT_STRUCTURE_HASH` vs `SP_GET_DETECTED_STRUCTURE_HASH`)
2. Contrôles volumétriques (`ROW_COUNT`, `MIN_MAX`)
3. DDS sur colonnes critiques
4. Agrégation finale dans `vigie_integrity_result` et synthèse dans `vigie_ctrl`
