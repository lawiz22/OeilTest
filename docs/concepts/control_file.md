# 📋 Control File (CTRL)

Chaque run d'extraction produit un fichier **JSON CTRL** stocké dans le lac à côté des données (ou dans un dossier dédié). Ce fichier sert de contrat d'exécution et d'audit trail immuable.

## Structure JSON (v2)

Exemple complet d'un fichier CTRL généré par le framework.

```json
{
  "ctrl_id": "accounts_2026-10-08_Q",
  "dataset": "accounts",
  "periodicity": "Q",
  "extraction_date": "2026-10-08",
  "volume": {
    "expected_rows": 1261,
    "actual_rows": 1261,
    "delta": 0,
    "variance_applied": false
  },
  "integrity": {
    "min_max": {
      "column": "account_id",
      "min": 100001,
      "max": 198772
    },
    "checksum": {
      "column": "account_id",
      "algorithm": "SHA256",
      "value": "ab3290c9..."
    }
  },
  "payload_canonical": "accounts|Q|2026-10-08|1261",
  "payload_hash_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "payload_hash_version": 1,
  "source_system": "CRM_PROD",
  "created_ts": "2026-10-08T14:30:00.123456"
}
```

## Sections du fichier

### Méta-données Run
- `ctrl_id` : Clé unique composite (`dataset` + `date` + `periodicity`).
- `dataset` / `periodicity` / `extraction_date` : Identifiants métier du run.

### Volume
- `expected_rows` : Le nombre de lignes que le système source déclare avoir envoyées.
- `actual_rows` : Le nombre de lignes effectivement chargées par ADF (reçu par l'ingestion).
- `delta` : Différence calculée (utilisé pour les alertes de volume).

### Integrity (v2)
Contient les métriques de validation fine calculées à la source ou par Synapse.
- `min_max` : Bornes observées sur la colonne clé.
- `checksum` : Empreinte cryptographique de la colonne clé (pour détecter des modifications silencieuses).

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
