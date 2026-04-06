from fastapi import FastAPI, Depends, Response, Request, Query
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel, Field, conint
from .auth import authenticate
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from .logger_middleware import LoggingMiddleware

app = FastAPI()

# Add Prometheus metrics instrumentation
Instrumentator().instrument(app)

# Add Logger Middleware
app.add_middleware(LoggingMiddleware)

# GET endpoint
@app.get("/status")
def get_status(param: bool = False, user: str = Depends(authenticate)):
    if param:
        return {"status": "API is running", "user": user, "details": f"Query parameter is provided as {param}"}
    return {"status": "API is running", "user": user}


# POST endpoint
class DataPayload(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    value: conint(ge=0, le=100)  # Integer between 0 and 100


@app.post("/data")
def post_data(payload: DataPayload, source: str = Query("unknown", min_length=2, max_length=20), user: str = Depends(authenticate)):
    return {"message": f"Data received from {user} via source {source}", "data": payload}


# Prometheus metrics endpoint (also protected)
@app.get("/metrics", include_in_schema=False)
def metrics(_user: str = Depends(authenticate)):
    """Protected Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# The handlers below would override the default FastAPI HTTP exception handler to customize the error response format.
# The handlers would allow us to log the error details, request path, and customize the structure of the returned JSON (e.g., add error codes, timestamps, etc.).
# It would also help to maintain a consistent error response format across the API.
# Otherwise, FastAPI would use a plain JSON error with the minimal context.
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "http_exception",
                "detail": exc.detail,
                "path": request.url.path
            }
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [
        {
            "field": ".".join(str(loc) for loc in err["loc"]),
            "message": err["msg"]
        }
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "type": "validation_error",
                "path": request.url.path,
                "details": errors
            }
        }
    )

@app.exception_handler(Exception)
async def internal_server_error_handler(request: Request):
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "internal_error",
                "detail": "An unexpected error occurred on server.",
                "path": request.url.path
            }
        }
    )