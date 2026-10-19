# Contrat d'authentification V3

## Contexte

La V2 utilise un login sans mot de passe : le nom d'utilisateur suffit et les sessions d'authentification sont conservées en mémoire du proxy. La V3 ajoute une authentification par mot de passe, les rôles `user` et `admin`, l'inscription automatique, une page d'administration et la gestion des comptes.

Ce document spécifie la cible V3 ; ces comportements ne sont pas encore implémentés.

## Décisions actées (2026-10-19)

### Rôles et comptes

- Deux rôles existent : `user` (rôle par défaut) et `admin`.
- Les utilisateurs peuvent s'inscrire eux-mêmes en V3 ; aucune approbation d'un administrateur n'est requise. Une validation par admin est hors périmètre V3, envisagée pour V4.
- Le premier compte créé après la migration devient `admin` s'il n'existe encore aucun administrateur. Tous les comptes suivants sont créés avec le rôle `user`.
- Une seule session d'authentification est active par utilisateur : un nouveau login révoque son ancien token.
- Un utilisateur désactivé (`is_active = 0`) ne peut pas se connecter.

### Création de compte

- `GET /register` sert le formulaire d'inscription.
- `POST /register` reçoit `username`, `password` et `password_confirm`.
- Le nom d'utilisateur, après retrait des espaces périphériques, doit contenir de 3 à 50 caractères et correspondre à `^[A-Za-z0-9_-]{3,50}$` ; il doit être unique.
- Le mot de passe doit contenir au moins 8 caractères. `password_confirm` doit correspondre au mot de passe.
- En cas de succès, le compte est créé et le navigateur est redirigé vers `/login`. L'inscription ne connecte donc pas automatiquement l'utilisateur.

### Mot de passe

- Le mot de passe est dérivé avec `hashlib.scrypt` (stdlib), jamais stocké ni journalisé en clair.
- Paramètres V3 : `n=16384` (`2^14`), `r=8`, `p=1`, salt aléatoire de 16 octets, résultat de 32 octets.
- Format de stockage : `scrypt$<n>$<r>$<p>$<salt_hex>$<hash_hex>`.
- La vérification recalcule le hash avec les paramètres et le salt stockés, puis compare avec `hmac.compare_digest`.
- Un échec de login renvoie le même statut et un message générique, que le nom soit inconnu, le mot de passe incorrect ou le compte désactivé ; la réponse ne révèle pas si le nom existe.

### Session

- Le cookie s'appelle `lacitadelle_session` et a `Max-Age=86400` (24 heures), `HttpOnly`, `SameSite=Strict` et `Path=/`.
- `Secure` n'est pas posé : le proxy reste en HTTP local sur loopback.
- L'expiration de 24 heures est appliquée côté serveur également ; l'expiration du cookie navigateur seule ne suffit pas à invalider le token conservé par le proxy.
- Les sessions restent en mémoire du proxy, comme en V2. Un redémarrage du proxy les invalide et impose une reconnexion.
- Un logout révoque le token et expire le cookie.

### Administration

- `GET /admin` sert la page d'administration uniquement à un administrateur.
- La page liste les utilisateurs avec `id`, `username`, `role`, `is_active`, `last_login_at` et `created_at`.
- Les actions admin permettent de créer un utilisateur, l'activer ou le désactiver, réinitialiser son mot de passe avec un mot de passe temporaire, supprimer un compte et changer son rôle.
- `DELETE /admin/users/{id}` ne peut pas supprimer le compte de l'administrateur qui fait la requête.
- Le non-admin reçoit un refus d'accès HTTP 403 ; l'interface peut ensuite le renvoyer vers `/`. Une requête non authentifiée est renvoyée vers `/login`.
- Il ne peut pas y avoir plusieurs administrateurs simultanément. L'attribution du rôle `admin` lors de la toute première inscription doit être atomique afin que deux inscriptions concurrentes ne créent pas deux admins.

## Modèle de données V3

