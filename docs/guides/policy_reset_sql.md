# 🔁 Policy Reset SQL (`Policy.sql`)

Guide d’utilisation du script [Policy.sql](../../Policy.sql) pour réinitialiser et reseeder les tables de policy.

> [!WARNING]
> **Déprécié (usage recommandé limité).**
> Pour la gestion courante des policies (création, édition, export), utiliser en priorité le **[Oeil Control Center](control_center.md)**.
> Ce document et `Policy.sql` restent conservés pour les besoins de requêtes SQL directes, maintenance avancée et dépannage.

## Objectif

Le script couvre 2 opérations distinctes :

1. **Reset + seed des policies dataset/test**
   - `dbo.vigie_policy_dataset`
   - `dbo.vigie_policy_test`
2. **Reset + seed du catalogue de types de test**
   - `dbo.vigie_policy_test_type`
3. **Migration schéma policy pour DDS / hash**
  - ajout colonnes dans `dbo.vigie_policy_test` :
    - `checksum_level`
    - `hash_algorithm`
    - `column_list`
    - `order_by_column`

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
- seed tests `ROW_COUNT` + `MIN_MAX` + `DISTRIBUTED_SIGNATURE` pour `DEV`.

### Mode B — Reset catalogue des types de test

Exécuter uniquement le bloc final :

- `DELETE/RESEED` sur `vigie_policy_test`
- `DELETE/RESEED` sur `vigie_policy_test_type`
- `INSERT` des types (`ROW_COUNT`, `MIN_MAX`, `DISTRIBUTED_SIGNATURE`, `NULL_COUNT`, `RUN_COMPARISON`)

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
- `DISTRIBUTED_SIGNATURE`
  - `frequency = 'DAILY'`
  - `column_name` mappée par dataset (même mapping que `MIN_MAX`)
  - `checksum_level = 1` (compatibilité legacy)
  - `hash_algorithm = 'SHA256'`
  - `column_list = NULL`, `order_by_column = NULL` (mode DDS simple)

  ## Support DDS / hash (migration)

  Le bloc `ALTER TABLE` en fin de `Policy.sql` ajoute les colonnes nécessaires au pilotage des stratégies hash/DDS avancées.

  - `checksum_level` : niveau de stratégie hash (legacy, conservé pour compatibilité)
  - `hash_algorithm` : algorithme utilisé (`SHA256`, etc.)
  - `column_list` : colonnes utilisées pour un hash déterministe
  - `order_by_column` : colonne d’ordre stable pour exécution déterministe

  Recommandation : garder un script **idempotent** (test `COL_LENGTH`) pour pouvoir rejouer la migration sans erreur.

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

### D. Vérifier les colonnes hash/DDS (schema)

```sql
SELECT 
    c.name AS column_name,
    t.name AS data_type,
    c.max_length,
    c.is_nullable
FROM sys.columns c
JOIN sys.types t
    ON c.user_type_id = t.user_type_id
WHERE c.object_id = OBJECT_ID('dbo.vigie_policy_test')
  AND c.name IN ('checksum_level', 'hash_algorithm', 'column_list', 'order_by_column')
ORDER BY c.name;
```
