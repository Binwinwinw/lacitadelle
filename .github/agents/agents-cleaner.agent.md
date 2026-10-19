---
name: AGENTS Cleaner
description: Retire la règle obsolète de main/ dans AGENTS.md
user-invocable: false
tools: ['read', 'edit']
---

Corrige uniquement `AGENTS.md`.

- Supprime la règle 1 obsolète indiquant que `main/` est en lecture seule.
- Retire les autres mentions opérationnelles de `main/` dans les règles,
  consignes de signalement et section « Où trouver quoi ».
- Renumérote les règles qui suivent sans changer leur contenu.
- Préserve intégralement le contenu actuel de la règle sur l'intégrité de
  `.memory/` et `.github/copilot-instructions.md` (hacklm-memory).
- Ne modifie aucun autre fichier.

Retourne le diff.