### Table `users`

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user' CHECK(role IN ('user','admin')),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    last_login_at TEXT
);
```

`last_login_at` est mis à jour après un login réussi. Les dates sont stockées au format ISO 8601 UTC, cohérent avec la couche mémoire existante.

## Migration V2 vers V3

La base V2 contient des utilisateurs sans `password_hash`. La migration V3 supprime tous les utilisateurs existants ; les clés étrangères en cascade suppriment également leurs sessions et leurs messages. Les conversations V2 ne sont pas conservées et les utilisateurs doivent se réinscrire.

La migration doit se terminer avec le schéma `users` V3 ci-dessus et s'exécuter de façon transactionnelle. Comme la table ne contient plus de données à préserver, sa reconstruction peut remplacer l'ancien schéma. Cette opération est destructive et ne doit pas être confondue avec une migration conservant les données.

Après la migration, la première inscription devient admin selon la règle de création de compte ci-dessus. Cette inscription initiale doit être effectuée sur la machine locale de confiance.

## Routes V3

### Routes de compte

| Méthode | Route | Comportement |
| --- | --- | --- |
| `GET` | `/register` | Sert le formulaire d'inscription. |
| `POST` | `/register` | Valide username/password/password_confirm, crée le compte et redirige vers `/login`. |
| `POST` | `/login` | Vérifie username, mot de passe et état actif ; établit une session de 24 h. Une erreur renvoie `401` sans révéler si le nom existe. |
| `POST` | `/logout` | Révoque le token et expire le cookie. |

### Routes d'administration

Toutes ces routes exigent une session valide avec le rôle `admin`.

| Méthode | Route | Comportement |
| --- | --- | --- |
| `GET` | `/admin` | Sert l'interface et la liste des utilisateurs. |
| `POST` | `/admin/users` | Crée un compte depuis l'administration. |
| `POST` | `/admin/users/{id}/reset` | Remplace le hash par celui d'un mot de passe temporaire fourni par l'admin. |
| `POST` | `/admin/users/{id}/toggle` | Active ou désactive le compte ciblé. |
| `POST` | `/admin/users/{id}/role` | Change le rôle entre `user` et `admin`, sans créer plusieurs admins simultanés. |
| `DELETE` | `/admin/users/{id}` | Supprime le compte et ses données liées ; refuse la suppression du compte appelant. |

### Routes V2 conservées

Les routes `/api/sessions`, `/api/sessions/{id}/messages` et les opérations de logout restent disponibles. Les API de sessions et messages continuent à filtrer chaque accès par `user_id` ; une ressource absente ou appartenant à un autre utilisateur ne doit pas être distinguable.

## Flux d'authentification

1. L'utilisateur visite `/register`, choisit un nom et un mot de passe, puis confirme ce mot de passe.
2. Le proxy valide les champs, calcule le hash scrypt et crée l'utilisateur. Si aucun admin n'existe, ce premier utilisateur reçoit le rôle `admin` ; sinon il reçoit `user`.
3. Le proxy redirige vers `/login`. Le login vérifie le hash et `is_active` avant de créer le token.
4. Le navigateur reçoit le cookie de session 24 h et accède au chat ainsi qu'aux routes API V2 filtrées par `user_id`.
5. Un admin peut ouvrir `/admin` pour gérer les comptes. Un `user` n'accède pas à cette page.
6. Le logout révoque le token. À l'expiration ou au redémarrage du proxy, l'utilisateur doit se reconnecter.

## Sécurité

- Les mots de passe ne sont jamais enregistrés en clair ni écrits dans les logs.
- La comparaison des hashes utilise `hmac.compare_digest`.
- Les échecs d'authentification ne divulguent pas l'existence d'un nom d'utilisateur.
- Les sessions et messages restent filtrés par `user_id` ; les accès inter-utilisateurs sont refusés sans révéler l'existence de la ressource.
- Le cookie est `HttpOnly`, `SameSite=Strict`, limité à `Path=/` et valable 24 heures ; pas de `Secure` car l'usage est local en HTTP.
- Le proxy doit rester lié à `127.0.0.1` et ne pas être exposé sur un réseau.
- V3 n'ajoute ni protection CSRF ni rate limiting ; ce sont des limites explicites du périmètre local V3, pas des garanties de sécurité.

## Non-objectifs V3

- Pas de mot de passe oublié public : reset réservé à l'admin ; reset par email reporté à V4.
- Pas de validation d'adresse email.
- Pas d'OAuth ni de SSO.
- Pas de 2FA.
- Pas de jeton CSRF.
- Pas de rate limiting.
- Pas de journal d'audit.
- Pas de plusieurs administrateurs simultanés.

## Critères d'acceptation

- Un utilisateur peut créer un compte avec un nom valide et un mot de passe d'au moins 8 caractères.
- Le premier compte créé après migration devient admin ; les inscriptions ultérieures deviennent `user` tant qu'un admin existe.
- Un utilisateur peut se connecter avec son nom et son mot de passe ; un mauvais mot de passe renvoie `401` sans indiquer si le nom existe.
- Un compte désactivé ne peut pas se connecter.
- Un admin peut ouvrir `/admin` et gérer les comptes ; un non-admin reçoit un refus d'accès.
- Un admin peut créer, désactiver, réactiver, réinitialiser et changer le rôle d'un compte.
- Un administrateur ne peut pas supprimer son propre compte.
- Le cookie et la validation côté serveur expirent après 24 heures.
- Les données V2 existantes (utilisateurs, sessions et messages) sont supprimées par la migration.

## Plan d'implémentation (Next Move)

1. **Next Move 8b** : migration SQLite, hash et vérification du mot de passe dans `citadelle_memory.py`, avec tests unitaires.
2. **Next Move 8c** : routes `/register`, modification de `/login` et frontend register/login.
3. **Next Move 8d** : page `/admin`, routes de gestion et frontend admin.
4. **Next Move 8e (optionnel)** : tests d'intégration complets.

## Points à préciser avant implémentation admin

- Le décideur a fixé l'unicité des admins mais pas le protocole de transfert du rôle. Le changement vers `admin` doit éviter deux admins simultanés ; le transfert atomique ou la séquence de rétrogradation/promotion est à choisir avant Next Move 8d.
- Le comportement pour le dernier admin n'est pas précisé : confirmer si sa désactivation ou sa rétrogradation doit être refusée afin de ne pas laisser l'installation sans administrateur.
- Le mot de passe temporaire du reset est fourni par l'admin ; la durée de validité et l'obligation de le changer au prochain login ne sont pas spécifiées.
- La désactivation doit empêcher les nouveaux logins. La révocation immédiate d'une session déjà ouverte lors de la désactivation est à confirmer pour l'implémentation.
