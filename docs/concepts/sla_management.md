# ⏱️ SLA Management

L'ŒIL propose un calcul de **Service Level Agreement (SLA)** différentié par moteur d'exécution (ADF, Synapse, L'ŒIL) pour détecter précisément les goulots d'étranglement.

## Marquage audit

- **[Implemented]** : confirmé dans les SP/pipelines versionnés.
- **[Recommended]** : règle de cadrage opérationnel recommandée.

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

## Cohérence temporelle (règles d'implémentation) [Recommended]

Pour éviter les durées incohérentes ou nulles :

- `start_ts` / `end_ts` (OEIL global) ne doivent pas être réécrits si déjà présents sur un run finalisé.
- Les durées doivent rester **séparées** par couche :
	- `adf_duration_sec` pour l'ingestion ADF,
	- `synapse_duration_sec` pour le compute Synapse,
	- `duration_sec` pour l'orchestration OEIL globale.
- Le calcul SLA OEIL (`oeil_sla_*`) ne doit pas fusionner les mesures ADF/Synapse ; il consomme la durée OEIL dédiée.

## Coût Synapse (estimation) [Implemented]

Formule de référence :

$$
	\text{cout\_estime\_cad} = \left(\frac{\text{synapse\_duration\_sec}}{60}\right) \times \text{cost\_per\_minute\_cad}
$$

Hypothèses minimales à documenter dans chaque environnement :

| Paramètre | Champ cible | Exemple |
|---|---|---|
| `synapse_duration_sec` | `vigie_ctrl.synapse_duration_sec` | `95` |
| `cost_per_minute_cad` | `vigie_ctrl.synapse_cost_rate_cad_per_min` | `0.002` |
| `cout_estime_cad` | `vigie_ctrl.synapse_cost_estimated_cad` | `0.003167` |
