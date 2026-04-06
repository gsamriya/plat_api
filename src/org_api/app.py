import argparse, os, uvicorn

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from prometheus_fastapi_instrumentator import Instrumentator

from .logger_middleware import LoggingMiddleware
from .monitor_middleware import MonitoringMiddleware
from .routes import api_routes
from .routes import items
from ichec_api.kafka_client import init_kafka, shutdown_kafka
from ichec_api.config_loader import load_config
from .db import init_db

def create_app(config_file: str = "config.yaml") -> FastAPI:

    config = load_config(config_file)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.config = config
        if config["kafka"].get("enabled"):
            await init_kafka(config, app)
        init_db() # DB tables created on startup
        yield
        if config["kafka"].get("enabled"):
            await shutdown_kafka(app)

    app = FastAPI(lifespan=lifespan)

    # Add Prometheus metrics instrumentation
    Instrumentator().instrument(app)

    # Add Logger Middleware
    app.add_middleware(LoggingMiddleware)

    app.add_middleware(MonitoringMiddleware)

    # Import and include routers
    app.include_router(api_routes.router)
    app.include_router(items.router)


    # The handlers below would override the default FastAPI HTTP exception handler to customize the error response format.
    # The handlers would allow us to log the error details, request path, and customize the structure of the returned JSON (e.g., add error codes, timestamps, etc.).
    # It would also help to maintain a consistent error response format across the API.
    # Otherwise, FastAPI would use a plain JSON error with the minimal context.
    from .exception_handlers import (
        http_exception_handler,
        validation_exception_handler,
        internal_server_error_handler,
    )
    app.exception_handler(StarletteHTTPException)(http_exception_handler)
    app.exception_handler(RequestValidationError)(validation_exception_handler)
    app.exception_handler(Exception)(internal_server_error_handler)


    return app
