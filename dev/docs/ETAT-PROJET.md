# État du projet La Citadelle

**Mis à jour** : 2026-11-24

**Commit de référence audité** : `fd34e82` (HEAD observé au préflight GO
16-PHASE-CLOSE; ce n'est pas le commit de livraison de ce GO).

Ce point de reprise inclut la clôture du sous-périmètre AIWorkflow et premier
incrément fichiers chat de la Phase 16. Les limites qui n’ont pas été mesurées
en live sont signalées; aucun chemin absolu de DB ou de modèle local n’est
publié ici.

## Résumé

La Citadelle est une application de chat IA locale destinée à un public
non-technique. L'archive source fournit les wrappers natifs; le bootstrap
télécharge le runtime llamafile-thin et le modèle GGUF séparément. Le webchat
communique avec le proxy Python local, qui relaie les requêtes vers llamafile
et conserve les données applicatives dans SQLite. Voir [README.md](../../README.md),
[OBJECTIF.md](./OBJECTIF.md) et [ARCHITECTURE.md](./ARCHITECTURE.md).

## Modèles

| Catégorie | État au 2026-11-23 | Source / limite |
|---|---|---|
| Runtime distribué | `llamafile-thin`, téléchargé séparément du GGUF. | [llamafile_config.json](../tools/llamafile_config.json) le déclare requis; le téléchargement réel n'a pas été testé dans ce GO. |
| Modèle distribué | Qwen3-4B Q4_K_M est l'asset GGUF requis au bootstrap; il n'est pas incorporé au binaire llamafile. | [llamafile_config.json](../tools/llamafile_config.json) et [BOOTSTRAP_CONTRACT.md](../tools/BOOTSTRAP_CONTRACT.md). |
| Modèles locaux autorisés | La whitelist SQLite lue en mode `ro` contient Ornith-1.5-9B, Qwen3.5-9B et le Qwen3-4B intégré. Les trois fichiers existaient lors du relevé. | Mesure de ce GO; les chemins machine-locaux ne sont pas reproduits. |
| Modèle actif enregistré | `current_model_path` pointe vers Ornith-1.5-9B. `previous_model_path` pointe vers le Qwen3-4B intégré. | Réglages SQLite lus en mode `ro` pendant ce GO. Cela ne prouve pas quel GGUF est actuellement chargé en mémoire. |
| Défaut / recommandation | Le lanceur choisit Ornith si son fichier est présent et explicitement whitelisté; sinon il retourne au Qwen3-4B intégré. L'API et l'UI exposent cette recommandation sans forcer le chargement. | [lancer.py](../tools/lancer.py#L67), [model_health.py](../tools/model_health.py#L19), [login_server.py](../tools/login_server.py#L726). |
| Modèle effectivement chargé | Non vérifié dans le GO 18. Le GO 17 avait observé Ornith sur `/v1/models` le 2026-11-23; cette observation antérieure ne remplace pas un contrôle live dans le présent GO. | Historique du GO 17; aucun serveur n'a été interrogé ou lancé dans ce GO. |

La batterie stricte rapportée le 2026-11-23 donne Ornith 4/7, Qwen3.5 5/7,
Granite 3/7 et Qwen3-4B 3/7 dans la reclassification stricte. Une entrée
antérieure du même journal donne Qwen3-4B à 4/7; les sorties brutes ne sont
pas archivées dans le dépôt. Ces scores sont historiques, non rejoués dans ce
GO, et ne sont pas comparables aux notes sur cinq critères de
[MODELES-TESTES.md](./MODELES-TESTES.md). Sources : [JOURNALDEBORD.md](./JOURNALDEBORD.md#L201),
[JOURNALDEBORD.md](./JOURNALDEBORD.md#L202) et [decisions.md](../../.memory/decisions.md#L2882).

## Tests et décisions

- **Tests mesurés dans ce GO** : `.\.venv\Scripts\python.exe -m pytest -q`
  — `327 passed in 81.38s`, le 2026-11-24.
- **Décisions datées** : 130 entrées, comptées dans
  [.memory/decisions.md](../../.memory/decisions.md) le 2026-11-24. Le comptage
  est calculé sur les titres `## [AAAA-MM-JJ]`; la décision #130 consigne la
  clôture du périmètre AIWorkflow + fichiers chat.
- **Décision modèle la plus récente** : Ornith recommandé s'il est local et
  whitelisté; Qwen3-4B reste le modèle intégré de fallback; Qwen3.5 reste local;
  Granite est retiré de la whitelist ([decisions.md](../../.memory/decisions.md#L2882)).

## Services et parcours

| Composant | Configuration observée dans le code | État runtime dans ce GO |
|---|---|---|
| llamafile | API locale sur `127.0.0.1:8080`. | Non vérifié. |
| Proxy web Python | `HTTPServer` sur `127.0.0.1:8081`; authentification, webchat, API et relais vers llamafile. | Non vérifié. |
| Données | Le schéma SQLite applicatif comprend comptes, sessions, messages, réglages et documents de conversation (migration v11). | Les GO 25 et 16-PHASE-CLOSE n’ont pas ouvert la DB utilisateur. |

Références : [lancer.py](../tools/lancer.py#L42), [login_server.py](../tools/login_server.py#L86),
[ARCHITECTURE.md](./ARCHITECTURE.md).

## Fonctions livrées, propositions et limites

- AIWorkflow est présent dans le code sous forme de workflows Python
  `analyse_md`, `analyse_pdf` et `analyse_sql`. Les chemins sont limités à des
  répertoires du projet et le workflow SQL n'accepte que `SELECT`
  ([workflow_runner.py](../tools/workflow_runner.py#L23),
  [ARCHITECTURE.md](./ARCHITECTURE.md#L269)).
- Le statut de périmètre reste contradictoire : [OBJECTIF.md](./OBJECTIF.md#L60)
  place AIWorkflow en proposition V4 conditionnelle au POC Graphify, tandis que
  le [BACKLOG.md](./BACKLOG.md#L691) indique que le POC Graphify est KO et
  l'implémentation Python AIWorkflow livrée. Graphify n'est pas intégré; ne pas
  présenter la proposition Graphify comme une fonctionnalité disponible.
- Le premier incrément de fichiers du chat accepte un `.md` attaché à une
  conversation, conserve le texte extrait par propriétaire et permet le suivi
  après rechargement. Les limites de contexte sont estimées; aucun benchmark
  ni test live de modèle n’a été exécuté dans le GO 25
  ([SPEC-FICHIERS-CHAT.md](./SPEC-FICHIERS-CHAT.md),
  [décision #129](../../.memory/decisions.md#L2941)). Le périmètre AIWorkflow
  + fichiers chat est clôturé par la décision #130; les tâches modèles/UX
  restantes ne sont pas déclarées terminées.
- Le chat général n'a pas de base RAG personnalisée ni d'accès web déclaré
  livré; un document attaché à une conversation ne constitue pas une
  bibliothèque générale. L'accès web figure encore comme proposition dans
  [TODO.md](../../TODO.md#L96) et [TODO.md](../../TODO.md#L102). Le retrieval
  FTS5 d'AIWorkflow est limité à ses workflows documentaires et ne constitue
  pas une base de connaissances générale du chat.
- Le serveur Python est mono-thread; la charge concurrente n'est pas validée.
  La mise en production derrière Caddy reste une préparation, pas un
  déploiement constaté ([README.md](../../README.md),
  [ARCHITECTURE-PROD.md](./ARCHITECTURE-PROD.md)).

## Écarts documentaires restant à traiter

- [CONTRIBUTING.md](../../CONTRIBUTING.md) et
  [CONTRIBUTING.fr.md](../../CONTRIBUTING.fr.md) consignent encore le résultat
  historique de 313 tests (GO 18); le GO 25 en mesure 327.
- [MODELES-TESTES.md](./MODELES-TESTES.md) est daté du 2026-11-19, décrit une
  ancienne batterie à cinq critères et conserve Qwen3-4B comme défaut.
- [JOURNALDESMODIFS.md](./JOURNALDESMODIFS.md) conserve des entrées historiques
  où le hash de livraison se résout par `git log`; les entrées de bilan citent
  le commit de référence observé au préflight.
- [TODO.md](../../TODO.md#L84) décrit encore une sélection automatique matérielle
  Qwen3.5/Qwen3-4B; [TODO.md](../../TODO.md#L92) et le [BACKLOG.md](./BACKLOG.md#L732)
  conservent une migration de whitelist dont les cibles ne correspondent pas
  à l'état SQLite relevé dans ce GO.
- La frontière produit entre AIWorkflow implémenté et proposition V4 dans
  [OBJECTIF.md](./OBJECTIF.md#L60) reste à clarifier par décision séparée.

## Prochaines suites possibles

1. Valider manuellement dans un navigateur et avec un modèle local le parcours
   fichiers chat; aucun navigateur ni modèle n’a été lancé dans ces GO.
2. Planifier le nettoyage des dettes Ruff/tokenizer/logs.
3. Étudier les extensions multiformat après validation du test live.

## Références de reprise

Suivre l'ordre de lecture défini dans [AGENTS.md](../../AGENTS.md#L47), puis
croiser le périmètre dans [OBJECTIF.md](./OBJECTIF.md), l'implémentation dans
[ARCHITECTURE.md](./ARCHITECTURE.md), les décisions dans
[.memory/decisions.md](../../.memory/decisions.md), les tâches dans
[TODO.md](../../TODO.md) et les derniers événements dans
[JOURNALDEBORD.md](./JOURNALDEBORD.md).
