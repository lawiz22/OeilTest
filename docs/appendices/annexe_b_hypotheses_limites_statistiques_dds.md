# 📊 Annexe B — Hypothèses & limites statistiques de la DDS

*Moteur d’intégrité L’ŒIL*

## 1) Hypothèses de validité

La DDS fournit une forte garantie pratique d’intégrité agrégée sous les hypothèses suivantes:

- normalisation cohérente des types (`NULL`, dates, décimaux, trimming),
- ordre stable des composantes de signature,
- choix de colonnes critiques représentatives,
- fonction de hachage finale robuste,
- agrégats calculés sur le même périmètre (partition, fenêtre temporelle, filtre).

Sans ces hypothèses, la comparaison peut dériver (faux positifs/faux négatifs).

## 2) Nature probabiliste de la non-collision

La DDS n’est pas une preuve d’égalité ligne-à-ligne; c’est une signature agrégée.

Pour deux datasets $D_1, D_2$:

$$
D_1 \neq D_2 \not\Rightarrow DDS(D_1) \neq DDS(D_2)
$$

Le risque de collision agrégée est non nul mais réduit en pratique si le vecteur de contrôle combine plusieurs familles d’agrégats:

$$
V(D)=\big(COUNT, SUM, MIN, MAX, CS, SS\big)
$$

avec $CS$ checksum agrégé et $SS$ signature structurelle.

## 3) Sensibilité statistique des agrégats

Chaque composante détecte des classes différentes d’anomalies:

- `COUNT`: pertes/duplications globales,
- `SUM`: dérive de masse sur colonnes numériques,
- `MIN/MAX`: anomalies d’enveloppe,
- `CHECKSUM_AGG`: perturbations de distribution difficiles à voir via `SUM`,
- `SS(S)`: dérive de schéma.

La puissance de détection vient de la combinaison, pas d’un agrégat unique.

## 4) Scénarios de faux négatifs possibles

Cas théoriques où la DDS peut rester identique malgré une différence réelle:

- permutations compensées (hausse/baisse symétrique conservant `SUM`),
- modifications internes sans impact sur `MIN/MAX` ni checksum choisi,
- changement sur colonnes non couvertes par la DDS.

Conséquence: la DDS doit être traitée comme **gate d’intégrité agrégée**, puis complétée par diagnostics ciblés.

## 5) Scénarios de faux positifs possibles

Cas où la DDS diverge alors que la sémantique métier est inchangée:

- normalisation incohérente des types entre moteurs,
- différence de précision numérique (arrondi, scale),
- gestion hétérogène des `NULL`,
- différences de collation/encodage.

Conséquence: standardiser les règles de casting/normalisation côté source et cible.

## 6) Garde-fous recommandés dans L’ŒIL

- Normalisation explicite par type avant agrégation.
- Couverture minimale: `ROW_COUNT` + `MIN_MAX` + DDS + gate structurel.
- Politique par criticité dataset (fréquence et profondeur des contrôles).
- Escalade automatique vers contrôle ciblé (hash ligne / drill-down) en cas de `FAIL`.
- Journalisation des entrées de signature (`signature_input_string`) pour audit.

## 7) Calibration par niveau de criticité

### Niveau standard

- Contrôles: `ROW_COUNT`, `MIN_MAX`, DDS périodique.
- Objectif: coût minimal avec haute couverture agrégée.

### Niveau sensible

- Contrôles: DDS plus fréquente + checksum enrichi + gate structurel strict.
- Objectif: réduire la probabilité de non-détection agrégée.

### Niveau critique / réglementaire

- Contrôles: DDS + réconciliation ciblée ligne-à-ligne sur segments sensibles.
- Objectif: combiner scalabilité et preuve fine sur zones critiques.

## 8) Lecture de risque (pratique)

La DDS réduit fortement le risque opérationnel d’écarts non détectés à coût maîtrisé, mais ne remplace pas une réconciliation transactionnelle complète dans tous les contextes.

Positionnement recommandé:

- DDS = contrôle primaire d’intégrité en analytique distribué,
- Hash ligne = contrôle secondaire ciblé pour exception, conformité ou litige.

## 9) Critères d’acceptation en exploitation

Une stratégie DDS est considérée robuste si:

- taux d’alertes non actionnables faible,
- absence d’incident majeur non détecté sur période de référence,
- stabilité des signatures à périmètre constant,
- coût Synapse compatible avec budget policy.

## 10) Conclusion

La DDS est statistiquement robuste pour la surveillance d’intégrité à grande échelle, à condition de:

- maîtriser la normalisation,
- multiplier les agrégats complémentaires,
- maintenir un mécanisme d’investigation fine en second niveau.

Cette approche correspond au design de L’ŒIL: **détection agrégée scalable d’abord, investigation ciblée ensuite**.
