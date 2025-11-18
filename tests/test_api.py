"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from dashscope_api_shim.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert data["name"] == "Bailian App API Shim"


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_list_models(client):
    """Test list models endpoint."""
    response = client.get("/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert len(data["data"]) > 0
    # Check for Bailian app model
    assert any(model["id"].startswith("bailian-app-") for model in data["data"])


def test_get_model(client):
    """Test get specific model endpoint."""
    # Get the actual model ID from list endpoint first
    response = client.get("/v1/models")
    models = response.json()["data"]
    model_id = models[0]["id"]

    response = client.get(f"/v1/models/{model_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == model_id
    assert data["object"] == "model"


def test_get_model_not_found(client):
    """Test get model with non-existent ID."""
    response = client.get("/v1/models/non-existent-model")
    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "model_not_found"


def test_chat_completion_no_auth(client):
    """Test chat completion without authorization (falls back to env var)."""
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "bailian-app-test",
            "messages": [{"role": "user", "content": "Hello"}],
        },
    )
    # Should use fallback to env var, so expect either 200 or error from API
    assert response.status_code in [200, 400, 500]


def test_chat_completion_invalid_auth(client):
    """Test chat completion with invalid authorization format."""
    response = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "InvalidFormat"},
        json={
            "model": "qwen-turbo",
            "messages": [{"role": "user", "content": "Hello"}],
        },
    )
    assert response.status_code == 401