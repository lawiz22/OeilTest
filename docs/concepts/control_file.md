# 📋 Control File (CTRL)

Chaque run d'extraction produit un fichier **JSON CTRL** stocké dans le lac à côté des données (ou dans un dossier dédié). Ce fichier sert de contrat d'exécution et d'audit trail immuable.

## Structure JSON (v2)

Exemple complet d'un fichier CTRL généré par le framework.

```json
{
  "ctrl_id": "clients_2026-05-08_Q",
  "dataset": "clients",
  "periodicity": "Q",
  "extraction_date": "2026-05-08",
  "expected_rows": 1479,
  "actual_rows": 1479,
  "variance_applied": false,
  "variance_delta": 0,
  "integrity": {
    "min_max": {
      "column": "client_id",
      "min": 100055,
      "max": 999689
    },
    "distributed_signature": {
      "column": "client_id",
      "algorithm": "SHA256",
      "components": "COUNT|MIN|MAX|SUM",
      "value": "c08ead66bab99fa4a07a995aa17b7a92ad689111d8017f39a2c47418911feb28"
    }
  },
  "payload_canonical": "clients|Q|2026-05-08|1479",
  "payload_hash_sha256": "ec753a461011a2760f4b514bc5e1ed1181d9fe93d2e7f97bed0c351eaf107c62",
  "payload_hash_version": 1,
  "source_system": "LEGACY_DS",
  "created_ts": "2026-02-23T03:32:07.306862",
  "pipeline_name": null,
  "trigger_name": null,
  "pipeline_run_id": null,
  "status": "CREATED",
  "start_ts": null,
  "end_ts": null
}
```

## Sections du fichier

### Méta-données Run
- `ctrl_id` : Clé unique composite (`dataset` + `date` + `periodicity`).
- `dataset` / `periodicity` / `extraction_date` : Identifiants métier du run.

### Volume
- `expected_rows` : Le nombre de lignes que le système source déclare avoir envoyées.
- `actual_rows` : Le nombre de lignes effectivement chargées par ADF (reçu par l'ingestion).
- `variance_applied` : Indique si une tolérance de variance a été appliquée.
- `variance_delta` : Écart de volume calculé (utilisé pour les alertes de volume).

### Integrity (v2)
Contient les métriques de validation fine calculées à la source ou par Synapse.
- `min_max` : Bornes observées sur la colonne clé.
- `distributed_signature` : Signature distribuée de la colonne clé (`COUNT|MIN|MAX|SUM`) avec hash SHA-256.

## 👁️ Concept “Œil gauche / Œil droit”

Ce framework confronte systématiquement ce qui est **déclaré** (intention) avec ce qui est **mesuré** (réalité).

| INTENTION (Ce qui est déclaré) | RÉALITÉ (Ce qui est observé) |
|---|---|
| 👁️ **Œil gauche** | 👁️ **Œil droit** |
| DataStage / Control-M | ADF + Synapse Serverless |
| Fichier CTRL préparé | Rowcount calculé |
| Volume attendu | Volume réel |
| Métadonnées run | MIN / MAX validés |
| Planification SLA | Durée mesurée |
| — | Écart % détecté |

Lecture opérationnelle :

- L’**œil gauche** fixe le contrat d’exécution attendu (CTRL).
- L’**œil droit** vérifie les faits observés en exécution (ADF, Synapse, SQL).
- La valeur de L’ŒIL est l’**écart** entre les deux, utilisé pour le statut, les SLA et les alertes.

## Source of Truth Hierarchy

1. `vigie_integrity_result` = atomic technical facts
2. `vigie_ctrl` = consolidated run state
3. `CTRL JSON` = immutable audit artifact

### Payload Hash
Sécurité et intégrité du fichier de contrôle lui-même.
- `payload_canonical` : Chaîne concaténée des champs critiques (`dataset|period|date|rows`).
- `payload_hash_sha256` : Hash de cette chaîne canonique. Permet de vérifier que le fichier CTRL n'a pas été altéré manuellement après génération.
