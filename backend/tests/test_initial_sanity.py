import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["database_connected"] is True
    assert "llm_service" in data

def test_active_candidate(client):
    res = client.get("/api/candidates/active")
    assert res.status_code == 200
    data = res.json()
    assert "full_name" in data
    assert data["full_name"] in ["Alex Rivera", "Marcus Vance"]
    assert len(data["skills"]) >= 5

def test_job_catalogue_populated(client):
    res = client.get("/api/jobs?page=1&page_size=5")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 200
    assert len(data["items"]) == 5
    job = data["items"][0]
    assert "title" in job
    assert "company" in job
    assert "skills" in job
