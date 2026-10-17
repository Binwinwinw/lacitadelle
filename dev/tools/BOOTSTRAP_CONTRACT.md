# Contrat de `bootstrap.py`

## Rôle

Télécharger et vérifier les binaires llamafile listés dans `llamafile_config.json`.
Ne pas exécuter les binaires. Ne pas installer de dépendance.

## Contrat de la configuration (`llamafile_config.json`)

### Structure racine

Objet JSON avec les clés obligatoires : `version` (str non vide), `assets` (dict non vide).
Clés optionnelles : `release_date` (str ISO 8601), `source` (str URL), `verified_on` (str ISO 8601).

### Chaque asset (clé du dict `assets`)

La clé est un identifiant logique (ex. `llamafile-thin`). Champs obligatoires :

| Champ      | Type | Règle                                                           |
| ---------- | ---- | --------------------------------------------------------------- |
| `url`      | str  | Non vide, doit commencer par `https://`                         |
| `sha256`   | str  | Exactement 64 caractères hexadécimaux (a-f, A-F, 0-9)           |
| `filename` | str  | Nom de fichier simple : pas de `/`, `\`, `..`, ni chemin absolu |
| `required` | bool | Booléen strict (pas de truthy). Absent = erreur                 |

Champs optionnels :

- `purpose` : chaîne libre, informative.

### Validation

Toute violation lève `BootstrapError` avec un message indiquant :

- l'asset concerné (nom de la clé),
- le champ concerné,
- la cause précise (ex. « sha256 doit faire 64 caractères, trouvé 63 »).

## Contrat des chemins

- `CONFIG_PATH` = `dev/tools/llamafile_config.json` (relatif à la racine du projet).
- `VENDOR_DIR` = `dev/tools/vendor/llamafile/`. Créé si absent (avec `mkdir(parents=True, exist_ok=True)`).
- Le dossier `dev/tools/vendor/` est gitignoré.

## Contrat de téléchargement

### Cycle par asset (avec mode réparateur)

Pour chaque asset avec `required: true` :

1. **Fichier final présent dans `VENDOR_DIR/filename`** :
   - Calculer son SHA-256.
   - **Conforme** → asset OK, passer au suivant.
   - **Non conforme** → **suppression du fichier**, puis exécuter le cycle de téléchargement (étape 2). Message sur stderr : « Fichier existant X corrompu, réparation en cours. »
2. **Fichier final absent (ou après suppression)** :
   - Télécharger vers un fichier temporaire dans `VENDOR_DIR` (nom unique : `.tmp-<filename>-<pid>`).
   - Calculer le SHA-256 du temporaire.
   - **Conforme** → publication atomique (renommer temporaire vers fichier final).
   - **Non conforme** → supprimer le temporaire, échec explicite. Message : « Checksum invalide pour X. Attendu Y, calculé Z. »
   - **Échec réseau** → supprimer le temporaire si présent, échec explicite.

**Une seule tentative de réparation par asset.** Pas de retry en boucle. Si la réparation échoue (téléchargement KO ou nouveau checksum KO), échec final explicite.

### Timeout réseau

`urlopen(url, timeout=60)`.

### Gestion des erreurs HTTP

Traiter `HTTPError` **avant** `URLError` (car `HTTPError` hérite de `URLError`). Le message doit inclure le code HTTP (`HTTPError.code`).

### Gestion des interruptions

Si une exception survient pendant le téléchargement, supprimer le fichier temporaire avant de propager.

## Contrat de sortie

- Code **0** : tous les assets `required` sont téléchargés et vérifiés.
- Code **1** : au moins un asset a échoué (téléchargement, checksum).
- Code **2** : erreur de configuration (JSON invalide, schéma violé).
- **Aucun traceback** pour les `BootstrapError`. Message sur `stderr`, format : `ERREUR [<asset>] : <cause>`.
- **Traceback autorisé** pour les exceptions non-`BootstrapError` (bugs de programmation).

## Contrat de `main()`

- Charger la config (`load_config()`).
- Filtrer les assets `required: true`.
- Pour chaque asset requis, exécuter `process_asset()`.
- Afficher un résumé final sur `stdout` : nombre d'assets traités, succès/échec.
- Retourner le code de sortie.
- Centraliser la gestion des `BootstrapError` (message stderr, code 1 ou 2).

## Non-objectifs (v1)

- Ne pas exécuter les binaires téléchargés.
- Ne pas gérer les mises à jour de version (l'utilisateur nettoie `dev/tools/vendor/llamafile/` manuellement).
- Pas d'option `--force`.
- Pas de parallélisation.
- Pas de reprise de téléchargement interrompu (HTTP Range).

## Compatibilité

- Python 3.10+.
- Stdlib uniquement.
- Pas de `hashlib.file_digest()` (Python 3.11+).

## Ordre d'implémentation

1. `load_config()` — validation stricte du schéma.
2. `compute_sha256()` + `verify_sha256()` — testables sur petits fichiers locaux.
3. `download()` — timeout, `HTTPError` avant `URLError`, écriture par blocs.
4. `process_asset()` — temporaire, vérification, publication atomique, mode réparateur.
5. `main()` — filtrage, orchestration, codes de sortie.
6. Tests d'intégration (étape ultérieure).
