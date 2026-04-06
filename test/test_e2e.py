import pytest
import pytest_asyncio
import base64

from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport, BasicAuth
from org_api.app import create_app

# Use actual username/password defined in the app
USERNAME = "admin"
PASSWORD = "secret"

config_path = Path(__file__).resolve().parent.parent / "src" / "org_api" / "configs" / "config.yaml"
app = create_app(config_path)


@pytest_asyncio.fixture(scope="module")
async def async_client():
    #TestClient is the context manager
    with TestClient(app) as client:
        yield client

def get_basic_auth_header(username, password):
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}

@pytest.mark.asyncio
async def test_login(async_client: TestClient):
    headers = get_basic_auth_header(USERNAME, PASSWORD)
    response = async_client.get("/status", headers=headers)
    print("Login GET status:", response.status_code)
    print("Response:", response.text)
    assert response.status_code == 200, "Expected 200 OK with basic auth"
    assert "API is running" in response.text

@pytest.mark.asyncio
async def test_post(async_client: TestClient):
    headers = get_basic_auth_header(USERNAME, PASSWORD)
    payload = {"name": "Vic", "value": 100} # Example payload
    response = async_client.post("/data", headers=headers, json=payload)
    print("POST / status:", response.status_code)
    print("Response:", response.text)
    assert response.status_code == 200, "Expected 200 OK with basic auth"
    assert "Data received" in response.text

@pytest.mark.asyncio
async def test_get_without_auth(async_client: TestClient):
    response = async_client.get("/status")
    print("Login GET status without auth:", response.status_code)
    print("Response:", response.text)
    assert response.status_code == 401, "Expected 401 Unauthorized without auth"

@pytest.mark.asyncio
async def test_post_triggers_kafka_send_when_enabled():
    mock_producer = AsyncMock()
    # Manually inject config and producer into app.state
    app.state.config = {
        "kafka": {
            "enabled": True,
            "bootstrap_servers": "localhost:9092",
            "topic": "test-topic"
        }
    }

    with patch("org_api.kafka_client.AIOKafkaProducer", return_value=mock_producer):
        # simulate startup
        await app.router.startup()
        app.state.kafka_producer = mock_producer

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as async_client:
            payload = {"name": "Test_name", "value": 42}
            auth = BasicAuth(USERNAME, PASSWORD)
            response = await async_client.post("/data", json=payload, auth=auth)

        assert response.status_code == 200
        mock_producer.send_and_wait.assert_awaited_once()

if __name__ == "__main__":
    print("Running E2E tests...\n")
    test_get_without_auth()
    print("\n---\n")
    test_login()
    print("\n---\n")
    test_post()
