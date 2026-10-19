# Base llamafile — mode external v1

## Décision

La V1 utilise un runtime llamafile précompilé et un GGUF externe. Le fichier
distribué contient le runtime et ses arguments par défaut, pas le modèle. Le
GGUF reste dans `dev/tools/vendor/llamafile/` et peut être mis à jour sans
réassembler le runtime.

## Version et assets retenus

**Version runtime** : `0.10.6` (release du 15 septembre 2026).

- Runtime : `llamafile-0.10.6-thin`, CPU only, environ 44 Mo.
- Assembleur : `zipalign-0.10.6`.
- Modèle externe : `Qwen3-1.7B-Q4_K_M.gguf`.

Les trois assets sont téléchargés et vérifiés par SHA-256 selon
`dev/tools/llamafile_config.json`.

**Checksums SHA-256** :

- Runtime thin : `756bf97febae557084e8ced9bde7a1cb0c7f6ce778530d582afa219406237a50`
- `zipalign` : `7eac59c658226027b365d92131babf06341f746fb20c0db33115bbdf5c5c6c4b`
- GGUF Qwen3 : `16da7ba1721b1620fa843e0978badd3d93756274fd209a01874b37e29750e207`

**URLs des binaires upstream** :

- Runtime thin : `https://github.com/mozilla-ai/llamafile/releases/download/0.10.6/llamafile-0.10.6-thin`
- `zipalign` : `https://github.com/mozilla-ai/llamafile/releases/download/0.10.6/zipalign-0.10.6`
- GGUF Qwen3 : `https://huggingface.co/smarttasks/Qwen3-1.7B-GGUF/resolve/4b9aca3fb9c8fcace456430347c2fc34752e515f/Qwen3-1.7B-Q4_K_M.gguf`

## Assemblage V1

`dev/tools/setup_lacitadelle.py` copie le runtime puis utilise `zipalign`
pour y intégrer uniquement `.args`. Le GGUF n'est pas inclus dans l'archive ;
`.args` le référence par son chemin local `dev/tools/vendor/llamafile/`.
`lancer.bat` démarre le serveur depuis la racine du projet.

Le résultat Windows est `dist/lacitadelle.llamafile.exe` (environ 44 Mo).
Aucune compilation du runtime n'est requise. Les assets téléchargés restent
locaux et ne sont pas versionnés.

## Non-objectifs V1

- Pas de compilation du runtime depuis ses sources.
- Pas de détection GPU ni de bascule automatique vers un runtime GPU.
