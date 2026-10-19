# Instructions agents — pointeur

La source de vérité des instructions structurelles est `AGENTS.md` à la racine. Le lire intégralement avant toute action.

## Fichiers de mémoire longue

À consulter selon le contexte :

- `.memory/decisions.md` : décisions actées, avant toute action structurante.
- `.memory/preferences.md` : préférences du décideur (langue, communication, Git).
- `.memory/quirks.md` : pièges et particularités, avant de coder.
- `.memory/security.md` : règles de sécurité, avant tout code de sécurité.
- `.memory/cleanup.log` : artefact d'outil ignoré par Git; ne pas versionner.

## Workflow

- Avant toute modification structurante, consulter `.memory/decisions.md`.
- Toute session se termine par une entrée d'une ligne dans `dev/docs/JOURNALDEBORD.md`.
- Appliquer le cycle Review → Simplify → Verif pour toute nouvelle fonctionnalité (voir `.github/agents/rules/review-simplify-verif.instructions.md`).

## Pattern documentaire

Voir `AGENTS.md`, section « Mémoire projet ».
