# Roadmap — Histoire du projet par phase

Vue macroscopique des phases majeures depuis le début. Pour le détail :

- Décisions : [`.memory/decisions.md`](../../.memory/decisions.md).
- Synthèse par commit : [`JOURNALDESMODIFS.md`](./JOURNALDESMODIFS.md).
- Chronologie fine : [`JOURNALDEBORD.md`](./JOURNALDEBORD.md).
- Tâches à venir : [`TODO.md`](../../TODO.md) (local, gitignoré).

Sources : `git log --reverse`, décisions datées et journaux, croisés avec la
mémoire du décideur. Les phases sans trace écrite sont marquées « hors trace
écrite, mémoire décideur ». Une entrée correspond à une phase majeure, pas à
chaque GO.

Le premier commit date du 2026-10-17. Le décideur a confirmé qu'aucune phase
antérieure sans trace écrite ne doit être ajoutée.

## Divergences et limites de vérification

- Le brief signale la release `v3-distribution`, mais aucun tag n'apparaît dans
  `git tag -l`. La consultation de la release GitHub n'a pas abouti, car `gh`
  n'est pas authentifié. Son existence distante reste à confirmer.
- L'état V3.0 d'`AGENTS.md` et la section V3.0 de `JOURNALDESMODIFS.md`
  indiquent 73 tests; la décision #26 et l'entrée Phase 8b consignent 76 tests
  stables. La valeur 76 correspond à l'état après Phase 8b; l'indication 73
  reste un état documentaire antérieur.
- La table mémoire d'`AGENTS.md` indique 23 décisions; `decisions.md` en
  contient 26. Cette valeur est également obsolète et n'est pas corrigée dans
  le présent GO.
- `JOURNALDESMODIFS.md` date la synthèse de refonte des Phases 1–7 du
  2026-10-22 au 2026-10-23, tandis que les dix commits qu'elle énumère sont
  datés du 2026-10-22 dans Git. Les dates des phases ci-dessous suivent les
  dates des commits; la période plus large du journal est conservée comme
  divergence de périmètre.

## [Phase 1] Socle et V1 (2026-10-17 → 2026-10-18)

**Commits** : `e91f000` (socle), `255376a` (modèle), `7bc2185` (build
`.llamafile`), `5e4ee4a` (mémoire SQLite V1), `4072032` (clôture V1).

**Décisions** : #1–12.

**Source** : Trace + Décideur.

**Objectif** : cadrer le produit local et construire le bootstrap, le runtime
et les premiers outils de conversation.

**Livrable** : V1 documentée, avec installation, lancement local et mémoire
SQLite; les décisions de départ concernant `main/` sont conservées comme
historique, puis déclarées obsolètes.

## [Phase 2] V2 — login et chat multi-utilisateur (2026-10-18 → 2026-10-19)

**Commits** : `68524b9` (cadrage V2), `d3111cf` (squelette du proxy),
`9b08c44` (sessions et cookies), `c0478b2` (login/logout), `df934af`
(frontend), `299463c` (clôture V2).

**Décisions** : aucune décision dédiée dans `decisions.md`; les jalons sont
tracés dans Git et `JOURNALDEBORD.md`.

**Source** : Trace + Décideur.

**Objectif** : faire évoluer la V1 vers un chat web avec authentification et
plusieurs utilisateurs.

**Livrable** : V2 fonctionnelle, avec proxy, interface de login/chat,
persistance SQLite et tests.

## [Phase 3] V3 — authentification et premier parcours de distribution (2026-10-19 → 2026-10-21)

**Commits** : `29ec99b` (cadrage auth), `90e7e29` (migration SQLite V3),
`2c54d16` (création admin), `9e52161` (test E2E auth), `b87db9a` et
`f103215` (distribution préconstruite), `ef33fcd` (sessions et périmètre
admin).

**Décisions** : #13–16.

**Source** : Trace + Décideur.

**Objectif** : définir et implémenter l'authentification V3, tout en séparant
la construction du runtime de son exécution par l'utilisateur.

**Livrable** : authentification V3, migration et parcours d'installation
fondé sur un runtime préconstruit.

## [Phase 4] Stabilisation UI et refonte de distribution (Phases 1–7) (2026-10-22)

**Commits** : `650f9da`, `b628249` et `97c2a58` (layout chat); `6bfba9d`,
`ee766ce`, `6db45c9`, `9c9df0e`, `92f36fd`, `f50691f`, `b5c7833` et
`64f0ba4` (refonte de distribution et clôture).

**Décisions** : #17–18.

**Source** : Trace + Décideur.

**Objectif** : stabiliser le défilement interne du chat et remplacer le
runtime regroupé par une archive autonome qui télécharge séparément le runtime
llamafile-thin et le modèle GGUF.

**Livrable** : archive ZIP sans Git ni binaires pré-intégrés, parcours
`install.bat`/`lancer.bat`, documentation et archive de distribution
renommées et mises à jour.

## [Phase 5] Assainissement et gouvernance documentaire (Phases 7C–7E) (2026-10-23)

**Commits** : `ad7aec6` (assainissement), `635ef2f` (corrections P1),
`81ab659`, `bfb12c2`, `e638582`, `7242075` et `92d7ffc` (corrections,
historique des décisions et suivi).

**Décisions** : #19–23.

**Source** : Trace + Décideur.

**Objectif** : corriger les écarts documentaires, formaliser l'attribution
`Assisted-by`, les règles de suivi et les décisions de licence et de
documentation bilingue.

**Livrable** : documentation de distribution et règles de traçabilité
alignées; la dette des tests intermittents est identifiée et reportée en
Phase 8, sans retry aveugle.

## [Phase 6] Phase 7F — progression et évaluation Spec Kit (2026-10-23)

**Commits** : `e531e15` (barre de progression), `4ed9190` (décision Spec Kit).

**Décisions** : #24–25.

**Source** : Trace + Décideur.

**Objectif** : rendre visibles les téléchargements et comparer Spec Kit à la
méthode du projet sans l'installer dans le dépôt.

**Livrable** : progression ASCII TTY/non-TTY et décision de conserver la
méthode actuelle; l'expérience 7F-B n'a pas de commit autonome et est tracée
par la décision #25.

## [Phase 7] Phase 8b — correction WinError 10053 (2026-10-23)

**Commits** : `996d5e9`.

**Décisions** : #26.

**Source** : Trace + Décideur.

**Objectif** : éviter l'abandon de connexion lorsqu'un POST est refusé avant
que son corps soit consommé.

**Livrable** : lecture bornée du corps POST avant contrôle d'authentification,
test de non-régression sur 200 requêtes et validation répétée de la suite.

## État actuel (2026-10-23)

- Distribution : `lacitadelle-distribution.zip`, 92 019 octets (taille
  vérifiée localement). La release GitHub `v3-distribution` est signalée dans
  le brief, mais reste non vérifiée par l'IDE.
- Tests : 76, validés 10/10 runs en Phase 8b.
- Décisions : 26 actées.
- Règles : sept règles structurelles dans `AGENTS.md`.
- Tâches à venir : voir `TODO.md` (local, gitignoré).

## Prochaines phases possibles (non clôturées)

Voir [`BACKLOG.md`](./BACKLOG.md) pour le détail. Ces phases ne sont pas
clôturées; elles ne deviendront des entrées définitives de cette Roadmap
qu'après leur implémentation.

- **Mode B-1** : page de réglages (user + admin + logs et indicateurs).
- **Mode B-2** : changement de modèle admin, avec rollback obligatoire et
  whitelist curée.
- **Nettoyage base locale** : à effectuer au moment de la production.
