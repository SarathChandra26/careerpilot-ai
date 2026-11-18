import io
import pytest
import pymupdf
import docx
from fastapi.testclient import TestClient
from app.main import app
from app.services.resume_parser import ResumeParserService

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_resume_parser_rule_extraction():
    sample_text = """
    Elena Rostova
    elena.rostova@techai.org | +1 415-555-0199
    San Francisco, CA
    
    Education:
    Bachelor of Science in Computer Science, Stanford University
    
    Technical Skills:
    Python, PyTorch, SQL, FastAPI, Docker, Kubernetes, Large Language Models, RAG
    
    Academic Projects:
    Built an agentic RAG pipeline for medical document search with ChromaDB and LangChain.
    """
    parsed = ResumeParserService.parse_resume_content(sample_text)
    assert parsed.full_name == "Elena Rostova"
    assert parsed.email == "elena.rostova@techai.org"
    assert parsed.degree == "Bachelor's Degree"
    assert "Python" in parsed.skills
    assert "PyTorch" in parsed.skills
    assert "SQL" in parsed.skills
    assert "Docker" in parsed.skills

def test_upload_txt_resume(client):
    active_cand = client.get("/api/candidates/active").json()
    cid = active_cand["id"]

    resume_content = (
        "Marcus Vance\n"
        "marcus.vance@career.io | (555) 345-6789\n\n"
        "Education:\n"
        "Master of Science in Machine Learning, Georgia Institute of Technology\n\n"
        "Skills:\n"
        "Python, TensorFlow, Scikit-Learn, SQL, n8n, Airflow\n"
    )

    files = {"file": ("resume.txt", io.BytesIO(resume_content.encode("utf-8")), "text/plain")}
    data = {"candidate_id": cid}

    res = client.post("/api/resumes/upload", data=data, files=files)
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["filename"] == "resume.txt"
    assert "Python" in res_data["parsed_data"]["skills"]
    assert "TensorFlow" in res_data["parsed_data"]["skills"]

def test_upload_pdf_resume(client):
    active_cand = client.get("/api/candidates/active").json()
    cid = active_cand["id"]

    # Generate a real PDF in memory with PyMuPDF
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text(
        pymupdf.Point(50, 72),
        "Samantha Reed\nsamantha.reed@example.com | 555-432-1098\n\n"
        "Bachelor of Science in Data Analytics\n\n"
        "Skills: Python, SQL, Tableau, Power BI, Excel, Pandas\n"
    )
    pdf_bytes = doc.tobytes()
    doc.close()

    files = {"file": ("samantha_resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    data = {"candidate_id": cid}

    res = client.post("/api/resumes/upload", data=data, files=files)
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["file_type"] == "pdf"
    assert "Tableau" in res_data["parsed_data"]["skills"]
    assert "Python" in res_data["parsed_data"]["skills"]

def test_upload_invalid_extension_rejected(client):
    active_cand = client.get("/api/candidates/active").json()
    cid = active_cand["id"]

    files = {"file": ("malicious.exe", io.BytesIO(b"binary content"), "application/octet-stream")}
    data = {"candidate_id": cid}

    res = client.post("/api/resumes/upload", data=data, files=files)
    assert res.status_code == 400
    assert "Unsupported format" in res.json()["detail"]
