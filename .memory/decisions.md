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
