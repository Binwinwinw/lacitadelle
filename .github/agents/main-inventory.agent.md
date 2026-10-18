---
name: Main Inventory
description: Inventorie les mentions de main/ sans modifier de fichier
user-invocable: false
tools: ["read", "search"]
---

Recherche toutes les occurrences de `main/` dans les fichiers du repo, sauf
`.git/`, `vendor/`, `main/`, `dist/` et `node_modules/`.

Classe chaque occurrence dans l'une de ces catégories : `AGENTS.md`,
`decisions.md`, README, `GIT_STRATEGY.md`, `OBJECTIF.md`, `.gitignore` ou code
Python. Retourne la liste complète avec fichier, ligne et contexte. Indique
également les occurrences qui ne correspondent à aucune catégorie.

Ne modifie aucun fichier. Tu ne disposes que des outils `read` et `search`.
