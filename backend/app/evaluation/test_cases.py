from typing import List, Dict, Any, Set

# Evaluation queries for search & ranking evaluation
SEARCH_BENCHMARK_CASES: List[Dict[str, Any]] = [
    {
        "query": "AI Engineer PyTorch",
        "target_category": "AI Engineer",
        "required_keyword": "Python",
    },
    {
        "query": "Remote Python Developer FastAPI",
        "target_category": "Python Developer",
        "required_keyword": "Python",
    },
    {
        "query": "Machine Learning Engineer Scikit-Learn",
        "target_category": "Machine Learning Engineer",
        "required_keyword": "Python",
    },
    {
        "query": "Data Analyst SQL Tableau",
        "target_category": "Data Analyst",
        "required_keyword": "SQL",
    },
    {
        "query": "Data Engineer Spark Kafka",
        "target_category": "Data Engineer",
        "required_keyword": "Python",
    },
    {
        "query": "Automation Engineer Selenium n8n",
        "target_category": "Automation Engineer",
        "required_keyword": "n8n",
    },
    {
        "query": "Backend Developer PostgreSQL REST",
        "target_category": "Backend Developer",
        "required_keyword": "PostgreSQL",
    },
    {
        "query": "Software Engineer Java Algorithms",
        "target_category": "Software Engineer",
        "required_keyword": "Java",
    }
]

# Benchmark for tool selection accuracy
TOOL_INTENT_BENCHMARK_CASES: List[Dict[str, Any]] = [
    {
        "message": "Find me remote AI Engineer internships",
        "expected_tool": "search_jobs"
    },
    {
        "message": "Search for Python backend positions in Austin",
        "expected_tool": "search_jobs"
    },
    {
        "message": "Show me my saved jobs",
        "expected_tool": "get_saved_jobs"
    },
    {
        "message": "Save this job opportunity to my list",
        "expected_tool": "save_job"
    },
    {
        "message": "Compare this job with my candidate profile",
        "expected_tool": "compare_job_with_candidate"
    },
    {
        "message": "What skills am I missing for this AI role?",
        "expected_tool": "identify_skill_gaps"
    },
    {
        "message": "What should I learn next to improve my match score?",
        "expected_tool": "identify_skill_gaps"
    },
    {
        "message": "Prepare interview questions for this position",
        "expected_tool": "generate_interview_questions"
    },
    {
        "message": "What application tasks do I need to complete?",
        "expected_tool": "get_application_tasks"
    },
    {
        "message": "Show my candidate profile and verified skills",
        "expected_tool": "get_candidate_profile"
    }
]

# Benchmark for resume parsing accuracy
RESUME_PARSING_BENCHMARK_CASES: List[Dict[str, Any]] = [
    {
        "text": """
        Priya Sharma
        priya.sharma@example.edu | +1 (555) 901-2345
        Education:
        Bachelor of Technology in Computer Engineering, National Institute of Technology
        Skills: Python, PyTorch, SQL, FastAPI, Docker, Kubernetes, Large Language Models
        Experience:
        6 months AI research intern developing RAG applications.
        """,
        "expected_name": "Priya Sharma",
        "expected_email": "priya.sharma@example.edu",
        "expected_degree": "Bachelor's Degree",
        "expected_skills": ["Python", "PyTorch", "SQL", "FastAPI", "Docker", "Kubernetes", "Large Language Models"]
    },
    {
        "text": """
        David Chen
        david.chen@datascience.org
        Education:
        Master of Science in Data Science, Columbia University
        Technical Competencies:
        Python, Scikit-Learn, Pandas, NumPy, SQL, Tableau, Power BI, Statistics
        Projects:
        Built a predictive customer churn model with 88% precision using XGBoost and Pandas.
        """,
        "expected_name": "David Chen",
        "expected_email": "david.chen@datascience.org",
        "expected_degree": "Master's Degree",
        "expected_skills": ["Python", "Scikit-Learn", "Pandas", "NumPy", "SQL", "Tableau", "Power BI"]
    },
    {
        "text": """
        Amina Al-Mansoor
        amina.mansoor@automation.io
        Education:
        Bachelor of Science in Software Engineering
        Skills: Python, Selenium, n8n, Git, CI/CD, Linux, Docker, REST APIs
        Summary:
        Automation specialist with experience designing webhooks and workflow triggers.
        """,
        "expected_name": "Amina Al-Mansoor",
        "expected_email": "amina.mansoor@automation.io",
        "expected_degree": "Bachelor's Degree",
        "expected_skills": ["Python", "Selenium", "n8n", "Git", "Linux", "Docker", "REST APIs"]
    }
]
