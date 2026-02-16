# ⚡ Design Decisions

L'ŒIL a été conçu avec des contraintes spécifiques de coût, traçabilité et simplicité opérationnelle.

## 1. Pourquoi SQL comme source de vérité ?

**Décision** : Utiliser Azure SQL (table `vigie_ctrl`) plutôt qu'un Data Lake ou Cosmos DB.

**Rationale** :
1.  **Relationnel** : Les métadonnées sont fortement structurées (run -> dataset -> metrics).
2.  **T-SQL** : Langage universel pour les Data Engineers.
3.  **Intégration Power BI** : Direct Query natif et performant.
4.  **Transactionnel** : `SP_Set_Start` et `SP_Set_End` garantissent l'atomicité des mises à jour d'état.

## 2. Gestion des Coûts Synapse

**Décision** : Synapse Serverless est utilisé **uniquement** si la policy du dataset l'autorise (`synapse_allowed = 1`).

**Rationale** :
*   Synapse facture au volume scanné (TB).
*   ADF peut faire des validations simples (row count, file size) gratuitement.
*   On réserve Synapse pour les validations complexes (checksum contenu, distribution statistique) qui nécessitent de lire tout le fichier.

### Comparatif des approches de validation (coût / complexité / latence)

Ce comparatif sert de référence stratégique pour choisir la bonne méthode de validation selon le contexte dataset/environnement.

| Méthode | Coût | Complexité | Latence | Usage recommandé |
|---|---|---|---|---|
| SQL External Table | 💲 faible | simple | rapide | Tests simples |
| Synapse Serverless | 💲 variable | moyen | moyen | Validations ciblées |
| Synapse Dedicated | 💲💲💲 | élevé | rapide | Workloads critiques |
| Spark Notebook | 💲💲 | plus lourd | plus lent | Analytics avancé |

### Architecture mature (pattern cible)

Dans une grande organisation, le pattern cible recommandé est le suivant :

| Type d’opération | Moteur |
|---|---|
| Row count | SQL |
| Min / Max | SQL |
| Null count | SQL |
| Simple delta | SQL |
| Checksum massif | Synapse |
| Agrégation lourde multi-partition | Synapse |
| Traitement distribué complexe | Spark |

## 3. Double SLA (Volume-Based vs Fixed)

**Décision** : Distinguer le calcul de SLA selon le moteur.

**Rationale** :
*   **ADF** : Le temps de copie est linéaire par rapport au volume. Un fichier de 10GB prendra 10x plus de temps qu'1GB.
    *   *Formule* : `Overhead + (Volume * CostFactor)`
*   **Synapse/OEIL** : Le temps est dominé par le "cold start" et l'overhead réseau.
    *   *Formule* : `Fixed Overhead`

## 4. Fichiers CTRL Immuables

**Décision** : Chaque run génère un JSON `CTRL` dans le lac.

**Rationale** :
*   **Audit Trail** : Même si la DB SQL est purgée ou corrompue, l'historique des runs est préservé dans le lac.
*   **Non-Répudiation** : Le hash SHA-256 du payload garantit que le résultat du contrôle n'a pas été modifié.
*   **Découplage** : Les consommateurs en aval peuvent lire le fichier `.done` et le `CTRL` associé sans toucher à la DB SQL.

## 5. Philosophie : Observabilité vs Blocage

> **"L'ŒIL ne doit pas être un moteur qui bloque, mais un moteur qui révèle."**

Le but fondamental du framework n'est pas d'arrêter les pipelines au moindre écart (ce qui paralyse le business), mais de fournir une visibilité totale sur la qualité.

Il doit :
1.  **Détecter** l'anomalie.
2.  **Classifier** sa sévérité.
3.  **Alerter** les bonnes personnes.
4.  **Mesurer** l'impact et la tendance.
5.  **Ne pas interférer** avec le flux de données critique, sauf en cas de corruption avérée.

## 6. Stratégie Environnementale (DEV vs PROD)

Le comportement du framework doit s'adapter au cycle de vie du développement.

### En DEV : "Fail Fast, Watch Closely"
*   **Validation stricte** : On veut casser le pipeline si la donnée n'est pas parfaite.
*   **Fréquence élevée** : Tests systématiques à chaque run.
*   **Checksum fréquent** : Validation de contenu agressive pour détecter les régressions de code.
*   **Monitoring agressif** : Le développeur doit voir immédiatement l'impact de ses changements.
*   **Observation des coûts** : Mesure précise de l'impact financier des nouvelles transformations.

### En PROD : "Business Continuity & Efficiency"
*   **Tests essentiels seulement** : On ne valide que ce qui protège le business.
*   **Fréquence optimisée** : Checksums lourds uniquement hebdomadaires ou mensuels.
*   **Compute contrôlé** : Usage de Synapse restreint pour maîtriser la facture cloud.
*   **Pas d’effet sur la performance métier** : Les contrôles ne doivent pas retarder la mise à disposition des données.
*   **Policy adaptée** : Les seuils sont ajustés selon le comportement réel observé ("drift" naturel accepté si non critique).

## 7. Chaîne décisionnelle & sémantique des statuts

Chaîne de traitement cible :

`Dataset → Policy → Tests autorisés → Moteur choisi → Résultat → SLA → Alert`

Clarification des statuts :

- `status` = statut opérationnel du run
- `status_global` = statut consolidé
- `alert_level` = sévérité finale

## 8. Risques connus

- Dépendance à la qualité du CTRL source.
- Risque de dérive si la policy est mal configurée.
- Coût Synapse sous-estimé si exécution multi-partitions.

