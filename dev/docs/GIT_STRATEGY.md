# Stratégie Git — La Citadelle

## État actuel

Le dépôt est versionné dans le dépôt GitHub privé
`https://github.com/Binwinwinw/lacitadelle`. La branche par défaut est `main`
et suit `origin/main`.

## Politique de versionnement

Les sources, la documentation, les scripts et les fichiers de configuration
sont suivis par Git. Les données utilisateur, modèles téléchargés, binaires
vendorisés et artefacts générés restent locaux et sont exclus par `.gitignore`.

## Assets de fabrication

La fabrication utilise les binaires précompilés de la release llamafile 0.10.6
et le modèle GGUF externe. `dev/tools/bootstrap.py` les télécharge et vérifie
leurs SHA-256 selon `dev/tools/llamafile_config.json`. Aucun checkout local des
sources upstream n'est requis pour construire la V1.

Les assets sont stockés dans `dev/tools/vendor/llamafile/` et ne sont pas
versionnés. Les scripts, manifestes et contrats de fabrication restent suivis
par Git.

## Historique Git

Les modifications sont publiées par des commits normaux sur la branche suivie.
La réécriture d'historique est interdite sans autorisation explicite, selon
`AGENTS.md`.
