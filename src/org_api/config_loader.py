import yaml
from pathlib import Path

def load_config(config_file: str) -> dict:
    config_path = Path(config_file)
    # Use configs/ folder relative to this script if path is not absolute
    if not config_path.is_absolute():
        base_dir = Path(__file__).resolve().parent
        config_path = base_dir / "configs" / config_file

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML file '{config_path}': {e}")
