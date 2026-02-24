# 🧪 Annexe C — Protocole de test empirique DDS

*Moteur d’intégrité L’ŒIL*

## 1) Objectif

Valider empiriquement que la DDS apporte:

- une détection fiable des écarts d’intégrité agrégée,
- une performance/coût compatible avec l’exploitation,
- une stabilité suffisante pour un usage régulier en DEV et ciblé en PROD.

## 2) Périmètre d’essai

Exécuter le protocole sur un échantillon représentatif de datasets:

- 2 petits (≤ 1M lignes),
- 2 moyens (1M à 20M),
- 2 volumineux (> 20M),
- au moins 1 dataset partitionné temporellement.

Inclure minimum:

- colonnes numériques critiques,
- colonnes de clé métier,
- variabilité de distribution (uniforme et skewée).

## 3) Baseline (run de référence)

Pour chaque dataset cible:

1. Fixer le périmètre: date/partition/environment.
2. Calculer la baseline des contrôles:
   - `ROW_COUNT`,
   - `MIN_MAX`,
   - DDS,
   - hash structurel.
3. Archiver les résultats de référence (timestamp + version policy).

Cette baseline sert de vérité de comparaison pour tous les scénarios injectés.

## 4) Matrice de scénarios de test

## 4.1 Scénarios attendus détectables

- S1: suppression de lignes (1%, 5%, 20%).
- S2: duplication de lignes (1%, 5%, 20%).
- S3: dérive numérique (offset constant sur colonne critique).
- S4: outliers injectés (changement de `MIN`/`MAX`).
- S5: permutation partielle de valeurs (impact checksum, `SUM` inchangé).
- S6: changement de type structurel (`INT` → `BIGINT`, `VARCHAR` → `NVARCHAR`).
- S7: ajout/suppression de colonne.

## 4.2 Scénarios de robustesse opérationnelle

- S8: même dataset, formatage différent (padding, casse, trims).
- S9: variation de précision numérique (scale décimale).
- S10: `NULL` remplacé par valeur par défaut.
- S11: exécution concurrente sur plusieurs partitions.

## 5) Métriques de validation

## 5.1 Qualité de détection

- Taux de détection: $Recall = TP/(TP+FN)$
- Précision d’alerte: $Precision = TP/(TP+FP)$
- Taux de faux positifs: $FPR = FP/(FP+TN)$
- Taux de faux négatifs: $FNR = FN/(TP+FN)$

## 5.2 Performance et coût

- Latence moyenne par contrôle (s),
- P95 latence (s),
- coût moyen Synapse par run (USD),
- volume scanné (GB).

## 5.3 Stabilité

- Écart de signature sur runs identiques (doit être nul),
- variance des temps d’exécution à périmètre constant.

## 6) Seuils d’acceptation recommandés

## 6.1 Détection

- `Recall >= 99%` sur S1–S7,
- `Precision >= 98%` sur S1–S11,
- `FNR <= 1%`,
- `FPR <= 2%`.

## 6.2 Performance

- P95 DDS ≤ 1.5 × P95 `ROW_COUNT` (même périmètre),
- coût DDS compatible avec budget policy dataset,
- aucune dérive de latence > 30% sans changement de volume.

## 6.3 Stabilité

- 0 divergence de signature sur runs strictement identiques,
- 0 alerte structurelle non justifiée après normalisation.

## 7) Procédure d’exécution

1. Exécuter baseline sur tous les datasets.
2. Injecter un scénario (S1…S11) à la fois.
3. Rejouer contrôles (`ROW_COUNT`, `MIN_MAX`, DDS, structure).
4. Capturer verdict (`PASS/FAIL`) et métriques temps/coût.
5. Répéter 5 itérations minimum par scénario.
6. Consolider un tableau de résultats (TP/FP/FN/TN + coûts).

## 8) Lecture des résultats

## 8.1 Verdict cible

- Les scénarios S1–S7 doivent déclencher un `FAIL` sur au moins un contrôle critique.
- Les scénarios S8–S11 doivent rester majoritairement stables après normalisation correcte.

## 8.2 Interprétation type

