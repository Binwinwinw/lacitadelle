def test_default_model_is_consistent_across_sources():
    """Vérifie que le modèle par défaut est identique dans les 3 sources."""
    import sys
    from pathlib import Path
    import json

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
    import lancer
    import model_health

    config_path = (
        Path(__file__).resolve().parent.parent
        / "tools"
        / "llamafile_config.json"
    )
    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    # Source 1 : lancer.py
    lancer_default = lancer.DEFAULT_MODEL_FILENAME

    # Source 2 : model_health.py
    health_default = model_health.DEFAULT_MODEL_FILENAME

    # Source 3 : llamafile_config.json
    assets = config.get("assets", {})
    config_default = None
    for asset in assets.values():
        if asset.get("filename", "").endswith(".gguf"):
            config_default = asset["filename"]
            break

    assert lancer_default == health_default, (
        f"lancer.py ({lancer_default}) != model_health.py ({health_default})"
    )
    assert lancer_default == config_default, (
        f"lancer.py ({lancer_default}) != config ({config_default})"
    )
