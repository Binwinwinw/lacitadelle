# Architecture de La Citadelle (V3.0)

## Vue d'ensemble

La Citadelle est distribuée sous forme d'une archive ZIP autonome, sans Git.
Après extraction, `install.bat` télécharge et vérifie le runtime llamafile-thin
et le modèle GGUF; `lancer.bat` démarre le serveur local, le proxy Python et le
webchat authentifié. Le runtime et le modèle restent séparés.

## Composants

### 1. Runtime : llamafile-thin

- Téléchargé directement depuis la release mozilla-ai/llamafile 0.10.6.
- Installé dans `dist/`; sous Windows, bootstrap le renomme `llamafile.exe`.
- N'embarque pas le GGUF; `lancer.bat` lui passe le chemin du modèle avec `-m`.
- Le serveur HTTP local écoute sur le port 8080 et expose l'API compatible OpenAI `/v1/chat/completions`.

### 2. Modèle externe

- Fichier `dev/tools/vendor/llamafile/Qwen3-1.7B-Q4_K_M.gguf`, d'environ 1,28 Go.
- Qwen3-1.7B Q4_K_M, licence Apache 2.0.
- Téléchargé et vérifié par checksum SHA-256 par `dev/tools/bootstrap.py` ; il n'est pas embarqué dans `dist/llamafile.exe`.

### 3. Bootstrap et packaging

- `dev/tools/llamafile_config.json` marque llamafile-thin et le GGUF comme requis.
- `dev/tools/bootstrap.py` télécharge llamafile-thin dans `dist/` et le GGUF dans `dev/tools/vendor/llamafile/`, puis vérifie les checksums.
- `dev/tools/creer_archive.py` crée `lacitadelle-distribution.zip` sans Git, runtime, GGUF, exécutables ni fichiers de plus de 10 MiB.

### 4. Lancement

- Après extraction de l'archive, `install.bat` vérifie la présence de Python, lance le bootstrap puis démarre `lancer.bat`.
- `lancer.bat` exécute `dist/llamafile.exe -m dev/tools/vendor/llamafile/Qwen3-1.7B-Q4_K_M.gguf --server --host 127.0.0.1 --port 8080 --nologo --log-timestamps`, démarre le proxy Python V3.0 et ouvre `http://localhost:8081`.
- L'installation et le client Python nécessitent Python 3.10+ ; l'exécutable llamafile lui-même est le runtime d'inférence.

### 5. Client conversationnel et mémoire SQLite

- `dev/tools/client.py` est un REPL séparé qui se connecte au serveur llamafile déjà lancé via l'API HTTP locale. Il ne démarre pas le serveur.
- `dev/tools/citadelle_memory.py` gère la base `citadelle_data/memory.db` et ses trois tables V1 : `users`, `sessions` et `messages`.
- Le client V1 utilise l'utilisateur par défaut `lacitadelle`, conserve les conversations localement et envoie au plus 15 messages de contexte.
- Le REPL historique V1 utilise le compte par défaut `lacitadelle`; le proxy web V3 utilise les helpers SQLite filtrés par utilisateur.
- La V1 n'avait pas de login ni de comptes multi-utilisateurs.

## Flux de première installation

1. L'utilisateur extrait `lacitadelle-distribution.zip`; aucun clone Git n'est requis.
2. Il double-clique sur `install.bat`.
3. `install.bat` lance `bootstrap.py`, qui télécharge llamafile-thin et le GGUF, puis vérifie leurs checksums.
4. `install.bat` lance `lancer.bat`, qui démarre llamafile-thin et le proxy puis ouvre le navigateur sur `localhost:8081`.

## Flux d'utilisation quotidienne

### Interface web

1. Double-cliquer sur `lancer.bat`.
2. Le serveur llamafile-thin démarre sur `localhost:8080` et le proxy sur `localhost:8081`.
3. Le navigateur s'ouvre sur `http://localhost:8081`; l'utilisateur se connecte et discute avec Qwen3-1.7B en local, sur CPU.

### Client avec mémoire

1. Démarrer les services avec `lancer.bat`.
2. Dans un terminal séparé, lancer `python dev/tools/client.py`.
3. Utiliser le REPL ; les sessions sont persistées dans SQLite.

## Décisions structurantes

- **Mode external** : llamafile-thin et le modèle restent deux téléchargements distincts.
- **Distribution ZIP** : l'utilisateur extrait l'archive sans Git; les binaires sont téléchargés à l'installation.
- **Contexte 8192** : valeur utilisée par le runtime V1.
- **Téléchargement vérifié** : le bootstrap valide les checksums des assets requis.
- **Mémoire séparée** : le client Python et SQLite fournissent la persistance, hors du runtime.

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

## Distribution et outils développeur

- La release GitHub v0.1.0 contenant l'ancien runtime regroupé est **OBSOLÈTE**; le décideur doit la déprécier manuellement.
