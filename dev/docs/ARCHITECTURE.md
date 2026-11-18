# Architecture de La Citadelle (V3.0)

## Vue d'ensemble

La Citadelle est distribuée sous forme d'une archive ZIP autonome, sans Git,
et d'un exécutable autonome Windows produit localement avec PyInstaller.
L'archive source utilise `install.py`/`lancer.py` et les wrappers natifs;
l'exécutable one-file fonctionne sans Python installé. Dans les deux modes,
runtime et modèle GGUF sont téléchargés et vérifiés séparément au premier
lancement.

## Composants

### 1. Runtime : llamafile-thin

- Téléchargé directement depuis la release mozilla-ai/llamafile 0.10.6.
- Installé dans `dist/` sous le nom `llamafile.exe`, `llamafile-linux` ou
  `llamafile-macos` selon l'OS.
- N'embarque pas le GGUF; `lancer.py` lui passe le chemin du modèle avec `-m`.
- Le serveur HTTP local écoute sur le port 8080 et expose l'API compatible OpenAI `/v1/chat/completions`.

### 2. Modèle externe

- Fichier `dev/tools/vendor/llamafile/Qwen3-4B-Q4_K_M.gguf`, d'environ 2,5 Go.
- Qwen3-4B Q4_K_M, licence Apache 2.0.
- Téléchargé et vérifié par checksum SHA-256 par `dev/tools/bootstrap.py` ;
  il n'est pas embarqué dans le runtime.

### 3. Bootstrap et packaging

- `dev/tools/packaging/build.spec` et `build.py` produisent
  `dist/release/LaCitadelle.exe` sous Windows. Les fichiers de travail sont
  temporaires; le build ne nettoie pas `dist/`.
- En mode gelé, les ressources en lecture seule sont chargées depuis le bundle
  PyInstaller; runtime et GGUF vont dans
  `%APPDATA%\LaCitadelle\assets\`, la base dans
  `%APPDATA%\LaCitadelle\citadelle_data\` et le log proxy dans
  `%APPDATA%\LaCitadelle\proxy.log`.
- L'exécutable relance son propre binaire avec un mode proxy interne; il ne
  dépend pas d'un interpréteur Python système.
- Sous Windows, llamafile utilise une console dédiée sans redirection stdout
  ou stderr; l'arrêt du proxy ne termine pas le runtime.
- `dev/tools/llamafile_config.json` décrit un seul asset runtime universel,
  ses destinations par OS et le GGUF requis.
- `dev/tools/bootstrap.py` choisit la destination selon l'OS, télécharge le
  runtime dans `dist/` et le GGUF dans `dev/tools/vendor/llamafile/`, puis
  vérifie les checksums et rend le runtime exécutable sur Unix.
- `dev/tools/creer_archive.py` crée `lacitadelle-distribution.zip` sans Git, runtime, GGUF, exécutables ni fichiers de plus de 10 MiB.

### 4. Lancement

- Après extraction, l'un des wrappers natifs lance `install.py`, qui exécute le
  bootstrap puis `lancer.py`.
- `lancer.py` démarre le binaire correspondant à l'OS avec le GGUF et les
  mêmes options de serveur (loopback, port 8080), démarre le proxy Python V3.1
  sur le port 8081 et ouvre `http://localhost:8081`.
- L'installation et le client Python nécessitent Python 3.10+ ; l'exécutable llamafile lui-même est le runtime d'inférence.

### 5. Client conversationnel et mémoire SQLite

- `dev/tools/client.py` est un REPL séparé qui se connecte au serveur llamafile déjà lancé via l'API HTTP locale. Il ne démarre pas le serveur.
- `dev/tools/citadelle_memory.py` gère la base `citadelle_data/memory.db` et ses trois tables V1 : `users`, `sessions` et `messages`.
- Le client V1 utilise l'utilisateur par défaut `lacitadelle`, conserve les conversations localement et envoie au plus 15 messages de contexte.
- Le REPL historique V1 utilise le compte par défaut `lacitadelle`; le proxy web V3 utilise les helpers SQLite filtrés par utilisateur.
- La V1 n'avait pas de login ni de comptes multi-utilisateurs.

## Flux de première installation

1. L'utilisateur extrait `lacitadelle-distribution.zip`; aucun clone Git n'est requis.
2. Il lance le wrapper d'installation natif correspondant à son OS.
3. `install.py` appelle `bootstrap.py`, qui télécharge le runtime universel
   et le GGUF, puis vérifie leurs checksums.
4. `install.py` lance `lancer.py`, qui démarre le runtime adapté, le proxy et
   le navigateur sur `localhost:8081`.

## Flux d'utilisation quotidienne

### Interface web

1. Lancer `lancer.bat`, `lancer.sh` ou `lancer.command` selon l'OS.
2. Le serveur llamafile-thin démarre sur `localhost:8080` et le proxy sur `localhost:8081`.
3. Le navigateur s'ouvre sur `http://localhost:8081`; l'utilisateur se connecte et discute avec Qwen3-4B en local, sur CPU.

### Client avec mémoire

1. Démarrer les services avec le wrapper natif `lancer.*`.
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

## AIWorkflow

Spécification de conception préalable à l'implémentation. Cette section ne
décrit pas des composants déjà livrés.

### 1. Vue d'ensemble

- **AIWorkflow** est une orchestration externe écrite en Python. Le code du
  workflow choisit les étapes et leur ordre; le LLM n'orchestre pas le
  processus.
