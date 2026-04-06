import base64
import httpx

BASE_URL = "http://localhost:8000"

# Use your actual username/password defined in the app
USERNAME = "admin"
PASSWORD = "secret"

def get_basic_auth_header(username, password):
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}

def test_login():
    headers = get_basic_auth_header(USERNAME, PASSWORD)
    response = httpx.get(f"{BASE_URL}/status", headers=headers)
    print("Login GET status:", response.status_code)
    print("Response:", response.text)
    assert response.status_code == 200, "Expected 200 OK with basic auth"
    assert "API is running" in response.text

def test_post():
    headers = get_basic_auth_header(USERNAME, PASSWORD)
    payload = {"name": "Vic","value": 100}
    response = httpx.post(f"{BASE_URL}/data", headers=headers, json=payload)
    print("POST / status:", response.status_code)
    print("Response:", response.text)
    assert response.status_code == 200, "Expected 200 OK with basic auth"
    assert "Data received" in response.text

def test_get_without_auth():
    response = httpx.get(f"{BASE_URL}/status")
    print("Login GET status without auth:", response.status_code)
    print("Response:", response.text)
    assert response.status_code == 401, "Expected 401 Unauthorized without auth"

if __name__ == "__main__":
    print("Running E2E tests...\n")
    test_get_without_auth()
    print("\n---\n")
    test_login()
    print("\n---\n")
    test_post()
