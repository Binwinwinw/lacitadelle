# Choix de la base llamafile

## Contexte

Le pipeline v1 doit produire un fichier `.llamafile` unique à partir d'un GGUF
et d'un binaire llamafile de base. Ce document cadre les options avant décision.

## Question

Où récupère-t-on le binaire llamafile qui sert de base à l'assemblage ?

## Option X — Binaire pré-compilé depuis les releases upstream

Source : releases GitHub de mozilla-ai/llamafile (ex. v0.10.0).
Avantages : simple, pas de compilation, pas de cosmocc à installer, versions stables.
Inconvénients : dépendance aux releases upstream (versions figées, pas de patches possibles
sans recompiler), version figée à la date de téléchargement.

## Option Y — Compiler llamafile depuis les sources (`main/`)

Source : `main/` (fork de llamafile upstream), compilé via cosmocc/make.
Avantages : flexibilité totale, patches possibles, maîtrise du binaire.
Inconvénients : nécessite chaîne de build complète (make, cosmocc), plus complexe,
sort du périmètre Python-first.

## Option Z — Hybride (binaire pré-compilé pour v1, `main/` pour référence)

Source : binaire pré-compilé pour le build v1, `main/` conservé comme référence documentaire.
Avantages : simplicité de X pour la v1, documentation de Y disponible sans l'exécuter.
Inconvénients : deux sources de vérité à maintenir.

## Décision du décideur

**Option X retenue** (binaire pré-compilé depuis les releases upstream) le 2026-10-17.

Justification : simplicité pour la v1, pas de chaîne de compilation à maintenir,
périmètre Python-first respecté. L'option Y (compilation) reste disponible pour
une version future si des patches deviennent nécessaires. `main/` reste en
référence documentaire (lecture seule) sans être compilé.

## Version de llamafile retenue

**Version retenue** : `0.10.6` (dernière release stable, 15 septembre 2026). Décision du décideur le 2026-10-17. Aucune raison factuelle de préférer une version antérieure.

**Asset runtime retenu pour la v1** : `llamafile-0.10.6-thin` (base nue, utilisée en CPU-only pour la v1, sans bibliothèques GPU préassemblées). Justification : robustesse maximale (pas de dépendance aux pilotes GPU de la machine cible), fichier plus petit (~44 Mo), promesse « fichier unique qui marche partout » mieux tenue. La performance sera moindre que sur GPU, mais acceptable pour un modèle 1B-3B en chat (5-15 tokens/s selon machine).

**Asset obligatoire** : `zipalign-0.10.6` (outil d'intégration du GGUF dans le `.llamafile` final).

**Checksums SHA-256 (source : API GitHub, 2026-10-17)** :

- `llamafile-0.10.6-thin` : `756bf97febae557084e8ced9bde7a1cb0c7f6ce778530d582afa219406237a50`
- `llamafile-0.10.6` (complet, pour usage futur) : `d579f61dcd3a306f518e6d90e599d77793ed5f09543023d09c96ad35fcfa63f0`
- `zipalign-0.10.6` : `7eac59c658226027b365d92131babf06341f746fb20c0db33115bbdf5c5c6c4b`

**URLs (source : release GitHub 0.10.6)** :

- `llamafile-0.10.6-thin` : `https://github.com/mozilla-ai/llamafile/releases/download/0.10.6/llamafile-0.10.6-thin`
- `llamafile-0.10.6` : `https://github.com/mozilla-ai/llamafile/releases/download/0.10.6/llamafile-0.10.6`
- `zipalign-0.10.6` : `https://github.com/mozilla-ai/llamafile/releases/download/0.10.6/zipalign-0.10.6`

**Plateformes supportées (documentation officielle)** : Linux, macOS, Windows 10+ AMD64, FreeBSD, NetBSD, OpenBSD. Limite Windows : exécutables sous 4 Go.

## Objectif futur (v2, hors périmètre v1) : détection GPU et bascule automatique

La v1 est CPU-only (asset thin). Une amélioration future consistera à détecter la présence d'un GPU compatible au lancement et à basculer sur un runtime accéléré si disponible. Deux pistes à explorer en v2 :

- Piste A : livrer deux `.llamafile` séparés (CPU et GPU), l'utilisateur télécharge celui qui correspond à sa machine.
- Piste B : fichier thin + téléchargement à la demande des bibliothèques GPU au premier lancement (stratégie Ollama).

Cette fonctionnalité est documentée ici pour mémoire, mais **n'est pas dans le périmètre v1**.

## Conséquences sur le pipeline Python

Le pipeline Python devra :

1. Télécharger le binaire llamafile de la version retenue.
2. Vérifier son checksum SHA-256.
3. L'utiliser comme base pour assembler un `.llamafile` avec un GGUF.
   Le binaire téléchargé ne sera PAS versionné dans Git (voir dev/tools/VENDOR_STRATEGY.md).
