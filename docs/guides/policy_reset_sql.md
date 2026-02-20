# 🔁 Policy Reset SQL (`Policy.sql`)

Guide d’utilisation du script [Policy.sql](../../Policy.sql) pour réinitialiser et reseeder les tables de policy.

## Objectif

Le script couvre 2 opérations distinctes :

1. **Reset + seed des policies dataset/test**
   - `dbo.vigie_policy_dataset`
   - `dbo.vigie_policy_test`
2. **Reset + seed du catalogue de types de test**
   - `dbo.vigie_policy_test_type`

## ⚠️ Point important (ordre d’exécution)

Le script contient **deux blocs de reset** dans le même fichier.

- Le premier bloc insère des lignes dans `vigie_policy_test` en joignant `vigie_policy_test_type`.
- Le second bloc supprime ensuite `vigie_policy_test` puis `vigie_policy_test_type`, puis réinsère seulement `vigie_policy_test_type`.

Donc, si tu exécutes le fichier complet d’un coup, tu termines avec :
- `vigie_policy_test_type` rempli,
- mais `vigie_policy_test` vide.

## Exécution recommandée

### Mode A — Reset policies dataset/test (sans toucher au catalogue test_type)

Exécuter jusqu’au `SELECT ... ORDER BY d.dataset_name;` inclus.

Effet:
- reset `vigie_policy_test` et `vigie_policy_dataset`,
- reseed IDs,
- seed datasets DEV/PROD,
- seed tests `ROW_COUNT` + `MIN_MAX` pour `DEV`.

### Mode B — Reset catalogue des types de test

Exécuter uniquement le bloc final :

- `DELETE/RESEED` sur `vigie_policy_test`
- `DELETE/RESEED` sur `vigie_policy_test_type`
- `INSERT` des types (`ROW_COUNT`, `MIN_MAX`, `CHECKSUM`, `NULL_COUNT`, `RUN_COMPARISON`)

Ensuite, **relancer Mode A** pour recréer `vigie_policy_test`.

## Ce que fait le seed principal

### 1) Datasets seedés

- `clients` (`DEV`, `PROD`)
- `accounts` (`DEV`, `PROD`)
- `transactions` (`DEV`, `PROD`)
- `contracts` (`DEV`, `PROD`)

avec :
- `is_active = 1`
- `synapse_allowed` selon dataset
- `max_synapse_cost_usd` selon environment

### 2) Tests seedés (DEV)

- `ROW_COUNT`
  - `frequency = 'DAILY'`
  - `column_name = NULL`
- `MIN_MAX`
  - `frequency = 'DAILY'`
  - `column_name` mappée par dataset:
    - clients -> `client_id`
    - accounts -> `account_id`
    - transactions -> `transaction_id`
    - contracts -> `contract_id`

## Requêtes de validation rapide

### A. Vérifier le catalogue test_type

```sql
SELECT test_type_id, test_code, description, requires_synapse
FROM dbo.vigie_policy_test_type
ORDER BY test_type_id;
```

### B. Vérifier les datasets policy

```sql
SELECT policy_dataset_id, dataset_name, environment, is_active, synapse_allowed, max_synapse_cost_usd
FROM dbo.vigie_policy_dataset
ORDER BY dataset_name, environment;
```

### C. Vérifier les tests rattachés

```sql
SELECT 
    d.dataset_name,
    d.environment,
    tt.test_code,
    t.column_name,
    t.is_enabled,
    t.frequency
FROM dbo.vigie_policy_test t
JOIN dbo.vigie_policy_dataset d 
    ON t.policy_dataset_id = d.policy_dataset_id
JOIN dbo.vigie_policy_test_type tt
    ON t.test_type_id = tt.test_type_id
ORDER BY d.dataset_name, d.environment, tt.test_code;
```
