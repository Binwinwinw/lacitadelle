## 1. Artefact principal livré à l'utilisateur final

Un fichier `.llamafile` unique, exécutable, sans installation.
L'utilisateur le télécharge, le rend exécutable si nécessaire, double-clique, ça discute.
Aucune dépendance Python côté utilisateur.

## 2. Public cible

Utilisateur non-technique souhaitant une IA locale « de poche ».
La v1 assume une interface terminal (celle fournie par llamafile).
Une GUI graphique viendra plus tard, pas en v1.

## 3. Contrainte d'exécution

Python requis chez l'utilisateur : NON.
Réseau requis au premier lancement : NON (modèle embarqué dans le fichier).
Systèmes cibles : ceux supportés par llamafile (macOS, Windows, Linux, BSD).

## 4. Rapport à llamafile upstream (mozilla-ai/llamafile)

llamafile est le RUNTIME et le FORMAT de distribution.
`main/` reste en lecture seule, utilisé comme outil de fabrication.
La Citadelle produit des llamafiles personnalisés via un pipeline Python de build.

## 5. Famille de produit visée

Famille 1 (binaire auto-exécutable unique), avec Python en rôle de FABRICATION uniquement.

## 6. Non-objectifs explicites (v1)

- PAS de téléchargement de modèles depuis l'interface (reporté v2).
- PAS de tool calling / agent / action sur l'ordinateur (reporté v3+).
- PAS de GUI graphique (v1 = interface texte de llamafile).
- PAS de Python côté utilisateur.
- PAS de modification du code C++ de llamafile en v1.

## 7. Décisions dérivées

- v1 = « Pocket Chat » : un llamafile avec un modèle 1B-3B embarqué, chat texte fonctionnel.
- Python = script de fabrication (entrée : fichier GGUF + paramètres ; sortie : `.llamafile`).
- Toute envie d'ajouter « IA qui contrôle le PC » est reportée à v3 minimum, sans exception.
