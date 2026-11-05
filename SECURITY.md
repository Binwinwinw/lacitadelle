# Sécurité — La Citadelle

## Bonnes pratiques utilisateur

### Configuration recommandée

- Windows, Linux et macOS sont pris en charge par l'archive source et ses
  wrappers natifs (`.bat`, `.sh`, `.command`), avec Python 3.10+. L'exécutable
  Windows PyInstaller ne requiert pas Python sur le poste utilisateur.
- Garder les ports 8080 et 8081 sur loopback et activer le pare-feu de l'OS.
- Vérifier le SHA-256 de l'archive et laisser l'installateur vérifier ceux du
  runtime et du GGUF avant leur utilisation.
- Sous macOS, n'autoriser un fichier `.command` bloqué par Gatekeeper qu'après
  avoir vérifié l'origine de l'archive.
- Sous Windows, ne contourner SmartScreen pour `LaCitadelle.exe` qu'après
  téléchargement depuis la source officielle et vérification du SHA-256.
  Le build n'étant pas signé, **Exécuter quand même** n'est pas une garantie
  d'authenticité.

### Mot de passe administrateur

- Le mot de passe admin initial est affiché une seule fois dans la console au
  premier démarrage. Le conserver hors des journaux et le remplacer par un
  secret long et unique.
- Utiliser au moins 12 caractères et ne pas réutiliser un mot de passe
  employé sur un autre service.
- Ne pas partager le compte administrateur avec d'autres utilisateurs.

### Sauvegardes

- Sauvegarder régulièrement `citadelle_data/memory.db` et protéger les copies
  par des ACL adaptées.
- Utiliser `VACUUM INTO` pour produire une copie SQLite cohérente.
- Stocker les sauvegardes chiffrées hors de la machine et vérifier
  périodiquement qu'une restauration est possible.

### Exposition réseau

- Ne pas exposer directement les ports 8080 (llamafile) ou 8081 (proxy) à
  Internet.
- Pour un accès distant, utiliser un reverse proxy HTTPS, tel que Caddy, avec
  un certificat valide; limiter le pare-feu aux ports publics nécessaires.
- Le cookie `Secure` n'est envoyé que lorsque le proxy indique une connexion
  HTTPS. Ne pas contourner les contrôles CSRF.
- Le rate limiting est en mémoire et ne protège pas contre un déni de service
  distribué.

### Sécurité des fichiers

La lecture de fichiers par Nexxus n'est pas activée. La politique de
classification préparatoire est définie dans `dev/tools/security_files.py` :

- **Public** : extensions textuelles, documents, images et code source pris en
  charge (par exemple `.txt`, `.md`, `.csv`, `.json`, `.pdf`, `.docx`, `.png`,
  `.jpg`, `.py`).
- **Sensible** : configuration, secrets, bases locales et archives; accès
  administrateur uniquement, avec journalisation.
- **Critique** : exécutables, scripts et clés privées; refus même pour un
  administrateur.

La classification vérifie l'extension et les signatures du contenu (exécutables,
bases SQLite et archives); les fichiers inconnus ou illisibles sont traités
comme sensibles. Cette politique ne constitue pas un outil de lecture : tout
futur outil devra aussi confiner les chemins autorisés et empêcher les
contournements par liens symboliques avant d'ouvrir un fichier.

### Mises à jour

- Télécharger l'archive depuis la source officielle et vérifier son SHA-256
  communiqué séparément.
- Le bootstrap vérifie les SHA-256 du runtime et du GGUF téléchargés.
- Ne pas remplacer manuellement un GGUF autorisé par un fichier non vérifié.

## Signaler une vulnérabilité

Contacter le mainteneur par un canal privé indiqué par le dépôt. Ne pas publier
les détails d'une vulnérabilité avant que le mainteneur ait pu l'évaluer et la
corriger. Le délai de réponse visé est de sept jours ouvrés.

## Limites de protection

La Citadelle ne protège pas contre :

- un accès physique à une machine déverrouillée; chiffrer le disque et
  verrouiller la session de l'OS hôte en l'absence;
- un déni de service ou une surcharge concurrente; l'usage mono-utilisateur
  est la cible actuelle;
- la saturation du proxy mono-thread : une inférence lente bloque les requêtes
  suivantes et la capacité multi-utilisateur n'est pas certifiée. Voir
  [RUNBOOK-PROD.md](./dev/docs/RUNBOOK-PROD.md) avant tout usage collectif;
- une compromission du système d'exploitation ou du compte Windows hôte.

Maintenir Windows, Linux ou macOS à jour, garder les protections de sécurité
du système activées et vérifier les alertes Gatekeeper/quarantaine avant
d'autoriser un runtime téléchargé.
