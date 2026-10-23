# La Citadelle — Instructions agents

## Identité du projet

Application locale pour public non-technique : runtime llamafile-thin et GGUF
téléchargés séparément, proxy Python et webchat. La distribution utilisateur
est une archive ZIP autonome, sans Git. Le projet s'appuie sur
mozilla-ai/llamafile.

## État actuel

V3.0 fonctionnelle localement. 73 tests permanents. `install.bat` télécharge
llamafile-thin et le GGUF; `lancer.bat` démarre le runtime et le proxy. La
distribution est `lacitadelle-distribution.zip`, sans Git ni binaires intégrés. La
release GitHub v0.1.0 est obsolète et doit être dépréciée manuellement.

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

## Où trouver quoi

- Cadre produit et périmètre : `dev/docs/OBJECTIF.md`
- Décisions : `.memory/decisions.md`
- Journal de bord : `dev/docs/JOURNALDEBORD.md`
- Modifications et TODO vivant : `dev/docs/JOURNALDESMODIFS.md`
- Code de production : `dev/` (à venir)

## Périmètre et non-objectifs

- V3.0 : pas de routes d'administration web.
- V3.1 : routes admin, HTTPS, CSRF et rate limiting.
- V3.2 : multi-admin.
- Pas de tool calling, d'agent PC ni de modification du code C++ de llamafile.

## Mémoire projet (.memory/)

Le dossier `.memory/` contient la mémoire longue des agents, complémentaire à `AGENTS.md`. Chaque contenu vit à un seul endroit; ne pas dupliquer les règles déjà définies ici ou dans `.github/copilot-instructions.md`.

| Fichier | Contenu | À lire quand |
| --- | --- | --- |
| `.memory/decisions.md` | Décisions actées (18) | Avant toute action structurante |
| `.memory/instructions.md` | Rappel et pointeurs | En début de session |
| `.memory/preferences.md` | Préférences du décideur | Avant de proposer une solution |
| `.memory/quirks.md` | Pièges et particularités | Avant de coder |
| `.memory/security.md` | Règles de sécurité | Avant tout code de sécurité |
| `.memory/cleanup.log` | Artefact d'outil, ignoré par Git | Ne pas versionner |

Avant d'ajouter une règle dans `.memory/`, vérifier qu'elle n'existe pas déjà dans `AGENTS.md` ou `.github/copilot-instructions.md`; si elle existe, ajouter un pointeur plutôt que la recopier.

**Pattern documentaire** : garder courts les fichiers fréquemment lus et les faire pointer vers les détails. Si un contrat dépasse environ 400 lignes, le scinder au cas par cas en `<NOM>.md` (principal, pointeur et résumé) et `<NOM>_V<version>.md` (détails par version). Voir aussi `.memory/preferences.md`.
