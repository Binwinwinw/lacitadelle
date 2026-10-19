# Journal des modifications

Ce document résume les travaux notables de la V1 et les évolutions prévues.

## V1 — Terminée (2026-10-18)

### Travaux accomplis

- **Socle documentaire** : instructions projet, périmètre, stratégie Git, base llamafile, stratégie de vendorisation et contrats bootstrap, external et mémoire.
- **Choix du runtime et du modèle** : llamafile 0.10.6 thin, `zipalign` et Qwen3-1.7B Q4_K_M en mode external.
- **Bootstrap** : `dev/tools/bootstrap.py` télécharge et vérifie les trois assets requis (runtime, `zipalign`, GGUF), avec réparation d'un fichier absent ou corrompu.
- **Fabrication** : `dev/tools/setup_lacitadelle.py` assemble l'exécutable external d'environ 44 Mo.
- **Lancement** : `install.bat` automatise la préparation et la fabrication ; `lancer.bat` démarre le serveur et ouvre le navigateur.
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

## V2 — Roadmap

### Objectifs

- Ajouter un login et la séparation des conversations par utilisateur.
- Ajouter un serveur proxy Python local sur `localhost:8081`, devant llamafile sur `localhost:8080`, pour gérer l'authentification et filtrer les sessions par `user_id`.
- Ajouter une page de login et une interface de chat connectée au proxy.
- Le login V2 est prévu sans mot de passe ; l'ajout d'un mot de passe est reporté en V2.5.

### Tâches V2

- [ ] Rédiger `LOGIN_CONTRACT.md` pour cadrer l'architecture du login.
- [ ] Créer le serveur proxy `dev/tools/login_server.py`.
- [ ] Créer la page de login HTML.
- [ ] Relier l'interface de chat au proxy authentifié.
- [ ] Filtrer les sessions par `user_id`.
- [ ] Ajouter les tests unitaires et d'intégration.

### Tâches V2.5+

- [ ] Ajouter un mot de passe au login.
- [ ] Implémenter la détection GPU et la bascule CPU/GPU.
- [ ] Permettre un prompt système personnalisé.
- [ ] Ajouter la reprise HTTP Range pour les téléchargements volumineux.