- Les modèles assurent uniquement le raisonnement local, sous la forme
  **texte en entrée → texte en sortie**.
- Les outils sont des fonctions Python appelées explicitement par les nœuds.
  Les traitements déterministes restent séparés des accès explicites aux
  fichiers, à SQLite, au modèle et, facultativement, au Web.
- Le retrieval documentaire utilise **SQLite FTS5**, hors ligne, intégré à
  SQLite et sans dépendance de recherche supplémentaire.
- Aucun tool calling natif : le modèle ne reçoit ni catalogue d'outils ni
  schémas de fonctions.

### 2. Moteur d'orchestration (`dev/tools/workflow_engine.py`)

- `Workflow` contient une liste ordonnée de nœuds et les exécute séquentiellement.
- `Node` est la classe abstraite des nœuds; sa méthode `execute(context)` reçoit
  le contexte partagé.
- `SharedContext` est un dictionnaire partagé contenant les entrées, les sorties
  intermédiaires et l'état d'exécution.
- `NodeOut` appelle une fonction Python explicitement associée au nœud.
- `NodeModel` appelle le modèle courant avec un prompt et transmet son texte de
  réponse au contexte.
- `NodeCondition` évalue une condition et choisit la suite du parcours parmi les
  nœuds déclarés.
- Chaque nœud peut définir sa politique de retry. Le moteur applique cette
  politique; si les tentatives sont épuisées, il signale l'erreur et arrête le
  workflow sans produire de résultat de succès de remplacement.
- Le moteur contrôle les transitions et les erreurs. Il n'expose jamais les
  outils au modèle et n'interprète pas la réponse du modèle comme un appel
  d'outil.

### 3. Nœuds outils (plug-ins)

Les premières fonctions outils prévues sont :

| Fonction | Rôle |
| --- | --- |
| `extract_text(path)` | Extrait le texte brut de PDF, Markdown ou TXT. La bibliothèque PDF reste à choisir; elle devra fonctionner hors ligne. |
| `index_fts5(path, content)` | Découpe et indexe le contenu d'un document dans SQLite FTS5. |
| `search_fts5(query)` | Recherche et retourne les passages les plus pertinents dans l'index FTS5. |
| `call_model(prompt, model_path)` | Envoie un prompt au modèle sélectionné via l'API locale llamafile. |
| `search_web(query)` | Recherche via une API à définir; optionnelle et dépendante du réseau. |
| `query_sql(sql)` | Interroge la base SQLite de La Citadelle; l'accès est en lecture seule. |

Chaque nœud devra avoir une signature claire, une docstring, une gestion
explicite des erreurs et pouvoir être testé isolément. L'accès Web ne fait pas
partie du parcours hors ligne et ne sera pas activé par défaut.

### 4. Retrieval documentaire (SQLite FTS5)

- Table virtuelle prévue : `documents_fts(content, path, metadata)`.
- L'indexation découpe les documents en chunks dont la taille est configurable;
  chaque chunk conserve le chemin source et ses métadonnées.
- La recherche utilise `MATCH` et retourne un top-N de passages pertinents,
  avec leur chemin source et leurs métadonnées.
- L'indexation et la recherche n'appellent aucun LLM.
- FTS5 est le choix retenu. Whoosh (Python pur) et LlamaIndex (si utilisable
  hors ligne) sont des alternatives étudiées, non des dépendances du moteur;
  elles ne seront réévaluées qu'en cas de besoin démontré.

### 5. Intégration modèles

- Modèles de raisonnement retenus : **Ornith-1.5-9B** et **Qwen3.5-9B**,
  co-champions avec des résultats de 5/5.
- **Llama-3.1-8B** reste optionnel pour des essais de tool calling natif si un
  besoin dynamique le justifie; ce n'est pas une priorité.
- Les appels passent par `NodeModel` et l'API llamafile compatible OpenAI déjà
  en place.
- Les modèles reçoivent du texte et retournent du texte. Le code Python effectue
  les appels aux outils; aucun tool calling natif n'est requis.

### 6. Associations et règles

- Un workflow est défini dans un fichier Python sous `dev/workflows/`.
- Chaque workflow déclare ses nœuds et leur ordre; les nœuds conditionnels
  définissent les branches possibles.
- Les nœuds outils sont placés sous `dev/tools/nodes/`.
- Les appels aux modèles passent exclusivement par `NodeModel`, jamais par un
  appel direct depuis un workflow.
- Le workflow applique la politique de retry de chaque nœud; une erreur non
  résolue arrête proprement l'exécution et reste observable.
- Prévoir au minimum un test par nœud et un test d'exécution par workflow
  complet.

### 7. Workflows prioritaires (après la spécification)

- **Analyse PDF** : extraction → indexation FTS5 → recherche → appel modèle →
  formatage.
- **Recherche Web** : recherche Web → appel modèle → formatage; workflow
  facultatif nécessitant le réseau.
- **Analyse SQL** : requête en lecture seule → appel modèle → formatage.
- **Analyse Markdown** : extraction → indexation FTS5 → recherche → appel
  modèle.

### 8. Hors périmètre

- **Graphify** : POC clôturé KO (backend LLM absent et réseau interdit); aucune
  intégration prévue.
- **Obsidian** : aucun rôle en production.
- **Tool calling natif LLM** : non retenu, notamment au vu du manque de fiabilité
  observé sur les modèles.
- **Frameworks lourds** tels que LangChain ou LlamaIndex : écartés pour cette
  conception, à réévaluer seulement si un besoin le justifie.
