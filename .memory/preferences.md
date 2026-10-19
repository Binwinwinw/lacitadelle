# Préférences du décideur

Ce fichier conserve les préférences de travail qui ne sont pas déjà définies dans `AGENTS.md` ou `.github/copilot-instructions.md`. Les décisions actées vivent dans `decisions.md`.

## Langue et communication

- Français pour la documentation et les échanges.
- Pas d'emoji dans le code, les commits ou les fichiers du projet.
- Coller les sorties brutes des commandes demandées, sans les remplacer par un résumé.
- Toujours indiquer le prochain Next Move en fin de rapport.
- Pour le cycle Review → Simplify → Verif et le statut final, suivre `AGENTS.md`.

## Style de code

- JavaScript et CSS sans framework : vanilla uniquement.
- Pour YAGNI, les dépendances et les changements chirurgicaux, suivre les règles agents de `AGENTS.md` et les fichiers `.github/agents/rules/*.instructions.md`.

## Git

- Messages de commit au format `type: description courte` (`feat`, `fix`, `docs`, `chore`, `refactor`, `test`).
- Commits atomiques : un commit par intention.
- Pour l'interdiction de réécrire l'historique, appliquer `AGENTS.md`.

## Fichiers protégés

Appliquer la règle de protection définie dans `AGENTS.md`; la liste n'est pas recopiée ici.

## Pattern documentaire

Le pattern et le seuil de scission des contrats sont définis dans `AGENTS.md`, section « Mémoire projet ».
