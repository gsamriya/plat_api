import argparse, os, uvicorn

from ichec_api import create_app
from ichec_api.config_loader import load_config

# Get config from ENV or CLI arg (CLI overrides ENV)
default_config = os.getenv("ICHEC_FASTAPI_CONFIG", "config.yaml")

parser = argparse.ArgumentParser()
parser.add_argument("--config", default=default_config, help="YAML config file")


if __name__ == "__main__":
    args = parser.parse_args()
    config = load_config(args.config)
    app = create_app(args.config)
    port = config.get("server", {}).get("port", 8000)
    host = config.get("server", {}).get("host", "0.0.0.0")

    uvicorn.run(app, host=host, port=port)
