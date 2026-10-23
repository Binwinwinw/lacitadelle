# Contrat d'authentification V3

## Contexte

La V2 historique utilisait un login sans mot de passe. La V3.0 livrée ajoute
l'authentification par mot de passe, l'inscription, le changement obligatoire
de mot de passe et les sessions en mémoire du proxy. Les routes
d'administration sont reportées en V3.1, avec HTTPS, CSRF et rate limiting.

Ce document décrit le comportement V3.0 livré et les extensions prévues en
V3.1 et V3.2. Les routes admin ci-dessous sont une cible V3.1, pas des routes
disponibles en V3.0.

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
- Le premier compte inscrit après la migration devient l'unique `admin` si aucun administrateur n'existe. Cette attribution doit être atomique pour que deux inscriptions concurrentes ne créent pas deux administrateurs.

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

### Administration (cible V3.1)

- `GET /admin` sert la page d'administration uniquement à un administrateur.
- La page liste les utilisateurs avec `id`, `username`, `role`, `is_active`, `last_login_at` et `created_at`.
- Les actions admin permettent de créer un utilisateur, l'activer ou le désactiver, réinitialiser son mot de passe avec un mot de passe temporaire, supprimer un compte et changer son rôle.
- `DELETE /admin/users/{id}` ne peut pas supprimer le compte de l'administrateur qui fait la requête.
- Le non-admin reçoit un refus d'accès HTTP 403 ; l'interface peut ensuite le renvoyer vers `/`. Une requête non authentifiée est renvoyée vers `/login`.
- En V3.1, il ne peut y avoir qu'un seul administrateur. Seul l'administrateur courant peut promouvoir un utilisateur ; cette opération rétrograde l'appelant et promeut la cible dans une même transaction SQLite. La rétrogradation de l'appelant est interdite en dehors de ce transfert atomique.
- Un administrateur ne peut pas se désactiver, se rétrograder hors transfert, ni supprimer son propre compte. Toute opération qui désactiverait, rétrograderait ou supprimerait le dernier admin actif est refusée.
- V3.2 autorise jusqu'à `max_admins` (2 par défaut) ; les changements de rôle et transferts restent atomiques et doivent conserver au moins un admin actif.
- En V3.1, lors d'un reset admin, un mot de passe temporaire aléatoire et fort de 16 caractères est généré, hashé et affiché à l'administrateur une seule fois. `must_change_password` est mis à `1`.
- Un login avec un mot de passe temporaire valide crée une session restreinte. Jusqu'au changement du mot de passe, seules `/change-password` et `/logout` sont accessibles ; les autres routes redirigent vers `/change-password`.
- En V3.1, la désactivation, le reset de mot de passe ou la suppression d'un utilisateur révoque immédiatement tous ses tokens en mémoire. Une requête ultérieure avec un token révoqué reçoit `401`.

## Décisions actées (complément 2026-10-19)

### Décision 1 — Transfert atomique du rôle admin

En V3.1, un seul admin est permis. La route de changement de rôle ne peut promouvoir un autre utilisateur que si l'appelant est l'admin courant ; l'appelant est alors rétrogradé en `user` et la cible promue en `admin` dans la même transaction SQLite. Aucun état validé ne contient deux admins. Un appelant non-admin ne peut changer aucun rôle. En V3.2, plusieurs admins sont permis dans la limite de `max_admins` ; les transferts dans les deux sens restent transactionnels.

### Décision 2 — Protection du dernier admin

En V3.1, un admin ne peut pas se désactiver lui-même, se rétrograder hors transfert, ni supprimer son propre compte. Toute opération qui laisserait zéro admin actif est refusée. Les actions sur un autre compte admin ne s'appliquent pas avant V3.2, où plusieurs admins sont permis.

### Décision 3 — Mot de passe temporaire

En V3.1, un reset admin génère un mot de passe temporaire fort et aléatoire de 16 caractères, le hash avec scrypt, positionne `must_change_password = 1` et affiche le secret à l'admin une seule fois. Le login avec ce secret est autorisé, mais la session porte le flag `must_change_password` : seules `/change-password` et `/logout` sont accessibles tant que le mot de passe n'a pas été changé. La nouvelle valeur doit faire au moins 8 caractères, être différente de l'ancienne et correspondre à sa confirmation ; le succès met à jour le hash, remet le flag à `0` et redirige vers `/`.

