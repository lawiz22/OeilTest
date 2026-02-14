# 📊 Power BI Dashboard

Le dashboard L'ŒIL est l'interface principale de surveillance. Il consolide les métriques de tous les runs d'extraction.

![Dashboard Preview](../screenshots/powerbi_dashboard_main.png)

## Indicateurs Clés

### 1. Runs Total

Nombre total de contrôles exécutés dans la période sélectionnée.

-   **FAST** (vert) : Runs exécutés dans le temps prévu par le SLA.Performance optimale.
-   **SLOW** (jaune) : Runs légèrement lents, mais acceptables (SLA warning).
-   **VERY SLOW** (rouge) : Runs critiques dépassant largement le SLA. Nécessitent investigation.

### 2. Santé Globale (SLA Buckets)

Classification des performances par moteur :

-   **ADF** : Temps d'ingestion (volume-dependent).
-   **SYNAPSE** : Temps de compute (fixed overhead).
-   **OEIL** : Temps d'orchestration globale.

### 3. Performance / Durée

Moyenne des temps d'exécution (en secondes) par moteur et par jour. Permet de détecter des dérives progressives.

### 4. Problèmes / Fail

Nombre de runs en erreur technique (status=`FAILED`).

-   **ADF FAIL** : Échec de copie ou timeout.
-   **SYNAPSE FAIL** : Erreur SQL ou timeout compute.
-   **OEIL FAIL** : Erreur logique ou timeout global.

### 5. Volume

Métriques de contrôle des données :

-   **Volume Issue Runs** : Nombre de runs où le volume réel diffère significativement du volume attendu.
-   **Volume Drift Detected** : Détection de tendance anormale (hausse ou baisse continue).
