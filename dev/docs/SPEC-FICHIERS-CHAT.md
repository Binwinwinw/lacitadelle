# Spécification fonctionnelle — fichiers dans les conversations

**Statut** : Fonctionnel validé et premier incrément implémenté (GO 25) ;
paramètres techniques validés; limites de tokens approximatives.

**Commit de référence** : `83305fe` (HEAD observé au préflight GO 25).

Les règles fonctionnelles du premier incrément ont été validées le
2026-11-24 et sont consignées dans la
[décision #128](../../.memory/decisions.md#L2904); les choix techniques et
l'implémentation sont consignés dans la décision #129. Les budgets de tokens
restent des estimations et n'ont pas fait l'objet d'un benchmark live.

## Statuts utilisés

- **Règle validée** : comportement fonctionnel décidé le 2026-11-24.
- **Choix technique validé** : valeur ou mécanisme accepté dans la décision #129.
- **Limite estimée** : valeur fondée sur une approximation, non une mesure exacte.
- **Question ouverte** : sujet hors du premier incrément qui requiert une décision.
- **Cible multiformat future** : évolution souhaitée, non incluse au premier lot.
- **Hors périmètre** : non inclus dans ce premier incrément; pas un abandon.

## 1. But et non-objectifs

### But

- **Besoin exprimé** : ajouter un ou plusieurs fichiers depuis l’interface
  du chat à la conversation en cours, sans exiger que le fichier soit déjà
  dans `dev/docs/`, `dev/tests/`, `dev/tools/` ou `dev/workflows/`.
- **Besoin exprimé** : demander au modèle de commenter, résumer, reformuler,
  expliquer ou analyser le contenu.
- **Besoin exprimé** : pouvoir poser plusieurs questions sur le document dans
  la conversation.
- **Besoin exprimé** : retrouver les questions et réponses à la réouverture
  de l’historique.
- **Règle validée** : le fichier original est temporaire; le contenu textuel
  extrait est conservé avec le propriétaire et la conversation.
- **Règle validée** : chaque compte n’accède qu’aux documents de ses propres
  conversations; `admin` n’accorde aucun accès automatique aux autres comptes.
- **Règle validée** : garder les fichiers généraux du chat distincts
  d’AIWorkflow et des workflows métier.
- **Besoin exprimé** : ne pas assimiler un rôle métier comme « enseignant »
  ou « coach » au rôle d’autorisation `admin`/`user`.

### Non-objectifs de cette spécification

- **Hors périmètre** : décider maintenant si AIWorkflow fait partie de V3 ou V4;
  cette spécification ne tranche pas ce point.
- **Hors périmètre** : construire une bibliothèque personnelle réutilisable
  entre plusieurs conversations. Ce besoin n’est pas validé.
- **Hors périmètre** : exécuter le contenu d’un fichier, notamment SQL,
  Dockerfile, script, binaire ou macro. Lire un tel fichier pour l’expliquer
  n’autorise pas son exécution.
- **Hors périmètre** : intégrer des rôles métier sélectionnables ou modifier
  le persona Nexxus.
- **Cible multiformat future** : photos, documents bureautiques, PDF, texte,
  SQL, Dockerfiles et autres formats souhaités; prise en charge à définir par
  évolution, sans promesse de compatibilité immédiate.

## 2. Repères de l’existant

Ces constats proviennent des lectures en mode investigation des GO 21 et 22;
ils ne sont pas des exigences nouvelles.

- **Hors périmètre — existant conservé** : AIWorkflow expose actuellement
  une action admin basée sur un chemin serveur et un prompt. Le chemin doit
  être dans un des répertoires autorisés du bundle
  ([chat.html](../tools/web/chat.html#L55),
  [workflow_runner.py](../tools/workflow_runner.py#L33)).
- **Hors périmètre — existant conservé** : les workflows enregistrés sont
  `analyse_md`, `analyse_pdf` et `analyse_sql`
  ([workflow_runner.py](../tools/workflow_runner.py#L23)).
- **Hors périmètre — différence avec l’objectif** : l’action actuelle affiche
  le résultat dans le DOM de la conversation, mais n’enregistre pas l’échange
  dans son historique serveur ([chat.js](../tools/web/chat.js#L491),
  [décision #117](../../.memory/decisions.md#L2706)).
- **Hors périmètre — existant conservé** : le chat normal persiste les messages
  de la session et les filtre par utilisateur; ce comportement est la référence
  pour l’historique ([login_server.py](../tools/login_server.py#L2473),
  [AUTH_CONTRACT.md](./AUTH_CONTRACT.md#L172)).
- **Hors périmètre — non équivalent** : le RAG FTS5 d’AIWorkflow travaille
  dans un workflow documentaire; il ne constitue pas une bibliothèque générale
  de fichiers du chat ([ARCHITECTURE.md](./ARCHITECTURE.md#L213),
  [TODO.md](../../TODO.md#L96)).

## 3. Parcours utilisateur validé

1. L’utilisateur choisit un fichier `.md` depuis l’interface dans une
   conversation; le serveur vérifie l’identité, la propriété de la conversation,
   les droits et le contenu du fichier.
2. L’interface montre le nom, le type et l’état du document. Le fichier
   original est temporaire; son texte extrait est conservé avec le propriétaire
   et la conversation.
3. L’utilisateur pose une première question; le modèle reçoit le contenu utile
   dans les limites approximatives de la section 11. Les questions et réponses
   sont enregistrées dans l’historique normal.
4. L’utilisateur peut poser des questions complémentaires sans téléverser à
   nouveau le fichier. Après rechargement, l’historique et le document associé
   restent consultables.
5. Le retrait supprime le contenu documentaire conservé et empêche sa
   réinjection. L’interface marque le document comme indisponible; les messages
   déjà enregistrés restent visibles et peuvent contenir des informations
   dérivées du document.
6. La suppression de la conversation supprime également le contenu
   documentaire qui lui est rattaché.
7. **Règle validée GO 25** : si un document est déjà attaché, le nouvel ajout
   est refusé avec un état explicite; le document existant n’est pas remplacé.
   L’utilisateur doit le retirer avant d’en joindre un autre.

## 4. Formats envisagés

Les types ci-dessous reflètent les souhaits exprimés, pas une promesse de
prise en charge. La mention d’une extension dans
[security_files.py](../tools/security_files.py#L15) indique une classification,
pas l’existence d’un extracteur ou d’une capacité visuelle.

| Famille | Usage attendu | Contenu à rendre disponible | Limite connue | Premier incrément / évolution |
|---|---|---|---|---|
| Markdown `.md` | Commenter, résumer, reformuler, expliquer ou analyser | Texte UTF-8 extrait, soumis aux limites appliquées | Le parcours AIWorkflow existant utilise un chemin serveur; il n’est pas un téléversement du chat. | **Premier incrément implémenté** : un document associé à une conversation. |
| Texte `.txt` | Même usage textuel | Texte décodé | Encodage et extraction à définir pour ce format. | **Cible multiformat future**, pas un abandon. |
| PDF | Résumer et questionner le texte extrait | Texte extrait; les scans peuvent nécessiter OCR | L’extraction actuelle dépend de `pypdf` et n’assure pas l’OCR ([extract_text.py](../tools/nodes/extract_text.py#L14)). | **Cible multiformat future**. |
| Bureautique `.docx`, `.xlsx`, `.pptx`, etc. | Lire et expliquer | Texte ou structures extraites | Une extension classée publique n’atteste pas l’existence d’un extracteur. | **Cible multiformat future**. |
| Photos et images | Décrire ou analyser | Pixels, OCR ou représentation visuelle | Ni OCR ni capacité vision du modèle n’est établie par la classification d’extension. | **Cible multiformat future**, capacité à vérifier séparément. |
| SQL, Dockerfiles et scripts | Expliquer le texte seulement | Texte; aucune exécution | AIWorkflow SQL est un autre parcours et peut interroger la base de l’application ([analyse_sql.py](../workflows/analyse_sql.py#L41)). | **Cible multiformat future**; contenu non exécuté. |

## 5. Conservation et suppression — règles validées

| Élément | Règle |
|---|---|
| Fichier original | Temporaire; il n’a pas à être conservé après extraction. |
| Texte extrait et métadonnées | Conservés avec le propriétaire et la conversation pour permettre des questions après rechargement. |
| Questions et réponses | Restent dans l’historique normal; elles peuvent contenir des informations dérivées du document. |
| Retrait du document | Supprime le contenu documentaire conservé et empêche sa réinjection. L’interface indique que le document est indisponible. Aucun effacement de toute information dérivée n’est promis. |
| Suppression de la conversation | Supprime aussi le contenu documentaire rattaché à cette conversation. |
| Bibliothèque personnelle multi-conversations | Hors périmètre du premier incrément; non validée. |

La conservation du texte ne signifie pas qu’il est recopié dans chaque bulle ni
qu’il est systématiquement transmis intégralement au modèle. La stratégie de
contexte reste technique; aucune analyse exhaustive n’est promise si seul un
extrait est utilisé.

## 6. Permissions — règles validées

« Public » est une classe de la politique de fichiers, jamais un partage entre
comptes. La propriété de la conversation reste le contrôle d’accès principal.

| Action | Propriétaire `user` | Autre compte | `admin` propriétaire |
|---|---|---|---|
| Ajouter | Autorisé pour les classes permises et formats pris en charge. | Refusé. | Même règle; aucun accès aux conversations d’autrui. |
| Lire / extraire | Public autorisé; sensible refusé. | Refusé, comme une ressource absente. | Public et sensible autorisés dans sa propre conversation. |
| Transmettre au modèle | Public autorisé à la demande; sensible refusé. | Refusé. | Public et sensible autorisés à la demande, dans sa propre conversation seulement. |
| Supprimer | Peut retirer son document. | Refusé. | Peut retirer un document de sa propre conversation seulement. |
| Critique | Refusé. | Refusé. | Refusé. |

La classification public/sensible/critique est une protection supplémentaire;
elle ne prouve ni le type réel ni la capacité d’extraction. L’isolation entre
comptes et conversations doit être contrôlée côté serveur.

## 7. Limites fonctionnelles et erreurs

Le format initial est `.md`. Un fichier vide, illisible, malformé, non UTF-8,
mal classé ou dépassant une limite technique échoue avec un état visible; aucun
dépassement n’est tronqué silencieusement. Une erreur d’autorisation,
d’extraction ou de modèle n’est pas présentée comme une réussite. Les limites
retenues figurent à la section 11.

Les demandes d’explication de SQL, de Dockerfiles ou de scripts ne les
exécutent jamais. Un contenu partiellement transmis doit être annoncé comme
partiel.

## 8. Sécurité fonctionnelle — règles validées

- Le chat reçoit un fichier choisi par l’utilisateur, pas un chemin arbitraire
  du système de fichiers serveur.
- Le serveur vérifie l’authentification, la propriété de la conversation et la
  classification pour chaque lecture, transmission et suppression.
- Le rôle `admin` ne donne aucun accès automatique aux documents d’autres
  comptes.
- Le contenu est une donnée non fiable; il ne peut modifier les règles ni
  autoriser l’appel d’outils.
- Aucun contenu de fichier n’est exécuté ni servi comme ressource statique.
- AIWorkflow, le RAG général et les rôles métier restent séparés.

## 9. Premier incrément — implémenté et vérifié

Un document Markdown `.md` par conversation; original temporaire; texte extrait
et métadonnées conservés avec le propriétaire et la conversation; questions et
réponses enregistrées dans l’historique; questions de suivi sans nouveau
téléversement, y compris après rechargement; retrait et suppression selon la
section 5. Les autres formats sont des évolutions futures, pas des abandons.
AIWorkflow et les profils métier ne changent pas.

**Ajout lorsqu’un document est déjà attaché — règle validée et implémentée** :
le serveur refuse le nouvel ajout et conserve le document existant. L’interface
indique qu’il faut retirer ce document avant d’en joindre un autre; aucun
remplacement implicite n’a lieu.

## 10. Réalisation technique implémentée (GO 25)

- **Stockage** : la migration v11 crée `conversation_documents` avec le texte,
  les métadonnées JSON, le propriétaire et les clés étrangères vers le compte
  et la conversation. L’index unique sur `session_id` impose un document au
  plus par conversation; sa suppression suit la cascade de la session
  ([citadelle_memory.py](../tools/citadelle_memory.py#L455)).
- **Réception et contrôle** : `POST /api/chat/upload` accepte un seul `.md`
  multipart. L’authentification, le CSRF et les limites du corps sont vérifiés
  avant la lecture; la propriété de la conversation est contrôlée avant
  extraction et stockage. Le nom client n’est jamais utilisé comme chemin
  persistant ([login_server.py](../tools/login_server.py)).
- **Extraction temporaire** : le fichier est classifié, décodé en UTF-8 strict
  et soumis aux limites; le répertoire temporaire est nettoyé après succès ou
  erreur ([extract_text.py](../tools/nodes/extract_text.py)).
- **Suivi et contexte** : chaque demande relit le document de la session
  propriétaire. Jusqu’à 6 000 caractères sont transmis en entier; sinon FTS5
  recherche jusqu’à 12 passages dans une connexion SQLite mémoire qui contient
  uniquement le document courant. Le texte transmis est plafonné à 6 000
  caractères; le prompt et l’UI indiquent si l’analyse est partielle. Le modèle
  ne choisit ni n’appelle d’outil.
- **Budget** : pour une conversation avec document, instructions, historique,
  question et document partagent un budget estimé de 8 000 tokens, dont jusqu’à
  1 024 réservés à la réponse. L’historique est réduit pour respecter cette
  estimation. Sans document, le chemin de conversation antérieur est conservé.
- **Retrait et reprise** : `DELETE /api/chat/document/{id}` retire le contenu
  documentaire sans supprimer les messages. L’API de messages retourne les
  métadonnées nécessaires pour retrouver le document après rechargement.
- **Interface** : les contrôles d’ajout, nom, indication d’extraits et retrait
  sont dans [chat.html](../tools/web/chat.html),
  [chat.js](../tools/web/chat.js) et [style.css](../tools/web/style.css). Le
  contenu du fichier n’est pas exposé par une route statique.
- **Périmètre préservé** : AIWorkflow, ses chemins autorisés et la whitelist
  des modèles ne changent pas.

## 11. Limites chiffrées retenues et approximations

| Limite appliquée | Valeur | Interprétation |
|---|---:|---|
| Taille du fichier | 256 KiB | Limite sur les octets du fichier; le corps multipart autorise 16 KiB supplémentaires pour ses en-têtes et délimiteurs. |
| Encodage et texte conservé | UTF-8 strict; 200 000 caractères | Limite sur les caractères décodés, distincte de la taille reçue en octets. |
| Document transmis au modèle | 1 500 tokens estimés, environ 6 000 caractères | Document court entier; pour un document plus long, jusqu’à 12 passages FTS5 de 500 caractères maximum, limités à 6 000 caractères au total. |
| Budget d’entrée et de réponse | 8 000 tokens estimés au total, dont jusqu’à 1 024 tokens de réponse | Environ 6 976 tokens restants pour instructions, historique, question et document, évalués avec l’approximation d’environ 4 caractères par token. |
| Stockage | Un document actif par conversation; 256 KiB maximum de texte UTF-8 | Aucun quota cumulé par compte n’est défini; le volume total dépend du nombre de conversations. |

Le calcul caractères/tokens est une approximation, pas une mesure du tokenizer.
Le lanceur ne fixe pas `--ctx-size`; le contexte effectif dépend du runtime,
du modèle, de la mémoire et des slots ([lancer.py](../tools/lancer.py#L32),
[MODELES-TESTES.md](./MODELES-TESTES.md#L241)). Aucun benchmark ni lancement de
modèle n’a été effectué dans le GO 25.

Au dépassement, l’upload ou la requête est refusé avec un état explicite; le
contenu n’est pas tronqué silencieusement. Lorsqu’un retrieval partiel est
utilisé, le libellé UI et le prompt signalent la couverture partielle. Aucun
résultat n’est présenté comme analyse exhaustive.

## 12. Critères d’acceptation et vérification

Les 14 tests ajoutés dans
[test_chat_documents.py](../tests/test_chat_documents.py) couvrent migration,
extraction et classification, upload, suivi après rechargement, isolation des
comptes y compris admin, limites, deuxième ajout refusé, retrait avec historique
conservé, suppression en cascade, nettoyage temporaire et contrôles UI. La
suite complète a passé à `327 passed`.

Le chat sans document et les routes AIWorkflow sont également vérifiés par la
suite existante; aucun code AIWorkflow n’a été modifié.

## 13. Limites observées et évolutions hors incrément

- Les budgets en tokens restent estimatifs et n’ont pas été validés par un
  tokenizer ni par un benchmark live.
- Aucun quota de stockage global par compte n’est appliqué.
- Les fichiers `.txt`, PDF, bureautiques, images, SQL et Docker restent des
  évolutions futures, pas des abandons.
- Le second ajout est refusé tant que le document courant n’est pas retiré;
  aucun remplacement automatique n’est pris en charge.

Les choix techniques acceptés et l’implémentation de ce premier incrément sont
consignés dans la [décision #129](../../.memory/decisions.md#L2941).

## 14. Proposition de contrat multiformat — non implémentée

**Statut** : proposition technique préparée pour revue au GO
16-MULTIFORMAT-CADRAGE-B; aucune dépendance, limite ou architecture de parsing
n’est approuvée. Les sections 1–13 restent le contrat livré du `.md`.
Vérifications ciblées du code au HEAD
`b3da82ea5e32734953efc11c998a53ad91070f85`; l’upload chat accepte toujours
`.md` seulement.

Le périmètre fonctionnel approuvé par la
[décision #135](../../.memory/decisions.md#2026-11-25-arbitrage-fonctionnel-du-premier-palier-multiformat)
est `.md`, `.txt`, `.csv`, `.json`, `.sql`, pour une réalisation future. La
version cible reste à déterminer; la proposition V4 n’est pas acquise.

| Format | Lecture proposée | Validation et résultat |
|---|---|---|
| `.md` | Conserver le lecteur UTF-8 et le texte du contrat courant. | Garder les limites, la classification, l’attachement et la récupération actuels. |
| `.txt` | Lire du texte UTF-8 brut, sans interprétation. | Nouveau chemin d’upload chat; le helper générique existant ne vaut pas intégration. |
| `.csv` | Lire enregistrements et cellules avec leurs en-têtes et positions. Aucune conversion numérique ni formule exécutée. | Parseur CSV strict; séparateur, règle d’en-tête et limites restent à valider. Les valeurs sont conservées comme chaînes. |
| `.json` | Lire objets, listes, clés, valeurs et racine structurée; localiser chaque fragment par JSON Pointer. | JSON strict, pas de `eval`; doublons/constantes non standard et bornes structurelles à arbitrer. |
| `.sql` | Lire le fichier comme texte source seulement. | Aucune analyse contre une base, exécution de requête ou ouverture de DB. `.sql` n’est pas dans `PUBLIC_EXTENSIONS` et est classé `SENSITIVE` par défaut; l’accès d’un compte `user` reste à trancher. |

### Codes HTTP : comportement actuel et proposition

Pour l’upload `.md` actuel, le handler renvoie 415 pour un `Content-Type` non
multipart ou un suffixe autre que `.md`; 400 pour un multipart mal formé ou un
Markdown invalide, y compris un encodage UTF-8 invalide; et 413 si le corps,
le fichier ou le texte extrait dépasse sa limite. Les autres contrôles actuels
renvoient notamment 401 (non authentifié), 403 (CSRF/droit), 404 (session
absente ou non possédée), 409 (document déjà présent) et 500 (erreur interne
ou de stockage).

Pour les formats futurs, 400 pour une syntaxe CSV/JSON invalide et 413 pour
leurs limites sont des codes proposés, non des comportements déjà livrés.
Réutiliser 415 pour les suffixes hors de la future allowlist est également
proposé, bien que le handler actuel renvoie déjà 415 pour tout suffixe autre
que `.md`. Un timeout de worker pourrait renvoyer 503; ce code n’est pas
actuellement utilisé par l’upload et dépend du choix d’architecture.

Les autres formats restent hors de ce premier palier : PDF, bureautique,
fichiers de code/configuration (dont `.py`), `Dockerfile`, images et OCR.
Une extension ou un MIME déclaré ne prouve pas qu’un contenu est sûr; le serveur
choisit le traitement selon une allowlist fermée et valide le contenu par le
lecteur concerné. Les archives compressées sont refusées, pas extraites.

### Contrat de validation proposé

- UTF-8 strict; pas de repli d’encodage. Pour les nouveaux formats, accepter
  un seul BOM UTF-8 initial et le retirer avant parsing; préserver le comportement
  `.md` existant jusqu’à décision explicite sur une éventuelle normalisation.
- Fins de ligne normalisées vers LF pour le texte conservé; le lecteur CSV
  garde une entrée compatible avec les cellules multilignes avant normalisation.
- NUL et contrôles non autorisés refusés. Les lignes vides, contrôles et erreurs
  de structure produisent un refus visible, jamais un succès partiel silencieux.
- Pour CSV, aucun heuristique silencieux de headerless : la proposition traite
  le premier enregistrement logique non vide comme en-tête. Les doublons sont
  conservés par ordinal; lignes incomplètes ou cellules supplémentaires sont
  identifiées, pas supprimées.
- Pour JSON, la limite de profondeur/nœuds doit être contrôlée avant la
  construction complète de l’arbre. Une limite seulement après `json.loads`
  ne protège pas les ressources déjà consommées.
- Le `.sql` reste du texte, même si sa syntaxe ressemble à une commande; les
  cellules CSV ressemblant à des formules restent des chaînes.

### Stockage, contexte et restitution proposés

Maintenir un document par conversation, l’original temporaire et le nettoyage
sur tous les chemins. Garder la chaîne normalisée dans `content TEXT` et les
métadonnées de format/version/compteurs dans le JSON existant; aucune migration
n’est proposée à ce stade. Le contenu actif reste filtré par propriétaire.
Le retrait supprime la ligne active, pas les messages déjà écrits. L’audit
conserve des métadonnées avec `content_redacted`; aucune suppression totale des
copies de sauvegarde ou pages SQLite n’est promise.

L’extraction proposée est atomique : une erreur ou un dépassement refuse
l’attachement au lieu de persister un fragment tronqué. Ensuite, le retrieval
peut rester partiel comme pour le `.md`; le serveur doit joindre à chaque
réponse un état de couverture et les locators sélectionnés (lignes CSV,
JSON Pointers ou segments textuels), dans le flux et les métadonnées existantes
des messages. La table `messages` a déjà un champ `metadata`; le chemin streaming
devra transmettre cette metadata à `add_message`, qui l’accepte déjà, et l’API
d’historique exposer explicitement le namespace `document_context` sans changer
le contenu/role des anciens messages. L’interface affiche ce statut par
`textContent` et ne dépend pas uniquement de la réponse du modèle. Le budget
actuel de contexte reste une approximation et n’est pas une garantie d’analyse
exhaustive.

### Questions bloquantes avant validation du contrat B

- `.sql` demeure sensible/admin-only selon la classification actuelle. Confirmer
  si ce niveau s’applique aussi au palier futur pour les comptes `user`; aucune
  extension à PUBLIC n’est déduite de l’allowlist.
- Confirmer le contrat CSV : séparateur détecté sans ambiguïté et première
  ligne logique traitée comme header, ou proposer un mode explicite headerless.
- Accepter un worker enfant pour imposer un timeout structuré, avec validation
  PyInstaller Windows/Linux/macOS; ou confirmer qu’une limite de durée/RSS dure
  n’est pas promise. Le worker n’est pas un sandbox.
- Le cadrage propose un timeout candidat de 5 s; il n’a pas été mesuré. Aucune
  limite RSS portable n’est disponible dans les mécanismes observés. Décider si
  une mesure ou protection OS-spécifique est un prérequis.

Les seuils candidats, la comparaison in-process/worker, les contrats d’erreur,
le plan de code/tests et les bloqueurs sont détaillés dans le
[BACKLOG 16-MULTIFORMAT](./BACKLOG.md#16-multiformat). Ce contrat reste une
proposition à valider; il ne démarre pas l’étape C, ne change pas le bouton et
ne rend aucun des quatre nouveaux formats disponible.
