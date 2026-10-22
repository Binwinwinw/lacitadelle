# Architecture de La Citadelle (V3.0)

## Vue d'ensemble

La Citadelle distribue un runtime llamafile léger préconstruit et un modèle GGUF externe. Le runtime démarre un serveur HTTP local ; en V1, l'utilisateur ouvre l'interface web intégrée avec `lancer_v1.bat`. En V3.0, le navigateur passe par le proxy Python démarré avec `lancer.bat`, qui fournit l'authentification et le webchat. Un client Python séparé permet aussi d'utiliser une mémoire SQLite. Le modèle et la base ne sont pas intégrés au runtime.

## Composants

### 1. Runtime : `dist/lacitadelle.llamafile.exe`

- Binaire APE (Cosmopolitan) d'environ 44 Mo, construit côté développeur par `dev/tools/setup_lacitadelle.py` à partir du runtime llamafile thin et de `zipalign`, puis distribué via GitHub Releases.
- Contient le runtime et un fichier `.args`, mais pas le modèle GGUF.
- Le fichier `.args` référence le modèle par le chemin relatif `dev/tools/vendor/llamafile/Qwen3-1.7B-Q4_K_M.gguf`.
- Démarre un serveur HTTP headless sur `localhost:8080` (`--server`) et expose l'API compatible OpenAI `/v1/chat/completions`.
- Paramètres V1 : contexte de 8192 tokens, température 0.7 et 4 threads.

### 2. Modèle externe

- Fichier `dev/tools/vendor/llamafile/Qwen3-1.7B-Q4_K_M.gguf`, d'environ 1,28 Go.
- Qwen3-1.7B Q4_K_M, licence Apache 2.0.
- Téléchargé et vérifié par checksum SHA-256 par `dev/tools/bootstrap.py` ; il n'est pas embarqué dans le `.llamafile.exe`.

### 3. Préparation et fabrication (outils de développement)

- `dev/tools/llamafile_config.json` décrit le runtime préconstruit et le GGUF requis au lancement. Le runtime thin et `zipalign` restent disponibles comme assets facultatifs pour le build développeur.
- `dev/tools/bootstrap.py` télécharge le runtime préconstruit dans `dist/` et le GGUF dans `dev/tools/vendor/llamafile/`, puis vérifie leurs checksums.
- `dev/tools/setup_lacitadelle.py` peut reconstruire le runtime côté développeur ; il récupère au besoin le runtime thin et `zipalign`.

### 4. Lancement

- `install.bat` vérifie la présence de Python, lance le bootstrap et démarre `lancer.bat` (V3.0) après succès. Il ne vérifie pas la version minimale Python et ne construit pas le runtime.
- `lancer_v1.bat` démarre le serveur V1 en arrière-plan puis ouvre `http://localhost:8080`.
- `lancer.bat` démarre llamafile et le proxy Python V3.0, puis ouvre `http://localhost:8081`.
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
3. `install.bat` lance `bootstrap.py`, qui télécharge et vérifie le runtime préconstruit et le GGUF.
4. `install.bat` lance `lancer.bat`, qui démarre llamafile et le proxy puis ouvre le navigateur sur `localhost:8081`.

## Flux d'utilisation quotidienne

### Interface web

1. Double-cliquer sur `lancer_v1.bat`.
2. Le serveur llamafile démarre sur `localhost:8080`.
3. Le navigateur s'ouvre sur `http://localhost:8080`.
4. L'utilisateur discute avec Qwen3-1.7B en local, sur CPU.

### Client avec mémoire

1. Démarrer le serveur V1 avec `lancer_v1.bat` ou `dist/lacitadelle.llamafile.exe`.
2. Dans un terminal séparé, lancer `python dev/tools/client.py`.
3. Utiliser le REPL ; les sessions sont persistées dans SQLite.

## Décisions structurantes

- **Mode external** : le modèle reste externe ; l'exécutable distribué fait environ 44 Mo au lieu d'embarquer le GGUF.
- **Serveur headless** (`--server`) : l'exécutable démarre le serveur HTTP local sans TUI.
- **Contexte 8192** : valeur utilisée par le runtime V1.
- **Téléchargement vérifié** : le bootstrap valide les checksums des assets requis.
- **Mémoire séparée** : le client Python et SQLite fournissent la persistance, hors du runtime llamafile.

## Limites du mode V1

