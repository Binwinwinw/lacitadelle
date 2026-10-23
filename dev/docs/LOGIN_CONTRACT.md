# Contrat du login multi-utilisateurs (V2)

> **HISTORIQUE** — contrat V2 remplacé par V3.0 (voir [AUTH_CONTRACT.md](./AUTH_CONTRACT.md)). Conservé pour traçabilité.

## Contexte et objectif

La V1 fournit un utilisateur par défaut (`lacitadelle`) et un client Python séparé qui persiste les conversations dans SQLite. La V2 ajoute une interface web avec login, servie par un proxy Python local. Le proxy possède la session utilisateur, applique l'isolation des données et relaie les requêtes d'inférence vers llamafile.

Ce document cadre la V2 ; il ne décrit pas une fonctionnalité déjà implémentée.

## Comparaison V1 / V2

| Composant                   | V1                                             | V2                                                  |
| --------------------------- | ---------------------------------------------- | --------------------------------------------------- |
| Utilisateur                 | `lacitadelle` par défaut                       | Login par nom d'utilisateur, plusieurs utilisateurs |
| Interface web               | `localhost:8080` (llamafile)                   | `localhost:8081` (proxy Python)                     |
| Mémoire                     | Client Python séparé                           | Gérée par le proxy avec SQLite                      |
| Login                       | Aucun                                          | Nom d'utilisateur, sans mot de passe                |
| Sessions de conversation    | Pas filtrées par utilisateur dans le client V1 | Toutes les opérations filtrées par `user_id`        |
| Authentification navigateur | Aucune                                         | Cookie HTTP-only et session en mémoire du proxy     |

## Architecture cible

- Le runtime llamafile reste sur `127.0.0.1:8080` et fournit l'inférence via `/v1/chat/completions`.
- Le proxy Python écoute uniquement sur `127.0.0.1:8081` ; l'interface navigateur et ses appels API passent par lui.
- Le proxy sert les pages de login et de chat, valide les sessions, lit et écrit la base SQLite, et relaie les requêtes de chat à llamafile.
- La base reste `citadelle_data/memory.db`. La V2 réutilise les tables V1 `users`, `sessions` et `messages` ; elle ne crée pas de nouvelle table pour les sessions HTTP.
- Les enregistrements existants, notamment l'utilisateur `lacitadelle` et ses conversations, sont conservés.

## Contrat du login et des cookies

1. Le formulaire demande un nom d'utilisateur, sans adresse email ni mot de passe en V2.
2. Le proxy nettoie les espaces périphériques et refuse un nom vide. Il retrouve l'utilisateur par `username` ou crée un enregistrement dans `users` si ce nom n'existe pas.
3. Un login réussi crée un token opaque imprévisible avec un générateur cryptographiquement sûr. Le proxy conserve le mapping en mémoire `token -> user_id` ; le token n'est jamais accepté comme `user_id` fourni par le navigateur.
4. Une seule session d'authentification est active par utilisateur : un nouveau login révoque le token précédent de cet utilisateur avant d'en émettre un nouveau. Cela concerne la session de login, pas le nombre de conversations SQLite.
5. Le navigateur reçoit le token dans un cookie de session avec `HttpOnly`, `SameSite=Strict` et `Path=/`. Le cookie est limité à l'hôte qui l'a créé ; aucun attribut `Domain` n'est défini.
6. Le service est exclusivement local et utilise HTTP. L'attribut `Secure` n'est donc pas posé en V2 ; le proxy ne doit pas écouter sur une interface réseau externe. Les opérations qui modifient des données vérifient l'origine de la requête et aucun CORS permissif n'est activé.
7. À la déconnexion, le proxy révoque le token et expire le cookie. Les routes protégées sans token valide redirigent vers le login ou répondent `401` pour une requête API.
8. Au redémarrage du proxy, le dictionnaire de sessions est vide. Un cookie restant dans le navigateur ne correspond plus à une session valide ; l'utilisateur doit se reconnecter.

## Limite de sécurité V2

Sans mot de passe, le nom d'utilisateur n'est pas une preuve d'identité : une personne pouvant accéder au service local peut se connecter sous le nom d'un autre utilisateur. V2 fournit une séparation des conversations entre noms d'utilisateur dans le contexte local, mais pas une authentification forte ni une protection contre les autres processus de la même machine. L'accès est réservé à un environnement local de confiance ; cette version ne doit pas être exposée sur un réseau.

