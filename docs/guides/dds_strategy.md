# 📘 Livre blanc — Signature Distribuée de Dataset (DDS) vs Hash Ligne Complète

## 1) Résumé exécutif

Les mécanismes de validation d’intégrité se divisent en deux grandes approches:

- Hash au niveau ligne (checksum ligne complète)
- Signature distribuée de dataset (DDS)

Ces deux approches sont déterministes, mais répondent à des objectifs architecturaux différents.
Le moteur L’ŒIL privilégie la **DDS** comme mécanisme principal d’intégrité pour les environnements distribués à grande échelle.

## 2) Hash ligne complète (checksum ligne)

### 2.1 Définition

Le hash ligne complète consiste à:

- concaténer toutes les colonnes d’un enregistrement (après normalisation),
- appliquer une fonction de hachage,
- comparer les signatures entre source et cible.

Représentation logique:

`HASH = SHA256(CONCAT(col1, '|', col2, '|', col3, ...))`

Le résultat représente l’état exact d’une ligne à un instant donné.

### 2.2 Caractéristiques techniques

- Granularité: ligne
- Déterministe
- Sensible à l’ordre des colonnes, au casting implicite, aux `NULL` et au formatage
- Nécessite une comparaison complète des jeux de données

### 2.3 Avantages

- Détection précise des modifications ligne par ligne
- Adapté aux systèmes transactionnels
- Utile pour la validation CDC
- Approche simple à expliquer
- Pertinent sur des volumes petits à moyens

### 2.4 Limites

- Coût computationnel élevé sur grands volumes
- Scalabilité limitée en environnement distribué (Lakehouse / MPP)
- Sensible aux différences non sémantiques
- Peu optimisé pour traitement massivement parallèle
- Nécessite un balayage complet pour validation globale

### 2.5 Cas d’usage typiques

- Validation de réplication transactionnelle
- Synchronisation SCD
- Réconciliation de migration
- Audit fin ligne à ligne
- Contrôle réglementaire détaillé

## 3) Signature Distribuée de Dataset (DDS)

### 3.1 Définition

Une DDS est une signature déterministe calculée au niveau:

- table,
- partition,
- dataset complet.

Au lieu de hacher chaque ligne individuellement, la DDS combine des agrégats déterministes en signature composite.

Exemple conceptuel:

`DDS = HASH(COUNT(*), SUM(...), MIN(...), MAX(...), CHECKSUM_AGG(...))`

La DDS représente l’état global d’un dataset.

### 3.2 Principes architecturaux

La DDS est conçue pour:

- les environnements MPP,
- les architectures distribuées,
- les data lakes / lakehouses,
- les pipelines d’ingestion à grande échelle.

Le calcul est naturellement:

- partitionnable,
- parallélisable,
- incrémental,
- optimisable en coût (serverless).

### 3.3 Avantages

- Haute scalabilité
- Compatibilité native avec moteurs distribués
- Coût réduit vs hash ligne complète
- Peu de mouvement de données
- Excellente performance sur volumes massifs
- Très adapté à la validation Bronze → Standardized → Curated

### 3.4 Limites

- N’identifie pas directement la ligne fautive
- Risque théorique de collision agrégée
- Nécessite une conception multi-contrôles
- Moins adapté aux validations transactionnelles fines

### 3.5 Cas d’usage typiques

- Validation d’ingestion dans un data lake
- Contrôle d’intégrité Bronze vs Standardized
- Validation de réplication massive
- Surveillance de dérive de données
- Monitoring d’intégrité en environnement analytique distribué

## 4) Analyse comparative

| Critère | Hash ligne complète | DDS |
|---|---|---|
| Granularité | Ligne | Dataset / Partition |
| Scalabilité | Limitée | Élevée |
| Performance gros volumes | Faible à moyenne | Excellente |
| Compatibilité MPP | Faible | Native |
| Précision d’identification | Très élevée | Agrégée |
| Coût opérationnel | Élevé | Optimisé |
| Adapté Lakehouse | Non | Oui |
| Adapté transactionnel | Oui | Limité |

## 5) Stratégie d’intégrité L’ŒIL

### 5.1 Principe fondamental

Privilégier les contrôles déterministes agrégés et distribués plutôt que le hash ligne complète pour les environnements analytiques massifs.

### 5.2 Architecture en couches

Le modèle recommandé combine:

1. DDS (signature globale dataset)
2. Validation du nombre de lignes (`COUNT`)
3. Contrôles `MIN/MAX` sur colonnes critiques
4. Agrégations numériques (`SUM`, `AVG` si pertinent)
5. Checksum de structure (schéma)
6. Hash ligne ciblé en analyse d’exception

Cette approche maximise la scalabilité, réduit les coûts et conserve une capacité d’investigation fine.

## 6) Recommandation architecturale

Dans les plateformes analytiques modernes (MPP SQL, Spark, Lakehouse cloud), une stratégie DDS apporte:

- meilleure performance,
- réduction des coûts d’exécution,
- haute scalabilité,
- séparation claire entre monitoring d’intégrité et réconciliation transactionnelle.

Le hash ligne complète doit rester ciblé:

- audits réglementaires,
- validations transactionnelles critiques,
- analyses d’écarts spécifiques.

## 7) Conclusion

Le hash ligne complète et la DDS répondent à des besoins distincts.
Le premier optimise la précision transactionnelle; la seconde optimise la scalabilité en environnement distribué.

Le moteur L’ŒIL adopte la DDS comme mécanisme central d’intégrité, renforcé par des contrôles complémentaires, pour un cadre robuste, scalable et économiquement optimisé.

## Référence implémentation L’ŒIL

- Procédure: `ctrl.SP_OEIL_DISTRIBUTED_SIGNATURE_PQ`
- Fichier Synapse: `sql/synapse/procedures/SP_OEIL_DISTRIBUTED_SIGNATURE_PQ.sql`
- Contrôles complémentaires: `ROW_COUNT`, `MIN_MAX`, gate structurel (`SP_GET_CONTRACT_STRUCTURE_HASH` / `SP_GET_DETECTED_STRUCTURE_HASH`)

## Annexe mathématique

- [Annexe A — Formalisation mathématique de la DDS](../appendices/annexe_a_formalisation_math_dds.md)
- [Annexe B — Hypothèses & limites statistiques de la DDS](../appendices/annexe_b_hypotheses_limites_statistiques_dds.md)
- [Annexe C — Protocole de test empirique DDS](../appendices/annexe_c_protocole_test_empirique_dds.md)
