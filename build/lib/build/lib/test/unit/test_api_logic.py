import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from pydantic import ValidationError
from pathlib import Path
import yaml
import json
import base64

# Import the components to test
from src.ichec_api.auth import authenticate, verify_basic_auth, verify_token_auth, basic_security, bearer_security, VALID_USERNAME, VALID_PASSWORD, VALID_TOKEN
from src.ichec_api.run import load_config
from src.ichec_api.app import app, DataPayload, http_exception_handler, validation_exception_handler, internal_server_error_handler
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError
from starlette.requests import Request


# --- Fixtures for TestClient and mock requests ---
# This client will run FastAPI app directly in the test process
# without needing `uvicorn`. It's integration-style unit tests.
@pytest.fixture(scope="module")
def client():
    # For simplicity, we'll test auth functions directly and
    # use the client for endpoint tests where auth is mocked or bypassed.
    return TestClient(app)

# Mocking the request object for exception handlers
@pytest.fixture
def mock_request():
    class MockRequest:
        def __init__(self, url_path="/mock-path"):
            self.url = type('obj', (object,), {'path': url_path})()
    return MockRequest()


# --- Tests for src/ichec_api/auth.py ---

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

# --- Tests for src/ichec_api/run.py ---

def test_load_config_success(tmp_path):
    # Create a temporary config file for testing
    temp_config_content = """
    server:
      host: "127.0.0.1"
      port: 8001
    app:
      name: "TestApp"
    """
    temp_config_path = tmp_path / "test_config.yaml"
    temp_config_path.write_text(temp_config_content)

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
    server:
      host: "127.0.0.1"
    - invalid_list_item: value
    """
    temp_config_path = tmp_path / "invalid_config.yaml"
    temp_config_path.write_text(invalid_yaml_content)

    with pytest.raises(yaml.YAMLError):
        load_config(temp_config_path)


# --- Tests for DataPayload (Pydantic Model) from src/ichec_api/app.py ---

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

# --- Tests for Custom Exception Handlers from src/ichec_api/app.py ---

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
    response = await internal_server_error_handler(mock_request)
    assert response.status_code == 500
    content = json.loads(response.body) # <--- CHANGE THIS LINE
    assert content["error"]["type"] == "internal_error"
    assert content["error"]["detail"] == "An unexpected error occurred on server."
    assert content["error"]["path"] == "/mock-path"