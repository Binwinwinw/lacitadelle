# Contrat de build_llamafile.py

## Rôle

Produire un fichier `dist/citadelle.llamafile` autonome à partir de :

- `dev/tools/vendor/llamafile/llamafile-0.10.6-thin` (runtime),
- `dev/tools/vendor/llamafile/zipalign-0.10.6` (outil d'assemblage),
- `dev/tools/vendor/llamafile/Qwen3-1.7B-Q4_K_M.gguf` (modèle, téléchargé si absent),
- un fichier `.args` généré avec les paramètres actés.

Voir `dev/docs/BUILD_LLAMAFILE.md` pour les décisions actées (modèle, source, args).

## Structure du script

Le script suit la même architecture que `bootstrap.py` :

- Python stdlib uniquement.
- Fonctions séparées, testables individuellement.
- Codes de sortie explicites (0 succès, 1 asset failed, 2 config error, 3 build error).
- Aucun traceback pour les erreurs attendues (`BuildError`).

## Fonctions à implémenter

### `load_config() -> dict` (réutilise bootstrap.load_config)

Charge la config existante (`llamafile_config.json`). Aucune duplication.

### `ensure_asset(name: str, meta: dict) -> Path`

Vérifie que l'asset est présent et valide, puis retourne son chemin. Le
téléchargement, la réparation et le contrôle SHA-256 sont délégués à
`bootstrap.process_asset(name, meta)`, sans duplication (voir
« Clarifications »).

### `create_args_file(gguf_filename: str, output_path: Path) -> None`

Crée le fichier `.args` avec le contenu acté :

```text
-m
/zip/Qwen3-1.7B-Q4_K_M.gguf
--port
8080
-c
4096
--temp
0.7
-t
4
```

Règles :

- Un argument par ligne, conformément au format upstream.
- Le fichier est créé dans `dist/_tmp/citadelle/.args`; son nom de base
  exact `.args` doit être conservé pour l'entrée embarquée.
- Le nom du GGUF doit rester exactement `Qwen3-1.7B-Q4_K_M.gguf` pour conserver l'assemblage reproductible.
- Aucune ligne de prompt système pour la v1.
- La ligne de modèle doit utiliser le préfixe `/zip/` pour les fichiers embarqués.

### `build_llamafile(runtime_path: Path, zipalign_path: Path, gguf_path: Path, args_path: Path, output_path: Path) -> None`

Orchestre l'assemblage du `.llamafile` final.

Responsabilités :

1. Vérifier la présence des chemins d'entrée.
2. Vérifier la validité du GGUF et de l'args file avant assemblage.
3. Copier le runtime vers un fichier de travail dans `dist/_tmp/citadelle/`.
4. Exécuter `zipalign -j0 <fichier-de-travail> <GGUF> <.args>` : la sortie
   vient en premier, puis les fichiers à embarquer dans cet ordre.
5. Publier le résultat vers `output_path` selon la règle de remplacement
   décrite dans « Clarifications ».
6. Déclencher une `BuildError` avec un message explicite si l'assemblage échoue.

Le build ne doit pas dépendre de Python côté utilisateur final. Le script est uniquement un outil de fabrication.

### `main() -> int`

Point d'entrée du script.

Logique attendue :

1. Charger la config.
2. Vérifier que les assets requis sont présents et valides.
3. Préparer `dist/`, `dist/_tmp/citadelle/` et le chemin final.
4. Générer le fichier `.args` dans `dist/_tmp/citadelle/.args`.
5. Appeler `build_llamafile()`.
6. Après publication réussie, supprimer le répertoire de travail temporaire;
   le conserver en cas d'échec pour le diagnostic.
7. Retourner :
   - `0` si succès,
   - `1` si un asset échoue,
   - `2` si la config est invalide,
   - `3` si la construction du `.llamafile` échoue.

## Comportement attendu de zipalign

Le script ne doit pas réinventer le workflow d'assemblage : la responsabilité est de faire appel à l'outil `zipalign` présent dans `dev/tools/vendor/llamafile/`.

Les points de contrat à respecter :

- `zipalign` est l'outil d'assemblage du runtime + GGUF + `.args`.
- Le runtime llamafile est la base exécutable.
- Le modèle GGUF doit être intégré dans le binaire final.
- Le fichier `.args` doit être présent dans le bundle et référencé avec le préfixe `/zip/`.
- La commande suit la forme `zipalign -j0 <runtime-copié> <GGUF> <.args>`;
  l'ordre des fichiers d'entrée est stable et reproductible.
- Les erreurs de construction doivent être signalées comme `BuildError` et ne doivent pas produire un traceback de débogage pour l'utilisateur final.

## Contrainte Windows / invocation de zipalign

`zipalign-0.10.6` est un exécutable APE multi-format : ses premiers octets
sont `MZqFpD=`, avec un en-tête PE valide à l'offset `0x10a58` et des
marqueurs ELF embarqués. Le fichier vendor reste sans extension.

Sous Windows, copier l'asset dans le répertoire de travail sous le nom
`zipalign.exe` et appeler cette copie. Sous POSIX, appeler directement
`zipalign-0.10.6`. La commande est `zipalign[.exe] -j0 <runtime-copié>
<GGUF> <.args>`; aucun fallback WSL ou Python n'est nécessaire.

Le test `--help` ne fournit aucune aide dans cette version (code `32512`,
stdout et stderr vides avec ou sans extension). La validation d'invocation
est donc l'opération réelle `-j0`, qui a réussi avec et sans suffixe `.exe`.

## Clarifications

### ensure_asset

`ensure_asset()` appelle directement `bootstrap.process_asset(name, meta)`;
aucune logique de téléchargement, de réparation ou de checksum n'est
dupliquée. Après succès, le chemin retourné est
`bootstrap.VENDOR_DIR / meta["filename"]`.

### Emplacement et cycle de vie du .args

Le fichier est `dist/_tmp/citadelle/.args`, avec le nom de base exact
`.args`. Le test `zipalign -j0` confirme que ce nom devient l'entrée racine
`.args`; un fichier `citadelle.args` resterait nommé `citadelle.args` dans
l'archive et ne suivrait pas la convention upstream. Le fichier temporaire
est supprimé après publication réussie du `.llamafile` et conservé en cas
d'échec pour le diagnostic.

### Comportement si le .llamafile existe déjà

Si `dist/citadelle.llamafile` existe, afficher exactement
`overwriting existing: dist/citadelle.llamafile`. Construire d'abord le
nouveau fichier dans le répertoire temporaire, puis remplacer la cible
seulement après un assemblage réussi. En cas d'échec, l'ancien `.llamafile`
reste intact.

## Règles de robustesse

- Aucune dépendance externe en dehors de la stdlib Python.
- Aucune modification de `bootstrap.py`.
- Le contrôle d'intégrité des assets ne les exécute pas ; l'exécution de `zipalign` est réservée à l'assemblage.
- Le script doit créer `dist/` et `dist/_tmp/citadelle/` s'ils sont absents.
- Le script doit utiliser des chemins absolus ou résolus depuis le fichier pour éviter les ambiguïtés de répertoire de travail.
- Si un asset absent est téléchargé, il faut vérifier son SHA-256 avant l'assemblage final.

## Non-objectifs (v1)

- Pas de détection GPU.
- Pas de prompt système avancé.
- Pas d'assemblage multi-modèle.
- Pas de téléchargement direct dans le script sans validation de checksum.
- Pas de modification de `llamafile_config.json` ou de `bootstrap.py`.

## Référence

- `dev/docs/BUILD_LLAMAFILE.md` — décisions de build actées.
- `dev/tools/bootstrap.py` — fonctions de validation et de téléchargement réutilisables.
- `dev/tools/llamafile_config.json` — configuration versionnée des assets.
