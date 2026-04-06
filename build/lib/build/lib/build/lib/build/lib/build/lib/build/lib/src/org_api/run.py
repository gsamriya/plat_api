import yaml
import uvicorn
from pathlib import Path

config_path = Path(__file__).parent / "config.yaml"


def load_config(config_path):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


if __name__ == "__main__":
    config = load_config()
    host = config["server"]["host"]
    port = config["server"]["port"]

    uvicorn.run("app:app", host=host, port=port, reload=True)
