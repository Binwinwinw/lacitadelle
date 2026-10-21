# Quirks et pièges du projet

Particularités techniques à connaître avant de coder ou déboguer.

## llamafile

- **Windows** : le binaire `.llamafile` doit être renommé `.exe` pour être exécuté. `setup_lacitadelle.py` le fait déjà.
- **`.args` chemin relatif** : le `.llamafile.exe` doit être lancé depuis la racine du projet pour résoudre `dev/tools/vendor/llamafile/...`. Sinon, erreur « no file found in zip archive ».
- **Timeout 20 s** dans `lancer.bat` : Qwen3 met du temps à charger. Si le délai est dépassé, le proxy démarre avant llamafile et les premières requêtes peuvent échouer.
- **Binaires `.tmp-*`** : les téléchargements interrompus laissent des fichiers `.tmp-*` orphelins dans `vendor/llamafile/`.

## Outils externes intrusifs

Les restrictions concernant Ponytail et hacklm-memory, ainsi que leur vérification post-session, sont définies dans `AGENTS.md` et `dev/docs/OUTILS_INTRUSIFS.md`.

- **hacklm-memory** (extension VS Code) : **configuré** via
  `hacklm-memory.manageInstructionFile: false` pour ne pas modifier
  `.github/copilot-instructions.md`. Si un bloc
  `<!-- hacklm-memory:start -->` réapparaît, restaurer via
  `git restore .github/copilot-instructions.md` et vérifier la configuration
  VS Code.
- `dev/tests/system-commandline-sentinel-files/` : artefact .NET/Git Credential Manager. Réapparaît automatiquement après certains pushs. Gitignoré. Ignorer. S'il réapparaît, le supprimer (pas de commit nécessaire).

## Python

- **Python 3.10+ requis** pour bootstrap, setup, client et proxy; pas pour llamafile.
- **Windows / RTK** : certains terminaux cassent l'encodage des accents. Utiliser `-X utf8` ou `PYTHONIOENCODING=utf-8`.

## Format

- Les règles `.mdc` ont été migrées en `.instructions.md` (format Copilot natif, `applyTo: "**"`).
- `.memory/cleanup.log` est ignoré par Git via le motif `*.log` de `.gitignore`.

## Retiré du projet

- **XAMPP** : retiré. Test sous proxy uniquement.
- **`main/`** : supprimé du worktree (fork llamafile retiré).
