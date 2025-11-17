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
    assert data["name"] == "DashScope API Shim"


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
    assert any(model["id"] == "qwen-turbo" for model in data["data"])


def test_get_model(client):
    """Test get specific model endpoint."""
    response = client.get("/v1/models/qwen-turbo")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "qwen-turbo"
    assert data["object"] == "model"


def test_get_model_not_found(client):
    """Test get model with non-existent ID."""
    response = client.get("/v1/models/non-existent-model")
    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "model_not_found"


def test_chat_completion_no_auth(client):
    """Test chat completion without authorization."""
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "qwen-turbo",
            "messages": [{"role": "user", "content": "Hello"}],
        },
    )
    assert response.status_code == 401


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