# 🌐 CareerPilot AI — REST API Documentation

The CareerPilot AI backend exposes a REST API built on **FastAPI**.
Interactive OpenAPI documentation is hosted at:
- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`

---

## 1. System Health

### `GET /health`
Returns system status, database connectivity, and local LLM availability.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "app_name": "CareerPilot AI",
  "version": "1.0.0",
  "database_connected": true,
  "llm_service": {
    "status": "connected",
    "model": "llama3.2:3b",
    "is_fallback": false
  }
}
```

---

## 2. Candidates & Profiles

### `GET /api/candidates/active`
Retrieves the primary active candidate or initializes the default profile if empty.

**PowerShell Example:**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/candidates/active" -Method Get
```

**Response (200 OK):**
```json
{
  "id": "c71e99c1-8409-43c2-a89c-097bf1229a21",
  "full_name": "Alex Rivera",
  "email": "alex.rivera@example.com",
  "phone": "+1 (555) 234-5678",
  "education": "Bachelor of Science in Computer Science",
  "degree": "Bachelor's Degree",
  "experience_years": 0.5,
  "experience_level": "Internship",
  "preferred_roles": ["AI Engineer", "Python Developer"],
  "preferred_locations": ["Remote"],
  "preferred_work_mode": "Remote",
  "completeness_score": 95.0,
  "skills": [
    { "id": 1, "skill_name": "Python", "category": "Programming", "proficiency": "Advanced" },
    { "id": 2, "skill_name": "Machine Learning", "category": "AI/ML", "proficiency": "Intermediate" }
  ]
}
```

### `POST /api/candidates`
Registers a new candidate profile.

**Request Body:**
```json
{
  "full_name": "Jordan Lee",
  "email": "jordan.lee@example.com",
  "phone": "+1 (555) 987-6543",
  "education": "M.S. in Data Science",
  "degree": "Master's Degree",
  "experience_years": 3.0,
  "experience_level": "Mid-Level",
  "preferred_roles": ["Data Engineer", "Backend Developer"],
  "preferred_locations": ["Remote", "New York, NY"],
  "preferred_work_mode": "Remote"
}
```

---

## 3. Resume Upload & Processing

### `POST /api/resumes/upload`
Accepts `multipart/form-data` containing `candidate_id` and `file` (`.pdf`, `.docx`, `.txt`). Extracts entities and updates the candidate's verified profile.

**PowerShell Example:**
```powershell
$form = @{
    candidate_id = "c71e99c1-8409-43c2-a89c-097bf1229a21"
    file = Get-Item "C:\path\to\resume.pdf"
}
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/resumes/upload" -Method Post -Form $form
```

---

## 4. Job Search & Filtering

### `GET /api/jobs`
Searches and filters vacancies across query keywords, category, work mode, and experience tier.

**Query Parameters:**
- `query` (str, optional): Keyword or semantic query.
- `role_category` (str, optional): AI Engineer, Python Developer, etc.
- `work_mode` (str, optional): Remote, Hybrid, On-site.
- `experience_level` (str, optional): Internship, Entry-Level, etc.
- `min_salary` (int, optional): Minimum annual salary.
- `page` (int, default: 1): Page number.
- `page_size` (int, default: 10): Items per page.

**Response (200 OK):**
```json
{
  "total": 251,
  "page": 1,
  "page_size": 2,
  "items": [
    {
      "id": "job_001",
      "company": "DeepMind Innovations",
      "title": "AI Research Engineer Intern",
      "role_category": "AI Engineer",
      "work_mode": "Remote",
      "location": "Remote",
      "experience_level": "Internship",
      "salary_min": 75000,
      "salary_max": 95000,
      "skills": [
        { "skill_name": "Python", "is_required": true },
        { "skill_name": "PyTorch", "is_required": true },
        { "skill_name": "Machine Learning", "is_required": true }
      ]
    }
  ]
}
```

---

## 5. Matching & Recommendations

### `GET /api/matching/{candidate_id}/recommendations`
Calculates ranked recommendations using the 7-factor weighted algorithm.

**Query Parameters:**
- `limit` (int, default: 10)
- `min_score` (float, default: 30.0)

**Response (200 OK):**
```json
{
  "candidate_id": "c71e99c1-8409-43c2-a89c-097bf1229a21",
  "total_evaluated": 251,
  "recommendations": [
    {
      "job_id": "job_001",
      "title": "AI Research Engineer Intern",
      "company": "DeepMind Innovations",
      "overall_score": 85.5,
      "matched_skills": ["Python", "Machine Learning"],
      "missing_required_skills": ["PyTorch"],
      "missing_preferred_skills": ["Docker"],
      "explanation": "High match (85.5%). 2/3 required skills matched. Work mode and experience level perfectly aligned."
    }
  ]
}
```

---

## 6. AI Agent Chat

### `POST /api/agent/chat`
Conversational entry point for the agent orchestration loop. Automatically selects, validates, and executes tools.

**Request Body:**
```json
{
  "candidate_id": "c71e99c1-8409-43c2-a89c-097bf1229a21",
  "message": "Find me suitable AI Engineer internships. I know Python, SQL, Machine Learning and n8n. I prefer remote opportunities."
}
```

**Response (200 OK):**
```json
{
  "message": "I searched our database and identified 5 AI Engineer opportunities matching your profile...",
  "tool_calls": [
    {
      "tool_name": "search_jobs",
      "arguments": { "query": "AI Engineer", "work_mode": "Remote", "experience_level": "Internship" },
      "success": true
    }
  ],
  "source": "fallback",
  "conversation_id": "conv_92384a"
}
```

---

## 7. Interview Preparation

### `POST /api/interview/generate`
Generates technical questions, project defense questions, and STAR behavioral frameworks.

**Request Body:**
```json
{
  "candidate_id": "c71e99c1-8409-43c2-a89c-097bf1229a21",
  "job_id": "job_001"
}
```
