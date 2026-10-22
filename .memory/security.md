# Règles de sécurité

Règles actées pour V3 et au-delà. Ne pas les contourner sans décision explicite du décideur consignée dans `decisions.md`.

## Mots de passe

- Ne jamais consigner de mot de passe (clair ou hashé) dans les logs, rapports ou commits.
- Ne jamais retourner un mot de passe en clair, sauf le mot de passe temporaire affiché une seule fois à l'admin lors du reset.
- Hash scrypt uniquement (`hashlib.scrypt`). Format : `scrypt$<n>$<r>$<p>$<salt_hex>$<hash_hex>`.
- Comparaison en temps constant avec `hmac.compare_digest`.

## Sessions

- Cookie : `HttpOnly`, `SameSite=Strict`, `Path=/`, `Max-Age=86400` (24 h).
- Vérifier aussi l'expiration côté serveur avec `SESSION_EXPIRY`; le cookie
  seul ne suffit pas.
- À chaque requête présentant un token expiré, révoquer la session. Les pages
  redirigent vers `/login` et les API renvoient `401`.
- Un nouveau login révoque l'ancien token de l'utilisateur.
- En V3.0, logout révoque la session. La désactivation, le reset de mot de
  passe par admin et la suppression de compte sont reportés en V3.1 avec les
  routes d'administration.

## Anti-énumération

- Login en échec : `401` sans révéler si le username existe.
- Ressource absente ou appartenant à un autre utilisateur : `404`, pas `403`.

## Isolation

- Filtrer systématiquement par `user_id` toutes les requêtes de sessions et de messages.
- Ne pas distinguer les ressources d'un autre utilisateur des ressources absentes.

## Réseau

- **V3.0** : HTTP local, loopback uniquement.
- **V3.1** : HTTPS auto-signé obligatoire; en entreprise, installer le certificat sur les clients (GPO Windows, MDM ou équivalent).
- **V3.2** : multi-admin possible, limité par `max_admins`.
- **V4** : certificat Let's Encrypt via reverse proxy (Caddy ou nginx).
- **CSRF** : obligatoire en V3.1, token par session validé sur POST/DELETE.
- **Rate limiting** : obligatoire en V3.1 pour le login.

## Références

Les règles de protection des fichiers mémoire et des outils intrusifs sont définies dans `AGENTS.md`; les détails du contrat d'authentification sont dans `dev/docs/AUTH_CONTRACT.md`.
