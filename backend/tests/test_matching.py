import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_deterministic_matching(client):
    cand = client.get("/api/candidates/active").json()
    cid = cand["id"]

    job = client.get("/api/jobs?query=AI&page_size=1").json()["items"][0]
    jid = job["id"]

    # Call compare twice to verify deterministic reproducibility
    res1 = client.get(f"/api/matching/{cid}/compare/{jid}")
    assert res1.status_code == 200
    data1 = res1.json()

    res2 = client.get(f"/api/matching/{cid}/compare/{jid}")
    assert res2.status_code == 200
    data2 = res2.json()

    # Exact score reproducibility
    assert data1["overall_score"] == data2["overall_score"]
    assert data1["matched_required_skills"] == data2["matched_required_skills"]
    assert data1["missing_required_skills"] == data2["missing_required_skills"]
    assert "breakdown" in data1
    assert "formula_weights" in data1["breakdown"]

def test_skill_gap_analysis(client):
    cand = client.get("/api/candidates/active").json()
    cid = cand["id"]

    job = client.get("/api/jobs?page=1&page_size=1").json()["items"][0]
    jid = job["id"]

    gap_res = client.get(f"/api/matching/{cid}/skill-gaps/{jid}")
    assert gap_res.status_code == 200
    data = gap_res.json()
    assert "overall_match_score" in data
    assert "missing_required_skills" in data
    assert "recommended_learning_topics" in data
    assert len(data["recommended_learning_topics"]) > 0
    assert "detailed_guidance" in data

def test_recommendations_ranking(client):
    cand = client.get("/api/candidates/active").json()
    cid = cand["id"]

    rec_res = client.get(f"/api/matching/{cid}/recommendations?limit=5")
    assert rec_res.status_code == 200
    data = rec_res.json()
    assert data["total_recommendations"] > 0
    recs = data["recommendations"]
    assert len(recs) <= 5

    # Verify descending score sort order
    scores = [r["overall_score"] for r in recs]
    assert scores == sorted(scores, reverse=True)
