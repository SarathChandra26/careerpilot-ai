import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_memory_crud_and_persistence(client):
    cand = client.get("/api/candidates/active").json()
    cid = cand["id"]

    # 1. Create explicit memory
    mem_payload = {
        "category": "career_goal",
        "memory_key": "target_salary",
        "memory_value": "$120,000+",
        "confidence": 1.0,
        "source": "user_settings"
    }
    create_res = client.post(f"/api/memory/{cid}", json=mem_payload)
    assert create_res.status_code == 201
    mem = create_res.json()
    assert mem["memory_key"] == "target_salary"
    mid = mem["id"]

    # 2. Get memories
    list_res = client.get(f"/api/memory/{cid}")
    assert list_res.status_code == 200
    assert any(m["id"] == mid for m in list_res.json())

    # 3. Update memory
    upd_res = client.put(f"/api/memory/item/{mid}", json={"memory_value": "$135,000+"})
    assert upd_res.status_code == 200
    assert upd_res.json()["memory_value"] == "$135,000+"

    # 4. Delete memory
    del_res = client.delete(f"/api/memory/item/{mid}")
    assert del_res.status_code == 204

    # 5. Verify deleted
    list_res_after = client.get(f"/api/memory/{cid}")
    assert not any(m["id"] == mid for m in list_res_after.json())
