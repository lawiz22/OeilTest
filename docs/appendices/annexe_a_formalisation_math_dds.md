# 🧮 Annexe A — Formalisation mathématique de la DDS

*Moteur d’intégrité L’ŒIL*

## 1) Modélisation du dataset

Soit un dataset $D$ défini par:

$$
D = \{r_1, r_2, \dots, r_n\}
$$

avec:

- $n$ = nombre total de lignes,
- $r_i$ = $i^\text{e}$ enregistrement,
- chaque $r_i$ est un vecteur de $m$ colonnes.

$$
r_i = (c_{i1}, c_{i2}, \dots, c_{im})
$$

## 2) Objectif de la DDS

Construire une signature déterministe:

$$
DDS(D)
$$

telle que:

$$
DDS(D_{source}) = DDS(D_{cible}) \Rightarrow D_{source} \equiv D_{cible}
$$

au sens de l’intégrité agrégée.

## 3) Fonctions d’agrégation déterministes

### 3.1 Cardinalité

$$
C(D) = |D| = n
$$

### 3.2 Agrégations numériques

Pour toute colonne numérique $k$:

$$
SUM_k(D) = \sum_{i=1}^{n} c_{ik}
$$

$$
MIN_k(D) = \min_{i=1..n}(c_{ik})
$$

$$
MAX_k(D) = \max_{i=1..n}(c_{ik})
$$

### 3.3 Checksum agrégé

On définit une projection ligne $f(r_i)$, puis:

$$
CS(D) = \sum_{i=1}^{n} f(r_i)
$$

(ou toute fonction d’agrégation déterministe équivalente).

## 4) Construction de la signature composite

On définit le vecteur d’intégrité:

$$
V(D) = \big(C(D), \{SUM_k(D)\}, \{MIN_k(D)\}, \{MAX_k(D)\}, CS(D)\big)
$$

La signature finale:

$$
DDS(D) = H(V(D))
$$

avec:

- $H$ fonction de hachage déterministe,
- ordre des composantes fixé,
- types normalisés.

## 5) Propriété de déterminisme

Pour deux datasets $D_1$ et $D_2$:

$$
V(D_1) = V(D_2) \Rightarrow DDS(D_1) = DDS(D_2)
$$

La probabilité que:

$$
D_1 \neq D_2 \;\wedge\; DDS(D_1)=DDS(D_2)
$$

est non nulle, mais négligeable si:

- les agrégats sont multiples,
- les types sont contrôlés,
- la fonction $H$ est robuste.

## 6) Extension partitionnée

Soit un dataset partitionné:

$$
D = \bigcup_{p=1}^{P} D_p
$$

On définit:

$$
DDS(D_p) = H(V(D_p))
$$

Puis la signature globale:

$$
DDS(D) = H\big(DDS(D_1), DDS(D_2), \dots, DDS(D_P)\big)
$$

Ce schéma permet:

- calcul parallèle,
- scalabilité horizontale,
- validation incrémentale.

## 7) Extension structurelle

Soit un schéma $S$ défini par:

$$
S = \{(nom_j, type_j, ordre_j)\}
$$

On définit la signature de structure:

$$
SS(S) = H(S)
$$

La signature complète:

$$
DDS_{global}(D) = H\big(DDS(D), SS(S)\big)
$$

Ce mécanisme détecte:

- changement de type,
- ajout/suppression de colonne,
- modification de l’ordre structurel.

## 8) Complexité computationnelle

### 8.1 DDS

- Temps: $O(n)$
- Mémoire: $O(1)$ (agrégats constants)
- Compatible MPP

### 8.2 Hash ligne complète

Temps asymptotique également $O(n)$, mais coût réel plus élevé en distribué à cause de:

- matérialisation ligne à ligne,
- comparaison inter-systèmes,
- stockage intermédiaire.

## 9) Résilience et collision

La robustesse dépend de:

- nombre d’agrégats,
- diversité des métriques,
- qualité de la fonction de hachage finale.

La combinaison cardinalité + agrégats numériques + checksum agrégé + signature structurelle rend la collision extrêmement improbable en contexte industriel.

## 10) Conclusion mathématique

La DDS se formalise comme:

$$
DDS(D) = H\big(C(D), A_1(D), A_2(D), \dots, A_k(D), SS(S)\big)
$$

avec $A_i$ fonctions d’agrégation déterministes.

La DDS est donc une application:

$$
DDS: \mathcal{D} \rightarrow \Sigma
$$

qui associe à tout dataset une signature compacte, déterministe, distribuable et scalable.
