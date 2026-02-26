# 🧭 Plan de migration — Pipelines + Vigie DB vers Synapse (DevOps)

> Objectif: centraliser l’orchestration et la couche SQL dans Synapse pour améliorer la gouvernance, l’industrialisation CI/CD et le contrôle opérationnel.

## 1) Contexte et intention

Aujourd’hui, L’ŒIL s’appuie sur:
- des pipelines ADF,
- une base `vigie_*` en Azure SQL.

La cible proposée est:
- pipelines orchestrés dans Synapse,
- objets SQL `vigie_*` hébergés dans Synapse SQL,
- exploitation Git/DevOps unifiée (branches, PR, release, rollback).

## 2) Principes de migration

- **Zéro big bang**: migration progressive par lots.
- **Compatibilité d’abord**: conserver les contrats d’interface (paramètres pipeline, schéma logique, JSON CTRL).
- **Mesure systématique**: comparer SLA/coûts/résultats avant et après.
- **Rollback explicite**: chaque étape doit être réversible.

## 3) Roadmap proposée (version initiale)

## Phase 0 — Cadrage & inventaire
- Cartographier les pipelines ADF existants (Guardian/Core/Quality + Bronze).
- Inventorier les procédures SQL, tables `vigie_*`, dépendances KQL/WebActivity, connexions linked services.
- Identifier les écarts de compatibilité Azure SQL vs Synapse SQL (T-SQL, transactions, perf, sécurité).

**Livrables**
- Inventaire technique versionné.
- Matrice dépendances (pipeline ↔ proc ↔ table ↔ dashboard).

## Phase 1 — Fondations Synapse
- Créer le workspace/artefacts Synapse (environnements DEV/QA/PROD).
- Mettre en place la structure Git/branches/release (DevOps).
- Définir la convention de nommage, variable management, secrets (Key Vault), permissions RBAC.

**Livrables**
- Repo/branching model validé.
- Templates de déploiement et pipeline CI de validation.

## Phase 2 — Migration base Vigie vers Synapse SQL
- Migrer le schéma `vigie_*` (tables + procédures) vers Synapse SQL.
- Adapter les procédures incompatibles et valider la parité fonctionnelle.
- Charger un jeu de données de référence pour tests de non-régression.

**Livrables**
- DDL/DML de migration versionnés.
- Rapport de validation (parité résultats + performance).

## Phase 3 — Migration pipelines ADF → Synapse pipelines
- Recréer/porter `PL_Oeil_Guardian`, `PL_Oeil_Core`, `PL_Oeil_Quality_Engine`.
- Reconnecter les activités SQL, Web/KQL, dépendances `.done`/CTRL.
- Exécuter des runs comparatifs A/B (ancien vs nouveau).

**Livrables**
- Pipelines Synapse opérationnels en DEV.
- Tableau de comparaison run par run.

## Phase 4 — Observabilité, sécurité et coûts
- Vérifier monitoring (logs, alertes, métriques SLA, coût compute).
- Ajuster watchdogs et seuils policy.
- Vérifier conformité sécurité (accès, secrets, audit trail).

**Livrables**
- Dashboard de supervision cible.
- Dossier de conformité technique.

## Phase 5 — Cutover contrôlé
- Activer un dataset pilote en production (canary).
- Monter progressivement la couverture datasets.
- Désactiver l’ancien chemin après stabilisation.

**Livrables**
- Plan de bascule exécuté.
- REX (retour d’expérience) et backlog d’optimisation.

## 4) Décisions à prendre ensemble (atelier)

1. Cible SQL Synapse: **Dedicated pool** ou **Serverless + design hybride** ?
2. Stratégie CI/CD: mono-repo ou multi-repo (SQL, pipelines, docs) ?
3. Niveau de parité attendu au démarrage: stricte (100%) ou pragmatique par capacités ?
4. Fenêtre de cutover: progressive par dataset ou bascule par domaine ?
5. KPI de succès: SLA, coût, temps de déploiement, MTTR incidents.

## 5) Journal de décision (temps réel)

| Date | Sujet | Décision | Impact | Owner | Prochaine action |
|---|---|---|---|---|---|
| TBD | Architecture SQL cible | À décider | Fort | Équipe Data | Atelier architecture |

## 6) Backlog initial

- [ ] Construire l’inventaire SQL complet (`tables`, `procédures`, dépendances).
- [ ] Produire la matrice compatibilité Azure SQL ↔ Synapse SQL.
- [ ] Définir stratégie de tests de non-régression (golden dataset).
- [ ] Prototyper migration d’un dataset pilote de bout en bout.
- [ ] Définir pipeline DevOps (lint SQL/JSON + déploiement contrôlé).

## 7) Mode de travail proposé dès maintenant

- **Cadence**: 1 point de décision court / jour pendant le cadrage.
- **Traçabilité**: ce document est la source vivante (mise à jour à chaque décision).
- **Rituels**: PR courte par évolution majeure (architecture, SQL, pipeline, cutover).

---

Si tu veux, prochaine étape: on remplit ensemble la section **“Décisions à prendre”** et on transforme ça en plan exécutable sprint par sprint.