## 9. FAQ stratégique — “Pourquoi ne pas utiliser un module Azure existant ?”

### Réponse courte

Il n’existe pas, à ce jour, de service unique qui couvre exactement le périmètre de L’ŒIL.

Azure propose des briques puissantes (monitoring, catalogage, observabilité technique), mais pas un framework run-level qui combine simultanément:

- Contrat métier (`CTRL`) et validation déclarée vs observée.
- SLA multi-moteur (`ADF` + `Synapse` + orchestration ŒIL).
- Policy dynamique SQL-first appliquée à l’exécution.
- Snapshot JSON immuable et hash de non-répudiation.
- Estimation de coût Synapse par contrôle.
- Bucket métier (`FAST` / `SLOW` / `VERY_SLOW`).
- Alerting contextualisé métier.

👉 L’ŒIL est un framework d’orchestration qualité orienté exécution, pas un simple outil de monitoring.

### Azure Purview — Différence stratégique

**Purview = gouvernance et catalogage global.**

Purview couvre très bien:

- Data catalog
- Lineage
- Discovery
- Classification (PII, etc.)
- Profiling qualité statique

Purview ne cible pas nativement:

- Comparaison `CTRL` vs réalité observée run par run
- SLA ingestion multi-moteur opérationnel
- Rowcount contractuel au contrôle
- Alerting orienté exécution pipeline
- Estimation coût Synapse par run
- Policy dynamique appliquée à chaud à l’exécution

👉 Purview = gouvernance transverse.
👉 L’ŒIL = contrôle opérationnel run-level.

### Dynatrace — Différence stratégique

**Dynatrace = APM / performance système applicative.**

Dynatrace couvre:

- Monitoring infrastructure
- Monitoring services
- Traces applicatives
- CPU / mémoire / latence

Dynatrace ne couvre pas nativement:

- Validation de volume métier
- Contrôle d’intégrité data contractuel
- Comparaison `expected_rows` vs `actual_rows`
- SLA orienté logique métier data
- Contrôles `MIN/MAX`, checksum ou règles data lake

👉 Dynatrace = santé système.
👉 L’ŒIL = qualité et conformité data.

### Azure natif (Monitor + Alerts) — Positionnement

Azure Monitor / Log Analytics:

- Donne des métriques techniques robustes
- Ne porte pas, seul, la sémantique métier dataset
- Ne gère pas nativement un contrat `expected_rows`
- Ne pilote pas, seul, une policy dynamique par dataset

👉 Azure fournit les briques.
👉 L’ŒIL orchestre, contextualise et consolide ces briques en décision métier actionnable.

## 10. Checksum (Hash) — stratégie (en cours)

Cette section formalise la trajectoire checksum pour L’ŒIL. Le sujet est en cours d’industrialisation, avec montée progressive de la profondeur de contrôle.

### Niveaux possibles

#### Niveau 1 — Hash clé unique

Exemple:

`HASH(client_id)`

Usage:

- Détection d’ajout/suppression de clés
- Contrôle léger à faible coût

#### Niveau 2 — Hash colonnes critiques

Exemple:

`HASH(client_id + statut + pays)`

Usage:

- Validation métier ciblée
- Détection de dérives sur attributs sensibles

#### Niveau 3 — Hash ligne complète

Exemple:

`HASH(CONCAT_WS('|', col1, col2, col3, col4))`

Usage:

- Intégrité forte au niveau enregistrement
- Détection d’altérations non visibles par rowcount/min-max

#### Niveau 4 — Hash dataset complet ordonné

Exemple:

`HASH_AGG(row_hash ORDER BY key)`

Usage:

- Garantie forte d’identité dataset
- Validation globale de non-altération entre deux états

### Cas pratiques pour L’ŒIL

#### En DEV

- Checksum ligne complète
- Fréquence `DAILY`
- Synapse autorisé

#### En PROD

- Checksum clé unique `DAILY`
- Checksum ligne complète `WEEKLY`
- Activation pilotée par policy

### Points critiques (implémentation)

#### 1) Normalisation obligatoire

Avant hash, appliquer systématiquement:

- `NULL` → chaîne vide
- `TRIM`
- format date ISO
- format décimal stable
- `UPPER()` sur les textes métier si nécessaire

Sans normalisation stricte, risque élevé de faux positifs.

#### 2) Ordre déterministe

Toujours imposer:

`ORDER BY primary_key`

Sans ordre stable, le hash agrégé peut varier à contenu identique.

#### 3) Types flottants

Les `FLOAT` peuvent varier légèrement selon moteur/conversion.

Toujours caster en chaîne formatée fixe avant calcul du hash.

### Positionnement policy dans L’ŒIL

Pattern recommandé: 3 niveaux de policy sélectionnables par dataset/environnement.

| Level | Type | Fréquence |
|---|---|---|
| `LIGHT` | Key hash | `DAILY` |
| `STANDARD` | Critical columns hash | `DAILY` |
| `STRICT` | Full row hash | `WEEKLY` |

La policy choisit dynamiquement le niveau selon criticité, coût et fréquence cible.

### Comparaison stratégique des contrôles

| Contrôle | Détecte ajout | Détecte modification | Détecte corruption |
|---|---|---|---|
| Rowcount | ✅ | ❌ | ❌ |
| Min/Max | ❌ | partiel | ❌ |
| Checksum clé | ✅ | ❌ | ✅ |
| Checksum ligne | ✅ | ✅ | ✅ |
