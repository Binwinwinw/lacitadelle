# Architecture de La Citadelle (V1)

## Vue d'ensemble

La Citadelle assemble un runtime llamafile léger et un modèle GGUF externe. Le runtime démarre un serveur HTTP local ; l'utilisateur ouvre l'interface web avec `lancer.bat`. Un client Python séparé permet aussi d'utiliser une mémoire SQLite. Le modèle et la base ne sont pas intégrés au runtime.

## Composants

### 1. Runtime : `dist/lacitadelle.llamafile.exe`

- Binaire APE (Cosmopolitan) d'environ 44 Mo, assemblé par `dev/tools/setup_lacitadelle.py` à partir du runtime llamafile thin et de `zipalign`.
- Contient le runtime et un fichier `.args`, mais pas le modèle GGUF.
- Le fichier `.args` référence le modèle par le chemin relatif `dev/tools/vendor/llamafile/Qwen3-1.7B-Q4_K_M.gguf`.
- Démarre un serveur HTTP headless sur `localhost:8080` (`--server`) et expose l'API compatible OpenAI `/v1/chat/completions`.
- Paramètres V1 : contexte de 8192 tokens, température 0.7 et 4 threads.

### 2. Modèle externe

- Fichier `dev/tools/vendor/llamafile/Qwen3-1.7B-Q4_K_M.gguf`, d'environ 1,28 Go.
- Qwen3-1.7B Q4_K_M, licence Apache 2.0.
- Téléchargé et vérifié par checksum SHA-256 par `dev/tools/bootstrap.py` ; il n'est pas embarqué dans le `.llamafile.exe`.

### 3. Préparation et fabrication (outils de développement)

- `dev/tools/llamafile_config.json` décrit les assets, leurs URLs et leurs checksums. Trois assets sont requis en V1 : runtime thin, `zipalign` et GGUF ; le runtime complet est facultatif et n'est pas utilisé.
- `dev/tools/bootstrap.py` télécharge et vérifie les assets requis, avec réparation d'un fichier absent ou corrompu.
- `dev/tools/setup_lacitadelle.py` assemble le runtime et le fichier `.args` avec `zipalign` pour produire l'exécutable dans `dist/`.

### 4. Lancement

- `install.bat` vérifie la disponibilité de Python, lance le bootstrap puis la fabrication, et démarre `lancer.bat` après succès.
- `lancer.bat` démarre le serveur en arrière-plan puis ouvre `http://localhost:8080` dans le navigateur.
- L'installation et le client Python nécessitent Python 3.10+ ; l'exécutable llamafile lui-même est le runtime d'inférence.

### 5. Client conversationnel et mémoire SQLite

- `dev/tools/client.py` est un REPL séparé qui se connecte au serveur llamafile déjà lancé via l'API HTTP locale. Il ne démarre pas le serveur.
- `dev/tools/citadelle_memory.py` gère la base `citadelle_data/memory.db` et ses trois tables V1 : `users`, `sessions` et `messages`.
- Le client V1 utilise l'utilisateur par défaut `lacitadelle`, conserve les conversations localement et envoie au plus 15 messages de contexte.
- Cette mémoire est disponible en V1 via le client Python, mais elle n'est ni embarquée dans le `.llamafile.exe` ni utilisée par l'interface web intégrée de llamafile.
- La V1 n'a pas de login ni de comptes multi-utilisateurs actifs.

## Flux de première installation

1. L'utilisateur clone le dépôt et installe Python 3.10+.
2. Il double-clique sur `install.bat`.
3. `install.bat` lance `bootstrap.py`, qui télécharge et vérifie le runtime, `zipalign` et le GGUF.
4. `install.bat` lance `setup_lacitadelle.py`, qui assemble `dist/lacitadelle.llamafile.exe`.
5. `install.bat` lance `lancer.bat`, qui démarre le serveur et ouvre le navigateur sur `localhost:8080`.

## Flux d'utilisation quotidienne

### Interface web

1. Double-cliquer sur `lancer.bat`.
2. Le serveur llamafile démarre sur `localhost:8080`.
3. Le navigateur s'ouvre sur `http://localhost:8080`.
4. L'utilisateur discute avec Qwen3-1.7B en local, sur CPU.

### Client avec mémoire

1. Démarrer le serveur avec `lancer.bat` ou `dist/lacitadelle.llamafile.exe`.
2. Dans un terminal séparé, lancer `python dev/tools/client.py`.
3. Utiliser le REPL ; les sessions sont persistées dans SQLite.

## Décisions structurantes

- **Mode external** : le modèle reste externe ; l'exécutable distribué fait environ 44 Mo au lieu d'embarquer le GGUF.
- **Serveur headless** (`--server`) : l'exécutable démarre le serveur HTTP local sans TUI.
- **Contexte 8192** : valeur utilisée par le runtime V1.
- **Téléchargement vérifié** : le bootstrap valide les checksums des assets requis.
- **Mémoire séparée** : le client Python et SQLite fournissent la persistance, hors du runtime llamafile.

## Limites actuelles

- Le client mémoire et le parcours d'installation nécessitent Python 3.10+.
- Le serveur V1 utilise le runtime CPU thin ; aucune détection ni bascule GPU n'est implémentée.
- Le client utilise un seul utilisateur par défaut ; aucun login ni multi-utilisateurs actifs.
- L'interface web peut saturer le contexte sur les conversations longues.
- Pas de prompt système personnalisable ni de reprise HTTP Range.