**Durée du mot de passe temporaire** : valide indéfiniment en V3.1 (pas d'expiration automatique). L'admin peut régénérer un nouveau mot de passe temporaire à tout moment via `POST /admin/users/{id}/reset`. En cas de doute, l'admin doit régénérer.

### Décision 4 — Révocation immédiate des sessions

En V3.1, la désactivation (`is_active = 0`), le reset de mot de passe et la suppression d'un utilisateur retirent immédiatement tous ses tokens de `SESSIONS`. Une requête ultérieure avec un ancien cookie reçoit `401` ; pour un compte supprimé, aucun utilisateur n'est retrouvé.

## Modèle de données V3

### Table `users`

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
| `GET` | `/change-password` | Sert le formulaire obligatoire si la session porte `must_change_password = 1`. |
| `POST` | `/change-password` | Vérifie l'ancien mot de passe, valide et confirme le nouveau, met à jour le hash, efface le flag et redirige vers `/`. |

Après une connexion avec un mot de passe temporaire, toute route autre que `/change-password` et `/logout` redirige vers `/change-password`.

### Routes d'administration (V3.1)

Toutes ces routes exigent une session valide avec le rôle `admin`.

| Méthode | Route | Comportement |
| --- | --- | --- |
| `GET` | `/admin` | Sert l'interface et la liste des utilisateurs. |
| `POST` | `/admin/users` | Crée un compte depuis l'administration. |
| `POST` | `/admin/users/{id}/reset` | Génère un mot de passe temporaire aléatoire de 16 caractères, stocke son hash, positionne `must_change_password = 1`, révoque les sessions et affiche le secret une seule fois. |
| `POST` | `/admin/users/{id}/toggle` | Active ou désactive le compte ciblé. |
| `POST` | `/admin/users/{id}/role` | Change le rôle entre `user` et `admin` selon le transfert atomique unique-administrateur défini ci-dessus. |
| `DELETE` | `/admin/users/{id}` | Supprime le compte et ses données liées ; refuse la suppression du compte appelant. |

La désactivation révoque immédiatement les tokens de l'utilisateur. Un administrateur ne peut désactiver ni rétrograder son propre compte ; une promotion d'un autre utilisateur est le seul transfert permis et rétrograde l'administrateur appelant dans la même transaction.

Les routes admin sont explicitement reportées en V3.1. Voir
`.memory/decisions.md`, entrée `[2026-10-21] Routes admin reportées en V3.1`.
Elles ne sont pas disponibles dans le proxy V3.0.

### Routes V2 conservées

Les routes `/api/sessions`, `/api/sessions/{id}/messages` et les opérations de logout restent disponibles. Les API de sessions et messages continuent à filtrer chaque accès par `user_id` ; une ressource absente ou appartenant à un autre utilisateur ne doit pas être distinguable.

- `POST /api/sessions/{id}/messages` accepte `Content-Type: application/json`
  avec le corps `{"content": "..."}`. En cas de succès, la réponse est
  `201 Created` avec le corps
  `{"assistant_message": {"role": "assistant", "content": "..."}}`.
- La requête reçoit `400 Bad Request` si `content` est vide ou n'est pas une
  chaîne.

## Flux d'authentification

1. L'utilisateur visite `/register`, choisit un nom et un mot de passe, puis confirme ce mot de passe.
2. Le proxy valide les champs, calcule le hash scrypt et crée l'utilisateur. Si aucun admin n'existe, ce premier utilisateur reçoit le rôle `admin` ; sinon il reçoit `user`.
3. Le proxy redirige vers `/login`. Le login vérifie le hash et `is_active` avant de créer le token.
4. Le navigateur reçoit le cookie de session 24 h et accède au chat ainsi qu'aux routes API V2 filtrées par `user_id`.
5. À partir de V3.1, un admin peut ouvrir `/admin` pour gérer les comptes. Un `user` n'accède pas à cette page.
6. Le logout révoque le token. À l'expiration ou au redémarrage du proxy, l'utilisateur doit se reconnecter.

## Sécurité

- Les mots de passe ne sont jamais enregistrés en clair ni écrits dans les logs.
- En V3.1, les mots de passe temporaires de reset sont générés aléatoirement, affichés une seule fois à l'admin et imposent un changement au prochain accès.
- La comparaison des hashes utilise `hmac.compare_digest`.
- Les échecs d'authentification ne divulguent pas l'existence d'un nom d'utilisateur.
- Les sessions et messages restent filtrés par `user_id` ; les accès inter-utilisateurs sont refusés sans révéler l'existence de la ressource.
- Le cookie est `HttpOnly`, `SameSite=Strict`, limité à `Path=/` et valable 24 heures ; pas de `Secure` car l'usage est local en HTTP.
- En V3.1, la révocation d'un token après désactivation, reset ou suppression est immédiate en mémoire ; les requêtes ultérieures de cette session reçoivent `401`.
- V3.0 reste liée à `127.0.0.1` et utilise HTTP local. Elle n'ajoute ni protection CSRF ni rate limiting ; ces limites ne sont acceptables que pour cet usage local.
- En V3.1, HTTPS, validation CSRF pour chaque POST/DELETE et limitation de débit sur le login deviennent obligatoires avant toute écoute sur le réseau local.
- Un certificat auto-signé V3.1 déclenche un avertissement navigateur. En entreprise, l'administrateur doit distribuer le certificat dans le magasin de confiance des clients (GPO Windows, MDM ou équivalent).

## Cadre de déploiement progressif (V3.0 / V3.1 / V3.2)

### V3.0 — Authentification de base, HTTP local

- Le proxy écoute uniquement sur `127.0.0.1:8081` en HTTP.
- CSRF et rate limiting ne sont pas actifs ; ce sont des limites explicites pour l'usage local.
- Les routes d'authentification disponibles sont register, login,
  change-password et logout. Le premier inscrit devient admin, mais les
  routes d'administration web ne sont pas implémentées.
- L'administration web et ses règles de gestion des comptes sont reportées
  en V3.1.
- La structure de `citadelle_data/config.json` prévoit `host` et `port`. La structure CSRF est prévue mais désactivée.

### V3.1 — HTTPS et protections pour réseau local

- Implémenter les routes admin `/admin`, `/admin/users`, reset, toggle, role
  et delete, avec un seul administrateur actif.
- Le proxy écoute sur `0.0.0.0:8081` ou une adresse LAN configurable dans `config.json`.
- HTTPS utilise un certificat auto-signé généré au premier lancement (OpenSSL en sous-processus ou solution standard disponible), puis un `SSLContext`.
- Un token CSRF par session est injecté dans le HTML et vérifié sur toutes les requêtes POST et DELETE.
- Le rate limiting du login est de 5 tentatives par minute par IP et de 5 tentatives par minute par nom d'utilisateur.
- Le certificat auto-signé affiche un avertissement navigateur. En entreprise, l'informaticien distribue le certificat dans le magasin de confiance des clients (GPO Windows, MDM ou équivalent).
- Let's Encrypt via reverse proxy (Caddy ou nginx) est reporté à V4.

### V3.2 — Multi-admin et configuration réseau avancée

- Plusieurs admins sont permis, avec `max_admins = 2` par défaut. Les transferts de rôle sont atomiques dans les deux sens.
- `citadelle_data/config.json`, généré au premier lancement avec des valeurs par défaut, contient `host`, `port`, `ssl_cert`, `ssl_key`, `max_admins` et `rate_limit_login`.

## Non-objectifs V3

- Pas de routes d'administration en V3.0 ; elles sont prévues en V3.1.
- Pas de mot de passe oublié public : reset réservé à l'admin ; reset par email reporté à V4.
- Pas de validation d'adresse email.
- Pas d'OAuth ni de SSO.
- Pas de 2FA.
- Pas de jeton CSRF ni de rate limiting en V3.0 ; ces protections sont prévues en V3.1.
- Pas de journal d'audit.
- Pas de plusieurs administrateurs simultanés avant V3.2.

## Critères d'acceptation

- **V3.0** : un utilisateur peut s'inscrire avec un mot de passe d'au moins
  8 caractères, se connecter, changer son mot de passe temporaire et se
  déconnecter. Le cookie et la validation serveur expirent après 24 heures.
- **V3.0** : le premier inscrit devient admin ; les inscriptions suivantes
  sont `user`. Les données V2 sont supprimées par la migration.
- **V3.1** : les routes admin permettent de gérer les comptes et refusent les
  opérations interdites sur le dernier admin.
- **V3.1** : HTTPS, CSRF et rate limiting sont actifs avant l'écoute réseau.

## Plan d'implémentation révisé (Next Move)

### V3.0 — Authentification locale (fait)

Register, login avec mot de passe, change-password, logout, gating
`must_change_password` et expiration de session 24 h côté cookie et serveur.
Les routes admin ne font pas partie de V3.0.

Le proxy reste sur `127.0.0.1:8081` en HTTP.

### V3.1 — Administration et déploiement réseau local

Routes admin, HTTPS auto-signé, jeton CSRF sur POST/DELETE, rate limiting
du login et configuration de l'écoute.

Voir `.memory/decisions.md`, entrée
`[2026-10-21] Routes admin reportées en V3.1`.

Le certificat auto-signé déclenche un avertissement navigateur. En entreprise, l'informaticien devra déployer le certificat dans les magasins de confiance des postes clients (GPO Windows, MDM ou équivalent).

### V3.2 — Multi-admin et configuration avancée

1. **Next Move 8j** : multi-admin configurable (`max_admins = 2` par défaut) et transferts de rôle atomiques dans les deux sens.
2. **Next Move 8k** : configuration réseau avancée dans `citadelle_data/config.json` : `host`, `port`, `ssl_cert`, `ssl_key`, `max_admins` et `rate_limit_login`, créée avec des valeurs par défaut au premier lancement.

### V4+

- Certificat Let's Encrypt via reverse proxy, par exemple Caddy ou nginx.
