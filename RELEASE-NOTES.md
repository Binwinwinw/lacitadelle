# La Citadelle — Release v3

Date : 2026-10-30
Commit source : `cc6594d`
Archive : `lacitadelle-distribution.zip` (source-only)
SHA-256 : communiqué séparément avec l'archive; non intégré aux notes pour
éviter une empreinte auto-référente.

## Nouveautés

- **V3.1 sécurité** : cookie `Secure` en HTTPS, protection CSRF des POST
  authentifiés et rate limiting du login, du chat et des routes admin.
- **Phase 12-FIX-WHITELIST** : initialisation de première installation avec
  vérification SHA-256 du GGUF intégré et refus explicite d'un rollback sans
  modèle précédent.
- **Phase 12-POLISH-TODO-GIT** : TODO.md versionné comme registre partagé des
  seules tâches actives; Règle 10 ajoutée à AGENTS.md.

## Tests

- 194 tests verts : 186 tests préexistants et huit nouveaux tests Phase 12.

## Installation

1. Extraire l'archive dans un dossier accessible en écriture.
2. Double-cliquer sur `install.bat`. Python et Internet sont requis au
   premier lancement si llamafile-thin ou le GGUF ne sont pas déjà présents.
3. Le bootstrap télécharge et vérifie les assets; le GGUF représente environ
   1,28 Go. `install.bat` démarre ensuite `lancer.bat`.
4. Si nécessaire, lancer `lancer.bat` séparément.
5. Ouvrir `http://127.0.0.1:8081/`.
6. Au premier démarrage, relever le mot de passe admin affiché une seule fois
   dans la console du proxy.

L'archive source-only n'embarque ni runtime ni GGUF; le parcours d'installation
est hors ligne seulement après leur téléchargement ou leur prépositionnement.

## Sécurité

- Cookie `Secure` en HTTPS, CSRF sur les POST authentifiés et rate limiting
  côté serveur.
- Ne pas exposer directement les ports locaux 8080/8081 sur Internet.
- Pour un accès distant, configurer un reverse proxy HTTPS avec un certificat
  valide et un pare-feu restrictif.

## Limites connues

- Le serveur est mono-thread; une inférence lente bloque les requêtes suivantes.
- Playwright E2E est reporté.
- L'upload GGUF n'est pas implémenté.
