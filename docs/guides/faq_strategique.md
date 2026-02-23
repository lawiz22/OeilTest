# ❓ FAQ Stratégique — Positionnement L'ŒIL

## Pourquoi ne pas utiliser un module Azure existant ?

### Réponse courte

Il n’existe pas, à ce jour, de service unique qui couvre exactement le périmètre de L’ŒIL.

Azure propose des briques puissantes (monitoring, catalogage, observabilité technique), mais pas un framework run-level qui combine simultanément:

- Contrat métier (`CTRL`) et validation déclarée vs observée.
- SLA multi-moteur (`ADF` + `Synapse` + orchestration ŒIL).
- Policy dynamique SQL-first appliquée à l’exécution.
- Snapshot JSON immuable et hash de non-répudiation.
- Estimation de coût Synapse par contrôle.
- Bucket métier (`FAST` / `SLOW` / `VERY_SLOW`).
- Alerting contextualisé métier.

👉 L’ŒIL est un framework d’orchestration qualité orienté exécution, pas un simple outil de monitoring.

## Azure Purview — Différence stratégique

**Purview = gouvernance et catalogage global.**

Purview couvre très bien:

- Data catalog
- Lineage
- Discovery
- Classification (PII, etc.)
- Profiling qualité statique

Purview ne cible pas nativement:

- Comparaison `CTRL` vs réalité observée run par run
- SLA ingestion multi-moteur opérationnel
- Rowcount contractuel au contrôle
- Alerting orienté exécution pipeline
- Estimation coût Synapse par run
- Policy dynamique appliquée à chaud à l’exécution

👉 Purview = gouvernance transverse.
👉 L’ŒIL = contrôle opérationnel run-level.

## Dynatrace — Différence stratégique

**Dynatrace = APM / performance système applicative.**

Dynatrace couvre:

- Monitoring infrastructure
- Monitoring services
- Traces applicatives
- CPU / mémoire / latence

Dynatrace ne couvre pas nativement:

- Validation de volume métier
- Contrôle d’intégrité data contractuel
- Comparaison `expected_rows` vs `actual_rows`
- SLA orienté logique métier data
- Contrôles `MIN/MAX`, signature distribuée ou règles data lake

👉 Dynatrace = santé système.
👉 L’ŒIL = qualité et conformité data.

## Azure natif (Monitor + Alerts) — Positionnement

Azure Monitor / Log Analytics:

- Donne des métriques techniques robustes
- Ne porte pas, seul, la sémantique métier dataset
- Ne gère pas nativement un contrat `expected_rows`
- Ne pilote pas, seul, une policy dynamique par dataset

👉 Azure fournit les briques.
👉 L’ŒIL orchestre, contextualise et consolide ces briques en décision métier actionnable.
