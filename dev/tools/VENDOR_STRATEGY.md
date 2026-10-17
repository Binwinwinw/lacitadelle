# Stratégie de vendorisation du binaire llamafile

## Contexte

La v1 utilise le binaire `llamafile-0.10.6-thin` (CPU only) + `zipalign-0.10.6` (voir dev/docs/BASE_LLAMAFILE.md). Ces binaires sont des dépendances externes, comme `main/`. Ils ne sont pas versionnés. Seuls le script de téléchargement et le fichier de configuration sont versionnés.

## Décisions actées (décideur, 2026-10-17)

### A — Où stocker les binaires téléchargés ?

Chemin : `dev/tools/vendor/llamafile/`. Ce dossier est ajouté au `.gitignore` via la ligne `dev/tools/vendor/`. Les binaires téléchargés ne vont jamais sur GitHub.

### B — Comment vérifier l'intégrité ?

Le script calcule le SHA-256 du fichier téléchargé et le compare à la valeur attendue (lue depuis `llamafile_config.json`). Si échec : suppression du fichier téléchargé, message d'erreur indiquant checksum attendu vs calculé, code de sortie non-zéro. Aucune exécution du binaire non-vérifié.

### C — Comment gérer les mises à jour de version ?

Fichier `dev/tools/llamafile_config.json` versionné dans Git, contenant :

- version (ex. `0.10.6`),
- URL et SHA-256 des assets utilisés (`llamafile-0.10.6-thin`, `zipalign-0.10.6`),
- URL et SHA-256 de `llamafile-0.10.6` complet (documenté pour usage futur, non téléchargé en v1).
  Le script lit ce fichier à chaque exécution. Mise à jour de version = modifier ce fichier + relancer le script.

### D — Échec de téléchargement ?

Message d'erreur clair (URL, code HTTP, cause), pas de fichier partiel laissé sur disque, code de sortie non-zéro.

### E — Checksum invalide ?

Refus immédiat, suppression du fichier téléchargé, message d'erreur indiquant checksum attendu vs calculé, code de sortie non-zéro. Aucune exécution du binaire non-vérifié.

## Composants à créer (prochaine étape)

1. `dev/tools/llamafile_config.json` — configuration versionnée.
2. `dev/tools/bootstrap.py` — script de téléchargement et vérification.
3. Ligne `dev/tools/vendor/` dans `.gitignore`.

## Non-objectifs (v1)

- Pas de compilation depuis les sources (`main/` reste documentaire).
- Pas de détection GPU.
- Pas d'exécution du binaire téléchargé dans ce script (juste téléchargement + vérification).
