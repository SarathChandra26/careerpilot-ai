import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_create_and_read_candidate(client):
    uniq = uuid.uuid4().hex[:6]
    payload = {
        "full_name": f"Jordan Lee {uniq}",
        "email": f"jordan.lee_{uniq}@example.com",
        "phone": "+1 555-987-6543",
        "education": "Master of Science in Artificial Intelligence",
        "degree": "Master's Degree",
        "experience_years": 2.0,
        "experience_level": "Mid-level",
        "preferred_roles": ["Machine Learning Engineer", "AI Engineer"],
        "preferred_locations": ["Remote", "Austin, TX"],
        "preferred_work_mode": "Remote",
        "career_interests": ["Computer Vision", "Deep Learning"]
    }
    create_res = client.post("/api/candidates", json=payload)
    assert create_res.status_code == 201
    cand = create_res.json()
    assert cand["full_name"] == f"Jordan Lee {uniq}"
    assert cand["email"] == f"jordan.lee_{uniq}@example.com"
    assert cand["profile_completeness"] > 0

    cid = cand["id"]
    get_res = client.get(f"/api/candidates/{cid}")
    assert get_res.status_code == 200
    assert get_res.json()["degree"] == "Master's Degree"

def test_add_and_remove_candidate_skill(client):
    active_res = client.get("/api/candidates/active")
    assert active_res.status_code == 200
    cid = active_res.json()["id"]

    # Add skill
    skill_payload = {
        "skill_name": "PyTorch",
        "category": "Frameworks",
        "proficiency": "Advanced",
        "verified": True
    }
    skill_res = client.post(f"/api/candidates/{cid}/skills", json=skill_payload)
    assert skill_res.status_code == 200
    skill_data = skill_res.json()
    assert skill_data["skill_name"] == "PyTorch"
    skill_id = skill_data["id"]

    # Remove skill
    del_res = client.delete(f"/api/candidates/{cid}/skills/{skill_id}")
    assert del_res.status_code == 204
