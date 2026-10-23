# Base llamafile — mode external v1

> **HISTORIQUE** — document d'analyse du build V1. Le parcours actuel utilise llamafile-thin téléchargé directement (voir [BOOTSTRAP_CONTRACT.md](../tools/BOOTSTRAP_CONTRACT.md) et [README.md](../../README.md)). Conservé pour traçabilité.

## Décision

La V1 utilisait un runtime llamafile et un GGUF externe. Le parcours actuel
télécharge le runtime et le modèle séparément; le GGUF reste dans
`dev/tools/vendor/llamafile/`.

## Version et assets retenus

**Version runtime** : `0.10.6` (release du 15 septembre 2026).

- Runtime : `llamafile-0.10.6-thin`, CPU only, environ 44 Mo.
- Modèle externe : `Qwen3-1.7B-Q4_K_M.gguf`.

Les assets sont téléchargés et vérifiés par SHA-256 selon
`dev/tools/llamafile_config.json`.

**Checksums SHA-256** :

- Runtime thin : `756bf97febae557084e8ced9bde7a1cb0c7f6ce778530d582afa219406237a50`
- GGUF Qwen3 : `16da7ba1721b1620fa843e0978badd3d93756274fd209a01874b37e29750e207`

**URLs des binaires upstream** :

- Runtime thin : `https://github.com/mozilla-ai/llamafile/releases/download/0.10.6/llamafile-0.10.6-thin`
- GGUF Qwen3 : `https://huggingface.co/smarttasks/Qwen3-1.7B-GGUF/resolve/4b9aca3fb9c8fcace456430347c2fc34752e515f/Qwen3-1.7B-Q4_K_M.gguf`

## Assemblage V1

L'ancien outil de build a été supprimé en Phase 5. Le parcours actuel télécharge
les assets via `dev/tools/bootstrap.py`; `lancer.bat` démarre le runtime depuis
la racine du projet.

Sous Windows, le runtime est placé dans `dist/llamafile.exe`. Les assets
téléchargés restent locaux et ne sont pas versionnés.

## Non-objectifs V1

- Pas de compilation du runtime depuis ses sources.
- Pas de détection GPU ni de bascule automatique vers un runtime GPU.
