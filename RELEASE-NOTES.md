# La Citadelle — Release v3

Date : 2026-10-31
Commit source : Phase 13-CROSS-PLATFORM (voir l'historique Git)
Archive : `lacitadelle-distribution.zip` (source-only)
SHA-256 : communiqué séparément avec l'archive; non intégré aux notes pour
éviter une empreinte auto-référente.

## Nouveautés

- **Phase 13-CROSS-PLATFORM** : exécution Windows, Linux et macOS avec un
  runtime llamafile thin universel, des destinations adaptées à l'OS et des
  wrappers natifs `.bat`, `.sh` et `.command`.
- **Phase 14-PERSONA-NEXXUS-V1** : persona système versionné, injection du
  contexte utilisateur et du modèle actif, et politique préparatoire de
  classification des fichiers. Aucun outil de lecture de fichiers n'est inclus.
- **V3.1 sécurité** : cookie `Secure` en HTTPS, protection CSRF des POST
  authentifiés et rate limiting du login, du chat et des routes admin.
- **Phase 12-FIX-WHITELIST** : initialisation de première installation avec
  vérification SHA-256 du GGUF intégré et refus explicite d'un rollback sans
  modèle précédent.
- **Phase 12-POLISH-INSTALL-DOC** : RUNBOOK-PROD documente le parcours de
  première installation Windows, la sortie one-time du mot de passe admin,
  la redirection des erreurs et le dépannage.
- **Phase 12-POLISH-TODO-GIT** : TODO.md versionné comme registre partagé des
  seules tâches actives; Règle 10 ajoutée à AGENTS.md.

## Tests

- 229 tests verts : 228 tests avant le correctif TER et un nouveau test du
  lancement Windows sans redirection.

## Persona Nexxus (Phase 14-PERSONA-NEXXUS-V1)

- Le chat utilise un prompt système versionné dans
  `dev/tools/prompts/system.txt`, avec identité Nexxus et contexte dynamique
  (date, utilisateur, modèle actif et session).
- La politique préparatoire de classification des fichiers comporte trois
  niveaux (public, sensible, critique). Aucun outil de lecture de fichiers
  n'est inclus dans cette version.

## Packaging autonome Windows (Phase 15-PACKAGING-PYINSTALLER-V1)

- Un build PyInstaller one-file produit `LaCitadelle.exe`; Python n'est pas
  requis sur le poste utilisateur.
- Au premier lancement, runtime et GGUF sont téléchargés et vérifiés.
- La base, les assets et les logs persistent dans `%APPDATA%\LaCitadelle\`.
- Sur Windows, llamafile garde sa console dédiée sans redirection stdout;
  il reste actif après l'arrêt du proxy.
- Ctrl+C arrête le proxy, pas llamafile; fermer sa console quand il n'est plus
  utilisé (le port 8080 reste occupé tant que le runtime tourne).
- L'exécutable n'est pas signé; vérifier son SHA-256 avant tout contournement
  de SmartScreen. Le ZIP source-only du projet reste disponible pour Linux et
  macOS.

## Corrections post-test (Phase 13-CROSS-PLATFORM-BIS)

Trois bugs ont été révélés par le test réel sur Linux et corrigés :

- **Wrappers Unix en CRLF** : les fichiers `.sh` et `.command` pouvaient être
  livrés avec des fins de ligne Windows, empêchant leur exécution. Corrigé par
  `.gitattributes` (LF forcé) et la normalisation dans `creer_archive.py`.
- **Exec format error sur llamafile** : le runtime est un APE (Actually
  Portable Executable); sur Unix, le lanceur passe la commande par `sh -c`
  avec les arguments échappés par `shlex.join`, plutôt que d'exécuter
  directement le binaire via `subprocess`.
- **Ordre des arguments llamafile** : `-m <GGUF>` doit précéder `--server`.

Les tests T8/T9/T10 couvrent ces corrections. Le SHA-256 de l'archive est
communiqué séparément avec la release; il n'est pas intégré à ces notes pour
éviter une empreinte auto-référente.

## Installation

1. Extraire l'archive dans un dossier accessible en écriture.
2. Lancer `install.bat` (Windows), `install.sh` (Linux) ou
   `install.command` (macOS). Python 3.10+ et Internet sont requis au premier
   lancement si le runtime ou le GGUF ne sont pas déjà présents.
3. Le bootstrap télécharge le runtime universel et vérifie les assets; le GGUF
   représente environ 1,28 Go. L'installateur démarre ensuite le lanceur natif.
4. Si nécessaire, relancer `lancer.bat`, `lancer.sh` ou `lancer.command`.
5. Ouvrir `http://127.0.0.1:8081/`.
6. Au premier démarrage, relever le mot de passe admin affiché une seule fois
   dans la console du proxy.

L'archive source-only n'embarque ni runtime ni GGUF; le parcours d'installation
est hors ligne seulement après leur téléchargement ou leur prépositionnement.

## Sécurité

- Cookie `Secure` en HTTPS, CSRF sur les POST authentifiés et rate limiting
  côté serveur.
- Ne pas exposer directement les ports locaux 8080/8081 sur Internet.
- Pour un accès distant, configurer un reverse proxy HTTPS avec un certificat
  valide et un pare-feu restrictif.

## Limites connues

- La validation manuelle sur Linux et macOS reste à effectuer avant diffusion.
- Le serveur est mono-thread; une inférence lente bloque les requêtes suivantes.
- Playwright E2E est reporté.
- L'upload GGUF n'est pas implémenté.

## Validation   2023-10-31

- ✅ Windows 10/11 : validé (install + lancer + chat).
- ✅ Linux (Ubuntu) : validé (install.sh + lancer.sh + chat).
- ⏳ macOS : wrappers fournis et testés unitairement, validation runtime en cours.

La version `v3.0.0-rc1` est publiée pour permettre les tests
Windows/Linux en attendant la validation macOS.
La version `v3.0.0` finale suivra après confirmation macOS.

## Corrections post-test (Phase 13-CROSS-PLATFORM-BIS)

Trois bugs ont été révélés par le test réel sur Linux et corrigés :
- **Wrappers Unix en CRLF** : les fichiers `.sh` et `.command` étaient
  livrés avec des fins de ligne Windows. Corrigé par `.gitattributes`
  (LF forcé) et normalisation dans `creer_archive.py`.
- **Exec format error sur llamafile** : `llamafile` est un APE qui
  doit être lancé via `sh -c` sur Unix.
- **Ordre des arguments llamafile** : `-m <GGUF>` doit précéder
  `--server`.

Corrigé par 3 tests supplémentaires (T8/T9/T10) → 205 tests verts.

## Vérification d'intégrité

SHA-256 de `lacitadelle-distribution.zip` :
`2581d1aa8804cb129ce3d23e2bc475d6ac071b487c69e5abd0934804a53f38c2`