En V2.5, l'ajout d'un mot de passe devra stocker uniquement un hash calculé avec bcrypt ou scrypt dans SQLite, jamais le mot de passe en clair. Le choix et les paramètres du mécanisme de hash devront être arrêtés avant l'implémentation V2.5.

## Contrat de séparation des données

- Le `user_id` courant est obtenu exclusivement à partir du token validé côté serveur.
- Toute création de conversation associe la ligne `sessions` à ce `user_id`.
- Toute liste, lecture, modification ou suppression de conversation vérifie simultanément l'identifiant de la conversation et le `user_id` propriétaire. Une session appartenant à un autre utilisateur est traitée comme inexistante ; son contenu n'est pas révélé.
- Les helpers SQLite V2 doivent prendre le `user_id` en paramètre, par exemple `list_sessions_for_user(user_id)` et `get_messages_for_user_session(user_id, session_id)`. Le proxy ne réutilise pas une requête V1 qui liste les conversations de tous les utilisateurs sans filtre.
- Les requêtes SQL utilisent des paramètres liés ; les identifiants fournis par le navigateur ne sont jamais concaténés dans du SQL.
- Les opérations de chat chargent le contexte uniquement depuis la conversation appartenant à l'utilisateur courant, appellent le serveur llamafile local, puis persistent les messages dans cette même conversation.

## Routes HTTP attendues

- `GET /login` : sert la page de login.
- `POST /login` : accepte le nom d'utilisateur, établit la session et redirige vers `/`.
- `GET /` : sert l'interface de chat si la session est valide ; sinon redirige vers `/login`.
- `POST /logout` : révoque la session courante, expire le cookie et redirige vers `/login`.
- `GET /api/sessions` : retourne uniquement les conversations de l'utilisateur courant.
- `POST /api/sessions` : crée une conversation pour l'utilisateur courant.
- `GET /api/sessions/{session_id}/messages` : retourne les messages seulement si la conversation appartient à l'utilisateur courant.
- `POST /api/sessions/{session_id}/messages` : vérifie le propriétaire, ajoute le message utilisateur, appelle llamafile sur `127.0.0.1:8080` et persiste la réponse de l'assistant.

Les routes API refusent les requêtes sans session valide. Les erreurs d'accès ne doivent pas permettre de distinguer l'existence d'une conversation appartenant à un autre utilisateur.

## Non-objectifs V2

- Pas de mot de passe (reporté en V2.5).
- Pas d'inscription avec adresse email (éventuellement V3).
- Pas de récupération de mot de passe (V3).
- Pas de HTTPS ; usage local uniquement et écoute loopback obligatoire.
- Pas de plusieurs sessions de login simultanées pour un même utilisateur. Les conversations multiples restent possibles.
- Pas de gestion de comptes à distance, de synchronisation cloud ni de déploiement réseau.

## Étapes d'implémentation

1. Créer `dev/tools/login_server.py` avec les routes, le cookie et le stockage des tokens en mémoire.
2. Ajouter les helpers SQLite qui créent les utilisateurs et imposent le filtrage par `user_id` pour toutes les opérations sur les conversations.
3. Créer les pages HTML de login et de chat, servies par le proxy.
4. Modifier `lancer.bat` pour démarrer llamafile sur le port 8080 et le proxy sur le port 8081, puis ouvrir l'interface du proxy.
5. Tester le parcours complet : login, création et reprise de conversation, persistance SQLite, séparation de deux utilisateurs, refus d'accès aux conversations d'autrui, logout et reconnexion après redémarrage du proxy.

## Critères d'acceptation

- Le proxy n'écoute que sur loopback et l'interface V2 est accessible sur `http://localhost:8081`.
- Les pages et routes protégées exigent un token valide ; le cookie est `HttpOnly` et `SameSite=Strict`.
- Le logout invalide immédiatement le token ; un redémarrage du proxy rend les anciens cookies invalides.
- Un utilisateur ne peut ni lister ni lire les conversations d'un autre en modifiant les identifiants envoyés par le navigateur.
- Les messages restent persistés dans SQLite et les conversations V1 existantes sont conservées.
- Aucun mot de passe en clair ni hash de mot de passe n'est stocké en V2.
