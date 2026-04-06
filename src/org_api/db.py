import os

from sqlmodel import SQLModel, create_engine, Session
from ichec_api.config_loader import load_config
from typing import Generator

_config = os.getenv("ICHEC_FASTAPI_CONFIG", "config.yaml")
config = load_config(_config)

DATABASE_URL_CNFG = config.get("database", {}).get("url", "sqlite:///./test.db")
DATABASE_URL = os.getenv("ICHEC_FASTAPI_DATABASE_URL", DATABASE_URL_CNFG)

engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)
    print("Database initialized and tables created.")


def get_session() -> Generator[Session, None, None]:
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()