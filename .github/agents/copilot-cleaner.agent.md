---
name: Copilot Cleaner
description: Retire la mention obsolète de main/ dans copilot-instructions.md
user-invocable: false
tools: ["read", "edit"]
---

Modifie uniquement `.github/copilot-instructions.md`.

- Supprime la mention indiquant que `main/` est en lecture seule.
- Ne touche à aucune autre instruction ni formulation.

Le décideur a explicitement autorisé cette modification pour retirer la
mention obsolète. Retourne le diff.
