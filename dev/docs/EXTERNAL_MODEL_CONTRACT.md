# Contrat du mode external

> **HISTORIQUE** — contrat d'analyse V1/V2. Le parcours actuel est décrit dans [BOOTSTRAP_CONTRACT.md](../tools/BOOTSTRAP_CONTRACT.md) et [README.md](../../README.md). Conservé pour traçabilité.

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

1. Le runtime et le modèle sont téléchargés séparément.
2. Le GGUF vit dans `dev/tools/vendor/llamafile/Qwen3-1.7B-Q4_K_M.gguf`,
   téléchargé une fois par bootstrap (asset `qwen3-1.7b-q4km`,
   `required: true`).
3. `lancer.bat` passe au runtime le chemin du GGUF dans
   `dev/tools/vendor/llamafile/`.
4. Politique de conservation : les versions futures ne suppriment pas
   les modèles précédents sans confirmation explicite de l'utilisateur.
5. Le runtime téléchargé est placé dans `dist/` et nommé `llamafile.exe`
   sous Windows.

## Comportement si le GGUF est absent

Au lancement, llamafile affichera une erreur claire (fichier introuvable).
Le bootstrap télécharge les assets requis depuis leurs sources configurées.

## Comportement si le .llamafile existe déjà

Le script affiche `overwriting existing: <chemin>` et remplace après
succès. Pas de perte silencieuse.

## Impact sur le code

- Le bootstrap télécharge le runtime et le GGUF séparément; tous deux sont
  requis dans `llamafile_config.json`.
- Le runtime est lancé avec le chemin local du modèle externe.

## Non-objectifs (v1)

- Pas de détection GPU.
- Pas de switch multi-modèles.
- Pas de prompt système.
