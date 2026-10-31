# Contrat de `bootstrap.py`

## Rôle

Télécharger et vérifier les assets listés dans `llamafile_config.json`.
Le runtime llamafile-thin et le modèle GGUF sont des téléchargements séparés.
Ne pas exécuter les assets. Ne pas installer de dépendance.

## Contrat de la configuration (`llamafile_config.json`)

### Structure racine

Objet JSON avec les clés obligatoires : `version` (str non vide), `assets` (dict non vide).
Clés optionnelles : `release_date` (str ISO 8601), `source` (str URL), `verified_on` (str ISO 8601).

### Chaque asset (clé du dict `assets`)

La clé est un identifiant logique (ex. `runtime-universal`). Champs obligatoires :

| Champ      | Type | Règle                                                           |
| ---------- | ---- | --------------------------------------------------------------- |
| `url`      | str  | Non vide, doit commencer par `https://`                         |
| `sha256`   | str  | Exactement 64 caractères hexadécimaux (a-f, A-F, 0-9)           |
| `source_filename` ou `filename` | str | Nom source simple : pas de `/`, `\` ou `..` |
| `required` | bool | Booléen strict (pas de truthy). Absent = erreur                 |
| `destination` ou `destination_by_os` | str / objet | Chemin relatif sous la racine, sans `..` |

Champs optionnels :

- `purpose` : chaîne libre, informative.
- `destination_by_os` : destinations exactes pour `Windows`, `Linux` et
  `Darwin` lorsqu'un asset dépend de l'OS.
- `post_download` : actions documentées par OS (`rename`, `chmod_x`).

### Validation

Toute violation lève `BootstrapError` avec un message indiquant :

- l'asset concerné (nom de la clé),
- le champ concerné,
- la cause précise (ex. « sha256 doit faire 64 caractères, trouvé 63 »).

## Contrat des chemins

- `CONFIG_PATH` = `dev/tools/llamafile_config.json` (relatif à la racine du projet).
- Le runtime unique `llamafile-0.10.6-thin` est publié dans `dist/` sous le
  nom configuré pour Windows, Linux ou macOS. Sous Linux/macOS, il reçoit les
  droits d'exécution.
- `VENDOR_DIR` = `dev/tools/vendor/llamafile/`, destination du GGUF.
- Les répertoires de destination sont créés si absents (avec
  `mkdir(parents=True, exist_ok=True)`).
- Le dossier `dev/tools/vendor/` est gitignoré.

## Contrat de téléchargement

### Cycle par asset (avec mode réparateur)

Pour chaque asset avec `required: true`, le bootstrap sélectionne la
destination correspondant à l'OS détecté; `runtime-universal` va dans `dist/`
et `qwen3-1.7b-q4km` dans `VENDOR_DIR`.

1. **Fichier final présent dans son répertoire de destination** :
   - Calculer son SHA-256.
   - **Conforme** → asset OK, passer au suivant.
   - **Non conforme** → **suppression du fichier**, puis exécuter le cycle de téléchargement (étape 2). Message sur stderr : « Fichier existant X corrompu, réparation en cours. »
2. **Fichier final absent (ou après suppression)** :
   - Télécharger vers un fichier temporaire dans le répertoire de destination
     (nom unique : `.tmp-<filename>-<pid>`).
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
- Détecter l'OS, puis filtrer les assets `required: true` et leurs destinations.
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

## Limites connues (v1)

1. **Nettoyage best-effort des temporaires** : en cas d'échec de
   téléchargement ou de vérification, `_cleanup_partial()` supprime le
   fichier temporaire (`.tmp-<filename>-<pid>`). Si la suppression
   échoue (fichier verrouillé par un antivirus, par exemple), un
   temporaire orphelin reste sur disque. **Il ne sera pas nettoyé
   automatiquement au prochain run** (le script ne cherche que le
   fichier final, pas les `.tmp-*`). Suppression manuelle nécessaire
   dans ce cas. Pas de risque de corruption silencieuse du fichier
   final, mais accumulation possible de temporaires orphelins.

2. **`KeyboardInterrupt` non intercepté** : si l'utilisateur fait
   Ctrl+C pendant le téléchargement, le fichier temporaire
   (`.tmp-<filename>-<pid>`) reste sur disque. **Il ne sera pas
   nettoyé automatiquement au prochain run.** Suppression manuelle
   nécessaire. Le fichier final n'est pas affecté. Pas de blocage,
   mais accumulation possible de temporaires orphelins.

3. **Encodage des accents sur Windows** : le script utilise des
   accents dans ses messages (`déjà`, `téléchargé`, etc.). Sur certains
   terminaux Windows configurés en code page non-UTF-8, cela peut
   produire des erreurs d'affichage ou des `UnicodeEncodeError`.
   Solution : `set PYTHONIOENCODING=utf-8` avant de lancer le script,
   ou `chcp 65001` pour passer le terminal en UTF-8.

4. **Pas de reprise HTTP Range** : si un téléchargement est interrompu
   au milieu, le prochain run le reprend depuis zéro. Pour ~44 Mo,
   c'est acceptable. V2 pourra ajouter la reprise.

5. **Pas de nettoyage des temporaires orphelins** : le script ne
   scanne pas `VENDOR_DIR` à la recherche de fichiers `.tmp-*` laissés
   par des exécutions précédentes. Si des temporaires orphelins
   s'accumulent, suppression manuelle : `rm dev/tools/vendor/llamafile/.tmp-*`
   (Unix) ou `del dev\tools\vendor\llamafile\.tmp-*` (Windows).
   Amélioration v2 : nettoyage automatique au démarrage.
