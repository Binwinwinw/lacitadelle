---
name: README Cleaner
description: Nettoie README, retire les mentions obsolètes de main/ et corrige l’état V1
user-invocable: false
tools: ['read', 'edit']
---

Corrige uniquement `README`.

- Retire toutes les mentions littérales de `main/`.
- Remplace l'état « Fabrication du .llamafile : à venir » par le statut
  réel : fabrication V1 fonctionnelle en mode external.
- Garde les instructions d'installation et ajoute Python 3.10+ aux
  prérequis si nécessaire.
- Conserve la mention d'inspiration mozilla-ai/llamafile.
- Ne modifie aucune autre section ni aucun autre fichier.

Retourne le diff.