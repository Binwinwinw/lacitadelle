# Stratégie Git — La Citadelle

## État actuel

Le dépôt est versionné dans le dépôt GitHub privé
`https://github.com/Binwinwinw/lacitadelle`. La branche par défaut est `main`
et suit `origin/main`.

## Politique de versionnement

Les sources, la documentation, les scripts et les fichiers de configuration
sont suivis par Git. Les données utilisateur, modèles téléchargés, binaires
vendorisés et artefacts générés restent locaux et sont exclus par `.gitignore`.

## Assets téléchargés

`dev/tools/bootstrap.py` télécharge le runtime llamafile-thin 0.10.6 dans
`dist/` (`dist/llamafile.exe` sous Windows, `dist/llamafile` sous Unix) et le
modèle GGUF séparément dans `dev/tools/vendor/llamafile/`. Les SHA-256 sont
vérifiés selon `dev/tools/llamafile_config.json`. Aucun checkout local des
sources upstream n'est requis pour utiliser la distribution.

Le runtime, le modèle et les autres assets téléchargés ne sont pas versionnés.
Les scripts, manifestes et contrats du bootstrap restent suivis par Git.

## Historique Git

Les modifications sont publiées par des commits normaux sur la branche suivie.
La réécriture d'historique est interdite sans autorisation explicite, selon
`AGENTS.md`.
