import csv
import random
from pathlib import Path

categories = [
    ("AI Engineer", ["Python", "PyTorch", "TensorFlow", "LLM", "RAG", "LangChain", "HuggingFace", "FastAPI"], ["Docker", "Kubernetes", "AWS", "Vector Databases", "Prompt Engineering"]),
    ("Machine Learning Engineer", ["Python", "Scikit-Learn", "PyTorch", "Pandas", "NumPy", "SQL"], ["MLOps", "Docker", "GCP", "Kafka", "Airflow"]),
    ("Python Developer", ["Python", "Django", "FastAPI", "PostgreSQL", "Git", "REST APIs"], ["Docker", "Redis", "Celery", "AWS", "Linux"]),
    ("Data Analyst", ["SQL", "Excel", "Tableau", "Power BI", "Python", "Data Visualization"], ["Pandas", "Statistics", "R", "Snowflake", "BigQuery"]),
    ("Data Engineer", ["Python", "SQL", "Apache Spark", "Kafka", "PostgreSQL", "Airflow"], ["Snowflake", "dbt", "AWS", "Docker", "Kubernetes"]),
    ("Software Engineer", ["Java", "Python", "C++", "Git", "Data Structures", "Algorithms"], ["Docker", "CI/CD", "Microservices", "Spring Boot", "Linux"]),
    ("Backend Developer", ["Node.js", "Go", "Python", "PostgreSQL", "Docker", "REST APIs"], ["Kubernetes", "Redis", "GraphQL", "AWS", "gRPC"]),
    ("Automation Engineer", ["Python", "Selenium", "n8n", "Bash", "Git", "CI/CD"], ["Docker", "Jenkins", "REST APIs", "Postman", "Linux"]),
    ("Business Analyst", ["Agile", "SQL", "Excel", "User Stories", "Jira", "Process Mapping"], ["Tableau", "Product Management", "Data Modeling", "Python"]),
    ("Product Support Engineer", ["Troubleshooting", "SQL", "Linux", "Customer Communication", "REST APIs"], ["Python", "Bash", "Postman", "Jira", "Networking"])
]

companies = [
    "Synthetix AI", "Apex Data Systems", "Vanguard Robotics", "NovaTech Solutions", "Cognitive Cloud",
    "Helix Analytics", "Pinnacle Software", "Hyperion Tech", "Starlight Data", "Quantum Automations",
    "BlueShift AI", "CipherWave Labs", "Aegis Security Tech", "Zenith Digital", "Orion Cloud Services",
    "Veritas AI Labs", "Beacon Systems", "Matrix Stream", "Prism AI", "Vector Dynamics",
    "DeepPulse Tech", "NeuralForge", "Skyline Digital", "EchoLogic AI", "Frontier Systems"
]

locations = ["Remote", "San Francisco, CA", "New York, NY", "Austin, TX", "Seattle, WA", "Boston, MA", "Chicago, IL", "London, UK", "Bengaluru, India", "Toronto, Canada"]
work_modes = ["Remote", "Hybrid", "On-site"]

rows = []
job_idx = 1
random.seed(42)

for cat_name, req_pool, pref_pool in categories:
    # 25 jobs per category = 250 jobs total
    for i in range(25):
        comp = companies[i % len(companies)]
        emp_type = "Internship" if i < 6 else ("Full-time" if i < 20 else "Contract")
        exp_lvl = "Internship" if emp_type == "Internship" else ("Entry-level" if i < 12 else ("Mid-level" if i < 20 else "Senior"))
        exp_years = 0.0 if exp_lvl in ["Internship", "Entry-level"] else (2.0 if exp_lvl == "Mid-level" else 5.0)
        wm = "Remote" if i % 2 == 0 else random.choice(work_modes)
        loc = "Remote" if wm == "Remote" else random.choice(locations[1:])
        
        prefix = "Intern " if emp_type == "Internship" else ("" if exp_lvl == "Entry-level" else ("Senior " if exp_lvl == "Senior" else ""))
        title = f"{prefix}{cat_name}"
        if i >= len(companies):
            title = f"{title} (Team {chr(65 + i % 5)})"

        req_skills = random.sample(req_pool, k=min(4, len(req_pool)))
        pref_skills = random.sample(pref_pool, k=min(3, len(pref_pool)))
        
        sal_min = 35000 if emp_type == "Internship" else (75000 if exp_lvl == "Entry-level" else (110000 if exp_lvl == "Mid-level" else 145000))
        sal_max = sal_min + random.choice([15000, 25000, 35000])
        
        desc = (
            f"Join {comp} as an {title}. You will design, develop, and deploy robust scalable systems using "
            f"{req_skills[0]} and {req_skills[1]}, collaborating with cross-functional product and engineering teams "
            f"to solve high-impact technical challenges."
        )
        
        rows.append({
            "job_id": f"JOB-{job_idx:03d}",
            "company": comp,
            "title": title,
            "role_category": cat_name,
            "description": desc,
            "required_skills": ", ".join(req_skills),
            "preferred_skills": ", ".join(pref_skills),
            "experience_level": exp_lvl,
            "experience_years_min": exp_years,
            "location": loc,
            "work_mode": wm,
            "employment_type": emp_type,
            "salary_min": sal_min,
            "salary_max": sal_max,
            "salary_currency": "USD",
            "application_url": f"https://demo-careers.example.org/jobs/job-{job_idx:03d}",
            "is_synthetic": True,
            "date_posted": "2026-11-10"
        })
        job_idx += 1

output_path = Path(__file__).resolve().parent.parent / "data" / "sample_jobs.csv"
output_path.parent.mkdir(parents=True, exist_ok=True)

with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows)} unique job records successfully at {output_path}")
