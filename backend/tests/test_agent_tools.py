import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.tools.registry import ToolRegistry, TOOL_DEFINITIONS
from app.tools.implementations import ToolExecutor
from app.database.session import SessionLocal

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_tool_definitions_valid():
    assert len(TOOL_DEFINITIONS) >= 12
    tool_names = [t["name"] for t in TOOL_DEFINITIONS]
    assert "search_jobs" in tool_names
    assert "get_candidate_profile" in tool_names
    assert "update_candidate_preferences" in tool_names
    assert "compare_job_with_candidate" in tool_names
    assert "save_job" in tool_names
    assert "remove_saved_job" in tool_names
    assert "get_saved_jobs" in tool_names
    assert "create_application_task" in tool_names
    assert "get_application_tasks" in tool_names
    assert "update_application_status" in tool_names
    assert "generate_interview_questions" in tool_names
    assert "identify_skill_gaps" in tool_names

def test_tool_executor_direct_execution(client):
    db = SessionLocal()
    cand = client.get("/api/candidates/active").json()
    cid = cand["id"]

    executor = ToolExecutor(db, candidate_id=cid)

    # 1. search_jobs
    search_res = executor.search_jobs({"query": "AI", "limit": 3})
    assert search_res["success"] is True
    assert len(search_res["jobs"]) <= 3

    # 2. get_candidate_profile
    prof_res = executor.get_candidate_profile({})
    assert prof_res["success"] is True
    assert prof_res["profile"]["full_name"] in ["Alex Rivera", "Marcus Vance"]

    # 3. create_application_task
    task_res = executor.create_application_task({"title": "Practice LeetCode Python"})
    assert task_res["success"] is True
    assert "Practice LeetCode" in task_res["title"]

    # 4. get_application_tasks
    tasks_res = executor.get_application_tasks({})
    assert tasks_res["success"] is True
    assert any("Practice LeetCode" in t["title"] for t in tasks_res["tasks"])

    db.close()

def test_agent_chat_api(client):
    cand = client.get("/api/candidates/active").json()
    cid = cand["id"]

    # Test conversational job search intent
    chat_payload = {
        "candidate_id": cid,
        "message": "Find me suitable AI Engineer internships. I prefer remote opportunities."
    }
    res = client.post("/api/agent/chat", json=chat_payload)
    assert res.status_code == 200
    data = res.json()
    assert "message" in data
    assert "llm_source" in data
    assert len(data["tools_called"]) >= 1
    assert data["tools_called"][0]["tool"] == "search_jobs"
    assert data["tools_called"][0]["status"] == "SUCCESS"

    # Verify memory was automatically extracted and saved
    mem_res = client.get(f"/api/memory/{cid}")
    assert mem_res.status_code == 200
    memories = mem_res.json()
    assert any(m["memory_value"] == "Remote" for m in memories)