- Le client mémoire et le parcours d'installation nécessitent Python 3.10+.
- Le serveur V1 utilise le runtime CPU thin ; aucune détection ni bascule GPU n'est implémentée.
- Le client utilise un seul utilisateur par défaut ; aucun login ni multi-utilisateurs actifs.
- L'interface web peut saturer le contexte sur les conversations longues.
- Pas de prompt système personnalisable ni de reprise HTTP Range.

## V3.0 — Authentification complète

### Composants V3.0

La V3.0 fournit un proxy Python (`dev/tools/login_server.py`) devant llamafile.
Elle repose sur trois composants :

1. **llamafile** (port 8080) : moteur d'inférence, inchangé depuis la V1.
2. **Proxy Python** (port 8081) : gère le login, filtre les sessions par
   `user_id`, sert le frontend et relaie les requêtes de chat vers llamafile.
3. **Frontend** (`dev/tools/web/`) : pages HTML/CSS/JS servies par le proxy,
   avec formulaire de login, chat et barre latérale des sessions.

### Flux d'authentification et de chat

1. L'utilisateur ouvre `http://localhost:8081/` ; sans session valide, le
   proxy redirige vers `/login`.
2. L'utilisateur s'inscrit via `POST /register`, puis se connecte via
   `POST /login` avec son mot de passe. Le proxy émet un cookie HTTP-only
   `SameSite=Strict`, `Max-Age=86400`, puis redirige vers `/`.
3. `GET /` sert `chat.html` après authentification.
4. `GET /api/sessions` retourne uniquement les sessions de l'utilisateur.
5. Le chat crée des sessions via `POST /api/sessions`, lit leur historique
   via `GET /api/sessions/{id}/messages`, puis envoie les messages au modèle.
6. `POST /api/sessions/{id}/messages` transmet au modèle le prompt système,
   les 15 derniers messages et le nouveau message, puis persiste les deux
   messages après une réponse réussie.
7. `POST /logout` révoque le token et expire le cookie.
8. Une session portant `must_change_password` est limitée au changement de
   mot de passe et au logout. Le serveur invalide aussi les sessions après
   24 heures.

Le premier compte inscrit devient admin, mais V3.0 ne comprend aucune route
d'administration web.

### Sécurité V3.0

- Cookie `HttpOnly`, `SameSite=Strict`, `Path=/` ; pas d'attribut `Secure`
  car le service local utilise HTTP.
- Le proxy écoute uniquement sur `127.0.0.1` (loopback) et n'active pas de
  CORS permissif.
- Le mot de passe est hashé avec scrypt; les erreurs de login ne révèlent pas
  si le compte existe.
- Le cookie et l'expiration serveur limitent les sessions à 24 heures.
- Les sessions d'authentification sont en mémoire du proxy ; un redémarrage
  invalide les anciens cookies et impose une reconnexion.
- Les sessions et messages sont filtrés par `user_id`. Une tentative de lire
  une session appartenant à un autre utilisateur reçoit 404, pas 403.
- Les routes d'administration web ne sont pas disponibles avant V3.1.

### Suite prévue

- V3.1 : routes admin, HTTPS, CSRF et rate limiting.
- V3.2 : multi-admin.

## Séparation build / run

La fabrication et l'installation utilisent des chemins distincts.

### Build (développeur)

- `dev/tools/setup_lacitadelle.py` assemble le runtime thin, le fichier
  `.args` et le GGUF avec `zipalign`.
- `dev/tools/vendor/llamafile/` conserve les assets du build, dont le runtime
  thin et `zipalign`.
- Le résultat est `dist/lacitadelle.llamafile.exe` sous Windows ; l'asset
  préconstruit est publié dans la release GitHub v0.1.0 après vérification de
  son SHA-256.

### Run (utilisateur)

- `dev/tools/bootstrap.py` télécharge le `.llamafile` préconstruit et le GGUF.
- Le runtime va dans `dist/`; le GGUF reste dans
  `dev/tools/vendor/llamafile/`.
- `install.bat` lance le bootstrap puis `lancer.bat`. Aucun build ni appel à
  `zipalign` n'a lieu sur l'ordinateur utilisateur.

Cette séparation retire `zipalign` du parcours utilisateur et réduit le
risque de blocage antivirus associé. Le `.llamafile` reste un exécutable et
peut lui-même être soumis aux règles antivirus de l'environnement.
L'URL de release v0.1.0 et le SHA-256 sont renseignés dans
`dev/tools/llamafile_config.json` ; le bootstrap valide le checksum avant
publication locale.
