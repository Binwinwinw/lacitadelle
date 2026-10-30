# La Citadelle — Instructions agents

## Identité du projet

Application locale pour public non-technique : runtime llamafile-thin et GGUF
téléchargés séparément, proxy Python et webchat. La distribution utilisateur
est une archive ZIP autonome, sans Git. Le projet s'appuie sur
mozilla-ai/llamafile.

## État actuel

V3.1 fonctionnelle localement. Phase 11 complète; 194 tests permanents et
70 décisions datées. `install.bat` télécharge llamafile-thin et le GGUF;
`lancer.bat` démarre le runtime et le proxy. La distribution V3 est
`lacitadelle-distribution.zip`, sans Git ni binaires intégrés. V3.0/V3.1
désignent les versions du périmètre d'authentification.

## Références projet

| Fichier | Rôle |
| --- | --- |
| [README.md](./README.md) / [README.fr.md](./README.fr.md) | Guide du produit pour l'utilisateur |
| [CONTRIBUTING.md](./CONTRIBUTING.md) / [CONTRIBUTING.fr.md](./CONTRIBUTING.fr.md) | Guide de contribution |
| [LICENSE](./LICENSE) | Licence du projet |
| [CHANGELOG.md](./CHANGELOG.md) | Pointeur vers les documents d'historique |
| [AGENTS.md](./AGENTS.md) | Instructions et règles agents |
| [ARCHITECTURE.md](./dev/docs/ARCHITECTURE.md) | Architecture et flux |
| [RUNBOOK.md](./dev/docs/RUNBOOK.md) | Procédures d'exploitation manuelles |
| [OBJECTIF.md](./dev/docs/OBJECTIF.md) | Objectifs et périmètre produit |
| [ROADMAP.md](./dev/docs/ROADMAP.md) | Histoire du projet par phase |
| [BACKLOG.md](./dev/docs/BACKLOG.md) | Tâches futures validées |
| [JOURNALDEBORD.md](./dev/docs/JOURNALDEBORD.md) | Chronologie des sessions |
| [JOURNALDESMODIFS.md](./dev/docs/JOURNALDESMODIFS.md) | Synthèse par commit |
| [.memory/decisions.md](./.memory/decisions.md) | Décisions actées |
| [.memory/instructions.md](./.memory/instructions.md) | Rappel et pointeurs agents |
| [.memory/preferences.md](./.memory/preferences.md) | Préférences du décideur |
| [.memory/quirks.md](./.memory/quirks.md) | Particularités et pièges |
| [.memory/security.md](./.memory/security.md) | Règles de sécurité |
| [TODO.md](./TODO.md) | Pense-bête immédiat, local et gitignoré |

## Ordre de lecture pour un contributeur ou un agent

Pour comprendre le projet et savoir quoi faire, lire dans cet ordre :

1. **README.md / README.fr.md** : comprendre le produit pour l'utilisateur final.
2. **CONTRIBUTING.md / CONTRIBUTING.fr.md** : comprendre comment contribuer.
3. **AGENTS.md** : comprendre les règles de collaboration (9 règles structurelles).
4. **dev/docs/ROADMAP.md** : comprendre l'histoire du projet par phase (V1 → Phase 11f).
5. **dev/docs/BACKLOG.md** : comprendre les tâches futures validées (B-1, B-2).
6. **.memory/decisions.md** : comprendre les décisions actées (70 décisions datées).
7. **dev/docs/JOURNALDEBORD.md / dev/docs/JOURNALDESMODIFS.md** : consulter la chronologie des sessions et la synthèse par commit.
8. **TODO.md** (local, gitignoré, si présent) : consulter le pense-bête immédiat du décideur.
9. **CHANGELOG.md** : suivre ses pointeurs vers les documents d'historique.

Après cette lecture, un contributeur ou un agent connaît le produit, les règles,
l'histoire, les décisions et les tâches futures validées.

## Règles agents

Les règles complètes sont dans `.github/agents/rules/*.instructions.md` (format
Cursor, lu nativement par Cursor). VS Code + Copilot ne les lit PAS
directement : cette section est le résumé opérationnel pour Copilot.
En cas de changement d'une règle, mettre à jour les deux.

- **karpathy-guidelines.instructions.md** : hypothèses explicites avant de coder,
   simplicité (pas d'abstraction spéculative), changements
   chirurgicaux (ne toucher que ce qui est nécessaire), critères
   vérifiables.
- **ponytail.instructions.md** : YAGNI, réutiliser l'existant (stdlib >
   dépendance installée > code nouveau), diff minimal, cause racine
   des bugs (grep les callers).
- **review-simplify-verif.instructions.md** : cycle obligatoire
   Review → Simplify → Verif pour toute nouvelle fonctionnalité.
   Interdit : coder → supposer → passer à autre chose. Statut final
   explicite : OK / BLOQUÉ / PARTIEL.

## Règles non-négociables

