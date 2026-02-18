from pathlib import Path
import yaml


def load_geometry_config(config: str | Path) -> dict:
    """
    Load a geometry YAML configuration.

    Parameters
    ----------
    config : str or Path
        Either:
        - the name of a config shipped with pygeom-scarf (e.g. "scarf_pen.yaml"), or
        - a path to a user-provided YAML config file.
    """
    config = Path(config)

    # Case 1: user passed an explicit path
    if config.exists():
        path = config
    else:
        # Case 2: fall back to built-in configs
        config_dir = Path(__file__).parent / "configs"
        path = config_dir / config

    if not path.exists():
        raise FileNotFoundError(f"Geometry config not found: {path}")

    with path.open() as f:
        return yaml.safe_load(f)
