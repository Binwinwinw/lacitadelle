# Contrat de `bootstrap.py`

> **Statut : contrat courant.** `dev/tools/bootstrap.py` référence ce fichier.
> Le manifeste [`llamafile_config.json`](./llamafile_config.json) fait foi pour
> les identifiants, noms source, URL, SHA-256, destinations et indicateurs
> `required`; ce document décrit le comportement du code, pas la disponibilité
> distante des URLs.

## Rôle

Télécharger et vérifier les assets listés dans `llamafile_config.json`.
Le runtime llamafile-thin et le modèle GGUF sont des téléchargements séparés.
Le GGUF est un asset distinct, pas un modèle incorporé au binaire runtime. Le
manifeste actuel ne déclare pas Ornith ni Qwen3.5; le bootstrap ne les
télécharge donc pas. Ne pas exécuter les assets. Ne pas installer de dépendance.

## Contrat de la configuration (`llamafile_config.json`)

### Structure racine

Objet JSON avec les clés obligatoires : `version` (str non vide), `assets`
(dict non vide). `load_config()` valide ces champs racine. Les clés
`release_date`, `source` et `verified_on` sont des métadonnées informatives :
le bootstrap ne valide pas leur type ni leur format.

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

- `purpose` : métadonnée informative, non validée par le bootstrap.
- `destination_by_os` : destinations exactes pour `Windows`, `Linux` et
  `Darwin` lorsqu'un asset dépend de l'OS.
- `post_download` : actions par OS parmi `rename` et `chmod_x`. Le bootstrap
  valide ces valeurs; le code exécute `chmod_x` lorsqu'il est présent. Le nom
  final vient de la destination du manifeste et la publication renomme le
  temporaire vers cette destination; `rename` n'ajoute pas d'étape distincte.

### Validation

Toute violation lève `BootstrapError` avec un message indiquant :

- l'asset concerné (nom de la clé),
- le champ concerné,
- la cause précise (ex. « sha256 doit faire 64 caractères, trouvé 63 »).

## Assets du manifeste actuel

Le manifeste actuellement présent contient deux entrées, toutes deux
`required: true` :

| Identifiant (`assets`) | Asset / destination source |
|---|---|
| `runtime-universal` | Runtime llamafile-thin; destinations par OS : `dist/llamafile.exe`, `dist/llamafile-linux` et `dist/llamafile-macos`. Le nom source, la version et les autres métadonnées restent dans le manifeste. |
| `qwen3-4b-q4km` | `Qwen3-4B-Q4_K_M.gguf`, destination `dev/tools/vendor/llamafile/Qwen3-4B-Q4_K_M.gguf`. |

Aucun asset n'est facultatif dans le manifeste actuel. L'identifiant
`qwen3-1.7b-q4km` appartient à l'ancien modèle décrit dans les documents
historiques; il n'est pas l'identifiant du modèle actuel.

## Contrat des chemins

- `CONFIG_PATH` = `dev/tools/llamafile_config.json` (relatif à la racine du projet).
- Le runtime `runtime-universal` est publié sous la destination par OS du
  manifeste. Sous Linux/macOS, il reçoit les droits d'exécution lorsque
  `chmod_x` est configuré. Le nom source et la version amont restent définis
  dans le manifeste.
- `VENDOR_DIR` = `dev/tools/vendor/llamafile/`, destination du GGUF.
- Dans le build PyInstaller one-file Windows, runtime et GGUF sont persistés
  dans `%APPDATA%\LaCitadelle\assets\`; les chemins source `dist/` et
  `vendor/` restent inchangés en développement.
- Les répertoires de destination sont créés si absents (avec
  `mkdir(parents=True, exist_ok=True)`).
- Le dossier `dev/tools/vendor/` est gitignoré.

## Contrat de téléchargement

### Cycle par asset (avec mode réparateur)

Pour chaque asset avec `required: true`, le bootstrap sélectionne la
destination correspondant à l'OS détecté. Pour le manifeste actuel,
`runtime-universal` utilise la destination `dist/` adaptée à l'OS et
`qwen3-4b-q4km` utilise `VENDOR_DIR` en développement. En mode PyInstaller,
les deux assets vont dans le dossier utilisateur décrit dans le contrat des
chemins.

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

Le téléchargement appelle `urllib.request.urlopen(req, timeout=HTTP_TIMEOUT)`;
`HTTP_TIMEOUT` vaut 60 secondes dans [`bootstrap.py`](./bootstrap.py).

### Gestion des erreurs HTTP

Traiter `HTTPError` **avant** `URLError` (car `HTTPError` hérite de `URLError`). Le message doit inclure le code HTTP (`HTTPError.code`).

### Gestion des interruptions

Si une exception survient pendant le téléchargement, supprimer le fichier temporaire avant de propager.

## Commande

La commande directe est `python dev/tools/bootstrap.py`; le script ne définit
pas d'option CLI et traite les assets requis du manifeste pour l'OS détecté.
Il ne lance pas le runtime. L'installateur `dev/tools/install.py` appelle le
bootstrap et ne lance `lancer.py` qu'après un succès.

## Contrat de sortie

- Code **0** : tous les assets `required` sont téléchargés et vérifiés.
- Code **1** : au moins un asset a échoué (téléchargement, checksum).
- Code **2** : erreur de configuration (JSON invalide, schéma violé) ou système
  d'exploitation non pris en charge.
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
