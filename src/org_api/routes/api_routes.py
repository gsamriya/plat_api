from fastapi import APIRouter, Depends, Query, Request, Response
from pydantic import BaseModel, Field, conint
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from ichec_api.auth import authenticate
from ichec_api.kafka_client import send_kafka_message

router = APIRouter()

# -------------------- Models --------------------
class DataPayload(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    value: conint(ge=0, le=100)  # Integer between 0 and 100
# -------------------- Endpoints --------------------

@router.get("/status")
def get_status(param: bool = False, user: str = Depends(authenticate)):
    if param:
        return {
            "status": "API is running",
            "user": user,
            "details": f"Query parameter is provided as {param}"
        }
    return {"status": "API is running", "user": user}

@router.post("/data")
async def post_data(
    request: Request,
    payload: DataPayload,
    source: str = Query("unknown", min_length=2, max_length=20),
    user: str = Depends(authenticate),
):
    # Kafka publishing if enabled
    config = request.app.state.config
    if config.get("kafka", {}).get("enabled"):
        message = {
            "source": source,
            "user": user,
            "name": payload.name,
            "value": payload.value
        }
        await send_kafka_message(request.app, str(message))

    return {
        "message": f"Data received from {user} via source {source}",
        "data": payload,
    }

@router.get("/metrics", include_in_schema=True)
def metrics(_user: str = Depends(authenticate)):
    """Protected Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
