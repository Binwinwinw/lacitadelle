---
name: Decisions Checker
description: Vérifie que decisions.md documente l'obsolescence selon Solution A
user-invocable: false
tools: ['read', 'edit']
---

Vérifie uniquement `.memory/decisions.md`.

- Recherche une entrée datée couvrant l'obsolescence des décisions qui
  mentionnaient `main/`.
- Si l'entrée Solution A du Temps 1 existe et dit de conserver les
  historiques sans les réécrire, ne modifie rien et retourne « aucune
  modification ».
- Si elle manque ou est incomplète, ajoute seulement une nouvelle entrée
  datée en respectant le format normatif et Solution A. Ne réécris jamais
  les entrées historiques.
- Ne modifie aucun autre fichier.

Retourne le diff ou « aucune modification ».