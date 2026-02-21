# 🔐 Validation Structurelle - Résumé Technique

## Vue d'ensemble

Le pipeline qualité `PL_Oeil_Quality_Engine` intègre désormais une **validation structurelle préalable** qui compare le contrat de données (configuration) avec la structure réelle détectée dans les fichiers Parquet.

## Architecture

### 📍 Localisation des SP

**Azure SQL Database** (`sql/procedures/`):
- `SP_REFRESH_STRUCTURAL_HASH.sql` - Recalcul batch des hash
- `SP_GET_CONTRACT_STRUCTURE_HASH.sql` - Récupération hash contractuel
- `SP_CHECKSUM_STRUCTURE_COMPARE.sql` - Comparaison et validation

**Synapse Serverless** (`sql/synapse/procedures/`):
- `SP_GET_DETECTED_STRUCTURE_HASH.sql` - Détection runtime de structure

## Flux d'exécution (PL_Oeil_Quality_Engine)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1️⃣ SP_GET_CONTRACT_STRUCTURE_HASH (Azure SQL)                  │
│    ├─ Lit ctrl.dataset_column                                   │
│    ├─ Génère JSON: [{ordinal, name, type_normalized}]           │
│    └─ Retourne contract_structural_hash (SHA-256)               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2️⃣ SC_GET_DETECTED_STRUCTURE_HASH (Synapse)                    │
│    ├─ Appelle ctrl.SP_GET_DETECTED_STRUCTURE_HASH               │
│    ├─ Lit INFORMATION_SCHEMA.COLUMNS sur ext.{dataset}_std      │
│    ├─ Génère JSON: [{ordinal, name, type_detected}]             │
│    └─ Retourne detected_structural_hash (SHA-256)               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3️⃣ SP_COMPARE_STRUCTURE (Azure SQL)                            │
│    ├─ Compare contract_hash vs detected_hash                    │
│    ├─ INSERT vigie_integrity_result (CHECKSUM_STRUCTURE)        │
│    │                                                             │
│    ├─ SI PASS ✅                                                │
│    │  └─ Continue → ForEach_Policy (ROW_COUNT, MIN_MAX, etc.)  │
│    │                                                             │
│    └─ SI FAIL ❌                                                │
│       └─ THROW 50001 → Pipeline arrêté immédiatement            │
└─────────────────────────────────────────────────────────────────┘
```

## Normalisation des types

### `SP_GET_CONTRACT_STRUCTURE_HASH`

Normalise les types `ctrl.dataset_column.type_sink`:

| Type source          | Type normalisé |
|---------------------|----------------|
| `VARCHAR(n)`        | `varchar`      |
| `CHAR(n)`           | `char`         |
| `DECIMAL(p,s)`      | `decimal`      |
| `DATETIME2`/`DATETIME` | `datetime2`  |
| `INT`               | `int`          |
| `BIGINT`            | `bigint`       |
| `DATE`              | `date`         |

### `SP_GET_DETECTED_STRUCTURE_HASH`

Utilise directement `INFORMATION_SCHEMA.COLUMNS.DATA_TYPE` (types SQL Synapse natifs).

## Cas d'usage de validation

### ✅ PASS - Structure conforme
```json
Contract: [{"ordinal":1,"name":"client_id","type_detected":"int"},
           {"ordinal":2,"name":"nom","type_detected":"varchar"}]

Detected: [{"ordinal":1,"name":"client_id","type_detected":"int"},
           {"ordinal":2,"name":"nom","type_detected":"varchar"}]

→ Hash match → PASS → Continue
```

### ❌ FAIL - Ordre colonnes différent
```json
Contract: [{"ordinal":1,"name":"client_id","type_detected":"int"},
           {"ordinal":2,"name":"nom","type_detected":"varchar"}]

Detected: [{"ordinal":1,"name":"nom","type_detected":"varchar"},
           {"ordinal":2,"name":"client_id","type_detected":"int"}]

→ Hash mismatch → FAIL → THROW 50001
```

### ❌ FAIL - Type incompatible
```json
Contract: [{"ordinal":1,"name":"client_id","type_detected":"int"}]
Detected: [{"ordinal":1,"name":"client_id","type_detected":"varchar"}]

→ Hash mismatch → FAIL → THROW 50001
```

### ❌ FAIL - Colonne manquante
```json
Contract: [{"ordinal":1,"name":"client_id","type_detected":"int"},
           {"ordinal":2,"name":"nom","type_detected":"varchar"}]

Detected: [{"ordinal":1,"name":"client_id","type_detected":"int"}]

→ Hash mismatch → FAIL → THROW 50001
```

## Traçabilité

Tous les résultats sont persistés dans `dbo.vigie_integrity_result`:

| Colonne | Valeur |
|---------|--------|
| `test_code` | `CHECKSUM_STRUCTURE` |
| `observed_value_text` | Hash détecté (hex) |
| `reference_value_text` | Hash contractuel (hex) |
| `status` | `PASS` ou `FAIL` |

## Impact sur le pipeline

**Avant cette validation**:
- Tests qualité (ROW_COUNT, MIN_MAX) s'exécutaient même si structure incorrecte
- Erreurs downstream cryptiques
- Coûts Synapse gaspillés

**Après cette validation**:
- **Stop immédiat** si structure non-conforme
- Message d'erreur explicite avec hash comparison
- Économie de temps et ressources
- Meilleure gouvernance des contrats de données

## Maintenance

Pour recalculer tous les hash contractuels:
```sql
EXEC ctrl.SP_REFRESH_STRUCTURAL_HASH @dataset_name = NULL;  -- tous
EXEC ctrl.SP_REFRESH_STRUCTURAL_HASH @dataset_name = 'clients';  -- un seul
```

## Références

- Documentation: `docs/technical_reference/stored_procedures.md`
- Pipeline: `PL_Oeil_Quality_Engine`
- Code SQL: `sql/procedures/SP_*STRUCTURE*.sql`
- Code Synapse: `sql/synapse/procedures/SP_GET_DETECTED_STRUCTURE_HASH.sql`
