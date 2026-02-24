# 🛠️ Oeil Control Center

Interface Python unifiée pour piloter les policies et les structures de données.

Le module est localisé dans `python/oeil_ui/` et fournit:

- une UI web FastAPI + Jinja2,
- un pilotage des policies (lecture, ajout, suppression, export JSON, export lake),
- un pilotage structurel (détection SQLite, import mapping, typage, hash),
- un accès Azure SQL via SQLAlchemy.

## Composants principaux

- `main.py` : bootstrap FastAPI
- `modules/home.py` : vue dashboard
- `modules/policy_routes.py` : endpoints policy
- `modules/structural_routes.py` : endpoints structure
- `templates/home.html` : dashboard principal
- `templates/policy.html` : gestion policy
- `templates/structural.html` : gestion structure
- `static/style.css` : styles UI

## Variables d’environnement

Définies dans `.env` (racine projet):

- `OEIL_AZURE_SQL_CONN`
- `OEIL_AZCOPY_DEST`
- `OEIL_STORAGE_CONN`
- `OEIL_STORAGE_CONTAINER`

## Lancer l’UI

```bash
& "C:\Users\Louis-Martin Richard\PycharmProjects\OeilTest\.venv2\Scripts\python.exe" -m uvicorn python.oeil_ui.main:app --reload
```

URL locale: `http://127.0.0.1:8000`

## Workflow recommandé

1. **Home**: choisir un dataset.
2. **Policy**: ajuster les tests actifs, exporter en JSON/lake.
3. **Structural**: détecter SQLite, importer les colonnes, appliquer les suggestions de type.
4. **Hash**: confirmer la mise à jour hash et vérifier le statut `MATCH`.

## Notes

- Le dataset `clients` reste protégé en écriture côté UI structurelle.
- Le refresh hash tente la SP `ctrl.SP_REFRESH_STRUCTURAL_HASH`, avec fallback inline si permission `EXECUTE` absente.
- Les captures d’écran seront ajoutées dans cette page après la prochaine passe visuelle.