- `ROW_COUNT FAIL` seul: dérive volumétrique probable.
- `MIN_MAX FAIL` avec `ROW_COUNT PASS`: anomalie de bornes/outliers.
- `DDS FAIL` avec autres PASS: dérive fine/distributionnelle à investiguer.
- `Structure FAIL`: rupture de contrat schéma.

## 9) Critères Go/No-Go (mise en prod)

`GO` si:

- tous les seuils section 6 sont respectés,
- aucune classe de dataset ne montre de dérive systémique,
- budget run validé par policy.

`NO-GO` si:

- `FNR` dépasse le seuil,
- coûts incompatibles avec la fréquence cible,
- instabilité de signature non expliquée.

## 10) Plan de remédiation

En cas de `NO-GO`:

- renforcer la normalisation typée,
- enrichir le vecteur DDS (checksum additionnel, colonnes critiques),
- ajuster fréquence par criticité,
- activer hash ligne ciblé sur périmètre d’exception,
- recalibrer les seuils après campagne de re-test.

## 11) Livrables de la campagne

- matrice de scénarios complétée,
- tableau métriques (qualité, coût, latence),
- décision `GO/NO-GO` argumentée,
- recommandations de tuning policy par dataset.

## 11.1 Template — Matrice de scénarios

| Dataset | Env | Scénario | Itération | Résultat attendu | Résultat observé | Contrôle déclencheur | Verdict |
|---|---|---|---:|---|---|---|---|
| clients | DEV | S1 (delete 5%) | 1 | FAIL | FAIL | `ROW_COUNT` | ✅ |
|  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |

## 11.2 Template — Métriques qualité

| Dataset | TP | FP | FN | TN | Recall | Precision | FPR | FNR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| clients | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0.00 | 0.00 |
| accounts | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0.00 | 0.00 |
| contracts | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0.00 | 0.00 |
| transactions | 0 | 0 | 0 | 0 | 0.00 | 0.00 | 0.00 | 0.00 |

## 11.3 Template — Performance & coût

| Dataset | Nb lignes | Latence moyenne DDS (s) | P95 DDS (s) | P95 ROW_COUNT (s) | Ratio P95 DDS/ROW_COUNT | Coût moyen run (USD) | Volume scanné (GB) |
|---|---:|---:|---:|---:|---:|---:|---:|
| clients | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| accounts | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| contracts | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| transactions | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

## 11.4 Template — Décision GO/NO-GO

| Critère | Seuil | Mesure observée | Statut |
|---|---|---|---|
| Recall S1–S7 | `>= 99%` |  | ⬜ |
| Precision S1–S11 | `>= 98%` |  | ⬜ |
| FNR | `<= 1%` |  | ⬜ |
| FPR | `<= 2%` |  | ⬜ |
| Ratio P95 DDS/ROW_COUNT | `<= 1.5` |  | ⬜ |
| Stabilité signature (runs identiques) | `0 divergence` |  | ⬜ |

Décision finale: `GO` / `NO-GO`

Commentaire comité:

- 

## 11.5 Template exécutif (ultra court, 1 tableau)

| Domaine | KPI clé | Seuil cible | Résultat campagne | Statut |
|---|---|---|---|---|
| Qualité de détection | Recall (S1–S7) | `>= 99%` |  | ⬜ |
| Qualité de détection | Precision (S1–S11) | `>= 98%` |  | ⬜ |
| Risque d’erreur | FNR | `<= 1%` |  | ⬜ |
| Risque d’erreur | FPR | `<= 2%` |  | ⬜ |
| Performance | Ratio P95 DDS / P95 ROW_COUNT | `<= 1.5` |  | ⬜ |
| Coût | Coût moyen run Synapse | Budget policy |  | ⬜ |
| Stabilité | Divergence signature sur runs identiques | `0` |  | ⬜ |
| Gouvernance | Décision finale | `GO` attendu | GO / NO-GO | ⬜ |

Usage:

- Remplir une ligne par KPI à la fin de campagne.
- Présenter ce tableau seul en comité, puis détailler via sections 11.1 à 11.4 si demandé.

## 12) Positionnement final

Ce protocole valide la DDS comme mécanisme primaire de contrôle agrégé dans L’ŒIL, tout en encadrant explicitement le recours au hash ligne ciblé pour investigation et conformité.
