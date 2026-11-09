# Limites des LLM locaux — La Citadelle

**Date** : 2026-11-09

## Contexte

Nexxus utilise Qwen3-4B-Q4_K_M.gguf via llamafile, exécuté localement.
Aucun accès à Internet. Les connaissances du modèle sont figées.

## Limite 1 — Knowledge cutoff

Tous les LLM locaux ont une date de coupure dans leurs données
d'entraînement :
- Qwen3-4B : ~mi-2024
- Llama 3.3 : ~décembre 2023
- Mistral 7B : ~mi-2023

Aucun modèle local actuel n'a de connaissances post-2024.
Ce n'est pas un bug, c'est une limite structurelle.

## Limite 2 — Hallucinations factuelles

Sur des questions factuelles précises (lois, chiffres, noms
d'institutions), le modèle peut inventer des informations
avec beaucoup d'assurance. C'est plus fréquent sur les
petits modèles (1B-4B) que sur les gros (7B+).

Exemples observés (tests manuels 2026-11-09) :
- "Loi sur la liberté de syndicalisme (2023)" : inventée
- "30 jours de congés non payés obligatoires" : faux
- "Loi sur la santé mentale au travail (2026)" : inventée
- "Smic 2 481 €/mois en 2026" : inventé

## Limite 3 — Pas de "patch" possible

Il n'existe pas de "patch" qui mettrait à jour les connaissances
d'un LLM local. Les connaissances sont distribuées dans les
milliards de paramètres du modèle. Pas de fichier de mise à jour
possible.

## Solutions possibles

### RAG local (Retrieval-Augmented Generation)

Principe : stocker une base de connaissances locale, chercher
les extraits pertinents pour chaque question, injecter dans le
prompt système.

Avantages : fonctionne offline, contrôlable, fiable sur les
sujets couverts.

Inconvénients : complexe à implémenter, base à maintenir.

### Accès web contrôlé

Principe : appeler une API externe (DuckDuckGo, Wikipedia,
Légifrance) quand la question nécessite une info récente.

Avantages : fiable sur l'actualité, pas de maintenance de base.

Inconvénients : casse la promesse offline, dépend d'Internet.

### Acceptation des limites (état actuel)

Afficher un avertissement clair (fait via persona V1.6 + UI).
L'utilisateur doit vérifier les informations factuelles.

## Recommandation

Pour La Citadelle V3.x : accepter les limites, avertir
l'utilisateur. RAG local = phase future (voir TODO.md).
