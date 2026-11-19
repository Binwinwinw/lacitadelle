"""Point d'extension hors ligne pour la recherche Web."""


def search_web(query: str, max_results: int = 5) -> list[dict[str, str]]:
    """Décrit la future recherche Web sans effectuer d'accès réseau.

    La recherche Web est hors ligne et devra être activée/configurée
    manuellement avant toute intégration d'un fournisseur.
    """
    raise NotImplementedError("API web non configurée (hors ligne)")
