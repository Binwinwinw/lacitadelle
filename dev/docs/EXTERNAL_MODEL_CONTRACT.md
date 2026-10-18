# Contrat du mode external

## Contexte

La v0 de La Citadelle embarquait le modèle Qwen3-1.7B Q4_K_M dans le
.llamafile (1.33 Go). Le décideur a décidé de passer à un mode
"external" : le .llamafile ne contient plus que le runtime llamafile
(~44 Mo), et pointe vers un GGUF externe au démarrage.

## Avantages

- .llamafile distribué : ~44 Mo au lieu de 1.33 Go.
- Changement de modèle possible sans rebuild.
- Compatible Windows 4 Go limit (contourne la limite pour les gros
  modèles futurs).
- Prépare la mémoire SQLite (dossier citadelle_data/ à côté).
- Prépare la détection GPU (v2).

## Décisions actées

1. Le .llamafile ne contient plus le modèle.
2. Le GGUF vit dans `dev/tools/vendor/llamafile/Qwen3-1.7B-Q4_K_M.gguf`,
   téléchargé une fois par bootstrap (asset `qwen3-1.7b-q4km`,
   `required: true`).
3. Le .args contient un chemin RELATIF vers le GGUF :
   `-m ../dev/tools/vendor/llamafile/Qwen3-1.7B-Q4_K_M.gguf` (chemin exact
   à calculer selon l'emplacement final du .llamafile, voir Tâche 2.3).
4. Politique de conservation : les versions futures ne suppriment pas
   les modèles précédents sans confirmation explicite de l'utilisateur.
5. Nom de sortie : `dist/lacitadelle.llamafile.exe` sous Windows,
   `dist/lacitadelle.llamafile` sous POSIX, avec `chmod +x` si applicable.
6. Point d'entrée : `dev/tools/setup_lacitadelle.py` (renommage de
   `build_llamafile.py`). Détecte la plateforme en premier, orchestre
   bootstrap + build + renommage.

## Comportement si le GGUF est absent

Au lancement, llamafile affichera une erreur claire (fichier introuvable).
Un README.txt dans `vendor/llamafile/` documentera la procédure
(lancer `python dev/tools/setup_lacitadelle.py`).

## Comportement si le .llamafile existe déjà

Le script affiche `overwriting existing: <chemin>` et remplace après
succès. Pas de perte silencieuse.

## Impact sur le code

- `dev/tools/build_llamafile.py` → renommé `dev/tools/setup_lacitadelle.py`.
- `bootstrap.py` : inchangé (asset `qwen3-1.7b-q4km` passe à
  `required: true`).
- `.args` : ne contient plus `-m /zip/...` mais `-m <chemin relatif>`.

## Non-objectifs (v1)

- Pas de détection GPU.
- Pas de switch multi-modèles.
- Pas de prompt système.
