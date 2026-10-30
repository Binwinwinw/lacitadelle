# Architecture cible de production

> Préparation uniquement : ce document ne configure ni DNS, ni pare-feu, ni
> certificat et ne constitue pas une autorisation de mise en service.

## Flux réseau

```text
Navigateur Internet
        │ HTTPS :443; HTTP :80 redirigé vers HTTPS
        ▼
Pare-feu Windows — entrées publiques : TCP 80 et 443 seulement
        ▼
Caddy — TLS public, certificats ACME, en-têtes et journaux
        │ reverse_proxy HTTP sur loopback
        ▼
login_server.py — 127.0.0.1:8081
        ├── SQLite : citadelle_data\memory.db
        └── HTTP sur loopback : 127.0.0.1:8080
                    ▼
                llamafile — inférence
                    └── dist\.current_model référence le GGUF actif
```

Le navigateur ne doit jamais pouvoir joindre directement les ports 8080,
8081 ou l'API d'administration Caddy. Caddy est le seul composant exposé.
Les services Python et llamafile restent liés à `127.0.0.1`; le proxy relaie
les requêtes vers le runtime local.

## Composants et ports

| Composant | Écoute cible | Rôle |
|---|---|---|
| Caddy | Interface publique, TCP 80/443 | Termine TLS, redirige HTTP vers HTTPS, ajoute les en-têtes et journalise les requêtes. |
| `login_server.py` | `127.0.0.1:8081` | Authentification, webchat, API et accès SQLite. |
| llamafile | `127.0.0.1:8080` | Inférence locale; ne pas ouvrir ce port au réseau. |
| SQLite | Fichier local | Comptes, sessions, conversations, réglages et métriques. |
| Caddy admin API | Local uniquement, normalement `127.0.0.1:2019` | Administration Caddy; ne jamais publier ni proxifier ce port. |

Le chemin de modèle actif est conservé dans SQLite et reflété par
`dist\.current_model`; le GGUF reste un fichier local. Les sauvegardes doivent
protéger ensemble la base et ce marqueur lorsqu'un changement de modèle est
en cours.

## DNS, certificats et pare-feu

1. Utiliser un nom de domaine public, par exemple `chat.example.net`.
2. Créer un enregistrement DNS `A` vers l'IPv4 publique. Ajouter un `AAAA`
   uniquement si l'IPv6 est réellement routée jusqu'au serveur.
3. Autoriser les connexions entrantes TCP 80 et 443 jusqu'à Caddy. Garder
   8080, 8081 et 2019 fermés depuis l'extérieur.
4. Autoriser les connexions sortantes nécessaires à ACME et conserver le
   répertoire de données de Caddy sur un disque persistant et accessible à
   son compte de service.

Une adresse de site publique dans le Caddyfile active automatiquement
l'obtention et le renouvellement des certificats ACME (par exemple Let's
Encrypt), ainsi que la redirection HTTP vers HTTPS. Le DNS doit pointer vers
le serveur et les ports 80/443 doivent être joignables. Aucun certificat
racine local n'est à installer pour un certificat public Let's Encrypt.
`caddy trust` concerne la CA locale de Caddy pour des noms internes; ce n'est
pas une réparation pour un certificat public.

Le Caddyfile fourni est un modèle : remplacer `citadelle.example.com` par le
FQDN réel avant toute validation ou exécution. Le chemin de journal
`C:/ProgramData/LaCitadelle/Caddy/` doit exister et être accessible en
écriture au compte Caddy. Limiter ses ACL et celles du répertoire de données
Caddy; ils peuvent contenir des informations d'accès et des clés de
certificat.

La configuration versionnée est [Caddyfile](../../Caddyfile). Les
comportements V3.0 et les contrôles V3.1 exigés avant l'écoute réseau sont
détaillés dans [AUTH_CONTRACT.md](./AUTH_CONTRACT.md).

## Configuration et prérequis d'hôte

Aucune variable d'environnement applicative n'est requise pour cette
architecture. Le seul paramètre spécifique au site est le FQDN dans le
Caddyfile. Caddy doit conserver son répertoire de données sous le même compte
Windows entre les redémarrages; la rotation des journaux exige aussi que le
compte puisse écrire dans le dossier ProgramData indiqué.

L'hôte doit disposer de Python 3.10+, du runtime llamafile téléchargé et du
GGUF configuré par `lancer.bat`. La base et le modèle restent sur disque local;
ils ne sont ni stockés par Caddy ni servis comme fichiers statiques.

## Sécurité et limites avant toute exposition

Cette architecture termine TLS, mais Caddy ne remplace pas les contrôles
d'authentification de l'application. Le contrat V3.0 confirme que le cookie
de session n'a pas l'attribut `Secure` et que CSRF et rate limiting ne sont
pas actifs. Ces contrôles sont requis par le contrat V3.1 avant toute écoute
sur le réseau. **Ne pas publier ce service avant un GO distinct qui les
implémente et les valide.**

Le serveur Python utilise `HTTPServer` mono-thread : une inférence lente
bloque les requêtes suivantes et la capacité simultanée n'est pas certifiée.
La dette P2 de concurrence demeure; faire accepter explicitement la capacité
attendue pour le lancement initial ou lancer un GO CONCURRENCE avant d'élargir
l'exposition.
Les en-têtes HSTS du Caddyfile incluent les sous-domaines : les conserver
uniquement si tous les sous-domaines du domaine choisi utilisent HTTPS.

## Références officielles

- [Téléchargement de Caddy pour Windows](https://caddyserver.com/download)
- [HTTPS automatique](https://caddyserver.com/docs/automatic-https)
- [Directive `reverse_proxy`](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy)
- [Directive `header`](https://caddyserver.com/docs/caddyfile/directives/header)
- [Directive `log`](https://caddyserver.com/docs/caddyfile/directives/log)
- [Commandes Caddy](https://caddyserver.com/docs/command-line)
- [SQLite `VACUUM INTO`](https://www.sqlite.org/lang_vacuum.html#vacuuminto)
- [SQLite Online Backup](https://www.sqlite.org/backup.html)
