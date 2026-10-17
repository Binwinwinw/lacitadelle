# La Citadelle — Instructions agents

## Identité du projet

Application de poche sous forme de fichier `.llamafile` unique, avec modèle 1B-3B
embarqué, interface texte, destinée à un public non-technique. Inspiré de
mozilla-ai/llamafile mais centré sur la fabrication de llamafiles personnalisés.

## État actuel

Socle documentaire en cours. Aucune fonctionnalité exécutable. Pas encore de
dépôt Git initialisé.

## Règles non-négociables

1. `main/` est en LECTURE SEULE. Aucune modification, aucun ajout, aucune suppression.
2. Toute décision structurante va dans `.memory/decisions.md`, datée, avec Contexte / Décision / Conséquences.
3. Règle de périmètre v1 : toute proposition d'ajout (tool calling, GUI, gestionnaire de téléchargement, agent PC) doit être reportée dans `dev/docs/OBJECTIF.md` section 6 avec version cible. Élargir le périmètre exige une nouvelle entrée dans `decisions.md` validée par le décideur.
4. Aucune décision technique structurante (langage, packaging, dépendance à llamafile) tant que `OBJECTIF.md` contient un `TODO:` non résolu.
5. `AGENTS.md` est la source de vérité des instructions agents. `.github/copilot-instructions.md` et `.memory/instructions.md` ne font que pointer vers lui et rappeler les règles vitales.
6. Intégrité de `.memory/` : aucun outil externe (skill, extension, agent de normalisation) ne peut modifier un fichier de `.memory/` sans instruction explicite du décideur. L'agent lui-même ne peut pas ajouter, modifier ou supprimer une entrée de `.memory/decisions.md` sans instruction explicite du décideur dans la conversation courante. Le format de `decisions.md` est normatif : chaque entrée commence par `## [AAAA-MM-JJ] Titre` et contient les champs Contexte / Décision(s) / Conséquences. Après chaque session, l'agent doit vérifier : (a) le nombre d'entrées datées, (b) la présence des trois champs dans chaque entrée, (c) l'absence d'entrées parasites non datées. En cas d'écart, signaler sans corriger — le décideur tranche. Le skill Ponytail (et tout outil similaire) est explicitement interdit d'action sur `.memory/`.

## Workflow attendu

Début de session : lire `AGENTS.md`, `.memory/decisions.md`, `.memory/instructions.md`.
Fin de session : ajouter une ligne dans `dev/docs/JOURNALDEBORD.md` (date + fait + prochaine étape).

## Où trouver quoi

- Cadre produit et périmètre : `dev/docs/OBJECTIF.md`
- Décisions : `.memory/decisions.md`
- Journal de bord : `dev/docs/JOURNALDEBORD.md`
- Modifications et TODO vivant : `dev/docs/JOURNALDESMODIFS.md`
- Code de production : `dev/` (à venir)
- Runtime llamafile : `main/` (lecture seule)

## Non-objectifs v1

- PAS de téléchargement de modèles depuis l'interface (reporté v2).
- PAS de tool calling / agent / action sur l'ordinateur (reporté v3+).
- PAS de GUI graphique (v1 = interface texte de llamafile).
- PAS de Python côté utilisateur.
- PAS de modification du code C++ de llamafile en v1.
