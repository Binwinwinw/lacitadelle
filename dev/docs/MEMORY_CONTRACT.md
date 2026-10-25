# Contrat de la mémoire SQLite — schéma V5

## Rôle et emplacement

`dev/tools/citadelle_memory.py` gère la base SQLite locale
`citadelle_data/memory.db`. Le proxy Python utilise les helpers de ce module
pour isoler les sessions et messages par utilisateur. La base et son contenu
ne sont pas envoyés à un service cloud.

## Schéma V3 de base

La migration V3 définit les tables de comptes, sessions et messages :

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user' CHECK(role IN ('user','admin')),
    is_active INTEGER NOT NULL DEFAULT 1,
    must_change_password INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    last_login_at TEXT
);

CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user','assistant','system')),
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    metadata TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
);
```

Les dates sont enregistrées en UTC au format ISO 8601. `metadata` est un champ
texte nullable utilisé pour les métadonnées JSON des messages.

## Tables ajoutées par les migrations V4 et V5

`migrate_to_v4()` ajoute les préférences :

```sql
CREATE TABLE preferences (
    user_id INTEGER PRIMARY KEY,
    theme TEXT NOT NULL DEFAULT 'light'
        CHECK (theme IN ('light', 'dark')),
    font_size TEXT NOT NULL DEFAULT 'normal'
        CHECK (font_size IN ('small', 'normal', 'large')),
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

`migrate_to_v5()` ajoute les métadonnées d'inférence :

```sql
CREATE TABLE inference_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_id INTEGER,
    timestamp TEXT NOT NULL,
    duration_ms INTEGER NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('ok','error','timeout')),
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE SET NULL
);
```

Les migrations V4 et V5 sont idempotentes et sont appelées par `init_db()`
et au démarrage du proxy. `inference_metrics` ne stocke que les métadonnées :
aucun prompt, aucune réponse générée ni secret.

## Migration V2 vers V3

`migrate_to_v3(db_path=None)` vérifie si `users` contient déjà
`password_hash`. Si le champ est présent, elle considère la migration
terminée et ne fait rien. Sinon, elle désactive temporairement les clés
étrangères et, dans une transaction, supprime puis recrée les tables
`messages`, `sessions` et `users` avec le schéma V3.

Cette migration est **destructive** : les anciens utilisateurs, sessions et
messages sont supprimés. Sauvegarder `citadelle_data/memory.db` avant toute
migration; ne pas lancer cette migration comme simple réparation d'une base
contenant des données à conserver.

Le proxy appelle cette migration au démarrage. `create_admin.py` l'appelle
également avant de créer le premier compte administrateur.

## Fonctions publiques

Le module expose les opérations suivantes :

- `migrate_to_v3(db_path=None)` : migration destructive décrite ci-dessus.
- `migrate_to_v4(db_path=None)` et `migrate_to_v5(db_path=None)` : ajoutent
  respectivement les préférences et les métadonnées d'inférence.
- `init_db(db_path=None)` : crée les tables du schéma V1 si elles sont
  absentes et applique les migrations additives V4/V5; ne migre pas une base
  existante vers V3.
- `record_inference(...)` : persiste uniquement user/session, horodatage,
  durée, statut et compteurs de tokens disponibles.
- `ensure_default_user(db_path=None)` : crée le compte historique
  `lacitadelle` si absent et retourne son identifiant.
- `hash_password(password)` et `verify_password(password, stored_hash)` :
  création et vérification de hash scrypt.
- `generate_strong_password(length=16)` : génère un mot de passe temporaire
  aléatoire; longueur minimale 16.
- `create_session(title=None, db_path=None)` : crée une session associée à
  l'utilisateur V1 par défaut.
- `create_session_for_user(user_id, title=None, db_path=None)` : crée une
  session pour un utilisateur existant.
- `list_sessions(db_path=None)` : liste les sessions du compte par défaut.
- `list_sessions_for_user(user_id, db_path=None)` : liste les sessions
  appartenant à l'utilisateur donné.
- `get_session_for_user(user_id, session_id, db_path=None)` : retourne une
  session seulement si elle appartient à cet utilisateur.
- `add_message(session_id, role, content, metadata=None, db_path=None)` :
  ajoute un message et met à jour `sessions.updated_at`.
- `get_messages(session_id, limit=None, db_path=None)` : récupère les
  messages d'une session, éventuellement limités aux plus récents.
- `get_messages_for_user(user_id, session_id, limit=None, db_path=None)` :
  retourne les messages uniquement si la session appartient à l'utilisateur.
- `delete_session(session_id, db_path=None)` : supprime une session; la clé
  étrangère supprime aussi ses messages.

La création des comptes V3 est faite par `login_server.py` lors de
l'inscription et par `create_admin.py` pour l'administrateur initial. Il n'y
a pas de fonction publique `create_user` ni `get_user_by_username` dans ce
module. L'attribution du rôle est stockée dans `users.role`.

## Limites et précautions

- SQLite et `citadelle_data/memory.db` sont locaux; aucune synchronisation
  cloud ni chiffrement de la base n'est fourni.
- Les helpers V1 `init_db`, `ensure_default_user`, `create_session` et
  `list_sessions` restent présents pour le REPL historique; le proxy web
  utilise les opérations filtrées par `user_id`.
- Les sessions d'authentification du proxy sont conservées en mémoire par le
  processus et disparaissent à son redémarrage.
- Les suppressions de sessions appliquent `ON DELETE CASCADE` aux messages.
