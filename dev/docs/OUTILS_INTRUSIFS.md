# Outils intrusifs identifiés

Ce document liste les outils d'environnement (skills, extensions,
automatisations) qui modifient des fichiers du projet sans instruction
explicite du décideur. Chaque outil identifié doit être surveillé et,
si possible, désactivé ou restreint.

## Ponytail

- **Source** : skill installé dans VS Code (DietrichGebert/ponytail).
- **Comportement identifié** : normalise les lignes, fusionne des entrées
  similaires, injecte du contenu dans les fichiers `.memory/*.md`.
- **Incident** : 2026-10-17, fusion d'entrées dans `decisions.md` et
  reformatage des fichiers `.memory/`, documenté dans `.memory/cleanup.log`.
- **Fichiers sensibles** : `.memory/*.md`.
- **Mesure** : interdit d'action sur `.memory/` (AGENTS.md règle 6). Vérifier
  après chaque session l'intégrité de `decisions.md`.

## hacklm-memory

- **Source** : extension / outil d'environnement (identifié par les marqueurs
  `<!-- hacklm-memory:start -->` / `<!-- hacklm-memory:end -->`).
- **Comportement identifié** : injecte un bloc d'instructions dans
  `.github/copilot-instructions.md`, avec instructions `storeMemory`
  contradictoires avec la règle 6 d'`AGENTS.md`.
- **Incident** : 2026-10-17, injection de 40 lignes dans
  `copilot-instructions.md`, restauré par `git restore`. Documenté dans
  `decisions.md`.
- **Fichiers sensibles** : `.github/copilot-instructions.md`, potentiellement
  `.memory/*.md`.
- **Mesure** : interdit d'action sur `.github/copilot-instructions.md` et
  `.memory/` (AGENTS.md règle 6). Vérifier après chaque session l'absence de
  blocs `<!-- hacklm-memory:* -->` dans `copilot-instructions.md`.

## Garde-fous généraux

1. Vérification post-session systématique (AGENTS.md règle 7) : `git status
--short` doit montrer uniquement les fichiers attendus.
2. Si un outil intrusif est identifié, ajouter une entrée dans ce document
   et une mention dans AGENTS.md règle 6.
3. Si un outil injecte du contenu malgré tout, restaurer la version HEAD
   (`git restore <fichier>`) et documenter l'incident dans `decisions.md`.
4. Envisager à terme un hook Git de pré-commit qui refuse les modifications
   non formatées de `decisions.md` ou les blocs `<!-- hacklm-memory:* -->`
   dans `copilot-instructions.md`.

## Outils à surveiller (non confirmés intrusifs)

Aucun pour l'instant. Si un outil est suspecté, l'ajouter ici avec la mention
"à confirmer" et documenter les observations.
