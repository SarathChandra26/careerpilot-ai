import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_job_search_and_filters(client):
    # Filter by role_category
    res_ai = client.get("/api/jobs?role_category=AI Engineer&page_size=5")
    assert res_ai.status_code == 200
    data_ai = res_ai.json()
    assert len(data_ai["items"]) > 0
    assert all("AI" in j["role_category"] for j in data_ai["items"])

    # Filter by work_mode
    res_remote = client.get("/api/jobs?work_mode=Remote&page_size=5")
    assert res_remote.status_code == 200
    data_remote = res_remote.json()
    assert all(j["work_mode"] == "Remote" for j in data_remote["items"])

    # Query text search
    res_q = client.get("/api/jobs?query=Python&page_size=5")
    assert res_q.status_code == 200
    assert len(res_q.json()["items"]) > 0

def test_create_and_deduplicate_job(client):
    uniq = uuid.uuid4().hex[:6]
    payload = {
        "company": f"Test AI Corp {uniq}",
        "title": f"Junior Prompt Engineer {uniq}",
        "description": "Design and evaluate robust prompts for local LLMs.",
        "role_category": "AI Engineer",
        "experience_level": "Entry-level",
        "experience_years_min": 0.0,
        "location": "Remote",
        "work_mode": "Remote",
        "employment_type": "Full-time",
        "salary_min": 80000,
        "salary_max": 100000,
        "salary_currency": "USD",
        "skills": [
            {"skill_name": "Python", "is_required": True, "importance_weight": 2.0},
            {"skill_name": "Prompt Engineering", "is_required": True, "importance_weight": 2.0},
            {"skill_name": "FastAPI", "is_required": False, "importance_weight": 1.0}
        ]
    }
    create_res = client.post("/api/jobs", json=payload)
    assert create_res.status_code == 201
    job = create_res.json()
    assert job["company"] == f"Test AI Corp {uniq}"
    assert job["title"] == f"Junior Prompt Engineer {uniq}"

    # Attempt to create exact duplicate
    dup_res = client.post("/api/jobs", json=payload)
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.json()["detail"]

def test_save_and_unsave_job(client):
    cand = client.get("/api/candidates/active").json()
    cid = cand["id"]

    job = client.get("/api/jobs?page=1&page_size=1").json()["items"][0]
    jid = job["id"]

    # Save job
    save_res = client.post(f"/api/jobs/{jid}/save?candidate_id={cid}&notes=Priority opportunity")
    assert save_res.status_code == 200

    # Verify in saved list
    saved_list = client.get(f"/api/jobs/saved/{cid}").json()
    assert any(s["job_id"] == jid for s in saved_list)

    # Unsave job
    del_res = client.delete(f"/api/jobs/{jid}/save?candidate_id={cid}")
    assert del_res.status_code == 204

    # Verify removed
    saved_list_after = client.get(f"/api/jobs/saved/{cid}").json()
    assert not any(s["job_id"] == jid for s in saved_list_after)
