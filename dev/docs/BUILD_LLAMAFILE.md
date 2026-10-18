# Fabrication du .llamafile

## Contexte

La v1 de La Citadelle doit produire un fichier `.llamafile` unique
contenant :

- le runtime `llamafile-0.10.6-thin` (déjà téléchargé par le bootstrap),
- le modèle GGUF Qwen3-1.7B Q4_K_M (source exacte proposée ci-dessous,
  confirmation en attente),
- des arguments minimaux pour la v1 (valeurs à confirmer avant
  implémentation),
- aucun prompt système pour la v1.

L'assemblage se fait avec `zipalign-0.10.6` (déjà téléchargé par le
bootstrap). Voir `dev/tools/BOOTSTRAP_CONTRACT.md` pour les détails
du bootstrap.

## Décisions à prendre

### Décision 1 — Quel modèle GGUF pour la v1 ?

Contraintes :

- Taille : le GGUF Qwen3-1.7B Q4_K_M sélectionné mesure 1 282 439 456
  octets selon les métadonnées HuggingFace.
- Licence permissive (Apache 2.0, MIT, ou équivalent, usage commercial OK).
- Bon en français (public cible francophone).
- Disponible sur HuggingFace avec des GGUF prêts à l'emploi.

Candidats :

- **Qwen3-1.7B** : Apache 2.0, multilingue, bon en français; fichier
  Q4_K_M de 1 282 439 456 octets (environ 1,28 Go décimaux).
- **Phi-3-mini** : MIT, 3.8B, excellent en raisonnement, ~2 Go Q4_K_M.
- **SmolLM2-1.7B** : Apache 2.0, HuggingFace, bon compromis taille/qualité.
- **TinyLlama-1.1B** : Apache 2.0, très petit, qualité limitée.
- **Gemma-2-2B** : licence restrictive (Gemma), usage commercial à vérifier.

**Décision actée** : Qwen3-1.7B, quantifié Q4_K_M (Apache 2.0, ~1,1 Go
selon l'estimation initiale, bon en français, disponible sur HuggingFace).
Les métadonnées Hugging Face consultées le 2026-10-17 indiquent une taille
de `1 282 439 456` octets (`~1,28 Go` décimaux, `~1,19 Gio`).

### Décision 2 — Où récupérer le GGUF ?

Options :

- **URL directe** vers un GGUF précis sur HuggingFace (dans
  llamafile_config.json ou un fichier de config dédié). Simple,
  vérifiable par checksum, reproductible.
- **Script qui interroge l'API HuggingFace** pour trouver le bon GGUF.
  Plus flexible (upgrade automatique), mais dépend de l'API.

**Décision actée sur le mécanisme** : URL directe vers un GGUF précis sur
HuggingFace; URL et checksum dans `dev/tools/llamafile_config.json`.

URL fixe immuable :
`https://huggingface.co/smarttasks/Qwen3-1.7B-GGUF/resolve/4b9aca3fb9c8fcace456430347c2fc34752e515f/Qwen3-1.7B-Q4_K_M.gguf`

SHA-256 :
`16da7ba1721b1620fa843e0978badd3d93756274fd209a01874b37e29750e207`.

Vérification technique le 2026-10-17 : le fichier existe sur HuggingFace,
l'URL immuable répond en HEAD 200 sans télécharger le GGUF, et son
identifiant LFS correspond au checksum ci-dessus. Le commit SHA de la branche
`main` a été récupéré pour figer la source et éliminer le risque de mutation
dans le temps entre le build et l'exécution.

### Décision 3 — Comment assembler le .llamafile ?

Méthode unique : `zipalign` avec les 3 fichiers (runtime, GGUF, args).
Le script `build_llamafile.py` (à créer) orchestrera :

1. Vérifier la présence du runtime et de zipalign (via bootstrap).
2. Télécharger le GGUF si absent depuis l'URL source confirmée et vérifier
   son checksum.
3. Créer un fichier `.args` avec les arguments par défaut.
4. Empaqueter le tout avec zipalign.
5. Nommer et placer le `.llamafile` final (à définir).

**Décision actée** : assemblage avec `zipalign` (déjà dans
`dev/tools/vendor/llamafile/`).

Nom et emplacement proposés : `dist/citadelle.llamafile` (à confirmer par
le décideur).

### Décision 4 — Que mettre dans le .args par défaut ?

**Décision actée** : args minimaux pour la v1.
Valeurs proposées (à confirmer avant implémentation) :

- `-m /zip/Qwen3-1.7B-Q4_K_M.gguf` (obligatoire; modèle embarqué).
- `--port 8080`.
- `-c 4096`.
- `--temp 0.7`.
- `-t N` : valeur numérique explicite (N = nombre de threads). Aucun
  mode `auto` n'est documenté dans la doc upstream, et aucun défaut
  intelligent n'a été trouvé ; la valeur N doit donc être validée
  manuellement avant usage. Proposition pour la v1 : `-t 4` (compromis
  raisonnable sur la plupart des machines), à ajuster après test.
- Pas de prompt système pour la v1.

Note : la documentation officielle llamafile exige le préfixe `/zip/`
dans le fichier `.args` pour référencer les fichiers embarqués.

## Contraintes techniques

- Le `.llamafile` final est estimé à environ 1,33 Go décimaux (runtime
  ~44 Mo + GGUF de 1 282 439 456 octets), hors variations d'assemblage.
- Il doit être exécutable sur Windows 10+, macOS, Linux, BSD (voir
  plateformes supportées dans BASE_LLAMAFILE.md).
- Il ne doit PAS dépendre de Python chez l'utilisateur final.

## Non-objectifs (v1)

- Pas de détection GPU (v2).
- Pas de prompt système avancé (v2).
- Pas de configuration interactive (v2).
- Pas de build multi-modèles (une seule version par défaut, v1).

## Étapes une fois les décisions prises

1. Confirmer la source exacte; l'URL et le checksum proposés sont inscrits
   dans `dev/tools/llamafile_config.json` avec `required=false`.
2. Implémenter `dev/tools/build_llamafile.py`.
3. Tester : produire un `.llamafile`, vérifier qu'il se lance et répond
   à une requête simple.
