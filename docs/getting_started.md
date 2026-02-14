# 🚀 Getting Started

## Prérequis

1.  **Python 3.12+** : Environnement d'exécution pour les outils de simulation et d'extraction.
2.  **ODBC Driver 18 for SQL Server** : Requis pour la connexion à Azure SQL.
    *   [Lien de téléchargement](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
3.  **Azure SQL Database** : Base de données provisionnée.
4.  **AzCopy** : Outil en ligne de commande pour le transfert de données vers Azure Storage.
    *   Assurez-vous qu'il est dans votre PATH.

## Installation

1.  Créer l'environnement virtuel :
    ```bash
    python -m venv .venv2
    ```

2.  Activer l'environnement :
    ```bash
    # Windows
    .venv2\Scripts\activate
    ```

3.  Installer les dépendances :
    ```bash
    pip install -r requirements.txt
    ```

4.  Configurer la base de données :
    *   Exécutez les scripts SQL dans `sql/tables/*.sql` pour créer les tables.
    *   Exécutez les scripts SQL dans `sql/procedures/*.sql` pour créer les procédures stockées.

## Exécuter une extraction (Fake Data)

Pour simuler une ingestion de données (et peupler la table `vigie_ctrl` avec des données de test) :

```bash
python -m python.runners.run_extractions
```

Cela va :
1.  Générer des fichiers CSV locaux simulant un système source.
2.  Créer les fichiers `CTRL` JSON correspondants.
3.  Insérer les métadonnées dans la base SQLite locale (pour développement) et appeler les procédures Azure SQL simulées.

## Simulations Avancées

### Injecter des runs vigie simulés
Pour tester le dashboard avec des données historiques massives :
```bash
python -m python.runners.run_vigie_faker
```

### Calculer les SLA
Pour recalculer les SLA sur les données existantes :
```bash
python -m python.runners.run_sla_compute
```

### Finaliser SLA + Alertes
Pour consolider les calculs et lever les alertes :
```bash
python -m python.runners.run_vigie_sla_finalize
```

## Reset de l'environnement

Pour repartir de zéro (⚠️ supprime toutes les données de test locales) :
```bash
python -m python.runners.reset_oeil_environment
```
