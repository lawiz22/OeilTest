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
