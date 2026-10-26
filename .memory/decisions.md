# Decisions

Décisions architecturales et structurantes du projet La Citadelle.
Format normatif : chaque entrée commence par `## [AAAA-MM-JJ] Titre` et contient
des champs explicites (Contexte, Décision(s), Conséquences).
Aucun outil externe n'est autorisé à reformater, fusionner ou normaliser ce fichier
sans instruction explicite du décideur (voir AGENTS.md, règle non-négociable n°6).

## [2026-10-17] Modèle Qwen3-1.7B Q4_K_M pour le .llamafile v1

*Supplantée partiellement par [2026-10-22] Distribution Phase 3 — voir décision du 2026-10-22.*

**Contexte** : le cadrage du build `.llamafile` a identifié 4 décisions à prendre. Le décideur a tranché la première : le modèle GGUF.

**Décision** :

1. Modèle : Qwen3-1.7B, quantifié Q4_K_M (Apache 2.0, ~1,1 Go selon l'estimation initiale).
2. Source : HuggingFace, URL immuable (commit SHA `4b9aca3fb9c8fcace456430347c2fc34752e515f`) : `https://huggingface.co/smarttasks/Qwen3-1.7B-GGUF/resolve/4b9aca3fb9c8fcace456430347c2fc34752e515f/Qwen3-1.7B-Q4_K_M.gguf`. La branche `main` était mutable ; l'URL immuable garantit la reproductibilité.
3. Checksum SHA-256 : `16da7ba1721b1620fa843e0978badd3d93756274fd209a01874b37e29750e207`.
4. Asset ajouté dans `llamafile_config.json` avec `required=false` (non téléchargé par `bootstrap.py`, réservé à `build_llamafile.py`).
5. Le `.args` devra référencer le modèle avec le préfixe `/zip/` (obligatoire pour les fichiers embarqués dans un llamafile).

**Conséquences** : les métadonnées HuggingFace indiquent une taille de 1 282 439 456 octets (`~1,28 Go` décimaux, `~1,19 Gio`); avec le runtime d'environ 44 Mo, le `.llamafile` final est estimé à environ 1,33 Go décimaux. `build_llamafile.py` pourra être implémenté une fois les 3 autres décisions (confirmation de la source exacte, nom/emplacement final, args détaillés) confirmées. Les args minimaux proposés sont `-m /zip/Qwen3-1.7B-Q4_K_M.gguf`, `--port 8080`, `-c 4096`, `--temp 0.7` et `-t auto`; la documentation actuelle indique `-t N` et ne documente pas `auto`, donc cette valeur reste à valider avant implémentation.

## [2026-10-17] Objectif v1 : Pocket Chat (llamafile + modèle embarqué, interface texte)

> **Supplantée par [2026-10-22] Distribution Phase 3** : distribution avec runtime llamafile-thin et GGUF séparés.

**Contexte** : llamafile fournit le format exécutable unique et le runtime C++. Python ne peut pas produire un exécutable multi-OS unique. La Citadelle utilise donc Python comme outil de FABRICATION, pas comme runtime livré.

**Décision** : v1 = fichier `.llamafile` unique, modèle 1B-3B embarqué, interface texte de llamafile. Pas de tool calling, pas de téléchargement de modèles dans l'app, pas de GUI graphique.

**Conséquences** : le succès de v1 se mesure par « un non-technique double-clique et obtient une conversation ». Tout le reste est hors périmètre v1.

## [2026-10-17] Python = fabrication uniquement

> **Supplantée par [2026-10-22] Distribution Phase 3** : Python est requis pour l'installation et le proxy de la distribution V3.

**Contexte** : Python ne peut pas produire un binaire APE multi-OS. llamafile (C++/cosmocc) fournit ce binaire. La Citadelle a besoin d'un pipeline pour transformer un GGUF en `.llamafile` prêt à l'emploi.

**Décision** : aucun code Python ne sera exécuté chez l'utilisateur final. Le pipeline Python prend un GGUF en entrée et produit un `.llamafile` exécutable.

**Conséquences** : l'utilisateur final ne dépend pas de Python. Le pipeline Python vit côté fabrication (dev/tools, dev/scripts). Aucune dépendance Python ne doit fuiter dans l'artefact livré.

## [2026-10-17] Stratégie Git : Option C + dépôt distant + .gitignore minimal

**Contexte** : projet pas sous Git, socle documentaire terminé, prochain chantier = mise sous version.

**Décisions** :

1. `main/` ignoré via `.gitignore`, re-téléchargé par script de bootstrap (dépendance externe en lecture seule, pas du code à nous).
2. Dépôt distant dès le départ (GitHub privé, nom proposé : `lacitadelle`).
3. `.gitignore` couvre Python, modèles GGUF, artefacts llamafile, build, et `main/`.

**Document de cadrage** : `dev/docs/GIT_STRATEGY.md`.

**Conséquences** : aucun fichier de `main/` ne sera versionné. Un script de bootstrap devra être créé avant tout clone sur une nouvelle machine. La mise sous Git effective (`git init`, création du dépôt distant, premier commit) est une tâche distincte, à exécuter sur instruction explicite du décideur.

## [2026-10-17] Compléments de mise sous Git

**Contexte** : stratégie Git actée (Option C, dépôt distant, `.gitignore` minimal). Dépôt distant déjà créé par le décideur.

**Décisions** :

1. Branche par défaut : `main`.
2. Dépôt distant : `https://github.com/Binwinwinw/lacitadelle` (privé), déjà créé par le décideur. La liaison via `git remote add origin` sera faite dans le temps 2 de la tâche de mise sous Git.
3. Premier commit : tout le socle actuel (README, `AGENTS.md`, `.memory/`, `dev/docs/`, `.github/`, `.gitignore`). `main/` est exclu via `.gitignore`.
4. RÈGLE NON-NÉGOCIABLE : `main/` ne doit JAMAIS apparaître sur GitHub. Le `.gitignore` garantit cette exclusion. Aucune exception sans décision explicite du décideur consignée dans ce fichier.

**Conséquences** : la mise sous Git est découpée en deux temps. Temps 1 (local) : `git init`, vérifications `git status`, `git add .`, commit. Temps 2 (réseau) : `git remote add origin`, `git push -u origin main`. Chaque temps est une tâche séparée, exécutée sur instruction explicite du décideur.

## [2026-10-17] Base llamafile : Option X (binaire pré-compilé upstream)

*Supplantée partiellement par [2026-10-22] Distribution Phase 3 — voir décision du 2026-10-22.*

**Contexte** : le pipeline v1 doit produire un `.llamafile` à partir d'un GGUF et d'un binaire llamafile de base. Trois options étaient documentées dans `dev/docs/BASE_LLAMAFILE.md` (X : binaire pré-compilé, Y : compilation depuis `main/`, Z : hybride).

**Décision** : Option X retenue par le décideur le 2026-10-17. Le binaire llamafile sera téléchargé depuis les releases upstream (version à figer après vérification factuelle). `main/` reste en référence documentaire, jamais compilé pour la v1.

**Conséquences** : un script de téléchargement avec vérification de checksum SHA-256 sera nécessaire (voir `dev/tools/VENDOR_STRATEGY.md`). Le binaire téléchargé sera gitignoré, comme `main/`. Aucune compilation n'est requise pour la v1.

## [2026-10-17] Base llamafile : version 0.10.6, asset thin, stratégie de vendorisation

> **Partiellement supplantée par [2026-10-22] Distribution Phase 3** : `zipalign` est retiré du parcours de distribution.

**Contexte** : la décision Option X (binaire pré-compilé upstream) est actée. La vérification factuelle a établi que `0.10.6` (15 septembre 2026) est la dernière release stable, avec checksums SHA-256 publiés par l'API GitHub.

**Décisions actées** :

1. **Version** : `0.10.6`.
2. **Asset runtime v1** : `llamafile-0.10.6-thin` (CPU only, robustesse maximale, fichier plus petit).
3. **Asset obligatoire** : `zipalign-0.10.6`.
4. **Détection GPU + bascule** : reportée en v2, documentée comme objectif futur.
5. **Vendorisation** : binaires dans `dev/tools/vendor/llamafile/` (gitignoré), configuration dans `dev/tools/llamafile_config.json` (versionné), vérification SHA-256 obligatoire, échec → arrêt sans exécution.

**Conséquences** : la prochaine étape est de créer `llamafile_config.json` puis `bootstrap.py`. Aucune compilation n'est requise. Le pipeline Python pourra assembler un `.llamafile` à partir du thin + zipalign + GGUF.

## [2026-10-17] Premier code : bootstrap.py en stdlib, structure squelette

**Contexte** : le cadrage est terminé. La première ligne de code du projet est `dev/tools/bootstrap.py` (script de téléchargement et vérification des binaires llamafile). Le décideur a tranché le style et la structure.

**Décisions** :

1. Style : Python stdlib uniquement (urllib, hashlib, json, pathlib, sys). Aucune dépendance externe.
2. Config : `dev/tools/llamafile_config.json`, JSON plat avec version + dict d'assets.
3. Structure : d'abord un squelette avec fonctions signature + docstrings + corps TODO, puis implémentation fonction par fonction avec tests.
4. Comportement : téléchargement des assets required=true, vérification SHA-256 obligatoire, échec → arrêt propre (code non-zéro), aucune exécution du binaire téléchargé.

**Conséquences** : la prochaine tâche implémentera `load_config()` (la plus simple, sans I/O réseau), puis `compute_sha256()` et `download()` séparément. Le décideur exécutera le script lui-même pour tester.

## [2026-10-17] Contrat bootstrap.py formalisé avant implémentation

*Supplantée partiellement par [2026-10-22] Distribution Phase 3 — voir décision du 2026-10-22.*

**Contexte** : la revue du squelette de `bootstrap.py` a identifié plusieurs contrats manquants (validation de config, gestion des fichiers existants, comportement d'erreur, compatibilité Python). Le décideur a tranché ces contrats avant d'implémenter.

**Décisions** :

1. Contrat complet dans `dev/tools/BOOTSTRAP_CONTRACT.md` (référence pour l'implémentation).
2. Fichier existant corrompu : **mode réparateur** — suppression + retéléchargement une seule fois + vérification. Échec explicite si la réparation échoue. Pas de boucle de retry.
3. Gestion de version dans le script : aucune (nettoyage manuel de vendor/ si changement de version).
4. `filename` distinct de la clé logique (traçabilité : le nom physique contient la version).
5. `HTTPError` traité avant `URLError` (préserver le code HTTP).
6. Timeout réseau : 60 secondes.
7. Python 3.10+ (pas de `hashlib.file_digest`).
8. Fonctions non implémentées : `raise NotImplementedError` au lieu de `pass`.
9. Codes de sortie : 0 (succès), 1 (asset échoué), 2 (config invalide).
10. Implémentation en 5 étapes, une par commit : `load_config`, `compute_sha256`+`verify_sha256`, `download`, `process_asset`, `main`.
11. Non-objectifs v1 : pas de `--force`, pas de parallélisation, pas de reprise HTTP Range, pas d'exécution du binaire.

**Conséquences** : la prochaine tâche implémentera `load_config()` seule, avec ses validations strictes. Tests unitaires à prévoir à chaque étape.

## [2026-10-17] Incident hacklm-memory : injection non autorisée dans copilot-instructions.md

**Contexte** : l'outil d'environnement `hacklm-memory` a injecté 40 lignes dans `.github/copilot-instructions.md` sans instruction du décideur. Le bloc injecté demandait à Copilot de modifier `.memory/` automatiquement (`storeMemory`), ce qui contredit la règle 6 d'`AGENTS.md` (interdiction de modifier `.memory/` sans instruction explicite du décideur dans la conversation courante).

**Décision** :

1. Restauration de `.github/copilot-instructions.md` à la version HEAD (commit 987f168).
2. L'outil `hacklm-memory` est désormais considéré comme intrusif au même titre que Ponytail. Son action sur `.github/copilot-instructions.md` et sur `.memory/` est interdite.
3. Un garde-fou sera ajouté dans `AGENTS.md` règle 6 pour mentionner explicitement `hacklm-memory` (temps 2, tâche suivante).
4. Après chaque session, vérifier que `.github/copilot-instructions.md` n'a pas été réinjecté.

**Conséquences** : la prochaine tâche (temps 2) renforcera `AGENTS.md` et mettra en place une vérification systématique du fichier Copilot. Si `hacklm-memory` réinjecte le bloc malgré tout, un garde-fou actif (hook Git ou script de pré-commit) sera nécessaire.

## [2026-10-17] Incident force-push : réécriture d'historique non autorisée

**Contexte** : lors de la tâche de mise à jour de l'URL Qwen3 et de la clarification de `-t`, l'IDE a exécuté `git commit --amend` puis `git push --force-with-lease` de sa propre initiative, sans autorisation explicite du décideur. Le commit `4310706` a été remplacé par `aadbdeb` dans l'historique distant.

**Décision** :

1. Aucun `git commit --amend`, `git rebase`, `git push --force` ou `git push --force-with-lease` ne peut être exécuté sans autorisation explicite du décideur.
2. Règle 8 ajoutée à `AGENTS.md` pour formaliser cette interdiction.
3. L'historique réécrit (`4310706` → `aadbdeb`) est conservé en l'état. Aucune tentative de restauration n'est faite (risque de casser davantage).
4. À l'avenir, si un commit doit être corrigé, créer un NOUVEAU commit par-dessus.

**Conséquences** : l'historique Git est désormais protégé par la règle 8. Toute violation doit être signalée. Le commit `4310706` n'existe plus dans l'historique, mais son contenu a été intégré dans `aadbdeb` (les deux commits portent le même message et les mêmes changements).

## [2026-10-18] Obsolescence des décisions antérieures mentionnant main/

**Contexte** : le dossier main/ (fork local de mozilla-ai/llamafile)
a été supprimé du worktree le 2026-10-18. Il n'était jamais utilisé
par le code : le bootstrap télécharge directement les binaires
depuis les releases officielles GitHub. Plusieurs décisions
antérieures mentionnent main/ (lecture seule, gitignore,
compilation optionnelle, etc.) et deviennent obsolètes.

**Décision** :

1. Les décisions antérieures qui mentionnent main/ restent dans ce
   fichier pour traçabilité historique (Solution A : pas de
   réécriture d'historique).
2. Elles sont considérées comme obsolètes à compter du 2026-10-18.
3. Le dossier main/ ne sera plus présent dans le worktree. La
   dépendance upstream llamafile est retirée du worktree.
4. Le dépôt mozilla-ai/llamafile reste la source d'inspiration du
   projet et sera mentionné explicitement dans le README (Temps 2).

**Conséquences** : les règles d'AGENTS.md et les documents
(README, GIT_STRATEGY.md, OBJECTIF.md, BASE_LLAMAFILE.md,
VENDOR_STRATEGY.md, copilot-instructions.md) seront nettoyés dans
le Temps 2 (tâche séparée). Aucun code Python n'est affecté
(0 occurrence de main/ dans le code).

## [2026-10-21] Séparation du build développeur et du run utilisateur

*Supplantée partiellement par [2026-10-22] Distribution Phase 3 — voir décision du 2026-10-22.*

**Contexte** : `install.bat` construisait le runtime avec `zipalign` sur
l'ordinateur utilisateur. Ce binaire peut être bloqué par les politiques
antivirus d'entreprise.

**Décision(s)** :

1. Le développeur construit le runtime avec `setup_lacitadelle.py` et publie
   le `.llamafile` préconstruit dans une release GitHub.
2. Le bootstrap utilisateur télécharge le runtime préconstruit dans `dist/`
   et le GGUF dans `dev/tools/vendor/llamafile/`. Il ne télécharge pas
   `zipalign` ni le runtime thin ; ces assets restent disponibles pour le
   build développeur.
3. `install.bat` exécute uniquement le bootstrap puis `lancer.bat`.
4. La vérification SHA-256 reste obligatoire. L'URL et le checksum TODO
   doivent être remplacés après publication de la release v0.1.0.

**Conséquences** : l'ordinateur utilisateur n'exécute plus `zipalign` et
n'effectue aucune compilation. Le bootstrap ne pourra fonctionner qu'une
fois l'URL et le checksum réels renseignés. Le `.llamafile` reste soumis aux
règles antivirus locales.

## [2026-10-21] Objectif v1 révisé : produit external assumé

*Supplantée partiellement par [2026-10-22] Distribution Phase 3 — voir décision du 2026-10-22.*

**Contexte** : le rapport de vérification documentaire a relevé que
`OBJECTIF.md` décrivait un fichier unique avec modèle embarqué, sans Python ni
réseau, alors que le parcours livré distribue le runtime et le GGUF séparément
et utilise un proxy Python avec une interface web.

**Décision(s)** : le produit v1 est le mode external actuel.
`OBJECTIF.md` décrit le runtime préconstruit, le GGUF séparé, le proxy Python,
le webchat, Python requis et le téléchargement au premier lancement.

**Conséquences** : la vision initiale « fichier unique sans Python ni réseau »
est remplacée par « installation Python et réseau au premier lancement, puis
runtime external utilisé localement ».

## [2026-10-21] Sessions avec expiration serveur (Max-Age 24h)

**Contexte** : `security.md` exige `Max-Age=86400` et une expiration serveur,
mais le code V3.0 ne les implémentait pas.

**Décision(s)** : ajouter `Max-Age=86400` et une échéance `SESSION_EXPIRY`
par token dans `login_server.py`. Invalider une session expirée lors de toute
requête qui présente son cookie.

**Conséquences** : les sessions expirent après 24 heures côté navigateur et
côté proxy; l'expiration ne dépend plus du cookie seul.

## [2026-10-21] Routes admin reportées en V3.1

**Contexte** : `AUTH_CONTRACT.md` décrit les routes d'administration, mais
`login_server.py` ne les implémente pas.

**Décision(s)** : V3.0 comprend register, login, change-password et logout.
Les routes `/admin` et de gestion des comptes sont reportées en V3.1, avec
HTTPS, CSRF et rate limiting.

**Conséquences** : `AUTH_CONTRACT.md` et `security.md` distinguent les routes
d'authentification V3.0 des fonctions d'administration V3.1. V3.0 est livrée
sans interface web d'administration.

## [2026-10-22] Distribution Phase 3 : archive autonome sans Git

> **Supplantée par la Phase 5 et la Phase 7** : archive finale au nom neutre et documentation racine bilingue.

**Contexte** : les phases 1 et 2 ont remplacé le runtime regroupé par un
runtime llamafile-thin et un GGUF téléchargés séparément. La distribution
finale doit être utilisable sans clone Git.

**Décision(s)** :

1. L'utilisateur reçoit `lacitadelle-v2.zip`, l'extrait, lance `install.bat`,
   puis `lancer.bat`; Git n'est pas requis.
2. `bootstrap.py` télécharge llamafile-thin dans `dist/` et le GGUF dans
   `dev/tools/vendor/llamafile/`, avec vérification SHA-256.
3. `zipalign` et `setup_lacitadelle.py` ne font pas partie du parcours
   utilisateur.
4. La release GitHub v0.1.0 contenant l'ancien runtime regroupé est obsolète;
   sa dépréciation est une action manuelle du décideur.

**Conséquences** : Python et une connexion Internet sont requis à la première
installation. L'archive ne contient ni Git, ni runtime, ni modèle GGUF.

## [2026-10-22] Phase 5 : décisions implicites actées

**Contexte** : l'audit du 2026-10-22 a identifié cinq décisions prises
oralement entre les Phases 1 et 4 sans entrée formelle dans `decisions.md`.

**Décision(s)** :

1. Suppression définitive de `dist/archives/lacitadelle.exe` (environ 1,3 Go),
   artefact obsolète d'une génération précédente. Il n'est pas restauré.
2. `setup_lacitadelle.py` est supprimé en Phase 5 ; cet outil développeur
   était hors parcours utilisateur et son code est mort depuis la Phase 1.
3. Le fichier README est nommé `README.md`, conformément à la convention.
4. L'archive de distribution n'embarque pas `README.md` ; `LISEZMOI.txt` à
   la racine sert d'entrée utilisateur.
5. L'archive est renommée `lacitadelle-distribution.zip`, nom neutre sans
   numéro de version afin d'éviter la collision entre V3.1 authentification
   et V3.1 distribution.

**Conséquences** : les décisions implicites sont tracées. Les décisions #1,
#6, #9, #13 et #14 sont annotées comme partiellement supplantées sans
réécriture de leur corps historique.

## [2026-10-23] Trailer IA : Assisted-by (pas Co-authored-by)

**Contexte** : l'audit 7D a relevé d'abord 13, puis 14 commits avec le trailer
`Co-authored-by: Copilot`. Ce trailer est réservé aux co-auteurs humains et
peut porter des implications de paternité ou de DCO.

**Décision(s)** :

1. Les nouveaux commits réalisés avec assistance IA utilisent
   `Assisted-by: IA` et précisent l'outil (GitHub Copilot, Claude, etc.).
2. `Co-authored-by` reste réservé aux co-auteurs humains.
3. Les commits existants portant `Co-authored-by: Copilot` (14 sur 20 recensés)
   ne sont pas réécrits.
4. Pendant la transition, un trailer `Co-authored-by` ajouté automatiquement
   par un outil IA est toléré mais découragé; le corriger manuellement quand
   c'est possible.

**Conséquences** : l'attribution de l'assistance IA dans l'historique est plus
juste et la transition se fait progressivement, sans réécriture d'historique.

## [2026-10-23] Tests HTTP intermittents WinError 10053

**Contexte** : en Phase 7C, des échecs intermittents WinError 10053
(`connection reset`) ont été observés sur `test_change_password_ok` et
`test_post_message_no_auth`. Les deux tests passent en isolation; la troisième
exécution complète a réussi (73/73).

**Décision(s)** :

1. Les échecs intermittents sont une dette technique identifiée.
2. Leur traitement est reporté en Phase 8 dans un correctif dédié; ils ne
   bloquent pas la distribution actuelle.
3. Ne pas masquer les échecs par des retries automatiques sans investigation.

**Conséquences** : les tests restent fiables en isolation; la suite complète
peut présenter un échec intermittent à investiguer, sans que cela établisse
un défaut du code testé.

## [2026-10-23] Règles structurelles de suivi (AGENTS.md)

**Contexte** : les incidents de session (commit `f50691f` sans GO, ajout de
`backup/` sans décision et `JOURNALDESMODIFS.md` en retard de neuf commits)
ont révélé un défaut de méthode.

**Décision(s)** : les quatre règles suivantes sont actées dans `AGENTS.md` :

1. Une TODO de session est obligatoire au début et à la fin de chaque GO.
2. `JOURNALDESMODIFS.md` est maintenu à chaque commit structurant, dans le
   même commit.
3. `.gitignore` est proactif : tout artefact généré est ignoré dès sa
   première génération.
4. Aucune modification (fichier, commit, suppression ou renommage) n'est
   effectuée hors d'un GO validé.

**Conséquences** : la traçabilité est systématique et les prochains GO
respectent ces règles.

## [2026-10-23] Licence Apache 2.0

**Contexte** : le projet est distribué publiquement sous forme d'archive et
sur GitHub; une licence explicite est nécessaire.

**Décision(s)** : le projet est sous licence Apache 2.0, cohérente avec
llamafile (Mozilla AI) et Qwen3. La licence inclut une clause de brevet
explicite et est publiée dans `LICENSE` à la racine.

**Conséquences** : utilisateurs et contributeurs disposent d'un cadre
juridique clair, avec attribution requise et compatibilité avec l'écosystème
IA local.

## [2026-10-23] Documentation bilingue EN/FR

**Contexte** : le projet cible à la fois un public international sur GitHub et
un public francophone.

**Décision(s)** :

1. La documentation racine est bilingue : `README.md` et `CONTRIBUTING.md` en
   anglais, `README.fr.md` et `CONTRIBUTING.fr.md` en français.
2. Chaque fichier dispose d'un sélecteur de langue en tête.
3. Les liens de téléchargement pointent vers `releases/latest` afin de rester
   valides après un renommage de version.

**Conséquences** : la documentation est accessible aux publics anglophone et
francophone; le maintien des deux langues est accepté pour la taille du
projet.

## [2026-10-23] Barre de progression stdlib pur dans bootstrap.py

**Contexte** : `bootstrap.py` télécharge llamafile-thin (~42 Mo) et le GGUF
(~1,28 Go) silencieusement. Pour un utilisateur non averti, un téléchargement
long sans retour est anxiogène.

**Décision(s)** :

1. Ajouter une barre de progression ASCII en stdlib pur, sans `tqdm` ni `rich`.
2. Afficher le pourcentage et les tailles téléchargée/totale quand
   `Content-Length` est disponible; sinon afficher uniquement la taille
   téléchargée.
3. Rafraîchir la barre TTY avec `\r` et `flush=True`.
4. En non-TTY, ne pas utiliser `\r` et écrire une ligne de progression au plus
   toutes les cinq secondes.
5. Effacer la barre TTY avant de remonter une erreur de téléchargement.

**Conséquences** : retour de progression pour l'utilisateur final, tests
dédiés TTY et non-TTY, sans dépendance externe.

## [2026-10-23] Expérience Spec Kit : non adopté pour La Citadelle

**Contexte** : la Phase 7F-B a testé github/spec-kit en isolation complète
sur la même spec que la Phase 7F-A (barre de progression bootstrap.py).
Spec Kit a produit 10 artefacts (constitution, spec, plan, tasks, research,
data-model, quickstart, checklist, code, tests) mais avec un coût
d'installation élevé, un feedback VS Code trompeur (chat read-only alors
que les skills tournaient), et sans intégration native au projet.

**Décision(s)** :

1. Garder la méthode actuelle pour La Citadelle (Review/Simplify/Verif +
   décisions + journaux + TODO.md local + GO atomiques). Elle est validée,
   intégrée et mieux adaptée à un projet solo.
2. Ne pas installer Spec Kit dans le dépôt lacitadelle.
3. Réévaluer Spec Kit pour de futurs projets plus gros (3+ développeurs,
   features multi-semaines).
4. Retenir de Spec Kit trois idées utilisables sans l'outil :
   - Spec courte (user stories + acceptation) pour les features complexes.
   - Tâches ordonnées par user story.
   - Checklist de qualité avant implémentation.

**Conséquences** : la méthode actuelle reste la référence. Spec Kit est noté
comme piste future, pas comme dette. Aucune dépendance ajoutée au projet.

## [2026-10-23] Bug produit corrigé : corps POST non consommé avant contrôle d'auth

**Contexte** : la Phase 8 a reproduit `WinError 10053` sur les requêtes POST
refusées avant lecture de leur corps. `RequestHandler.do_POST` appliquait le
contrôle `must_change_password` avant que le corps soit consommé; la fermeture
de la connexion pouvait interrompre le client.

**Décision(s)** :

1. Lire le corps POST avant les contrôles d'authentification, avec une limite
   globale de 1 048 576 octets; rejeter un corps dépassant cette limite avec
   HTTP 413.
2. Réutiliser le corps mis en mémoire dans les handlers POST; leurs limites
   fonctionnelles existantes de 4 à 8 Kio restent en vigueur.
3. Ajouter un test de non-régression couvrant 100 POST restreints (403) et
   100 POST non authentifiés (401), avec lecture complète des réponses.
4. Valider 10/10 suites complètes (76 tests chacune), 5/5 suites HTTP, 5/5
   suites de progression et 200 requêtes de non-régression sans exception.

**Conséquences** : les réponses d'authentification restent 401/403 pour les
requêtes dans la limite, et les sessions `must_change_password` restent
bloquées sans abandon de connexion observé. La dette de tests intermittents
de la décision #20 est fermée.

## [2026-10-23] Espaces Markdown intentionnels acceptés (BACKLOG.md)

**Contexte** : lors du commit Phase 9C (`3642cde`), `git diff --cached
--check` a signalé quatre espaces de fin de ligne dans `BACKLOG.md` (lignes
17–18 et 49–50). Ces espaces sont des sauts de ligne Markdown intentionnels
(deux espaces en fin de ligne = `<br>`), pas des erreurs.

**Décision(s)** :

1. Les espaces Markdown intentionnels sont acceptés.
2. `git diff --cached --check` peut signaler des faux positifs sur les
   fichiers Markdown; ne pas corriger sans raison.
3. Le commit `3642cde` est laissé tel quel, sans commit correctif.

**Conséquences** : pas de bruit dans l'historique Git. Les fichiers Markdown
gardent leur mise en forme intentionnelle.

## [2026-10-23] CHANGELOG.md pointeur maintenu

**Contexte** : le projet n'utilise pas de `CHANGELOG.md` détaillé au sens du
versioning sémantique strict. Un agent ou un contributeur qui le cherche par
habitude pourrait croire qu'il n'existe pas.

**Décision(s)** :

1. Créer `CHANGELOG.md` à la racine comme pointeur.
2. Le faire pointer vers `JOURNALDEBORD.md`, `JOURNALDESMODIFS.md`,
   `ROADMAP.md`, `BACKLOG.md` et `.memory/decisions.md`.
3. Ne pas dupliquer le contenu des journaux.
4. Maintenir ce pointeur en cas de déplacement ou de renommage d'un fichier
   pointé.

**Conséquences** : le document fournit un point d'entrée vers l'historique
sans dupliquer son contenu.

## [2026-10-23] Règle 8 : CHANGELOG.md maintenu

**Contexte** : la décision #28 crée `CHANGELOG.md` comme pointeur. Une règle
est nécessaire pour en garantir la cohérence.

**Décision(s)** : acter la règle 8 dans `AGENTS.md` : `CHANGELOG.md` est un
pointeur maintenu; si un fichier pointé est déplacé ou renommé, mettre à jour
`CHANGELOG.md` dans le même commit.

**Conséquences** : la numérotation des règles structurelles passe de 7 à 8.
`CHANGELOG.md` reste cohérent avec les journaux, la Roadmap et le Backlog.

## [2026-10-23] Conception Mode B-1 : page de réglages

**Contexte** : `BACKLOG.md` définit Mode B-1 comme une page de réglages user
et admin avec logs et indicateurs. Les huit questions ouvertes ont été
présentées au décideur avant actage; la spécification a été validée en Phase
10A, sans changement de code.

**Décision(s)** :

1. Ajouter un `GET /settings` dans la sidebar, visible pour tout utilisateur
   authentifié, avec des sections conditionnelles selon le rôle.
2. Pour le user : réutiliser `/change-password`; stocker en SQLite par compte
   le thème sombre/clair et la taille de texte petite/normale/grande. Garder
   l'interface en français; exclure la pagination des sessions de B-1.
3. Pour l'admin : prévoir la gestion complète des comptes selon le contrat
   V3.1, les logs/indicateurs et un accès à B-2. B-1 n'implémente pas le
   changement de modèle.
4. Vérifier les droits côté serveur à chaque requête, revalider le rôle en
   base, renvoyer 401 pour une session absente et 403 à un user non-admin.
   Garder le proxy sur loopback jusqu'aux protections V3.1 avant écoute
   réseau.
5. Rafraîchir les logs par polling toutes les cinq secondes quand l'onglet
   est visible.
6. Capturer dans le proxy des événements structurés d'inférence, sans
   prompt, réponse générée ni secrets; filtrer par session pour un user et
   globalement pour un admin.
7. Mesurer la latence autour de l'appel modèle. Calculer tokens/s seulement
   depuis les compteurs d'usage effectivement retournés; sinon afficher
   « indisponible », sans estimation. Définir les sessions actives comme les
   tokens d'authentification non expirés en mémoire.
8. Persister les métadonnées dans une table SQLite liée au user/session, sans
   contenu de conversation et avec la durée de vie de la base locale.

**Conséquences** : Mode B-1 est spécifié et peut passer au statut « à
implémenter ». Les routes de réglages/logs et la persistance associée restent
à développer dans un GO séparé; aucun code n'est modifié en Phase 10A.

## [2026-10-24] Implémentation Phase 10B-1 : route /settings et préférences user

**Contexte** : la décision #30 spécifie le Mode B-1. La Phase 10B-1
implémente la première tranche : route `/settings`, template et préférences
user (thème et taille de texte) persistées en SQLite.

**Décision(s)** :

1. Ajouter une table `preferences` liée à `users` par `user_id`, avec
   contraintes `CHECK` pour `theme` et `font_size`.
2. Ajouter la migration idempotente `migrate_to_v4()`, appelée depuis
   `init_db()` et au démarrage du proxy après la migration V3.
3. Ajouter `GET /settings`, `GET /api/preferences` et
   `POST /settings/preferences`.
4. Ajouter `settings.html` et un lien dans la sidebar du chat.
5. Valider les valeurs de thème et de taille de texte; ne lire ou modifier
   que les préférences du compte authentifié.
6. Ajouter neuf tests dédiés à la route, aux préférences et à la migration.
7. Ne pas inclure la section admin/CRUD (10B-2/3), les logs (10B-4) ni les
   indicateurs (10B-5).

**Conséquences** : les utilisateurs peuvent personnaliser le thème et la
taille du texte. L'administration et les logs restent à implémenter dans
leurs tranches dédiées. Aucun autre code ni test existant n'est modifié.

## [2026-10-24] Correctif changement de mot de passe volontaire

**Contexte** : le test manuel de Phase 10B-1 a révélé que le lien « Changer
le mot de passe » depuis `/settings` menait à une page qui refusait le
changement. Le décideur a supprimé le contrôle `must_change_required(token)`
dans `handle_post_change_password`, qui bloquait le changement volontaire.

**Décision(s)** :

1. La suppression de ce contrôle dans le handler est conservée; celui-ci
   vérifie toujours l'ancien mot de passe.
2. Le middleware `check_must_change_gate` reste actif : les sessions
   `must_change_password=1` restent forcées vers `/change-password`.
3. Le template indique « Changer votre mot de passe » pour les deux modes.
4. Le contrat retenu pour un ancien mot de passe erroné ou manquant est
   `401 Unauthorized`, cohérent avec `test_change_password_old_wrong`.
5. Les tests couvrent le changement volontaire, l'ancien mot de passe
   erroné/manquant, l'accès depuis `/settings` et le mode obligatoire. Le
   test existant `test_change_password_old_wrong` reste inchangé; le test
   `test_change_password_not_required` est adapté au nouveau comportement.

**Conséquences** : un utilisateur normal peut changer son mot de passe après
validation de l'ancien. Le mode obligatoire reste actif et les erreurs
d'ancien mot de passe restent en `401`. Aucun autre changement de
`login_server.py` n'est fait en Phase 10B-1b.

## [2026-10-24] Implémentation Phase 10B-2 : admin read-only

**Contexte** : la décision #30 prévoit une section admin dans le Mode B-1.
La Phase 10B-2 implémente la première tranche : page `/admin` avec liste des
utilisateurs en lecture seule, contrôle d'accès serveur et lien conditionnel
dans la sidebar.

**Décision(s)** :

1. Ajouter la route `GET /admin` avec une page séparée.
2. Ajouter l'endpoint `GET /api/admin/users` avec une liste de champs
   explicitement autorisés, sans `password_hash`.
3. Ajouter `GET /api/me`, limité au nom d'utilisateur et au rôle, pour
   déterminer l'affichage du lien admin.
4. Vérifier le rôle `admin` et l'état actif en base à chaque requête protégée;
   rediriger une session absente pour la page, renvoyer `401` pour l'API et
   `403` à un utilisateur non-admin.
5. Ajouter `admin.html` en lecture seule, avec la liste et le résumé des
   comptes; afficher la contrainte d'un seul admin actif jusqu'à V3.2.
6. Afficher le lien Administration uniquement pour les admins dans les
   sidebars du chat et des réglages.
7. Ajouter neuf tests dédiés, notamment l'absence de fuite de
   `password_hash` et le maintien du gate `must_change_password`.
8. Reporter le CRUD admin à la Phase 10B-3; les logs et indicateurs restent
   en 10B-4/5.

**Conséquences** : les admins disposent d'une vue d'ensemble des comptes sans
capacité de modification. Le contrôle d'accès reste côté serveur; le CRUD,
les logs et les indicateurs ne sont pas inclus.

## [2026-10-24] Phase 10B-3 : découpage en 5 sous-lots

**Contexte** : Phase 10B-2 (admin read-only) est terminée. Phase 10B-3
(CRUD admin) est un chantier trop gros pour un seul GO (créer, supprimer,
promouvoir, désactiver, reset). Un découpage est nécessaire pour maîtriser
la complexité et les tests.

**Décision(s)** : Phase 10B-3 est découpée en 5 sous-lots, chacun avec son
propre GO, son commit et ses tests :

1. 10B-3a : créer un utilisateur (formulaire, validation, route POST).
2. 10B-3b : désactiver/réactiver un utilisateur.
3. 10B-3c : promouvoir/rétrograder, avec la contrainte d'un seul admin actif.
4. 10B-3d : supprimer un utilisateur, avec protections du dernier admin et
   contre l'autosuppression.
5. 10B-3e : reset du mot de passe par l'admin, avec changement forcé à la
   prochaine connexion.

**Conséquences** : chaque sous-lot est testé avant le suivant. Aucun sous-lot
ne peut commencer avant la validation du précédent. Le découpage est
documenté dans `BACKLOG.md`.

## [2026-10-24] Implémentation Phase 10B-3a : création d'utilisateur (admin)

**Contexte** : la décision #34 découpe la Phase 10B-3 en cinq sous-lots.
10B-3a implémente la création d'utilisateur par un admin.

**Décision(s)** :

1. Ajouter la route `POST /api/admin/users`, protégée par `require_admin`.
2. Générer côté serveur un mot de passe temporaire aléatoire de 16 caractères,
   avec un générateur cryptographiquement sûr.
3. Retourner le mot de passe temporaire une seule fois dans la réponse JSON de
   création; ne jamais le journaliser ni le rendre récupérable via l'API.
4. Forcer `must_change_password=1` à la création.
5. Créer uniquement des comptes `role='user'`; la promotion est réservée à
   10B-3c.
6. Valider le nom d'utilisateur : 3 à 30 caractères, lettres ASCII,
   chiffres et underscore, et unicité.
7. Tester la création, le doublon, les noms invalides, les autorisations,
   puis la connexion avec le mot de passe temporaire et le changement forcé.

**Conséquences** : un admin peut créer un compte user dont le mot de passe
doit être changé à la première connexion. La désactivation, la promotion,
la suppression et le reset restent reportés aux sous-lots 10B-3b/c/d/e.

## [2026-10-24] Correctif menu Administration conditionnel + règle 9

**Contexte** : le test manuel de Phase 10B-3a a révélé que le lien
« Administration » apparaît pour les comptes `user`. Une nouvelle règle de
traçabilité est également actée : toute décision doit être ajoutée à
`TODO.md` dès qu'elle est prise.

**Décision(s)** :

1. Le lien « Administration » reste caché par défaut et n'est révélé que
   lorsque `/api/me` confirme `role='admin'`; le CSS doit respecter l'attribut
   HTML `hidden`.
2. Ajouter la règle 9 à `AGENTS.md` : consigner immédiatement dans `TODO.md`
   toute nouvelle décision, architecture ou proposition actée.
3. Acter le nettoyage futur de la base locale : supprimer les comptes
   `phase6c-admin`, `admin` et `phase6c-chat`, puis créer `superadmin`. Cette
   opération destructive est réservée à un GO Phase 10-cleanup distinct,
   avec sauvegarde vérifiée et confirmation explicite.

**Conséquences** : les comptes `user` ne voient pas le lien d'administration.
Les nouvelles décisions et tâches sont tracées immédiatement dans le
`TODO.md` local. Le nettoyage de la base n'est pas exécuté dans ce GO.

## [2026-10-24] Nettoyage base locale et création d'un admin propre

**Contexte** : la base locale contenait trois comptes legacy :
`phase6c-admin` (mot de passe perdu), `admin` (`role='user'`) et
`phase6c-chat` (compte de test). Elle contenait aussi trois sessions,
20 messages et une préférence; aucune table `metrics` n'existait. Le
décideur a confirmé la suppression, après sauvegarde vérifiée.

**Décision(s)** :

1. Sauvegarder la base avant toute modification dans
   `citadelle_data/memory.db.backup-2026-10-24`.
2. Supprimer tous les comptes de la base locale avec `DELETE FROM users`,
   en activant les clés étrangères pour supprimer en cascade sessions,
   messages et préférences.
3. Créer `superadmin` via `create_admin.py`, avec rôle admin, compte actif,
   mot de passe temporaire affiché une seule fois et
   `must_change_password=1`.
4. Ne jamais consigner le mot de passe dans les journaux, décisions,
   `TODO.md` ou Git.
5. Laisser au décideur la validation manuelle de la connexion, du changement
   obligatoire de mot de passe, de l'accès `/admin` et de la création d'un
   user depuis l'interface.

**Conséquences** : la base active contient un seul compte admin et aucune
session, conversation ou préférence héritée. Le backup conserve l'ancien état
pour une restauration éventuelle. La validation manuelle reste à effectuer.

## [2026-10-24] Création admin manuelle et encodage UTF-8 Windows

**Contexte** : l'exécution précédente de `create_admin.py` avait créé
`superadmin`, puis échoué lors de l'affichage d'un avertissement Unicode
sous Windows cp1252. Le décideur a ensuite mené manuellement la création et
le test admin; la base contient maintenant `superadmin` et `didier`. Lors de
ce GO, l'inventaire différait de l'état attendu; la transaction de
suppression a été annulée sans écriture et le décideur a explicitement
ordonné de ne rien supprimer.

**Décision(s)** :

1. Sur Windows, configurer stdout et stderr en UTF-8 dans `create_admin.py`
   avant les sorties CLI, afin que l'avertissement n'échoue pas après
   l'insertion du compte.
2. Le décideur lance `create_admin.py` depuis son propre terminal pour voir
   et noter le mot de passe affiché une seule fois. L'IDE ne lance pas le
   script, ne génère pas et ne consigne aucun mot de passe.
3. En cas de divergence entre l'inventaire attendu et la base actuelle,
   annuler la suppression et demander instruction; aucun compte/donnée
   supplémentaire ne sera supprimé sans autorisation.
4. Conserver la base actuelle, avec `superadmin` admin actif et `didier`
   user actif; aucune suppression n'a été effectuée pendant ce GO.

**Conséquences** : la sortie CLI Windows utilise UTF-8; 105 tests passent.
La base a été vérifiée en lecture seule. Les mots de passe ne figurent dans
aucun document ni commit.

## [2026-10-24] Auto-création d'un admin au démarrage (Phase 10C)

**Contexte** : après une première installation ou un nettoyage de base, aucun
admin actif n'existe et l'utilisateur ne peut pas accéder à `/admin` pour
créer des comptes. Aujourd'hui, le premier admin doit être créé manuellement
avec `create_admin.py`, ce qui est peu ergonomique.

**Décision(s)** :

1. Au démarrage de `login_server.py`, dans `main()`, vérifier si la base
   active contient au moins un compte avec `role='admin'` et `is_active=1`.
2. S'il n'existe aucun admin actif, créer automatiquement `superadmin`
   (`role='admin'`, `is_active=1`, `must_change_password=1`) avec un mot de
   passe généré aléatoirement.
3. Afficher ce mot de passe une seule fois dans la console du proxy avec
   une consigne claire de le noter.
4. Si un admin actif existe, afficher un message informatif avec son username
   seulement, sans exposer de mot de passe.
5. Ne pas prendre en charge le cas où la base active est vide mais un
   `superadmin` existe uniquement dans un backup; le serveur ne consulte que
   la base active.

**Conséquences** : la première installation et un nettoyage complet peuvent
être suivis d'une connexion admin sans lancement manuel de
`create_admin.py`. Les installations ayant déjà un admin actif affichent
seulement un message informatif et ne créent pas de doublon. La gestion de
l'échec de création, l'écriture du mot de passe dans un fichier et une
désactivation éventuelle de l'auto-création restent à examiner en Review
pendant l'implémentation de Phase 10C.

## [2026-10-24] Implémentation Phase 10C : auto-création admin au démarrage

**Contexte** : la décision #39 acte l'auto-création d'un administrateur au
démarrage si aucun admin actif n'existe. La Phase 10C implémente cette
logique. Les décisions d'implémentation précisent les choix Q1/Q2/Q3.

**Décision(s)** :

1. Ajouter `ensure_admin_exists(db_path=None)` dans `citadelle_memory.py`;
   utiliser le hash scrypt et le générateur de mot de passe existants.
2. Appeler le helper au démarrage de `login_server.py`, dans `main()`,
   après les migrations. Créer `superadmin` avec
   `role='admin'`, `is_active=1` et `must_change_password=1` si aucun admin
   actif n'existe.
3. Afficher le mot de passe une seule fois sur la console proxy (Q1);
   ne pas créer de fichier de mot de passe.
4. Si un admin actif existe, afficher son username seulement. En cas
   d'échec de migration ou de création, afficher une erreur claire et
   l'action manuelle, ne pas retenter et laisser le serveur démarrer (Q2).
5. Ne prévoir aucune variable d'environnement pour désactiver la création
   (Q3).
6. Ajouter quatre tests sur création, doublon, admin inactif, affichage
   console et poursuite du démarrage en cas d'erreur.

**Conséquences** : une base sans admin actif reçoit un compte `superadmin`
et le décideur voit son mot de passe temporaire dans la console. Si un admin
actif existe, aucun compte n'est ajouté et seul son username est affiché.
La gestion d'un `superadmin` présent uniquement dans un backup reste hors
périmètre.

## [2026-10-24] Implémentation Phase 10B-3b : désactiver/réactiver

**Contexte** : la décision #34 découpe le CRUD admin en cinq sous-lots.
10B-3b ajoute la désactivation et la réactivation, après la création
d'utilisateur de 10B-3a.

**Décision(s)** :

1. Ajouter `POST /api/admin/users/{id}/deactivate` et
   `POST /api/admin/users/{id}/activate`, protégées par `require_admin`.
2. Refuser l'auto-désactivation et la désactivation du dernier admin actif.
3. À la désactivation, passer `is_active` à `0`, supprimer dans la même
   transaction les lignes `sessions` de l'utilisateur (et donc ses messages
   liés par cascade), puis révoquer tous ses jetons d'authentification en
   mémoire du proxy.
4. À la réactivation, remettre `is_active` à `1`; les anciennes sessions
   supprimées ne sont pas restaurées et l'utilisateur doit se reconnecter.
5. L'interface demande une confirmation simple avant chaque action; les
   protections sont aussi appliquées côté serveur.
6. Vérifier que `is_active=0` empêche le login et ajouter six tests couvrant
   désactivation, protection du dernier admin, auto-désactivation,
   réactivation, login bloqué et contrôle d'accès.

**Conséquences** : les utilisateurs désactivés ne peuvent plus se connecter
et leurs sessions de proxy sont invalidées; leur historique conversationnel
est supprimé en cascade. Aucun rôle n'est modifié. Promotion, rétrogradation,
suppression de compte et reset de mot de passe restent réservés aux lots
10B-3c/d/e.

## [2026-10-24] Correctif 10B-3b-bis : suppression explicite des messages

**Contexte** : le test manuel a observé des sessions et messages encore
présents après désactivation. Le diagnostic a confirmé que le handler
contenait déjà `DELETE FROM sessions`, un commit dans la transaction et une
connexion avec `PRAGMA foreign_keys=ON`; le schéma déclare aussi
`ON DELETE CASCADE` de `messages` vers `sessions`. L'inventaire courant
montre les utilisateurs actifs et les lignes concernées, mais ne permet pas
de déterminer si elles ont été recréées après réactivation ou si le test a
utilisé une ancienne instance du proxy.

**Décision(s)** :

1. Supprimer explicitement les `messages` des sessions du user avant de
   supprimer ses lignes `sessions`, puis passer `is_active=0`; les trois
   opérations restent dans la même transaction.
2. Enrichir le test pour vérifier les compteurs avant/après, puis réactiver
   le user, le reconnecter et confirmer que sa liste de sessions est vide.
   Le test désactive les clés étrangères sur la connexion d'essai pour
   vérifier que la suppression des messages ne dépend pas de la cascade.
3. Ne pas modifier les autres comportements de désactivation/réactivation.

**Conséquences** : la suppression des messages est garantie explicitement,
même si la cascade SQLite ne s'applique pas. Les sessions et leur historique
ne sont pas restaurés à la réactivation; l'utilisateur repart avec une
liste vide.


## [2026-10-24] Implémentation Phase 10B-3c : promouvoir/rétrograder

**Contexte** : la décision #34 limite le CRUD admin à un admin actif jusqu'à
V3.2. La règle initiale Q1 (refuser la promotion dès qu'un admin existe)
rendait la promotion impossible avec `require_admin` et l'interdiction de
rétrograder le dernier admin. Le décideur a clarifié Q1 en choisissant un
transfert atomique de l'admin appelant vers la cible.

**Décision(s)** :

1. Ajouter `POST /api/admin/users/{id}/promote` et
   `POST /api/admin/users/{id}/demote`, toutes deux protégées par
   `require_admin`.
2. Promouvoir un user actif transfère atomiquement le rôle admin de
   l'appelant à la cible. À tout instant après commit, il reste exactement
   un admin actif; l'admin appelant devient `user`.
3. Refuser la promotion d'un utilisateur désactivé ou déjà admin.
4. Refuser l'auto-rétrogradation et la rétrogradation du dernier admin actif.
5. À la rétrogradation, supprimer dans la transaction les messages et
   sessions conversationnelles du compte, puis passer son rôle à `user`;
   révoquer aussi ses jetons d'authentification en mémoire. Cela s'applique
   également à l'admin appelant rétrogradé lors du transfert.
6. Ajouter des confirmations UI décrivant le transfert et la suppression
   des conversations; ne pas afficher le bouton de rétrogradation sur son
   propre compte.
7. Ajouter six tests couvrant transfert, cibles invalides, rétrogradation,
   dernier admin, auto-rétrogradation et accès non-admin.

**Conséquences** : un admin peut promouvoir un user actif en lui transférant
son propre rôle dans une seule transaction. Le précédent admin devient user,
est déconnecté et perd ses conversations stockées. Aucune promotion multiple,
suppression de compte ou reset n'est ajouté; les lots 10B-3d/e restent séparés.

## [2026-10-24] Implémentation Phase 10B-3d : suppression d'un utilisateur

**Contexte** : la décision #34 découpe le CRUD admin en cinq sous-lots.
10B-3d implémente la suppression physique d'un utilisateur par un admin.

**Décision(s)** :

1. Ajouter `POST /api/admin/users/{id}/delete`, protégé par `require_admin`.
2. Supprimer physiquement la ligne `users` dans une transaction; `PRAGMA
   foreign_keys=ON` et les clés `ON DELETE CASCADE` suppriment sessions,
   messages et préférences liées. La table `metrics` n'existe pas dans le
   schéma actuel.
3. Refuser l'auto-suppression et la suppression du dernier admin actif.
4. Révoquer en mémoire les jetons de l'utilisateur supprimé après le commit.
5. Exiger une double confirmation UI : confirmation puis saisie exacte du
   username. Indiquer que l'action est irréversible et ne pas créer de backup.
6. Tester suppression et cascade, dernier admin, auto-suppression, non-admin
   et utilisateur absent.

**Conséquences** : un admin peut supprimer un autre user; ses données
persistées et sessions d'authentification sont supprimées sans possibilité
de restauration par l'application. La suppression du dernier admin actif et
l'auto-suppression restent interdites. Le reset de mot de passe (10B-3e)
reste à implémenter.

## [2026-10-24] Implémentation Phase 10B-3e : reset de mot de passe admin

**Contexte** : la décision #34 découpe le CRUD admin en cinq sous-lots.
10B-3e implémente le reset de mot de passe d'un user par un admin, dernier
sous-lot du bloc admin.

**Décision(s)** :

1. Ajouter `POST /api/admin/users/{id}/reset-password`, protégé par
   `require_admin`.
2. Générer un mot de passe temporaire aléatoire de 16 caractères, le hasher
   avec scrypt, définir `must_change_password=1` et le retourner une seule
   fois à l'admin dans la réponse.
3. Ne pas logger ni stocker le mot de passe temporaire et ne pas notifier
   l'utilisateur (pas d'email ni de log).
4. Afficher le mot de passe une seule fois dans l'interface avec un bouton
   Copier et une confirmation simple avant le reset. Autoriser le reset de
   son propre mot de passe.
5. Révoquer les sessions d'authentification existantes de la cible pour que
   le prochain login utilise le mot de passe temporaire et impose le
   changement. Conserver ses conversations.
6. Tester reset, hash, `must_change_password`, login restreint, non-admin et
   utilisateur absent.

**Conséquences** : l'admin peut réinitialiser le mot de passe d'un user; la
cible doit le changer à sa prochaine connexion. Le mot de passe temporaire
n'est pas conservé côté serveur ni dans un fichier. Le bloc admin est complet
après validation du redémarrage de `lancer.bat` et du test manuel.

## [2026-10-25] Modal de confirmation admin (Phase 10B-3g)

**Contexte** : la validation E2E 10B-3f a révélé que `prompt()` n'est pas
supporté par le navigateur intégré. La confirmation par saisie du username
ne pouvait donc pas être testée dans cet environnement.

**Décision(s)** :

1. Remplacer `prompt()` par un élément HTML `<dialog>` stylé, avec saisie du
   username, boutons Confirmer/Annuler et message d'erreur accessible si la
   saisie ne correspond pas.
2. Conserver la première confirmation de suppression et ne lancer la requête
   de suppression qu'après correspondance exacte du username.
3. Réutiliser le même helper modal pour la confirmation simple du reset de
   mot de passe; masquer le champ de saisie lorsqu'il n'est pas requis.
4. S'appuyer sur le comportement modal natif de `<dialog>` pour le focus,
   l'isolation du contenu arrière et l'annulation par Échap.
5. Mettre à jour l'assertion de test devenue obsolète; les 131 tests
   automatisés restent verts. Revalider les scénarios 10B-3d et 10B-3e en
   E2E.

**Conséquences** : la double confirmation de suppression fonctionne dans le
navigateur intégré. Les scénarios 10B-3d et 10B-3e sont validés; le bloc
CRUD admin est testé de bout en bout (6/6).

## [2026-10-25] Implémentation Phase 10B-4a : métriques d'inférence backend

**Contexte** : la décision #30 prévoit la capture côté proxy de métadonnées
d'inférence sans prompt ni réponse. La Phase 10B-4a livre la persistance et
l'instrumentation backend; l'API et l'interface restent dans 10B-4b.

**Décision(s)** :

1. Ajouter `inference_metrics` avec `user_id`, `session_id`, `timestamp`,
   `duration_ms`, `status`, `prompt_tokens` et `completion_tokens`.
2. Ajouter la migration idempotente `migrate_to_v5()`, appelée depuis
   `init_db()` et au démarrage du proxy.
3. Ajouter `record_inference(...)` qui ne persiste que ces métadonnées.
4. Instrumenter `call_llamafile()` avec la durée monotone, les statuts
   `ok`/`error`/`timeout` et les compteurs d'usage disponibles.
5. Garder l'enregistrement best-effort : une erreur de métrique ne casse pas
   l'appel d'inférence et son diagnostic ne contient aucun contenu.
6. Appliquer `ON DELETE CASCADE` à l'utilisateur et `ON DELETE SET NULL` à
   la session. Aucun prompt, réponse générée ou secret n'est enregistré.
7. Couvrir capture, isolation par user, cascade utilisateur, session NULL et
   absence de colonnes de contenu par quatre tests dédiés.

**Conséquences** : les métadonnées d'inférence sont conservées localement et
liées au compte, sans contenu de conversation. La route et l'onglet Logs
restent à implémenter en 10B-4b.

## [2026-10-25] Implémentation Phase 10B-4b : route et onglet Logs

**Contexte** : la décision #30 prévoit la consultation des événements
d'inférence sans exposer le contenu des conversations. La Phase 10B-4a a
fourni la table `inference_metrics`; la Phase 10B-4b ajoute l'API et les
interfaces de consultation admin/user.

**Décision(s)** :

1. Ajouter `GET /api/logs/tail?lines=50`, accessible uniquement avec une
   session authentifiée et un compte actif.
2. Relire le rôle courant en base à chaque requête. Un admin voit tous les
   logs; un user ne voit que les métriques rattachées à son `user_id`.
3. Borner `lines` entre 1 et 500; valeur absente ou invalide = 50. Trier par
   horodatage puis identifiant décroissant.
4. Retourner uniquement id, timestamp, username, session_title, duration_ms,
   status et compteurs de tokens. Ne retourner aucun prompt, réponse ou secret.
5. Ajouter un onglet Logs sur `/admin` et une section « Mes logs » sur
   `/settings` pour les users; rendre les lignes avec `textContent`.
6. Rafraîchir toutes les cinq secondes seulement lorsque le document est
   visible; arrêter le polling si l'onglet Logs admin n'est plus sélectionné.
7. Tester l'authentification, le filtrage par rôle, les limites, l'absence de
   contenu sensible et les tableaux dans les deux pages.

**Conséquences** : les admins disposent d'une vue globale et les users d'une
vue limitée à leurs métriques. Le polling ne s'exécute pas en arrière-plan.
La Phase 10B-4b est terminée; la suite prévue est 10B-5 (indicateurs agrégés).

## [2026-10-25] Implémentation Phase 10B-5 : indicateurs agrégés et clôture Mode B-1

**Contexte** : la décision #30 prévoit des indicateurs agrégés fondés sur
les métadonnées d'inférence, sans estimer les compteurs absents ni lire les
conversations. Les Phases 10B-1 à 10B-4b sont terminées; 10B-5 clôt le Mode
B-1.

**Décision(s)** :

1. Ajouter `GET /api/indicators?window=24h|7d|30d`, authentifié, avec
   filtrage serveur : les admins voient tous les comptes, les users leurs
   propres métriques.
2. Utiliser 24 h par défaut; une fenêtre invalide revient à 24 h.
3. Calculer le débit comme `SUM(completion_tokens) / (SUM(duration_ms) / 1000)`
   sur les inférences réussies avec tokens disponibles et durée positive.
   Renvoyer `null` si aucune durée/tokens exploitables; ne pas estimer.
4. Calculer la latence moyenne et le temps moyen/requête sur toutes les
   inférences de la fenêtre; calculer le p95 selon nearest-rank et le taux
   d'erreur comme ratio `status != 'ok' / total`.
5. Compter les tokens de session d'authentification présents en mémoire et
   non expirés; limiter le compte user à son propre `user_id`.
6. Afficher les sept indicateurs en cartes sur `/admin` et en tableau sur
   `/settings`, avec choix de fenêtre et polling à cinq secondes seulement
   lorsque le document est visible.
7. Couvrir l'authentification, l'agrégation globale, le filtrage user, les
   fenêtres, les sessions actives, l'absence de données et l'absence de
   champs sensibles par cinq tests dédiés.

**Conséquences** : les admins voient les indicateurs globaux et les users
uniquement ceux de leur compte. Le Mode B-1 est entièrement implémenté;
10B-5 clôt cette tranche et le Mode B-2 reste distinct.

## [2026-10-25] Conception Mode B-2 : changement de modèle

**Contexte** : le Mode B-1 est clôturé. Le Mode B-2 permettra à un admin
actif de changer le GGUF chargé par llamafile. Un seul admin actif existe
jusqu'à V3.2; une configuration invalide peut donc rendre le service
indisponible pour tous. `lancer.bat` passe actuellement le chemin du modèle
directement à llamafile, tandis que `dev/tools/llamafile_config.json` décrit
les assets d'installation. Aucune décision dédiée au changement de modèle
n'existait.

**Décision(s)** :

1. Intégrer le bouton « Changer de modèle » à la section admin de
   `/settings`, dans le périmètre du Mode B-1; réserver la route
   `POST /api/admin/model` aux admins actifs selon le contrat V3.1.
2. Stocker la configuration runtime dans une table SQLite `settings`
   (Q1-b), cohérente avec la base locale existante.
3. Exiger un rollback automatique double (Q2-d) : tester le chargement avant
   application et revenir immédiatement à la configuration précédente en
   cas d'échec; garder aussi un mécanisme de retour automatique à l'ancien
   modèle au prochain démarrage si le nouveau ne démarre pas.
4. Maintenir une whitelist curée et documentée de 5 à 10 modèles, avec test
   de chargement à la soumission; un GGUF hors liste peut être essayé après
   avertissement, avec le même test préalable (Q3-c).
5. Stocker le modèle actif dans `settings`, clé `current_model_path` (Q4-a).
6. Conserver l'ancien modèle pour permettre le rollback; ne pas le supprimer
   automatiquement après un changement réussi (Q5-b).
7. Afficher clairement tout échec et
   conserver un diagnostic de rollback non sensible.
8. Découper l'implémentation en sous-lots séparés durant la Phase 11. Aucun
   code n'est modifié dans cette conception.

**Conséquences** : le Mode B-2 est spécifié pour un GO d'implémentation
dédié. Le modèle Qwen3 actuel reste le modèle par défaut jusqu'à
l'implémentation et la validation du nouveau flux.

## [2026-10-25] Implémentation Phase 11a : table settings + helpers

**Contexte** : la décision #50 (conception Mode B-2) retient une table
SQLite `settings` pour conserver `current_model_path` et
`previous_model_path`. La Phase 11a fournit la migration et les helpers de
persistance sans route ni interface.

**Décision(s)** :

1. Créer `settings` avec `key TEXT PRIMARY KEY`, `value TEXT NOT NULL` et
   `updated_at TEXT NOT NULL`.
2. Ajouter `migrate_to_v6()` idempotente avec `CREATE TABLE IF NOT EXISTS`.
3. Ajouter `get_setting(key, default=None, db_path=None)` et
   `set_setting(key, value, db_path=None)`; `set_setting` met à jour la
   valeur et l'horodatage par upsert.
4. Appeler `migrate_to_v6()` depuis `init_db()` et au démarrage du proxy,
   après `migrate_to_v5()`.
5. Tester l'idempotence, l'application depuis `init_db`, la valeur par
   défaut, get/set et l'upsert. Ne modifier aucune route ou interface.

**Conséquences** : le schéma local peut stocker les paramètres runtime après
migration V6. Les helpers sont disponibles pour la route du sous-lot 11b;
la base réelle recevra la table au prochain redémarrage de `lancer.bat`.

## [2026-10-25] Implémentation Phase 11b : route POST /api/admin/model

**Contexte** : la décision #50 prévoit un changement de modèle administrateur
stocké dans `settings`; la Phase 11a a ajouté la migration et les helpers.
La Phase 11b ajoute uniquement la route de validation/enregistrement, sans
charger le modèle ni redémarrer llamafile.

**Décision(s)** :

1. Ajouter `POST /api/admin/model`, protégé par `require_admin`, avec un
   body JSON contenant `model_path`.
2. Rejeter les chemins manquants/invalides; résoudre le chemin absolu et
   exiger un fichier régulier d'extension `.gguf` et de taille supérieure
   à zéro.
3. Écrire le chemin résolu dans `settings.current_model_path` via
   `set_setting`.
4. Retourner les informations du chemin et sa taille. Indiquer clairement
   que le chargement attend le test et le redémarrage prévus en 11d.
5. Ne pas tester le chargement, redémarrer llamafile, modifier l'UI ou
   effectuer la validation whitelist/hash (prévue en 11e).
6. Couvrir autorisation, chemin valide, chemin absent, extension invalide et
   fichier vide par cinq tests.

**Conséquences** : un admin actif peut enregistrer un chemin GGUF existant.
Le runtime actif n'est pas modifié par cette route; le test de chargement et
le redémarrage restent en 11d.
