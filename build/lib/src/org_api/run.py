import yaml
import uvicorn
from pathlib import Path

config_path = Path(__file__).resolve().parent / "configs" / "config.yaml"

def load_config(path=config_path):
    with open(path, "r") as f:
        return yaml.safe_load(f)

if __name__ == "__main__":
    config = load_config()
    host = config["server"]["host"]
    port = config["server"]["port"]

    uvicorn.run("ichec_api.app:app", host=host, port=port, reload=True)
