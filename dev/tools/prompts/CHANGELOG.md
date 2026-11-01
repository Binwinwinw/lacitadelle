# Historique des prompts système

## V1.1 — 2026-10-31 (Phase 14-PERSONA-NEXXUS-BIS)

Corrections après les tests manuels :

- Interdiction explicite des formules flatteuses et des amorces de politesse.
- Précision du périmètre des recommandations professionnelles : elles
  concernent les demandes explicites d'avis médical, juridique ou financier,
  pas les questions philosophiques générales.
- Ajout de l'environnement technique local et de la reconnaissance de l'API
  llamafile.

Le prompt est plus directif sur ces points.

## V1 — 2026-10-31 (Phase 14-PERSONA-NEXXUS-V1)

- Création du persona Nexxus, assistant IA de La Citadelle.
- Séparation de l'identité de l'assistant et du modèle via `{model_name}`.
- Injection dynamique de la date, de l'utilisateur et de la session.
- Détection du registre de langue et maintien d'une forme cohérente.
- Ton neutre et direct, avec limites explicites.
- Aucune mention d'outils de lecture de fichiers non activés.
