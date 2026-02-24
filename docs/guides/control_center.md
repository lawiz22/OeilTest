# 🛠️ Oeil Control Center

Le **Control Center** est l’interface opérationnelle de L’ŒIL.
Il permet de piloter rapidement les datasets, les policies et la structure, sans passer en SQL manuel à chaque étape.

Cette page documente l’outil pour:

- les **usagers** (exploitation, QA, validation de run),
- les **développeurs** (maintenance, endpoints, logique backend).

---

## 1) À quoi sert le Control Center

Le Control Center couvre trois besoins principaux:

1. **Visualiser l’état global** des datasets (Home)
2. **Gérer les policies** de contrôle qualité (Policy)
3. **Gérer le contrat structurel** et comparer avec Synapse (Structural)

---

## 2) Lancer l’application

Commande locale:

```bash
& "C:\Users\Louis-Martin Richard\PycharmProjects\OeilTest\.venv2\Scripts\python.exe" -m uvicorn python.oeil_ui.main:app --reload
```

URL:

`http://127.0.0.1:8000`

Variables importantes:

- `OEIL_AZURE_SQL_CONN` (connexion Azure SQL)
- `OEIL_AZCOPY_DEST` (destination lake / SAS URL)

---

## 3) Écran Home (vue d’ensemble)

L’écran Home donne une vue tabulaire par dataset et environnement (DEV/PROD).

### Capture

![Home - vue d’ensemble](../screenshots/cc_home.png)

Légende rapide:
- Bandeau service: vérifier Azure SQL et Lake avant toute action.
- Ligne dataset: accès direct Policy/Structural pour l’environnement choisi.
- Policy/Structure/Synapse: confirmer l’état global en un coup d’œil.

### Ce qu’on y voit

- **Bandeau de service** en haut:
	- statut `Azure SQL`
	- statut `Lake`
	- bouton `Reconnect`
- **Filtre d’environnement**: `ALL`, `DEV`, `PROD`
- Par ligne dataset:
	- accès rapide via icônes vers **Policy** et **Structural**
	- statut policy `ENABLED` / `DISABLED`
	- switch rapide ON/OFF pour activer/désactiver la policy
	- statut structure (`MATCH`, `DRIFT`, `NO STRUCTURE`)
	- version de mapping
	- indicateur Synapse autorisé

### Actions rapides possibles

- Filtrer uniquement DEV/PROD
- Ouvrir directement Policy ou Structural
- Activer/Désactiver une policy sans changer de page
- Vérifier si les connexions techniques sont vivantes

---

## 4) Écran Policy (gouvernance des tests)

L’écran Policy sert à configurer ce qui doit être validé pour un dataset donné.

### Capture

![Policy - configuration et export](../screenshots/cc_policy.png)

Légende rapide:
- Haut de page: environnement, Synapse Allowed et coût max.
- Bloc tests: ajouter/supprimer et vérifier les champs réellement utilisés.
- Export: générer JSON puis pousser au Lake.

### Ce qu’on y voit

- Métadonnées du dataset (env, synapse_allowed, coût max)
- Actions:
	- `Export JSON`
	- `Export to Lake`
	- `Set Synapse ON/OFF`
- Tableau des tests configurés
- Section `Policy JSON` (aperçu de configuration)

### Ce qu’on peut faire

- Ajouter un test policy
- Supprimer un test policy
- Voir uniquement les **champs réellement utilisés** par test
- Configurer `DISTRIBUTED_SIGNATURE` avec:
	- `algorithm`
	- `components` (`COUNT|MIN|MAX|SUM`)
- Exporter la policy en JSON et la pousser vers le lake

---

## 5) Écran Structural (contrat structurel)

L’écran Structural sert à piloter le contrat de structure et vérifier le drift avec Synapse.

### Capture

![Structural - hash contract vs detected](../screenshots/cc_structural.png)

Légende rapide:
- Compact Summary: comparer rapidement DB hash et Contract hash.
- Synapse Gate Check: coller detected_hash et lancer la comparaison.
- Verdict MATCH/DRIFT: valider ou corriger le contrat structurel.

### Ce qu’on y voit

- **Compact Summary**:
	- DB hash
	- Contract hash (celui à passer dans le pipeline)
	- verdict `MATCH/DRIFT`
- **Synapse Gate Check**:
	- champ pour coller `detected_hash`
	- comparaison directe `contract_hash vs detected_hash`
- Sections avancées repliables (actions, ajout de table, ajout de colonne, JSON)

### Ce qu’on peut faire

- Prévisualiser le recalcul de hash
- Mettre à jour le hash structurel
- Importer la structure depuis SQLite
- Ajouter une table de mapping depuis SQLite
- Ajouter une colonne de mapping manuellement
- Appliquer des suggestions de type
- Vérifier immédiatement si le hash est aligné avec Synapse

---

## 6) Workflow recommandé

1. **Home**: sélectionner dataset + environnement
2. **Policy**: ajuster les tests et exporter si nécessaire
3. **Structural**: vérifier/aligner le contrat et comparer avec Synapse
4. **Retour Home**: valider les statuts globaux

---

## 7) Notes développeur

Composants principaux:

- `python/oeil_ui/main.py` : bootstrap FastAPI
- `python/oeil_ui/modules/home.py` : home + status services
- `python/oeil_ui/modules/policy_routes.py` : routes policy
- `python/oeil_ui/modules/structural_routes.py` : routes structural
- `python/oeil_ui/modules/db.py` : gestion engine SQL + ping/reconnect
- `python/oeil_ui/lake_writer.py` : opérations lake
- `python/oeil_ui/templates/*.html` : UI

Points d’implémentation importants:

- Les routes lisibles utilisent le format `/{dataset_name}/{environment}`
- Les endpoints techniques restent par ID pour les actions API
- Le check de service lake utilise un probe compatible SAS
- Le check SQL supporte le reconnect (reset engine + ping)

---

## 8) Évolution prévue

Le Control Center est maintenant une brique centrale du workflow.
Il est prévu de l’étendre progressivement (nouveaux tests, plus d’automatisation, UX avancée), tout en gardant une approche simple et opérationnelle.
