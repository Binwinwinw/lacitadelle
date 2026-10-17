# Contrat de `bootstrap.py`

## Rôle
Télécharger et vérifier les binaires llamafile listés dans `llamafile_config.json`.
Ne pas exécuter les binaires. Ne pas installer de dépendance.

## Contrat de la configuration (`llamafile_config.json`)

### Structure racine
- Objet JSON avec les clés obligatoires : `version` (str), `assets` (dict).
- Clés optionnelles : `release_date` (str, ISO 8601), `source` (str, URL), `verified_on` (str, ISO 8601).

### Chaque asset (clé du dict `assets`)
La clé est un identifiant logique (ex. `llamafile-thin`). Champs obligatoires :
- `url` : chaîne non vide, **doit commencer par `https://`**. Les URLs `http://`, `file://` ou autres sont refusées.
- `sha256` : chaîne de **exactement 64 caractères hexadécimaux** (a-f, A-F, 0-9). Comparaison insensible à la casse.
- `filename` : nom de fichier simple (pas de `/`, pas de `\`, pas de `..`). Utilisé comme nom dans `VENDOR_DIR`.
- `required` : booléen **strict** (pas de truthy). Si absent, erreur (on exige explicite).

Champs optionnels :
- `purpose` : chaîne libre, informative.

### Validation
Toute violation lève une erreur explicite indiquant :
- l'asset concerné (nom de la clé),
- le champ concerné,
- la cause (ex. « sha256 doit faire 64 caractères, trouvé 63 »).

## Contrat des chemins
- `CONFIG_PATH` = `dev/tools/llamafile_config.json`.
- `VENDOR_DIR` = `dev/tools/vendor/llamafile/`. Créé si absent.
- Le dossier `dev/tools/vendor/` est gitignoré. Aucun fichier de `vendor/` ne va sur GitHub.

## Contrat de téléchargement

### Cycle par asset
Pour chaque asset avec `required: true` :
1. Si le fichier final existe dans `VENDOR_DIR/filename` :
   - Calculer son SHA-256.
   - Si conforme → asset OK, passer au suivant.
   - Si non conforme → **échec explicite**. Message : « Le fichier X existe mais son checksum est invalide. Supprimez-le manuellement et relancez. » Pas de réparation automatique.
2. Si le fichier final n'existe pas :
   - Télécharger vers un fichier temporaire dans `VENDOR_DIR` (nom unique, ex. `.tmp-<filename>-<pid>`).
   - Calculer le SHA-256 du temporaire.
   - Si conforme → publication atomique (renommer temporaire vers fichier final).
   - Si non conforme → **supprimer le temporaire**, échec explicite. Message : « Checksum invalide pour X. Attendu Y, calculé Z. »

### Timeout réseau
`urlopen(url, timeout=60)`. 60 secondes pour le bootstrap initial.

### Gestion des erreurs HTTP
Traiter `HTTPError` **avant** `URLError` (car `HTTPError` hérite de `URLError`). Le message d'erreur doit inclure le code HTTP (`HTTPError.code`).

### Gestion des interruptions
Si un `KeyboardInterrupt` ou une exception survient pendant le téléchargement, **supprimer le fichier temporaire** avant de propager.

## Contrat de sortie
- Code 0 : tous les assets `required` sont téléchargés et vérifiés.
- Code 1 : au moins un asset a échoué (téléchargement, checksum, config).
- Code 2 : erreur de configuration (JSON invalide, schéma violé). Distinct du code 1 pour permettre un diagnostic rapide.
- **Aucun traceback** pour les erreurs attendues (config, réseau, checksum). Message sur `stderr`, format : `ERREUR [<asset>] : <cause>`.
- **Traceback autorisé** pour les bugs de programmation (erreurs inattendues), pour ne pas les masquer.

## Contrat de `main()`
- Charger la config.
- Filtrer les assets `required: true`.
- Pour chaque asset requis, exécuter le cycle de téléchargement.
- Afficher un résumé final sur `stdout` : nombre d'assets traités, succès/échec.
- Retourner le code de sortie.

## Non-objectifs
- Ne pas exécuter les binaires téléchargés.
- Ne pas gérer les mises à jour de version (l'utilisateur supprime `dev/tools/vendor/llamafile/` et relance si la config change).
- Ne pas proposer d'option `--force` pour forcer le retéléchargement (v2).
- Ne pas paralléliser les téléchargements (v2).

## Compatibilité
- Python 3.10+.
- Stdlib uniquement.
- Pas de `hashlib.file_digest()` (Python 3.11+).

## Ordre d'implémentation
1. `load_config()` — validation stricte du schéma.
2. `compute_sha256()` + `verify_sha256()` — testables sur petits fichiers locaux.
3. `download()` — timeout, `HTTPError` avant `URLError`, écriture par blocs.
4. `process_asset()` — temporaire, vérification, publication atomique, nettoyage.
5. `main()` — filtrage, orchestration, codes de sortie.
6. Tests d'intégration.