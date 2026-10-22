# Journal des modifications

Ce document résume les travaux notables de la V1 et les évolutions prévues.

## V1 — Terminée (2026-10-18)

### Travaux accomplis

- **Socle documentaire** : instructions projet, périmètre, stratégie Git, base llamafile, stratégie de vendorisation et contrats bootstrap, external et mémoire.
- **Choix du runtime et du modèle** : llamafile 0.10.6 thin, `zipalign` et Qwen3-1.7B Q4_K_M en mode external.
- **Bootstrap actuel** : `dev/tools/bootstrap.py` télécharge et vérifie le runtime préconstruit depuis GitHub Releases et le GGUF séparément. Le runtime thin et `zipalign` ne sont utilisés que pour le build développeur.
- **Fabrication** : `dev/tools/setup_lacitadelle.py` assemble l'exécutable external d'environ 44 Mo.
- **Lancement actuel** : `install.bat` lance le bootstrap sans construire le runtime ; `lancer.bat` démarre le serveur et le proxy puis ouvre le navigateur.
- **Conversation et mémoire** : le serveur headless sert l'API locale et l'interface web ; `dev/tools/client.py` fournit un REPL relié à `dev/tools/citadelle_memory.py` et à la base SQLite à trois tables.
- **Reproductibilité** : le décideur a confirmé le parcours de zéro ; l'installation retélécharge les assets requis, fabrique l'exécutable et permet le lancement.
- **Nettoyage documentaire Temps 2** : les mentions opérationnelles obsolètes liées à `main/` ont été retirées ; les historiques de décisions ont été conservés selon Solution A.

### Décisions clés

- Modèle externe : le GGUF n'est pas embarqué dans l'exécutable llamafile.
- Modèle V1 : Qwen3-1.7B Q4_K_M, licence Apache 2.0.
- Serveur local headless sur le port 8080, contexte de 8192 tokens.
- Mémoire SQLite locale disponible via le client Python séparé ; un seul utilisateur par défaut en V1.
- Les cinq agents de nettoyage documentaire du Temps 2 ont été créés et utilisés.

### Limites connues

- L'interface web transmet l'historique et peut saturer le contexte sur les longues conversations ; le client REPL borne l'historique envoyé.
- Pas de login ni de multi-utilisateurs actifs.
- Pas de détection GPU ni de bascule automatique.
- Pas de prompt système personnalisable ni de reprise HTTP Range.

## V3.0 — Terminée

### Réalisations

- Inscription avec mot de passe, login scrypt, changement forcé de mot de passe et logout.
- Sessions d'authentification avec cookie `Max-Age=86400` et expiration côté serveur.
- Proxy local et webchat; sessions et messages filtrés par utilisateur.
- Distribution préconstruite : runtime via GitHub Releases et GGUF séparé; `install.bat` ne lance pas le build.
- 73 tests permanents passent.

### V3.1 — Roadmap

- Routes d'administration : comptes, reset, activation/désactivation, rôles et suppression.
- HTTPS avec certificat auto-signé.
- Protection CSRF pour les requêtes POST/DELETE.
- Rate limiting du login.

### V3.2+

- Multi-admin configurable.
- Détection GPU, prompt système personnalisé et reprise HTTP Range restent des évolutions futures.
