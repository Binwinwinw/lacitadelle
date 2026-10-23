# Contrat de la mémoire SQLite

> **Note** : ce contrat couvre le schéma mémoire actuel. Les passages décrivant le client V1 et le login V2 sont historiques.

## Contexte

La Citadelle doit offrir une mémoire persistante des conversations.
Le décideur a tranché : une seule base SQLite, 3 tables en V1
(users, sessions, messages). Une 4e table (lacitadelle) est documentée
pour la V2 (traçage des instances de l'assistant).

## Décisions actées (V1)

1. Une seule base SQLite : `citadelle_data/memory.db`.
2. Trois tables :
   - `users` : id (PK), username (UNIQUE), created_at.
   - `sessions` : id (PK), user_id (FK → users.id), title,
     created_at, updated_at.
   - `messages` : id (PK), session_id (FK → sessions.id),
     role CHECK IN ('user','assistant','system'), content,
     created_at, metadata.
3. Hiérarchie : user → session → message.
   - Une session = une conversation (dans la V1).
   - `lacitadelle` = rôle `'assistant'` dans `messages`. Pas d'entité
     séparée en V1.
4. La base est créée au premier lancement si absente.
5. Un utilisateur par défaut est créé : `username = 'lacitadelle'`
   (utilisateur humain, pas l'assistant — le nom est cosmétique et
   peut être changé en V2).
6. `citadelle_data/` est gitignoré (données utilisateur).
7. La mémoire est gérée côté client ou proxy Python, pas côté llamafile.

## Schéma SQL V1

    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('user','assistant','system')),
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        metadata TEXT,
        FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
    );

## Schéma documenté pour V2 (non implémenté)

Ajout d'une 4e table `lacitadelle` :

- id (PK), model_name, system_prompt, created_at.
- `messages.lacitadelle_id` (FK → lacitadelle.id) pour tracer quelle
  instance de l'assistant a répondu (utile si on change de modèle
  ou si on garde plusieurs versions).

## Politique de conservation

V1 : conservation illimitée (suppression manuelle du fichier memory.db
par l'utilisateur). V2+ : purge, archivage, chiffrement éventuel.

## Non-objectifs (v1)

- Pas de synchronisation cloud.
- Pas de chiffrement.
- Pas de multi-utilisateurs actifs (le user par défaut est unique).
- Pas d'interface UI dédiée (client texte).

## Impact sur le code

- Nouveau module `dev/tools/citadelle_memory.py` (à créer dans une
  tâche ultérieure).
- Fonctions : init_db, ensure_default_user, create_session,
  add_message, get_messages.
- Utilisé par le futur client texte.

## Évolutions futures (V2+)

### Lancement automatique de llamafile par le client

En V1, le client ne lance pas llamafile : l'utilisateur lançait
`dist/lacitadelle.llamafile.exe` dans un terminal séparé, puis
`python dev/tools/client.py` dans un autre. Ce choix séparait les
responsabilités (serveur d'inférence vs client conversationnel) et
permet à l'utilisateur de voir les logs du serveur.

En V2+, on pourrait envisager un lancement automatique par le
client. Cela nécessiterait :

- Le lancement du processus llamafile avec les
  arguments adéquats.
- L'attente que le serveur HTTP soit prêt (polling sur `/v1/models`
  jusqu'à succès, avec timeout).
- La capture des logs (stdout/stderr) pour les remonter dans
  l'interface utilisateur.
- La gestion du cycle de vie (kill propre à la sortie du client,
  gestion des ports occupés, détection d'une instance déjà lancée).
- La gestion des erreurs de lancement (binaire manquant, permissions).

Ces fonctionnalités sont hors périmètre V1. Le mode actuel
(lancement manuel) est le comportement documenté et supporté pour
toutes les versions jusqu'à ce qu'une décision explicite acte le
changement.

### Multi-utilisateurs (login)

La table `users` existe avec `username UNIQUE`. En V1, un
utilisateur par défaut (`lacitadelle`) est utilisé. En V2+, on
pourra ajouter une authentification et filtrer les sessions par
`user_id` (via `list_sessions_for_user(user_id)`). L'architecture
actuelle supporte cette évolution sans modification du schéma.
