import os
import requests
from typing import Optional, Dict, Any, List

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8005")

class APIClient:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        try:
            resp = requests.get(f"{self.base_url}{endpoint}", params=params, timeout=25)
            if resp.status_code in [200, 201]:
                return resp.json()
            return None
        except Exception:
            return None

    def _post(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None, files: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None) -> Any:
        try:
            resp = requests.post(f"{self.base_url}{endpoint}", json=json_data, params=params, files=files, data=data, timeout=60)
            if resp.status_code in [200, 201]:
                return resp.json()
            return None
        except Exception:
            return None

    def _put(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None) -> Any:
        try:
            resp = requests.put(f"{self.base_url}{endpoint}", json=json_data, timeout=25)
            if resp.status_code in [200, 201]:
                return resp.json()
            return None
        except Exception:
            return None

    def _delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> bool:
        try:
            resp = requests.delete(f"{self.base_url}{endpoint}", params=params, timeout=25)
            return resp.status_code in [200, 204]
        except Exception:
            return False

    # Health
    def get_health(self) -> Dict[str, Any]:
        res = self._get("/health")
        if res:
            return res
        return {
            "status": "offline",
            "database_connected": False,
            "llm_service": {"status": "offline", "model": "llama3.2:3b", "is_fallback": True}
        }

    # Candidates
    def get_active_candidate(self) -> Optional[Dict[str, Any]]:
        return self._get("/api/candidates/active")

    def list_candidates(self) -> List[Dict[str, Any]]:
        res = self._get("/api/candidates")
        return res if res else []

    def get_candidate(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        return self._get(f"/api/candidates/{candidate_id}")

    def create_candidate(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self._post("/api/candidates", json_data=payload)

    def update_candidate(self, candidate_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self._put(f"/api/candidates/{candidate_id}", json_data=payload)

    def add_skill(self, candidate_id: str, skill_name: str, category: str = "General", proficiency: str = "Intermediate") -> Optional[Dict[str, Any]]:
        return self._post(f"/api/candidates/{candidate_id}/skills", json_data={
            "skill_name": skill_name,
            "category": category,
            "proficiency": proficiency
        })

    def remove_skill(self, candidate_id: str, skill_id: int) -> bool:
        return self._delete(f"/api/candidates/{candidate_id}/skills/{skill_id}")

    # Resumes
    def upload_resume(self, candidate_id: str, file_name: str, file_bytes: bytes) -> Optional[Dict[str, Any]]:
        files = {"file": (file_name, file_bytes)}
        data = {"candidate_id": candidate_id}
        return self._post("/api/resumes/upload", files=files, data=data)

    def list_resumes(self, candidate_id: str) -> List[Dict[str, Any]]:
        res = self._get(f"/api/resumes/{candidate_id}/list")
        return res if res else []

    def delete_resume(self, resume_id: str) -> bool:
        return self._delete(f"/api/resumes/{resume_id}")

    # Jobs
    def get_jobs(
        self,
        query: Optional[str] = None,
        role_category: Optional[str] = None,
        experience_level: Optional[str] = None,
        work_mode: Optional[str] = None,
        location: Optional[str] = None,
        min_salary: Optional[int] = None,
        page: int = 1,
        page_size: int = 12
    ) -> Dict[str, Any]:
        params = {
            "query": query,
            "role_category": role_category,
            "experience_level": experience_level,
            "work_mode": work_mode,
            "location": location,
            "min_salary": min_salary,
            "page": page,
            "page_size": page_size
        }
        # filter out None
        clean_params = {k: v for k, v in params.items() if v is not None and v != ""}
        res = self._get("/api/jobs", params=clean_params)
        return res if res else {"total": 0, "page": page, "page_size": page_size, "items": []}

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        return self._get(f"/api/jobs/{job_id}")

    def save_job(self, candidate_id: str, job_id: str, notes: Optional[str] = None) -> bool:
        res = self._post(f"/api/jobs/{job_id}/save", params={"candidate_id": candidate_id, "notes": notes})
        return bool(res)

    def remove_saved_job(self, candidate_id: str, job_id: str) -> bool:
        return self._delete(f"/api/jobs/{job_id}/save", params={"candidate_id": candidate_id})

    def get_saved_jobs(self, candidate_id: str) -> List[Dict[str, Any]]:
        res = self._get(f"/api/jobs/saved/{candidate_id}")
        return res if res else []

    def submit_job_feedback(self, candidate_id: str, job_id: str, feedback: str, notes: Optional[str] = None) -> bool:
        res = self._post(f"/api/jobs/{job_id}/feedback", params={"candidate_id": candidate_id}, json_data={"feedback": feedback, "notes": notes})
        return bool(res)

    def import_sample_jobs(self) -> Dict[str, Any]:
        res = self._post("/api/jobs/import/sample")
        return res if res else {"message": "Failed to trigger import"}

    # Matching & Recommendations
    def get_recommendations(self, candidate_id: str, limit: int = 10, min_score: float = 30.0) -> Dict[str, Any]:
        res = self._get(f"/api/matching/{candidate_id}/recommendations", params={"limit": limit, "min_score": min_score})
        return res if res else {"candidate_id": candidate_id, "total_evaluated": 0, "recommendations": []}

    def compare_job(self, candidate_id: str, job_id: str) -> Optional[Dict[str, Any]]:
        return self._get(f"/api/matching/{candidate_id}/compare/{job_id}")

    def get_skill_gaps(self, candidate_id: str, job_id: str) -> Optional[Dict[str, Any]]:
        return self._get(f"/api/matching/{candidate_id}/skill-gaps/{job_id}")

    # Agent Chat
    def send_chat_message(self, candidate_id: str, message: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        payload = {
            "candidate_id": candidate_id,
            "message": message,
            "conversation_id": conversation_id
        }
        res = self._post("/api/agent/chat", json_data=payload)
        if res:
            return res
        return {
            "message": "Error connecting to AI Assistant service. Please verify backend is running.",
            "tool_calls": [],
            "source": "fallback",
            "conversation_id": conversation_id or "default"
        }

    def get_chat_history(self, candidate_id: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
        res = self._get(f"/api/agent/history/{candidate_id}", params={"conversation_id": conversation_id})
        return res if res else {"conversation_id": conversation_id or "default", "title": "New Chat", "messages": []}

    def get_agent_tools(self) -> List[Dict[str, Any]]:
        res = self._get("/api/agent/tools")
        if res and "tools" in res:
            return res["tools"]
        return []

    # Application Tracker
    def get_applications(self, candidate_id: str, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {"status_filter": status_filter} if status_filter else None
        res = self._get(f"/api/applications/{candidate_id}", params=params)
        return res if res else []

    def create_application(self, candidate_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self._post("/api/applications", params={"candidate_id": candidate_id}, json_data=payload)

    def update_application(self, application_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self._put(f"/api/applications/{application_id}", json_data=payload)

    def delete_application(self, application_id: str) -> bool:
        return self._delete(f"/api/applications/{application_id}")

    def get_tasks(self, candidate_id: str, is_completed: Optional[bool] = None) -> List[Dict[str, Any]]:
        params = {"is_completed": is_completed} if is_completed is not None else None
        res = self._get(f"/api/applications/tasks/{candidate_id}", params=params)
        return res if res else []

    def create_task(self, candidate_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self._post("/api/applications/tasks", params={"candidate_id": candidate_id}, json_data=payload)

    def update_task(self, task_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self._put(f"/api/applications/tasks/{task_id}", json_data=payload)

    # Interview Prep
    def generate_interview(self, candidate_id: str, job_id: str) -> Optional[Dict[str, Any]]:
        return self._post("/api/interview/generate", json_data={"candidate_id": candidate_id, "job_id": job_id})

    # Memory & Preferences
    def get_memories(self, candidate_id: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {"category": category} if category else None
        res = self._get(f"/api/memory/{candidate_id}", params=params)
        return res if res else []

    def create_memory(self, candidate_id: str, key: str, value: str, category: str = "preference", confidence: float = 1.0) -> Optional[Dict[str, Any]]:
        payload = {"key": key, "value": value, "category": category, "confidence": confidence}
        return self._post(f"/api/memory/{candidate_id}", json_data=payload)

    def delete_memory(self, memory_id: str) -> bool:
        return self._delete(f"/api/memory/item/{memory_id}")

api = APIClient()
