# 🤖 CareerPilot AI — Agent Workflow & Tool Execution Specification

## 1. Agent Architecture Philosophy

CareerPilot AI explicitly avoids large, opaque agent frameworks (such as LangChain or AutoGen) in favor of a clean, testable **Python-first Agent Orchestrator**. 

The benefits of this architecture include:
- **Zero Hallucinated Tool Executions:** Tools execute real Python functions with strictly validated arguments, rather than the LLM simply pretending an action occurred.
- **Strict Pydantic Validation:** Every tool argument is checked against a typed Pydantic v2 schema prior to execution.
- **Auditability:** Every tool invocation, its input arguments, execution duration, and results are persisted in SQLite (`agent_tool_logs`).
- **Resilient Fallback:** If Ollama is offline, the Intent Detector and Deterministic Orchestrator execute the exact same tool and return verified results.

---

## 2. The 12 Implemented Agent Tools

| # | Tool Name | Description | Requires Confirmation |
| :-: | :--- | :--- | :-: |
| 1 | `search_jobs` | Searches catalogue by query, role category, work mode, and experience tier | No |
| 2 | `get_candidate_profile` | Retrieves candidate profile, skills, education, and target roles | No |
| 3 | `update_candidate_preferences` | Updates preferred roles, work mode, locations, and salary range | No |
| 4 | `compare_job_with_candidate` | Performs 7-factor match comparison between candidate and job | No |
| 5 | `save_job` | Bookmarks an opportunity in the candidate's saved list | No |
| 6 | `remove_saved_job` | Removes an opportunity from the saved list | No |
| 7 | `get_saved_jobs` | Retrieves all opportunities bookmarked by the candidate | No |
| 8 | `create_application_task` | Creates a preparation task linked to a job application | No |
| 9 | `get_application_tasks` | Retrieves active or completed preparation checklist items | No |
| 10 | `update_application_status` | Updates the candidate's lifecycle stage for a job vacancy | No |
| 11 | `generate_interview_questions` | Generates technical, project, and STAR behavioral questions | No |
| 12 | `identify_skill_gaps` | Identifies missing required skills and generates learning roadmap | No |

---

## 3. Tool Schemas & Pydantic Definitions

Every tool has a corresponding Pydantic schema in `backend/app/tools/schemas.py`. For example:

```python
class SearchJobsArgs(BaseModel):
    query: Optional[str] = Field(None, description="Keywords or role title")
    role_category: Optional[str] = Field(None, description="Domain category")
    work_mode: Optional[str] = Field(None, description="Remote, Hybrid, or On-site")
    experience_level: Optional[str] = Field(None, description="Internship, Entry-Level, Mid-Level, Senior")
    limit: int = Field(5, ge=1, le=20, description="Maximum results to return")

class SaveJobArgs(BaseModel):
    candidate_id: str = Field(..., description="Target candidate ID")
    job_id: str = Field(..., description="Job identifier to save")
    notes: Optional[str] = Field(None, description="Optional personal notes")
```

---

## 4. End-to-End Execution Trace

### Example User Request:
> *"Find me suitable AI Engineer internships. I know Python, SQL, Machine Learning and n8n. I prefer remote opportunities."*

### Step 1: Intent & Parameter Extraction
The orchestrator detects:
- **Primary Intent:** `search_jobs`
- **Extracted Role:** `"AI Engineer"`
- **Extracted Work Mode:** `"Remote"`
- **Extracted Experience Level:** `"Internship"`
- **Preference Update Trigger:** The user explicitly stated *"I prefer remote opportunities"*. The orchestrator schedules a preference update task.

### Step 2: Tool Execution
The orchestrator instantiates `SearchJobsArgs(query="AI Engineer", work_mode="Remote", experience_level="Internship", limit=5)` and invokes the `search_jobs` tool implementation:
```
[TOOL CALL]: search_jobs(query='AI Engineer', work_mode='Remote', experience_level='Internship', limit=5)
[TOOL RESULT]: {
    "total_found": 18,
    "jobs": [
        {"id": "job_001", "title": "AI Research Engineer Intern", "company": "DeepMind Innovations", "work_mode": "Remote"},
        {"id": "job_004", "title": "Junior Machine Learning Engineer", "company": "Apex Dynamics", "work_mode": "Remote"}
    ]
}
```

### Step 3: Candidate Profiling & Match Ranking
The orchestrator retrieves candidate profile `c71e99c1...`, checks skills against each job's requirements, and computes the 7-factor match score.

### Step 4: Audit Logging
The action is recorded in `agent_tool_logs`:
```sql
INSERT INTO agent_tool_logs (id, candidate_id, tool_name, arguments, result, execution_time_ms, success)
VALUES ('log_182f', 'c71e99c1...', 'search_jobs', '{"query":"AI Engineer",...}', '{"total_found":18,...}', 14.2, 1);
```

### Step 5: Final Response Synthesis
The orchestrator generates a comprehensive response explaining:
1. Which jobs matched and their respective match scores.
2. Why each opportunity is suitable based on the candidate's skills (`Python`, `Machine Learning`, `n8n`).
3. Which required skills are missing (e.g. `PyTorch`).
4. Actionable next steps: *"Would you like me to save Job #job_001 or prepare interview questions for it?"*
