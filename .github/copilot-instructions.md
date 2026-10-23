# La Citadelle — contexte Copilot

La Citadelle est une application locale de chat IA : le runtime llamafile-thin
et le modèle GGUF sont téléchargés séparément, puis un proxy Python sert un
webchat local. Le modèle s'exécute sur la machine de l'utilisateur.

## Références

- `AGENTS.md` : règles de travail et de suivi des GO.
- `.memory/decisions.md` : décisions actées.
- `dev/docs/ARCHITECTURE.md` : architecture et flux.
- `dev/docs/OBJECTIF.md` : produit et périmètre.

## Rappels obligatoires

1. Chaque GO commence et se termine par la même TODO de session; cocher les
   tâches terminées et lister les tâches restantes.
2. Chaque commit structurant inclut son entrée dans
   `dev/docs/JOURNALDESMODIFS.md`; le journal de bord trace les sessions.
3. Ignorer les artefacts générés dès leur création selon `.gitignore`.
4. Ne rien modifier hors du GO validé; signaler toute modification inattendue
   sans la corriger automatiquement.

Consulter `AGENTS.md` avant d'agir et respecter les protections de `.memory/`
et de `.github/copilot-instructions.md`.
