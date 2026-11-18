import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_application_lifecycle_and_tasks(client):
    cand = client.get("/api/candidates/active").json()
    cid = cand["id"]

    job = client.get("/api/jobs?page=1&page_size=1").json()["items"][0]
    jid = job["id"]

    # 1. Create Application
    app_payload = {
        "job_id": jid,
        "status": "Preparing",
        "notes": "Tailoring resume for AI Engineer role"
    }
    app_res = client.post(f"/api/applications?candidate_id={cid}", json=app_payload)
    assert app_res.status_code == 201
    app_data = app_res.json()
    assert app_data["status"] == "Preparing"
    app_id = app_data["id"]

    # 2. Update Application Status
    upd_res = client.put(f"/api/applications/{app_id}", json={"status": "Applied", "notes": "Submitted via company portal"})
    assert upd_res.status_code == 200
    assert upd_res.json()["status"] == "Applied"

    # 3. Create Task
    task_payload = {
        "application_id": app_id,
        "job_id": jid,
        "title": "Complete technical take-home test",
        "is_completed": False
    }
    task_res = client.post(f"/api/applications/tasks?candidate_id={cid}", json=task_payload)
    assert task_res.status_code == 201
    task_id = task_res.json()["id"]

    # 4. Mark Task Completed
    task_upd = client.put(f"/api/applications/tasks/{task_id}", json={"is_completed": True})
    assert task_upd.status_code == 200
    assert task_upd.json()["is_completed"] is True
    assert task_upd.json()["completed_at"] is not None

    # 5. Filter Applications
    applied_apps = client.get(f"/api/applications/{cid}?status_filter=Applied").json()
    assert any(a["id"] == app_id for a in applied_apps)
