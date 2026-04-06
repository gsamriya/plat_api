import pytest
import yaml
import json
from fastapi import HTTPException, status
from pydantic import ValidationError
from pathlib import Path
from unittest.mock import AsyncMock, patch
from types import SimpleNamespace
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError

# Import the components to test
from org_api.auth import authenticate, verify_basic_auth, verify_token_auth, VALID_USERNAME, VALID_PASSWORD, VALID_TOKEN
from org_api.exception_handlers import http_exception_handler, validation_exception_handler, internal_server_error_handler
from org_api.routes.api_routes import DataPayload
from org_api.app import create_app
from org_api.config_loader import load_config
from org_api.kafka_client import init_kafka, shutdown_kafka, send_kafka_message


config_path = Path(__file__).resolve().parent.parent / "src" / "org_api" / "configs" / "config.yaml"
app = create_app(config_path)

# --- Fixtures for mock requests ---
# Mocking the request object for exception handlers
@pytest.fixture
def mock_request():
    class MockRequest:
        def __init__(self, url_path="/mock-path"):
            self.url = type('obj', (object,), {'path': url_path})()
    return MockRequest()

# --- Tests for src/org_api/auth.py ---

def test_verify_basic_auth_valid_credentials():
    credentials = type('obj', (object,), {'username': VALID_USERNAME, 'password': VALID_PASSWORD})()
    assert verify_basic_auth(credentials) == VALID_USERNAME

def test_verify_basic_auth_invalid_credentials():
    credentials = type('obj', (object,), {'username': "wrong", 'password': "credentials"})()
    with pytest.raises(HTTPException) as excinfo:
        verify_basic_auth(credentials)
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Incorrect basic authentication credentials" in excinfo.value.detail

def test_verify_basic_auth_missing_credentials():
    with pytest.raises(HTTPException) as excinfo:
        verify_basic_auth(None) # Simulate no credentials
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Incorrect basic authentication credentials" in excinfo.value.detail


def test_verify_token_auth_valid_token():
    credentials = type('obj', (object,), {'scheme': "bearer", 'credentials': VALID_TOKEN})()
    assert verify_token_auth(credentials) == VALID_USERNAME

def test_verify_token_auth_invalid_token():
    credentials = type('obj', (object,), {'scheme': "bearer", 'credentials': "wrongtoken"})()
    with pytest.raises(HTTPException) as excinfo:
        verify_token_auth(credentials)
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid bearer token" in excinfo.value.detail

def test_verify_token_auth_missing_credentials():
    with pytest.raises(HTTPException) as excinfo:
        verify_token_auth(None) # Simulate no credentials
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid bearer token" in excinfo.value.detail


# Test the unified authenticate dependency
@pytest.mark.asyncio # Mark as async test for async authenticate function
async def test_authenticate_with_valid_basic_credentials():
    basic_creds = type('obj', (object,), {'username': VALID_USERNAME, 'password': VALID_PASSWORD})()
    # Mocking Dependencies for authenticate
    # Here we are calling authenticate directly, so we pass the "mocked" dependencies
    result = await authenticate(basic_credentials=basic_creds, bearer_credentials=None)
    assert result == VALID_USERNAME

@pytest.mark.asyncio
async def test_authenticate_with_valid_bearer_credentials():
    bearer_creds = type('obj', (object,), {'scheme': "bearer", 'credentials': VALID_TOKEN})()
    result = await authenticate(basic_credentials=None, bearer_credentials=bearer_creds)
    assert result == VALID_USERNAME

@pytest.mark.asyncio
async def test_authenticate_with_invalid_credentials_from_both():
    invalid_basic = type('obj', (object,), {'username': "bad", 'password': "bad"})()
    invalid_bearer = type('obj', (object,), {'scheme': "bearer", 'credentials': "bad"})()
    with pytest.raises(HTTPException) as excinfo:
        await authenticate(basic_credentials=invalid_basic, bearer_credentials=invalid_bearer)
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid authentication credentials" in excinfo.value.detail

@pytest.mark.asyncio
async def test_authenticate_with_no_credentials():
    with pytest.raises(HTTPException) as excinfo:
        await authenticate(basic_credentials=None, bearer_credentials=None)
    assert excinfo.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid authentication credentials" in excinfo.value.detail

# --- Tests for src/org_api/run.py ---

def test_load_config_success(tmp_path):
    valid_config_content = """
        server:
          host: 127.0.0.1
          port: 8001
        app:
          name: TestApp
        """
    # Create the temporary config file within the tmp_path directory
    temp_config_path = tmp_path / "config_test.yaml"
    temp_config_path.write_text(valid_config_content)  # Write the content to the file

    # Call load_config with the path to the temporary file
    config = load_config(temp_config_path)

    assert isinstance(config, dict)
    assert config["server"]["host"] == "127.0.0.1"
    assert config["server"]["port"] == 8001
    assert config["app"]["name"] == "TestApp"

def test_load_config_file_not_found():
    non_existent_path = Path("non_existent_config.yaml")
    with pytest.raises(FileNotFoundError):
        load_config(non_existent_path)

