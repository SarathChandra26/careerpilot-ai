import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import pymupdf  # PyMuPDF
import docx
from app.schemas.candidate import ResumeParsedData

# Canonical skill casing mapping
CANONICAL_SKILLS: Dict[str, str] = {
    "python": "Python",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "django": "Django",
    "react": "React",
    "vue": "Vue",
    "angular": "Angular",
    "node.js": "Node.js",
    "express": "Express",
    "scikit-learn": "Scikit-Learn",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "scipy": "SciPy",
    "langchain": "LangChain",
    "llama-index": "LlamaIndex",
    "huggingface": "HuggingFace",
    "transformers": "Transformers",
    "opencv": "OpenCV",
    "streamlit": "Streamlit",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "java": "Java",
    "c++": "C++",
    "c#": "C#",
    "go": "Go",
    "golang": "Go",
    "rust": "Rust",
    "r": "R",
    "sql": "SQL",
    "html": "HTML",
    "css": "CSS",
    "bash": "Bash",
    "shell": "Shell",
    "powershell": "PowerShell",
    "git": "Git",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "aws": "AWS",
    "azure": "Azure",
    "gcp": "GCP",
    "linux": "Linux",
    "postgresql": "PostgreSQL",
    "mysql": "MySQL",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "sqlite": "SQLite",
    "elasticsearch": "Elasticsearch",
    "kafka": "Kafka",
    "rabbitmq": "RabbitMQ",
    "n8n": "n8n",
    "airflow": "Airflow",
    "jira": "Jira",
    "postman": "Postman",
    "chromadb": "ChromaDB",
    "faiss": "FAISS",
    "tableau": "Tableau",
    "power bi": "Power BI",
    "excel": "Excel",
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "nlp": "NLP",
    "natural language processing": "NLP",
    "computer vision": "Computer Vision",
    "large language models": "Large Language Models",
    "llm": "Large Language Models",
    "rag": "RAG",
    "prompt engineering": "Prompt Engineering",
    "agentic ai": "Agentic AI",
    "data science": "Data Science",
    "data engineering": "Data Engineering",
    "generative ai": "Generative AI",
}

class ResumeParserService:
    @staticmethod
    def extract_text_from_file(file_path: str, file_type: str) -> str:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Resume file not found at {file_path}")

        ext = file_type.lower().replace(".", "")
        if ext == "pdf":
            text = ""
            doc = pymupdf.open(str(path))
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
            return text.strip()
        elif ext in ["docx", "doc"]:
            doc = docx.Document(str(path))
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        full_text.append(cell.text)
            return "\n".join(full_text).strip()
        elif ext == "txt":
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read().strip()
        else:
            raise ValueError(f"Unsupported resume format: {ext}. Allowed: PDF, DOCX, TXT")

    @classmethod
    def parse_resume_content(cls, raw_text: str) -> ResumeParsedData:
        sanitized_text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', raw_text)
        lines = [line.strip() for line in sanitized_text.splitlines() if line.strip()]

        # Email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', sanitized_text)
        email = email_match.group(0).lower() if email_match else None

        # Phone
        phone_match = re.search(
            r'(\+?\d{1,3}[-.\s]?)?(\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}',
            sanitized_text
        )
        phone = phone_match.group(0).strip() if phone_match else None

        # Name
        name = None
        for line in lines[:5]:
            if "@" in line or "http" in line or any(char.isdigit() for char in line):
                continue
            if len(line.split()) in [2, 3, 4] and len(line) < 40:
                name = line.strip().title()
                break

        # Degree & Education
        education = None
        degree = None
        degree_patterns = [
            (r'\b(bachelor(\'s)?|b\.?tech|b\.?e|b\.?s|bca)\b', "Bachelor's Degree"),
            (r'\b(master(\'s)?|m\.?tech|m\.?e|m\.?s|mca|mba)\b', "Master's Degree"),
            (r'\b(ph\.?d|doctorate)\b', "Ph.D."),
            (r'\b(diploma|associate(\'s)?)\b', "Associate / Diploma")
        ]
        text_lower = sanitized_text.lower()
        for pattern, deg_name in degree_patterns:
            if re.search(pattern, text_lower):
                degree = deg_name
                break

        edu_match = re.search(
            r'([A-Za-z\s]+(University|Institute|College|Academy|School)[\w\s,]*)',
            sanitized_text,
            re.IGNORECASE
        )
        if edu_match:
            education = edu_match.group(0).strip().splitlines()[0]

        # Extract Skills
        extracted_skills = set()
        extracted_tech = set()
        extracted_tools = set()

        for skill_key, canonical in CANONICAL_SKILLS.items():
            pattern = r'\b' + re.escape(skill_key) + r'\b'
            if re.search(pattern, text_lower):
                extracted_skills.add(canonical)
                if skill_key in ["python", "javascript", "typescript", "java", "c++", "c#", "go", "sql"]:
                    extracted_tech.add(canonical)
                elif skill_key in ["docker", "kubernetes", "aws", "git", "linux", "tableau", "power bi", "n8n"]:
                    extracted_tools.add(canonical)

        # Extract Sections
        projects = []
        experience = []
        certifications = []

        current_section = None
        for line in lines:
            lower_line = line.lower()
            if any(h in lower_line for h in ["project", "academic projects", "key projects"]):
                current_section = "projects"
                continue
            elif any(h in lower_line for h in ["experience", "work history", "employment", "internship"]):
                current_section = "experience"
                continue
            elif any(h in lower_line for h in ["certification", "certificates", "licenses"]):
                current_section = "certifications"
                continue
            elif any(h in lower_line for h in ["education", "skills", "interests", "summary", "awards"]):
                current_section = None
                continue

            if current_section == "projects" and len(line) > 15:
                if len(projects) < 5:
                    projects.append(line)
            elif current_section == "experience" and len(line) > 15:
                if len(experience) < 5:
                    experience.append(line)
            elif current_section == "certifications" and len(line) > 10:
                if len(certifications) < 5:
                    certifications.append(line)

        interests = []
        if any(s in extracted_skills for s in ["Machine Learning", "Deep Learning", "PyTorch", "TensorFlow", "Large Language Models", "RAG"]):
            interests.append("AI / Machine Learning")
        if any(s in extracted_skills for s in ["FastAPI", "Django", "Flask", "SQL", "PostgreSQL", "Node.js"]):
            interests.append("Backend Development")
        if any(s in extracted_skills for s in ["React", "Vue", "JavaScript", "TypeScript"]):
            interests.append("Full-Stack / Frontend")
        if any(s in extracted_skills for s in ["Docker", "Kubernetes", "AWS", "GCP", "Linux"]):
            interests.append("Cloud / DevOps")

        return ResumeParsedData(
            full_name=name,
            email=email,
            phone=phone,
            education=education,
            degree=degree,
            skills=sorted(list(extracted_skills)),
            technical_skills=sorted(list(extracted_tech)),
            tools_and_frameworks=sorted(list(extracted_tools)),
            projects=projects,
            work_experience=experience,
            certifications=certifications,
            career_interests=interests,
            raw_summary=sanitized_text[:500] if sanitized_text else None,
        )
