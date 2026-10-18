# Fabrication du .llamafile

## Contexte

La v1 de La Citadelle doit produire un fichier `.llamafile` unique
contenant :

- le runtime `llamafile-0.10.6-thin` (déjà téléchargé par le bootstrap),
- un modèle GGUF (à choisir),
- des arguments par défaut (à définir),
- éventuellement un prompt système (à définir).

L'assemblage se fait avec `zipalign-0.10.6` (déjà téléchargé par le
bootstrap). Voir `dev/tools/BOOTSTRAP_CONTRACT.md` pour les détails
du bootstrap.

## Décisions à prendre

### Décision 1 — Quel modèle GGUF pour la v1 ?

Contraintes :

- Taille : 1B-3B paramètres, quantifié Q4_K_M ou Q5_K_M (~600-800 Mo).
- Licence permissive (Apache 2.0, MIT, ou équivalent, usage commercial OK).
- Bon en français (public cible francophone).
- Disponible sur HuggingFace avec des GGUF prêts à l'emploi.

Candidats :

- **Qwen3-1.7B** : Apache 2.0, multilingue, bon en français, ~1 Go Q4_K_M.
- **Phi-3-mini** : MIT, 3.8B, excellent en raisonnement, ~2 Go Q4_K_M.
- **SmolLM2-1.7B** : Apache 2.0, HuggingFace, bon compromis taille/qualité.
- **TinyLlama-1.1B** : Apache 2.0, très petit, qualité limitée.
- **Gemma-2-2B** : licence restrictive (Gemma), usage commercial à vérifier.

TODO — décision du décideur :

### Décision 2 — Où récupérer le GGUF ?

Options :

- **URL directe** vers un GGUF précis sur HuggingFace (dans
  llamafile_config.json ou un fichier de config dédié). Simple,
  vérifiable par checksum, reproductible.
- **Script qui interroge l'API HuggingFace** pour trouver le bon GGUF.
  Plus flexible (upgrade automatique), mais dépend de l'API.

TODO — décision du décideur :

### Décision 3 — Comment assembler le .llamafile ?

Méthode unique : `zipalign` avec les 3 fichiers (runtime, GGUF, args).
Le script `build_llamafile.py` (à créer) orchestrera :

1. Vérifier la présence du runtime et de zipalign (via bootstrap).
2. Télécharger le GGUF si absent (mécanisme à définir selon Décision 2).
3. Créer un fichier `.args` avec les arguments par défaut.
4. Empaqueter le tout avec zipalign.
5. Nommer et placer le `.llamafile` final (à définir).

TODO — décision du décideur sur le nom et l'emplacement du fichier final :

### Décision 4 — Que mettre dans le .args par défaut ?

Paramètres à définir :

- `--port` (port HTTP, 8080 par défaut ?).
- `-c` (taille du contexte, 2048 ou 4096 ?).
- `-t` (threads, nombre de cœurs disponibles ?).
- `--temp` (température, 0.7 ?).
- `--prompt` ou fichier `.prompt` (prompt système).
- Autres paramètres (flash-attn, mmap, etc.).

TODO — décision du décideur sur chaque paramètre :

## Contraintes techniques

- Le `.llamafile` final fait ~650-850 Mo (runtime ~44 Mo + GGUF
  ~600-800 Mo).
- Il doit être exécutable sur Windows 10+, macOS, Linux, BSD (voir
  plateformes supportées dans BASE_LLAMAFILE.md).
- Il ne doit PAS dépendre de Python chez l'utilisateur final.

## Non-objectifs (v1)

- Pas de détection GPU (v2).
- Pas de prompt système avancé (v2).
- Pas de configuration interactive (v2).
- Pas de build multi-modèles (une seule version par défaut, v1).

## Étapes une fois les décisions prises

1. Créer `dev/tools/build_llamafile_config.json` (ou ajouter au config
   existant) avec l'URL et le checksum du GGUF choisi.
2. Implémenter `dev/tools/build_llamafile.py`.
3. Tester : produire un `.llamafile`, vérifier qu'il se lance et répond
   à une requête simple.
