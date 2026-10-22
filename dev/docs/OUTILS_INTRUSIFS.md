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
- **Mesure** : interdit d'action sur `.memory/` (AGENTS.md règle 5). Vérifier
  après chaque session l'intégrité de `decisions.md` (AGENTS.md règle 6).

## hacklm-memory

- **Source** : extension VS Code (Visual Studio Marketplace).
- **Comportement par défaut** : injecte un bloc
  `<!-- hacklm-memory:start --> ... end -->` dans
  `.github/copilot-instructions.md` (setting `manageInstructionFile: true`
  par défaut).
- **Incident** : 2026-10-17, injection de 40 lignes. Restauré via
  `git restore`.
- **Configuration actuelle (2026-10-21)** : setting
  `hacklm-memory.manageInstructionFile = false`. L'extension ne modifie plus
  `copilot-instructions.md`. Elle continue d'apprendre passivement dans
  `.memory/` (comportement de l'extension, non intrusif pour notre projet).
- **Fichiers sensibles** : `.github/copilot-instructions.md` (protégé par la
  configuration), `.memory/*.md` (l'extension peut écrire si
  `autoApproveStore` est activé — actuellement `false`).
- **Mesure de sécurité** : si un bloc `<!-- hacklm-memory:start -->`
  réapparaît dans `copilot-instructions.md`, exécuter
  `git restore .github/copilot-instructions.md` et vérifier la configuration
  VS Code.

## system-commandline-sentinel-files (.NET / Git Credential Manager)

- **Source** : artefact .NET (Git Credential Manager).
- **Comportement** : réapparaît automatiquement après certains pushs dans
  `dev/tests/system-commandline-sentinel-files/`.
- **Mesure** : gitignored. Supprimer manuellement s'il réapparaît (pas de
  commit nécessaire). Voir `.memory/quirks.md`.

## Garde-fous généraux

1. Vérification post-session systématique (AGENTS.md règle 6) : `git status
--short` doit montrer uniquement les fichiers attendus.
2. Si un outil intrusif est identifié, ajouter une entrée dans ce document
   et mettre à jour les garde-fous des règles 5 et 6 d'AGENTS.md.
3. Si un outil injecte du contenu malgré tout, restaurer la version HEAD
   (`git restore <fichier>`) et documenter l'incident dans `decisions.md`.
4. Envisager à terme un hook Git de pré-commit qui refuse les modifications
   non formatées de `decisions.md` ou les blocs `<!-- hacklm-memory:* -->`
   dans `copilot-instructions.md`.

## Outils à surveiller (non confirmés intrusifs)

Aucun pour l'instant. Si un outil est suspecté, l'ajouter ici avec la mention
"à confirmer" et documenter les observations.
