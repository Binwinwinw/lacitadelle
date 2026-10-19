---
name: Docs Cleaner
description: Nettoie OBJECTIF, GIT_STRATEGY, BASE_LLAMAFILE et VENDOR_STRATEGY
user-invocable: false
tools: ["read", "edit"]
---

Corrige uniquement les quatre documents suivants :

- `dev/docs/OBJECTIF.md` : retire la mention opérationnelle de `main/` en
  lecture seule; conserve le périmètre du pipeline de fabrication.
- `dev/docs/GIT_STRATEGY.md` : retire les mentions obsolètes de l'option C,
  de l'ignorance et du re-téléchargement du dépôt local; reflète la stratégie
  actuelle des assets upstream précompilés vendorisés. Évite toute mention
  littérale `main/` dans le texte opérationnel.
- `dev/docs/BASE_LLAMAFILE.md` : retire les options de compilation locale et
  hybride qui dépendent du dépôt supprimé; ne garde que l'option X actuelle
  (mode external, binaire précompilé), avec les décisions et assets V1 utiles.
- `dev/tools/VENDOR_STRATEGY.md` : retire les mentions de `main/` comme
  dépendance externe et conserve les règles de vendorisation actuelles.

Ne modifie aucun autre fichier et ne change pas les décisions techniques
actuelles. Retourne les quatre diffs.
