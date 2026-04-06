from fastapi import FastAPI, Depends
from pydantic import BaseModel
from auth import verify_basic_auth

app = FastAPI()


# GET endpoint
@app.get("/status")
def get_status(user: str = Depends(verify_basic_auth)):
    return {"status": "API is running", "user": user}


# POST endpoint
class DataPayload(BaseModel):
    name: str
    value: int


@app.post("/data")
def post_data(payload: DataPayload, user: str = Depends(verify_basic_auth)):
    return {"message": f"Data received from {user}", "data": payload}
