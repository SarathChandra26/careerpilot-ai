# 🛠️ CareerPilot AI — Complete Windows Setup & Troubleshooting Guide

This guide provides step-by-step instructions for installing, configuring, running, and troubleshooting CareerPilot AI on **Windows 10/11** using PowerShell.

---

## 1. System Requirements

- **Operating System:** Windows 10 or Windows 11 (64-bit)
- **Processor:** Intel Core i5 / i7 or AMD Ryzen 5 / 7 (CPU execution)
- **Memory (RAM):** 8 GB minimum, 16 GB recommended
- **Storage:** 5 GB free disk space (includes SQLite DB and optional local model)
- **Terminal:** Windows PowerShell 5.1+ or PowerShell 7

---

## 2. Step-by-Step Installation

### Step 1: Open Windows PowerShell
Press `Win + X` and select **Windows Terminal** or **Windows PowerShell**.

Navigate to your workspace directory:
```powershell
cd "E:\New folder (3)\careerpilot-ai"
```

### Step 2: (Optional) Configure Virtual Environment
While CareerPilot AI can run with your global Python 3.10+ environment, you can isolate dependencies:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*Note: If you receive a script execution error, run:*
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### Step 3: Run Automated Environment Check
Verify your Python version, packages, and system storage:
```powershell
.\scripts\check_environment.ps1
```

### Step 4: Run Initial Setup
Install all dependencies and seed the 250-record job catalogue:
```powershell
.\scripts\setup.ps1
```

---

## 3. Local LLM Setup (Ollama)

CareerPilot AI is designed to use **Ollama** running the lightweight `llama3.2:3b` model locally.

### Installing Ollama
1. Download and install Ollama for Windows from [https://ollama.com/download/windows](https://ollama.com/download/windows).
2. Once installed, download the default model:
   ```powershell
   .\scripts\download_models.ps1
   ```
   Or manually:
   ```powershell
   ollama pull llama3.2:3b
   ```
3. Start the Ollama server:
   ```powershell
   ollama serve
   ```

### ⚡ Offline Deterministic Fallback Mode
If you do not want to install Ollama or are on a constrained network, **CareerPilot AI functions completely offline**. 
The application includes an integrated deterministic rule engine that handles tool selection, job search, skill gap calculations, and interview questions without needing Ollama.

---

## 4. Running the Application

Launch both the backend and frontend simultaneously:
```powershell
.\scripts\start.ps1
```

Once running:
- **Streamlit Web Dashboard:** [http://localhost:8501](http://localhost:8501)
- **FastAPI REST API Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

To stop both servers, press `Ctrl + C` in your PowerShell terminal.

---

## 5. Running the Test Suite & Benchmarks

Verify system integrity:
```powershell
.\scripts\run_tests.ps1
```
This runs:
1. `pytest backend/tests -v` (20 unit and integration tests)
2. `app.evaluation.benchmark_runner` (Quantitative evaluation metrics)

---

## 6. Common Windows Troubleshooting

### 1. `Execution_Policies` Error in PowerShell
**Symptom:** `File ... cannot be loaded because running scripts is disabled on this system.`
**Solution:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### 2. Port 8000 or 8501 Already in Use
**Symptom:** `Error: [Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000)`
**Solution:** Check which process is using the port and terminate it:
```powershell
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force
```

### 3. ModuleNotFoundError for `fitz` or `docx`
**Symptom:** `No module named 'fitz'`
**Solution:**
```powershell
python -m pip install pymupdf python-docx
```

### 4. SQLite File Permission or Lock Error
**Symptom:** `sqlite3.OperationalError: database is locked`
**Solution:** Ensure only one instance of the FastAPI backend is running. Check with `Get-Process python`.
