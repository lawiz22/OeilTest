# ⏱️ SLA Management

L'ŒIL propose un calcul de **Service Level Agreement (SLA)** différentié par moteur d'exécution (ADF, Synapse, L'ŒIL) pour détecter précisément les goulots d'étranglement.

## Principes Généraux

Un run est classifié selon sa durée d'exécution par rapport à un **seuil attendu** (threshold).

-   **FAST** (vert) : Durée ≤ Expected
-   **SLOW** (jaune) : Expected < Durée ≤ Threshold
-   **VERY SLOW** (rouge) : Durée > Threshold
-   **FAIL** : Erreur technique ou fonctionnelle

## Formules de Calcul

### 1. SLA ADF (Volume-Based)

Le temps d'ingestion est proportionnel au volume de données.

```
Expected  = Base Overhead + (Rows / 1000) * Sec_Per_1k_Rows
Threshold = Expected * (1 + Tolerance %)
```

*   **Base Overhead** : Temps fixe de démarrage du pipeline (ex: 30s).
*   **Sec_Per_1k_Rows** : Temps moyen pour traiter 1000 lignes (ex: 5s).
*   **Tolerance** : Marge d'erreur acceptée (ex: 25%).

### 2. SLA Synapse (Fixed Overhead)

Le compute Synapse a un temps de démarrage (warm-up) significatif, mais le traitement est ensuite très rapide. On utilise souvent un modèle à overhead fixe.

```
Expected  = Base Overhead (ex: 120s)
Threshold = Expected * (1 + Tolerance %)
```

### 3. SLA L'ŒIL (Fixed Overhead)

L'orchestration globale (procédure stockée, appels API) est considérée comme un overhead fixe.

```
Expected  = Base Overhead (ex: 360s)
Threshold = Expected * (1 + Tolerance %)
```

## Configuration

Les paramètres sont stockés dans la table `sla_profile_execution_type` :

| Execution Type | Base Overhead | Sec / 1k | Tolerance |
|---|---|---|---|
| **ADF** | 30s | 5s | 25% |
| **SYNAPSE** | 120s | — | 30% |
| **OEIL** | 360s | — | 22% |

> **Note** : Une future version permettra de surcharger ces profils par dataset via la table `sla_profile`.
