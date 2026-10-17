# Stratégie Git — La Citadelle

## Contexte

Le projet n'est pas encore sous Git. `main/` est un fork de mozilla-ai/llamafile
en lecture seule. Le socle documentaire est terminé. Ce document acte les décisions
prises par le décideur le 2026-10-17.

## Décision 1 — Traitement de `main/`

Option retenue : **C** — `main/` est ignoré via `.gitignore` et re-téléchargé
par un script de bootstrap (`dev/tools/bootstrap.py`, à créer en temps voulu).
Justification : `main/` est une dépendance externe en lecture seule, pas du code
à nous. Le repo reste léger et honnête sur son périmètre. Un script de bootstrap
sera de toute façon nécessaire pour télécharger les modèles GGUF — les deux
iront ensemble. **Règle non-négociable du décideur (2026-10-17) : `main/` ne
doit JAMAIS apparaître sur GitHub.** Le `.gitignore` garantit cette exclusion.
Cette règle est structurante et ne peut être remise en cause sans décision
explicite du décideur.

## Décision 2 — Dépôt distant

Option retenue : **dépôt distant dès le départ**, GitHub privé, nom proposé
`lacitadelle`. Dépôt créé par le décideur le 2026-10-17 :
`https://github.com/Binwinwinw/lacitadelle` (privé). La liaison via
`git remote add origin` sera faite dans une tâche ultérieure.

## Décision 3 — `.gitignore` initial

Contenu retenu :

- Python : `__pycache__/`, `.venv/`, `venv/`, `*.pyc`, `*.pyo`, `.pytest_cache/`
- Modèles : `*.gguf`, `*.safetensors`
- Artefacts llamafile : `*.llamafile`
- Build : `build/`, `dist/`, `*.egg-info/`
- Dépendance externe : `main/`
- OS / IDE : `.DS_Store`, `Thumbs.db`, `.vscode/`, `.idea/`

`.vscode/` est ignoré globalement. Des exceptions ciblées pourront être ajoutées
si le décideur souhaite versionner des configurations partagées.

## Actions restantes (hors de cette tâche)

### Fait

1. Dépôt GitHub privé créé par le décideur le 2026-10-17 : `https://github.com/Binwinwinw/lacitadelle`.
2. Fichier `.gitignore` à la racine validé.

### Temps 1 — Mise sous Git locale (tâche suivante, sur instruction explicite du décideur)

1. `git init` à la racine du projet.
2. `git status` — vérifier qu'aucun fichier de `main/` n'apparaît.
3. `git add .`.
4. `git status` — vérifier que seuls les fichiers du socle sont stagés, aucun fichier de `main/`.
5. `git commit -m "Initial commit: project skeleton"`.

### Temps 2 — Liaison distante (tâche séparée, après validation du commit local)

1. `git remote add origin https://github.com/Binwinwinw/lacitadelle`.
2. `git push -u origin main`.

### Phase de développement (plus tard, pas maintenant)

1. Créer `dev/tools/bootstrap.py` pour re-télécharger `main/` sur une nouvelle machine.

### Paramètres

- Branche par défaut : `main`.
- Premier commit : tout le socle actuel (README, `AGENTS.md`, `.memory/`, `dev/docs/`, `.github/`, `.gitignore`). `main/` exclu par `.gitignore` (règle non-négociable).
