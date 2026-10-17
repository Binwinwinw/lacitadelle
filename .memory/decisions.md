# Decisions

Décisions architecturales et structurantes du projet La Citadelle.
Format normatif : chaque entrée commence par `## [AAAA-MM-JJ] Titre` et contient
des champs explicites (Contexte, Décision(s), Conséquences).
Aucun outil externe n'est autorisé à reformater, fusionner ou normaliser ce fichier
sans instruction explicite du décideur (voir AGENTS.md, règle non-négociable n°6).

## [2026-10-17] Objectif v1 : Pocket Chat (llamafile + modèle embarqué, interface texte)

**Contexte** : llamafile fournit le format exécutable unique et le runtime C++. Python ne peut pas produire un exécutable multi-OS unique. La Citadelle utilise donc Python comme outil de FABRICATION, pas comme runtime livré.

**Décision** : v1 = fichier `.llamafile` unique, modèle 1B-3B embarqué, interface texte de llamafile. Pas de tool calling, pas de téléchargement de modèles dans l'app, pas de GUI graphique.

**Conséquences** : le succès de v1 se mesure par « un non-technique double-clique et obtient une conversation ». Tout le reste est hors périmètre v1.

## [2026-10-17] Python = fabrication uniquement

**Contexte** : Python ne peut pas produire un binaire APE multi-OS. llamafile (C++/cosmocc) fournit ce binaire. La Citadelle a besoin d'un pipeline pour transformer un GGUF en `.llamafile` prêt à l'emploi.

**Décision** : aucun code Python ne sera exécuté chez l'utilisateur final. Le pipeline Python prend un GGUF en entrée et produit un `.llamafile` exécutable.

**Conséquences** : l'utilisateur final ne dépend pas de Python. Le pipeline Python vit côté fabrication (dev/tools, dev/scripts). Aucune dépendance Python ne doit fuiter dans l'artefact livré.

## [2026-10-17] Stratégie Git : Option C + dépôt distant + .gitignore minimal

**Contexte** : projet pas sous Git, socle documentaire terminé, prochain chantier = mise sous version.

**Décisions** :

1. `main/` ignoré via `.gitignore`, re-téléchargé par script de bootstrap (dépendance externe en lecture seule, pas du code à nous).
2. Dépôt distant dès le départ (GitHub privé, nom proposé : `lacitadelle`).
3. `.gitignore` couvre Python, modèles GGUF, artefacts llamafile, build, et `main/`.

**Document de cadrage** : `dev/docs/GIT_STRATEGY.md`.

**Conséquences** : aucun fichier de `main/` ne sera versionné. Un script de bootstrap devra être créé avant tout clone sur une nouvelle machine. La mise sous Git effective (`git init`, création du dépôt distant, premier commit) est une tâche distincte, à exécuter sur instruction explicite du décideur.

## [2026-10-17] Compléments de mise sous Git

**Contexte** : stratégie Git actée (Option C, dépôt distant, `.gitignore` minimal). Dépôt distant déjà créé par le décideur.

**Décisions** :

1. Branche par défaut : `main`.
2. Dépôt distant : `https://github.com/Binwinwinw/lacitadelle` (privé), déjà créé par le décideur. La liaison via `git remote add origin` sera faite dans le temps 2 de la tâche de mise sous Git.
3. Premier commit : tout le socle actuel (README, `AGENTS.md`, `.memory/`, `dev/docs/`, `.github/`, `.gitignore`). `main/` est exclu via `.gitignore`.
4. RÈGLE NON-NÉGOCIABLE : `main/` ne doit JAMAIS apparaître sur GitHub. Le `.gitignore` garantit cette exclusion. Aucune exception sans décision explicite du décideur consignée dans ce fichier.

**Conséquences** : la mise sous Git est découpée en deux temps. Temps 1 (local) : `git init`, vérifications `git status`, `git add .`, commit. Temps 2 (réseau) : `git remote add origin`, `git push -u origin main`. Chaque temps est une tâche séparée, exécutée sur instruction explicite du décideur.

## [2026-10-17] Chantier base llamafile — 1 décision ouverte

**Contexte** : projet sous Git et sur GitHub, socle documentaire terminé, prochaine étape = construction du pipeline de fabrication `.llamafile`. Question préalable : où récupérer le binaire llamafile qui sert de base à l'assemblage.

**Décision(s)** : en attente. Trois options documentées dans `dev/docs/BASE_LLAMAFILE.md` (X : binaire pré-compilé, Y : compilation depuis `main/`, Z : hybride).

**Conséquences** : aucun code ne peut être écrit tant que cette décision n'est pas prise. Le pipeline Python dépend directement du binaire choisi.
