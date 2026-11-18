# 🚀 CareerPilot AI — Autonomous Agentic Career Assistant

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red.svg)](https://streamlit.io)
[![Ollama](https://img.shields.io/badge/LLM-Llama_3.2_3B-purple.svg)](https://ollama.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**CareerPilot AI** is an intelligent, autonomous career copilot designed to empower candidates with deep job market insights, automated resume parsing, transparent multi-factor job matching, personalized skill gap diagnostics, tailored interview coaching, and agentic tool-assisted workflows.

Built strictly with **free and open-source technologies**, CareerPilot AI runs entirely locally on CPU, requires **zero paid APIs or OpenAI keys**, and includes an integrated **offline deterministic fallback engine** that ensures 100% feature availability even when no local LLM is active.

---

## 📑 Table of Contents

- [Architectural Overview](#-architectural-overview)
- [Key Features & Modules](#-key-features--modules)
- [System Architecture](#-system-architecture)
- [Quick Start Guide (Windows PowerShell)](#-quick-start-guide-windows-powershell)
- [Evaluation & Benchmark Results](#-evaluation--benchmark-results)
- [Technology Stack](#-technology-stack)
- [Application Modules Overview](#-application-modules-overview)
- [Docker Deployment](#-docker-deployment)
- [Documentation Suite](#-documentation-suite)

---

## 🏛️ Architectural Overview

CareerPilot AI avoids fragile, heavy third-party agent frameworks in favor of a clean, testable, and robust Python architecture:

```
                                  ┌───────────────────────────┐
                                  │   Streamlit Web UI (8501) │
                                  │   12 Interactive Pages    │
                                  └─────────────┬─────────────┘
                                                │ REST API (JSON)
                                  ┌─────────────▼─────────────┐
                                  │   FastAPI Backend (8000)  │
                                  └─────────────┬─────────────┘
                ┌───────────────────────────────┼───────────────────────────────┐
                │                               │                               │
        ┌───────▼────────┐              ┌───────▼────────┐              ┌───────▼────────┐
        │  Agent Engine  │              │ Matching Scorer│              │ Resume Parser  │
        │ - Intent Router│              │ - 7-Factor Wtd │              │ - PyMuPDF      │
        │ - 12 Tool Exec │              │ - Gap Roadmap  │              │ - python-docx  │
        │ - LLM/Fallback │              │ - Hybrid Search│              │ - Regex & NER  │
        └───────┬────────┘              └───────┬────────┘              └───────┬────────┘
                │                               │                               │
                └───────────────────────────────┼───────────────────────────────┘
                                                │
                                  ┌─────────────▼─────────────┐
                                  │ SQLAlchemy 2.0 ORM Engine │
                                  │  SQLite Database Storage  │
                                  └───────────────────────────┘
```

---

## ✨ Key Features & Modules

1. **📄 Candidate Profile & Resume Ingestion (Module A):**
   - Supports PDF, DOCX, and TXT resume uploads.
   - Extracts contact details, education, degree, experience years, and technical skills with canonical capitalization.
   - Pydantic v2 schema validation with complete candidate privacy isolation.

2. **🗄️ Job Database & Ingestion (Module B):**
   - 250+ realistic job records across 10 domains (AI Engineer, ML Engineer, Python Dev, Data Engineer, etc.).
   - CSV and JSON automated ingestion with duplicate detection and incremental indexing.

3. **💬 AI Career Assistant & Tool Orchestration (Modules C & D):**
   - Natural language conversation with multi-turn context retention.
   - **12 Registered Agent Tools** with strict Pydantic argument validation and irreversible action safety checks.
   - Full audit logging of all executed tools in SQLite.

4. **⚖️ Transparent Multi-Factor Matching (Module E):**
   - 7-factor deterministic scoring algorithm: Required Skills (35%), Preferred Skills (15%), Experience Fit (15%), Role Fit (15%), Work Mode (10%), Location Fit (5%), Interests (5%).
   - Explicit scoring rationale: no black-box arbitrary scores.

5. **⭐ Personalized Recommendations & Feedback Loop (Module F):**
   - Ranked recommendation feed with dynamic feedback weighting (+1.1x boost for relevant, 0.7x weight for not relevant).

6. **🧠 Persistent Candidate Memory (Module G):**
   - SQLite-backed memory store capturing preferences, constraints, and career goals across sessions.

7. **💡 Role-Specific Interview Preparation (Module H):**
   - Generates technical questions, project defense queries, and behavioral questions with structured **STAR answer frameworks**.
   - One-click export of interview checklists into actionable tasks.

8. **📋 Application Tracker & Task Pipeline (Module I):**
   - Multi-stage pipeline (Interested, Saved, Preparing, Applied, Interview Scheduled, Offer Received, Rejected).
   - Priority task manager with due dates and completion tracking.

---

## 🚀 Quick Start Guide (Windows PowerShell)

### Prerequisites
- **Operating System:** Windows 10 or 11
- **Python:** Python 3.10+ (Check via `python --version`)
- **RAM:** 8 GB minimum (16 GB recommended)
- **Optional Local LLM:** [Ollama](https://ollama.com) with model `llama3.2:3b`

### Step 1: Open PowerShell and Navigate to Project
```powershell
cd "careerpilot-ai"
```

### Step 2: Run Automated Environment Check
```powershell
.\scripts\check_environment.ps1
```

### Step 3: Run Initial Setup & Dependency Installation
```powershell
.\scripts\setup.ps1
```
*This installs all required packages, initializes the SQLite database, and populates the 250-record job catalogue.*

### Step 4 (Optional): Download Local LLM Model
```powershell
.\scripts\download_models.ps1
```
*If Ollama is not installed or running, CareerPilot AI will automatically utilize its offline deterministic fallback engine with 0 configuration.*

### Step 5: Launch CareerPilot AI
```powershell
.\scripts\start.ps1
```
- **Streamlit Web UI:** [http://localhost:8501](http://localhost:8501)
- **FastAPI Backend Swagger Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 📊 Evaluation & Benchmark Results

CareerPilot AI has been rigorously benchmarked using automated quantitative evaluation suites across candidate retrieval, tool selection, and resume entity extraction:

| Metric | Target | Measured Result | Status |
| :--- | :---: | :---: | :---: |
| **Search Precision@3** | $\ge 80.0\%$ | **100.0%** | ✅ PASSED |
| **Search Precision@5** | $\ge 75.0\%$ | **100.0%** | ✅ PASSED |
| **Mean Reciprocal Rank (MRR)** | $\ge 0.85$ | **1.0000** | ✅ PASSED |
| **Agent Tool Selection Accuracy** | $\ge 85.0\%$ | **90.0%** | ✅ PASSED |
| **Resume Name Extraction** | $\ge 90.0\%$ | **100.0%** | ✅ PASSED |
| **Resume Email Extraction** | $\ge 95.0\%$ | **100.0%** | ✅ PASSED |
| **Resume Degree Extraction** | $\ge 85.0\%$ | **100.0%** | ✅ PASSED |
| **Resume Technical Skill F1** | $\ge 80.0\%$ | **91.07%** | ✅ PASSED |

Run the benchmarks yourself anytime:
```powershell
.\scripts\run_tests.ps1
```

---

## 🛠️ Technology Stack

| Layer | Component | Description |
| :--- | :--- | :--- |
| **Backend** | FastAPI + Uvicorn | High-performance asynchronous REST API with OpenAPI documentation |
| **Database** | SQLite + SQLAlchemy 2.0 | Zero-configuration local relational database with ACID compliance |
| **Frontend** | Streamlit + Plotly | Interactive reactive web dashboard with dynamic data visualizations |
| **AI / Inference**| Ollama (`llama3.2:3b`) | Lightweight local CPU-friendly LLM with deterministic offline fallback |
| **Embeddings** | Sentence Transformers | Local sentence-transformers/all-MiniLM-L6-v2 + TF-IDF Vectorizer |
| **Document Parsing**| PyMuPDF + python-docx | Text and metadata extraction for PDF, DOCX, and TXT resumes |
| **Testing** | pytest + TestClient | Complete 20/20 test suite covering endpoints, tools, and matching |

---

## 🐳 Docker Deployment

To build and run CareerPilot AI in isolated containers:

```bash
docker-compose up --build
```
Access the Streamlit web dashboard at `http://localhost:8501`.

---

## 📚 Documentation Suite

Comprehensive technical guides are available in the [`docs/`](docs/) directory:

- [**Architecture Guide**](docs/ARCHITECTURE.md) — Detailed layer interactions, agent loop, and vector search design.
- [**Database Design**](docs/DATABASE_DESIGN.md) — Complete ER diagrams, schemas for all 14 tables, and indexing strategy.
- [**API Documentation**](docs/API_DOCUMENTATION.md) — Complete REST endpoint reference with request/response schemas.
- [**Agent Workflow & Tool Guide**](docs/AGENT_WORKFLOW.md) — Tool execution protocol, validation rules, and audit logging.
- [**Setup & Troubleshooting Guide**](docs/SETUP_GUIDE.md) — Step-by-step Windows setup and common configuration solutions.
- [**Interview & Technical Concepts Guide**](docs/INTERVIEW_PREPARATION.md) — In-depth explanations of LLMs, agent tool calling, CPU optimization, and deterministic algorithms.
- [**Evaluation Benchmark Report**](docs/EVALUATION_REPORT.md) — Quantitative metrics, methodology, and test cases.

---

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).
