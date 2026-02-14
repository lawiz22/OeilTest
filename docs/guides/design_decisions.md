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
