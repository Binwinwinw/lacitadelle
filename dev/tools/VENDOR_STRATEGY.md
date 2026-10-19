# Vendorisation des binaires llamafile

## Contexte

La v1 utilise trois assets téléchargés et vérifiés : le runtime précompilé
`llamafile-0.10.6-thin`, `zipalign-0.10.6` et le GGUF externe
`Qwen3-1.7B-Q4_K_M.gguf`. La configuration et le script de téléchargement
sont versionnés ; les assets sont téléchargés dans
`dev/tools/vendor/llamafile/` et ne sont pas versionnés.

## Règles actées (décideur, 2026-10-17)

### Stockage

Le répertoire `dev/tools/vendor/` est exclu de Git. Les binaires téléchargés ne
sont pas publiés dans le dépôt.

### Intégrité

Le script calcule le SHA-256 de chaque asset et le compare à la valeur attendue
dans `dev/tools/llamafile_config.json`. En cas d'échec, le fichier est supprimé,
une erreur indique le checksum attendu et calculé, et le processus s'arrête avec
un code non-zéro. Aucun binaire non vérifié n'est exécuté.

### Versions et configuration

`dev/tools/llamafile_config.json` est versionné dans Git. Il décrit la version,
les URL, les SHA-256 et le statut requis des assets. En v1, les assets requis
sont `llamafile-0.10.6-thin`, `zipalign-0.10.6` et
`Qwen3-1.7B-Q4_K_M.gguf`. La mise à jour d'une version se fait en modifiant
cette configuration puis en relançant le bootstrap.

### Erreurs et réparation

Une erreur de téléchargement précise l'URL, le code HTTP et la cause ; aucun
fichier partiel n'est conservé. Si un fichier existant a un checksum invalide,
il est supprimé et téléchargé une seule fois de nouveau. Si la vérification ou
le téléchargement échoue encore, le script s'arrête explicitement, sans boucle
de nouvelle tentative.

## Composants

1. `dev/tools/llamafile_config.json` — configuration versionnée des assets.
2. `dev/tools/bootstrap.py` — téléchargement et vérification SHA-256.
3. `dev/tools/vendor/llamafile/` — répertoire local des assets, exclu de Git.

## Hors périmètre v1

- Détection GPU.
- Exécution des binaires par le script de téléchargement ; il télécharge et
  vérifie uniquement les assets.
