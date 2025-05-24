from fastapi.testclient import TestClient

from orchestra_api.main import app

client = TestClient(app)


def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert "dragonfly" in resp.json()
    assert "qdrant" in resp.json()
    assert "firestore" in resp.json()


def test_create_and_get_memory():
    payload = {
        "id": "test123",
        "content": "Integration test memory",
        "source": "pytest",
        "timestamp": "2025-05-24T02:56:00Z",
        "metadata": {"test": True},
        "priority": 0.9,
        "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
    }
    # Create
    resp = client.post("/memory/", json=payload)
    assert resp.status_code == 200
    assert resp.json()["id"] == "test123"
    # Get
    resp = client.get("/memory/test123")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "test123"
    assert data["content"] == "Integration test memory"
    # Delete
    resp = client.delete("/memory/test123")
    assert resp.status_code == 200
    assert resp.json()["deleted"] is True
    # Confirm deletion
    resp = client.get("/memory/test123")
    assert resp.status_code == 404
