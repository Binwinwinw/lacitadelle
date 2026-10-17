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

## TODO — Décision du décideur

## TODO — Version de llamafile retenue

## TODO — Conséquences sur le pipeline Python
