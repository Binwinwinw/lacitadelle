# Plan de nettoyage de main/

## Contexte

Le dossier main/ (fork de mozilla-ai/llamafile) est présent dans le
worktree mais n'est JAMAIS utilisé par le code. Le bootstrap télécharge
les binaires directement depuis les releases GitHub. Le décideur a
décidé de le supprimer complètement, y compris ses mentions dans la
documentation.

## Inventaire (issu du sous-agent Main Inventory)

Inventaire validé par le décideur : **42 occurrences dans 12 fichiers**,
hors `.git/`, `vendor/`, `main/`, `dist/` et `node_modules/`. Les numéros
ci-dessous sont ceux du relevé validé.

### AGENTS.md (3)

- L16 : `main/` est en lecture seule.
- L41 : `main/` figure parmi les modifications inattendues à signaler.
- L64 : le runtime llamafile se trouve dans `main/`.

### .memory/decisions.md (8)

- L45 : `main/` est ignoré et retéléchargé par le bootstrap.
- L47 : la liste des exclusions `.gitignore` inclut `main/`.
- L51 : aucun fichier de `main/` ne sera versionné.
- L61 : `main/` est exclu du premier commit.
- L62 : `main/` ne doit pas apparaître sur GitHub.
- L68 : l'option Y décrit la compilation depuis `main/`.
- L70 : `main/` reste une référence documentaire, jamais compilée en v1.
- L72 : le binaire téléchargé sera ignoré comme `main/`.

### README (1)

- L41 : `main/` est décrit comme le dépôt upstream, en lecture seule et non versionné.

### dev/docs/GIT_STRATEGY.md (10)

- L5 : `main/` est présenté comme un fork de mozilla-ai/llamafile.
- L9 : titre « Traitement de `main/` ».
- L11 : `main/` est ignoré et retéléchargé.
- L13 : justification, dépendance externe en lecture seule.
- L16 : règle non négociable concernant `main/`.
- L36 : `main/` figure dans la liste des dépendances externes.
- L52 : vérifier qu'aucun fichier de `main/` n'apparaît dans git status.
- L54 : vérifier qu'aucun fichier de `main/` n'est stagé.
- L64 : le bootstrap doit retélécharger `main/`.
- L69 : `main/` est exclu du premier commit.

### dev/docs/OBJECTIF.md (1)

- L22 : `main/` reste en lecture seule et sert d'outil de fabrication.

### .gitignore (2)

- L20 : commentaire indiquant que `main/` est un fork externe en lecture seule.
- L21 : règle d'exclusion `main/`.

### Code Python (0)

Aucune occurrence retenue dans le code Python hors répertoires exclus.

### Autres fichiers (17)

- `.github/agents/cleanup-plan-writer.agent.md` : L3 décrit le plan de
   nettoyage de `main/`; L15 interdit de supprimer ou modifier ses fichiers.
- `.github/agents/main-inventory.agent.md` : L3 décrit l'inventaire; L8
   demande de rechercher `main/`; L9 cite les répertoires exclus.
- `.github/copilot-instructions.md` : L3 indique que `main/` est en lecture
   seule.
- `dev/docs/BASE_LLAMAFILE.md` : L19 et L21 décrivent la compilation/source
   depuis `main/`; L26 et L28 décrivent l'option hybride et la référence
   documentaire; L38 précise que `main/` reste en lecture seule.
- `dev/docs/JOURNALDEBORD.md` : L2 note que `main/` est ignoré; L3 qu'il est
   exclu; L4 qu'aucun chemin `main/` n'est sur la branche distante; L5 évoque
   l'option de compilation depuis `main/`.
- `dev/tools/VENDOR_STRATEGY.md` : L5 compare `main/` aux dépendances
   externes; L42 précise qu'il n'y a pas de compilation depuis `main/`.

## Plan d'action

Pour chaque fichier identifié dans l'inventaire :

- `AGENTS.md` : supprimer la règle 1 et retirer ses références dans les
   consignes de signalement et l'emplacement du runtime; remplacer la règle
   seulement si nécessaire.
- `.memory/decisions.md` : ne pas réécrire les entrées historiques; ajouter
   une nouvelle entrée datée qui documente leur obsolescence (Solution A).
- `README` : retirer la référence au dossier `main/`; conserver la mention
   explicite « Inspiré de mozilla-ai/llamafile » comme source d'inspiration.
- `dev/docs/GIT_STRATEGY.md` : retirer les mentions opérationnelles de
   `main/`, en conservant les règles de protection Git encore pertinentes.
- `dev/docs/OBJECTIF.md` : retirer la mention de `main/` et préserver le
   cadrage du pipeline de fabrication.
- `.gitignore` : retirer la ligne `main/` après suppression du dossier, puis
   vérifier que son contenu n'apparaît pas dans le status.
- Code Python : aucune action (zéro occurrence recensée).
- `.github/agents/cleanup-plan-writer.agent.md` : retirer la référence
   spécifique à `main/` ou retirer cet agent ponctuel après exécution du plan.
- `.github/agents/main-inventory.agent.md` : retirer la cible et les
   exclusions liées à `main/` ou retirer cet agent ponctuel après validation
   de l'inventaire et exécution du plan.
- `.github/copilot-instructions.md` : retirer la mention devenue obsolète;
   toute modification exigera l'instruction explicite du décideur prévue par
   la règle 6 d'`AGENTS.md`.
- `dev/docs/BASE_LLAMAFILE.md` : retirer ou reformuler les options de
   compilation/hybride fondées sur `main/`; conserver l'option X et la source
   des binaires depuis les releases upstream.
- `dev/docs/JOURNALDEBORD.md` : traiter les quatre mentions recensées sans
   modifier les entrées sans rapport; consigner l'obsolescence dans une
   nouvelle entrée.
- `dev/tools/VENDOR_STRATEGY.md` : reformuler les deux mentions de `main/`
   pour rester cohérent avec les assets téléchargés depuis les releases.

## Décisions actées

1. Le dossier main/ est supprimé du worktree.
2. La ligne main/ est supprimée de .gitignore.
3. La règle 1 d'AGENTS.md ("main/ est en LECTURE SEULE") est supprimée
    et remplacée par une règle plus utile si nécessaire.
4. Les mentions dans README, GIT_STRATEGY.md, OBJECTIF.md sont supprimées.
5. Une nouvelle entrée est ajoutée dans decisions.md pour documenter
    l'obsolescence des décisions antérieures qui mentionnent main/
    (Solution A : on ne réécrit pas les entrées historiques).
6. Le dépôt upstream mozilla-ai/llamafile sera mentionné explicitement
    dans le README comme source d'inspiration ("Inspiré de ...").

## Exécution

Ce plan sera exécuté dans une tâche ultérieure, après validation de
l'inventaire par le décideur. Chaque suppression sera vérifiée par grep
post-exécution.