1. Toute décision structurante va dans `.memory/decisions.md`, datée, avec Contexte / Décision / Conséquences.
2. Règle de périmètre v1 : toute proposition d'ajout (tool calling, GUI, gestionnaire de téléchargement, agent PC) doit être reportée dans `dev/docs/OBJECTIF.md` section 6 avec version cible. Élargir le périmètre exige une nouvelle entrée dans `decisions.md` validée par le décideur.
3. Aucune décision technique structurante (langage, packaging, dépendance à llamafile) tant que `OBJECTIF.md` contient un `TODO:` non résolu.
4. `AGENTS.md` est la source de vérité des instructions agents. `.github/copilot-instructions.md` et `.memory/instructions.md` ne font que pointer vers lui et rappeler les règles vitales.
5. Intégrité de `.memory/` et `.github/copilot-instructions.md` : aucun
   outil externe (skill, extension, agent de normalisation) ne peut modifier
   un fichier de `.memory/` ou `.github/copilot-instructions.md` sans
   instruction explicite du décideur. L'agent lui-même ne peut pas ajouter,
   modifier ou supprimer une entrée de `.memory/decisions.md` sans instruction
   explicite du décideur dans la conversation courante. Le format de
   `decisions.md` est normatif : chaque entrée commence par
   `## [AAAA-MM-JJ] Titre` et contient les champs Contexte / Décision(s) /
   Conséquences. Après chaque session, l'agent doit vérifier : (a) le nombre
   d'entrées datées, (b) la présence des trois champs dans chaque entrée,
   (c) l'absence d'entrées parasites non datées, (d) l'absence de blocs
   injectés par des outils externes dans `copilot-instructions.md`. En cas
   d'écart, signaler sans corriger — le décideur tranche. Les outils Ponytail
   et hacklm-memory (et tout outil similaire) sont explicitement interdits
   d'action sur `.memory/` et `.github/copilot-instructions.md`. Voir
   `dev/docs/OUTILS_INTRUSIFS.md` pour la liste à jour.
6. Vérification post-session des fichiers sensibles : à la fin de chaque
   session, l'agent doit exécuter `git status --short` et confirmer que les
   SEULS fichiers modifiés sont ceux attendus dans la tâche courante. Toute
   modification non attendue (notamment sur `.memory/`,
   `.github/copilot-instructions.md`, `.github/agents/rules/`,
   `AGENTS.md`) doit être signalée immédiatement au décideur, sans correction
   automatique. Vérifier aussi l'absence de réinjection hacklm-memory dans
   `.github/copilot-instructions.md` et si l'artefact gitignored
   `dev/tests/system-commandline-sentinel-files/` réapparaît après un push ;
   voir `dev/docs/OUTILS_INTRUSIFS.md` pour sa suppression manuelle.
7. Interdiction de réécrire l'historique Git : aucun `git commit
--amend`, `git rebase`, `git push --force` ou `git push
--force-with-lease` ne peut être exécuté sans autorisation explicite
   du décideur dans la conversation courante. Si un commit doit être
   corrigé, créer un NOUVEAU commit par-dessus (ex. "fix: correction
   X"), pas un amend. Si un fichier a été oublié dans un commit
   précédent, créer un NOUVEAU commit, pas un amend. Toute violation
   de cette règle doit être signalée immédiatement au décideur.

## Workflow attendu

Début de session : lire `AGENTS.md`, `.memory/decisions.md`, `.memory/instructions.md`.
Fin de session : ajouter une ligne dans `dev/docs/JOURNALDEBORD.md` (date + fait + prochaine étape).

## Suivi et traçabilité

Ce projet applique neuf règles structurelles pour garantir la traçabilité.
Elles s'appliquent à tous les GO (décideur, IDE, agents IA).

### Règle 1 — TODO de session obligatoire

Toute réponse associée à un GO commence par une TODO explicite et se termine
par la même TODO avec les cases cochées :

```text
TODO Phase X :

- [ ] Tâche 1 : ...
- [ ] Tâche 2 : ...
- [ ] Tâche 3 : ...
```

Les tâches non terminées sont explicitement listées en fin de GO.

### Règle 2 — JOURNALDESMODIFS.md maintenu à chaque commit structurant

Tout commit qui touche du code, de la configuration, de la documentation ou
des dépendances doit avoir une entrée dans `dev/docs/JOURNALDESMODIFS.md`
dans le même commit :

```text
[YYYY-MM-DD] <Titre court>
Commit : <hash court>

