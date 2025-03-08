import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

@pytest.mark.parametrize("payload,expected", [
    (None, 422),
    ({"message": ""}, 400),
    ({"invalid": "data"}, 422),
])
def test_error_cases(payload, expected):
    response = client.post("/chat", json=payload)
    assert response.status_code == expected

@pytest.mark.parametrize("service", ["ai", "cache", "vector"])
def test_missing_service(service, monkeypatch):
    monkeypatch.delenv(f'{service.upper()}_API_KEY', raising=False)
    response = client.get("/health")
    assert response.json()["status"] == "degraded"
