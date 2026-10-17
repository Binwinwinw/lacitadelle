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
TODO — à préciser après vérification factuelle de la dernière release stable
(voir Tâche 2). Version, URL de l'asset, checksum SHA-256 à figer.

## Conséquences sur le pipeline Python
Le pipeline Python devra :
1. Télécharger le binaire llamafile de la version retenue.
2. Vérifier son checksum SHA-256.
3. L'utiliser comme base pour assembler un `.llamafile` avec un GGUF.
Le binaire téléchargé ne sera PAS versionné dans Git (voir dev/tools/VENDOR_STRATEGY.md).
