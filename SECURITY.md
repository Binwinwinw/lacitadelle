# Sécurité — La Citadelle

## Bonnes pratiques utilisateur

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
  verrouiller la session Windows en l'absence;
- un déni de service ou une surcharge concurrente; l'usage mono-utilisateur
  est la cible actuelle;
- une compromission du système d'exploitation ou du compte Windows hôte.

Maintenir Windows et l'antivirus à jour, et garder le pare-feu activé.