Fichiers modifiés : liste
Raison : pourquoi
Impact : code / distribution / tests
```

Pas d'exception : un commit structurant sans entrée dans
`JOURNALDESMODIFS.md` n'est pas terminé.
`JOURNALDEBORD.md` reste la chronologie des sessions (une ligne par session,
datée). `JOURNALDESMODIFS.md` est la synthèse par commit (une entrée par
commit structurant).

### Règle 3 — .gitignore proactif

Tout artefact généré (archives, backups, logs, caches, binaires) doit être
gitignoré dès sa première génération, jamais après avoir été commité par
erreur. `.gitignore` doit couvrir :

```text
dist/, backup/, *.zip, *.gguf,
*.log, __pycache__/, .pytest_cache/,
citadelle_data/, dev/tools/vendor/
```

### Règle 4 — Aucune modification hors GO

Aucune modification (fichier, commit, suppression, renommage) ne doit se
produire en dehors d'un GO validé. Si un besoin émerge en cours de route :
STOP, rédiger un GO complémentaire, puis l'exécuter.

Corollaires :

- Pas de `git commit --amend`, `git rebase` ni force-push.
- Pas de suppression de fichier suivi sans `git rm`.
- Pas de création de fichier dans un dossier non couvert par `.gitignore`
  sans vérifier les règles d'exclusion.

### Règle 5 — TODO.md maintenu à chaque GO

`TODO.md` (racine, gitignoré) liste les tâches à venir en ordre
anti-chronologique (plus récent en haut). À chaque fin de GO : la tâche
terminée est retirée, la suivante promue, les tâches futures restent, les
tâches abandonnées sont tracées dans `JOURNALDEBORD.md`.

`TODO.md` n'est jamais commité, jamais publié dans l'archive, jamais référencé
dans les documents publics. Il vit exclusivement en local.

### Règle 6 — ROADMAP.md maintenue à chaque phase majeure

Mettre à jour `dev/docs/ROADMAP.md` à la clôture d'une phase majeure pour
consigner son objectif, son livrable et les commits et décisions associés.
Ne pas créer une entrée par GO; les phases majeures restent celles validées
dans la Roadmap.

### Règle 7 — BACKLOG.md maintenu (versionné)

`dev/docs/BACKLOG.md` est le plan de route daté des tâches validées,
versionné et public sur GitHub. Chaque tâche décrit son statut, sa date de
décision, ses dépendances, son périmètre, ses questions ouvertes et son
moment de traitement (à décider).

À chaque nouvelle tâche validée, ajouter une entrée datée dans `BACKLOG.md`.
À chaque clôture, mettre son statut à jour. Ne pas créer une entrée par GO.

Relation avec `TODO.md` (local, gitignoré) :

- `BACKLOG.md` : plan versionné et daté, public, tâches validées uniquement.
- `TODO.md` : pense-bête immédiat, local, pouvant contenir des notes internes.

Ne pas dupliquer dans `BACKLOG.md` le détail des décisions de
`.memory/decisions.md`.

### Règle 8 — CHANGELOG.md maintenu (pointeur)

`CHANGELOG.md` (racine) est un pointeur maintenu vers les documents
d'historique réels : `JOURNALDEBORD.md`, `JOURNALDESMODIFS.md`, `ROADMAP.md`,
`BACKLOG.md` et `.memory/decisions.md`.

Il ne duplique pas le contenu des journaux. En cas de déplacement ou de
renommage d'un de ces fichiers, mettre à jour `CHANGELOG.md` dans le même
commit.

### Règle 9 — Traçabilité immédiate dans TODO.md

Toute nouvelle décision, architecture ou proposition actée pendant une
conversation ou un GO doit être intégrée à `TODO.md` (local, gitignoré)
immédiatement, sans attendre la fin du GO.

Cela évite la perte de contexte entre deux sessions et garantit que les
décisions sont tracées au moment où elles sont prises.

`TODO.md` reste la source de vérité pour les tâches à venir. Une décision
actée mais non planifiée doit apparaître dans la section « À trancher » de
`TODO.md`.

## Périmètre et non-objectifs

- V3.0 : pas de routes d'administration web.
- V3.1 : routes admin, HTTPS, CSRF et rate limiting.
- V3.2 : multi-admin.
- Pas de tool calling, d'agent PC ni de modification du code C++ de llamafile.

## Mémoire projet (.memory/)

Le dossier `.memory/` contient la mémoire longue des agents, complémentaire à `AGENTS.md`. Chaque contenu vit à un seul endroit; ne pas dupliquer les règles déjà définies ici ou dans `.github/copilot-instructions.md`.

| Fichier | Contenu | À lire quand |
| --- | --- | --- |
| `.memory/decisions.md` | Décisions actées (70) | Avant toute action structurante |
| `.memory/instructions.md` | Rappel et pointeurs | En début de session |
| `.memory/preferences.md` | Préférences du décideur | Avant de proposer une solution |
| `.memory/quirks.md` | Pièges et particularités | Avant de coder |
| `.memory/security.md` | Règles de sécurité | Avant tout code de sécurité |
| `.memory/cleanup.log` | Artefact d'outil, ignoré par Git | Ne pas versionner |

Avant d'ajouter une règle dans `.memory/`, vérifier qu'elle n'existe pas déjà dans `AGENTS.md` ou `.github/copilot-instructions.md`; si elle existe, ajouter un pointeur plutôt que la recopier.

**Pattern documentaire** : garder courts les fichiers fréquemment lus et les faire pointer vers les détails. Si un contrat dépasse environ 400 lignes, le scinder au cas par cas en `<NOM>.md` (principal, pointeur et résumé) et `<NOM>_V<version>.md` (détails par version). Voir aussi `.memory/preferences.md`.