def test_load_config_invalid_yaml(tmp_path):
    invalid_yaml_content = """
        key:
          - item1
        invalid: {
          key: value
        """
    # Create the temporary invalid config file within the tmp_path directory
    temp_config_path = tmp_path / "config_invalid.yaml"
    temp_config_path.write_text(invalid_yaml_content)

    with pytest.raises(yaml.YAMLError):
        load_config(temp_config_path)


# --- Tests for kafka_client.py ---

@pytest.mark.asyncio
async def test_init_kafka_starts_producer():
    mock_producer = AsyncMock()

    config = {"kafka": {"bootstrap_servers": "localhost:9092"}}
    app = SimpleNamespace()
    app.state = SimpleNamespace()

    with patch("org_api.kafka_client.AIOKafkaProducer", return_value=mock_producer):
        await init_kafka(config, app)

        mock_producer.start.assert_awaited_once()
        assert app.state.kafka_producer == mock_producer

@pytest.mark.asyncio
async def test_shutdown_kafka_stops_producer():
    mock_producer = AsyncMock()
    app = SimpleNamespace()
    app.state = SimpleNamespace(kafka_producer=mock_producer)

    await shutdown_kafka(app)
    mock_producer.stop.assert_awaited_once()

@pytest.mark.asyncio
async def test_send_kafka_message_when_enabled():
    mock_producer = AsyncMock()
    config = {"kafka": {"enabled": True, "topic": "test-topic"}}
    app = SimpleNamespace()
    app.state = SimpleNamespace(config=config, kafka_producer=mock_producer)

    await send_kafka_message(app, "Hello Kafka")
    mock_producer.send_and_wait.assert_awaited_once_with("test-topic", b"Hello Kafka")

@pytest.mark.asyncio
async def test_send_kafka_message_when_disabled():
    mock_producer = AsyncMock()
    config = {"kafka": {"enabled": False, "topic": "test-topic"}}
    app = SimpleNamespace()
    app.state = SimpleNamespace(config=config, kafka_producer=mock_producer)

    await send_kafka_message(app, "Hello Kafka")
    mock_producer.send_and_wait.assert_not_called()

# --- Tests for DataPayload (Pydantic Model) from src/org_api/app.py ---

def test_data_payload_valid():
    payload = DataPayload(name="ValidName", value=50)
    assert payload.name == "ValidName"
    assert payload.value == 50

def test_data_payload_name_too_short():
    with pytest.raises(ValidationError) as excinfo:
        DataPayload(name="ab", value=50)
    assert "String should have at least 3 characters" in str(excinfo.value) # New assertion

def test_data_payload_name_too_long():
    with pytest.raises(ValidationError) as excinfo:
        DataPayload(name="a" * 51, value=50)
    assert "String should have at most 50 characters" in str(excinfo.value) # New assertion

def test_data_payload_value_below_min():
    with pytest.raises(ValidationError) as excinfo:
        DataPayload(name="Valid", value=-1)
    assert "greater than or equal to 0" in str(excinfo.value)

def test_data_payload_value_above_max():
    with pytest.raises(ValidationError) as excinfo:
        DataPayload(name="Valid", value=101)
    assert "less than or equal to 100" in str(excinfo.value)

def test_data_payload_value_not_int():
    with pytest.raises(ValidationError) as excinfo:
        DataPayload(name="Valid", value="abc")
    assert "Input should be a valid integer" in str(excinfo.value) # New assertion

# --- Tests for Custom Exception Handlers from src/org_api/app.py ---

@pytest.mark.asyncio
async def test_http_exception_handler(mock_request):
    exc = StarletteHTTPException(status_code=404, detail="Not Found")
    response = await http_exception_handler(mock_request, exc)
    assert response.status_code == 404
    content = json.loads(response.body) # <--- CHANGE THIS LINE
    assert content["error"]["type"] == "http_exception"
    assert content["error"]["detail"] == "Not Found"
    assert content["error"]["path"] == "/mock-path"

@pytest.mark.asyncio
async def test_validation_exception_handler(mock_request):
    # Create a mock RequestValidationError
    class MockValidationError(RequestValidationError):
        def errors(self):
            return [{"loc": ("body", "name"), "msg": "field required", "type": "value_error.missing"}]

    exc = MockValidationError([]) # The actual errors list doesn't matter for this test
    response = await validation_exception_handler(mock_request, exc)
    assert response.status_code == 422
    content = json.loads(response.body) # <--- CHANGE THIS LINE
    assert content["error"]["type"] == "validation_error"
    assert content["error"]["path"] == "/mock-path"
    assert len(content["error"]["details"]) == 1
    assert content["error"]["details"][0]["field"] == "body.name"
    assert content["error"]["details"][0]["message"] == "field required"

@pytest.mark.asyncio
async def test_internal_server_error_handler(mock_request):
    mock_exception = Exception("Something went wrong")
    response = await internal_server_error_handler(mock_request, mock_exception)
    assert response.status_code == 500
    content = json.loads(response.body) # <--- CHANGE THIS LINE
    assert content["error"]["type"] == "internal_error"
    assert content["error"]["detail"] == "An unexpected error occurred on server."
    assert content["error"]["path"] == "/mock-path"