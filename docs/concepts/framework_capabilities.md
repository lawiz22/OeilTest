# 🧠 Framework Capabilities

## v1 — En production (Current)

La version 1 se concentre sur l'observabilité opérationnelle, le volume et la performance (SLA).

| Contrôle | Description |
|---|---|
| **Row Count** | Comparaison entre les lignes attendues (source) et les lignes chargées (ADF ingestion). |
| **SLA OEIL/ADF/Synapse** | Calcul automatique de la performance avec classification en buckets (FAST / SLOW / VERY_SLOW). |
| **Volume Status** | Qualification du volume chargé : `OK`, `LOW` (alerte mineure), ou `ANOMALY` (écart critique). |
| **Alert Level** | Niveau de sévérité unifié : `NO_ALERT`, `INFO`, `WARNING`, `CRITICAL`. |
| **Coût Synapse** | Estimation en $CAD basée sur la durée d'exécution du compute Synapse et le tarif unitaire. |
| **Hash SHA256** | Hash canonique déterministique du payload de contrôle (intégrité du fichier CTRL lui-même). |

## v2 — Intégrité Configurable (En cours)

La version 2 ajoute une couche de validation fine sur le contenu des données, activable dynamiquement via la `policy`.

| Contrôle | Description |
|---|---|
| **Min/Max** | Validation que les valeurs d'une colonne numérique sont dans une plage attendue (ou cohérente avec l'historique). |
| **Checksum** | Calcul d'un hash (SHA256/MD5) sur une colonne clé pour garantir l'intégrité des données (détection de corruption bit-level). |
| **Null Count** | Validation stricte ou tolérante du nombre de valeurs nulles dans des colonnes critiques. |
| **Delta Previous** | Comparaison statistique avec le dernier run réussi (ex: variation brutale du row count ou de la somme de contrôle). |
| **Policy Engine** | Moteur de règles stocké en SQL permettant d'activer/désactiver ces tests par dataset et environnement sans redéployer de code. |
