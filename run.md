# 🚀 How to Run IP-SAKTI Sahayak (Backend & Frontend)

This guide provides step-by-step instructions for running both the **FastAPI Backend** and the **Next.js Frontend** locally on Windows.

---

## ⚡ Option 1: Quick Start (1-Click Scripts)

The easiest way to start the application is using the provided startup scripts. Open two separate terminal windows or double-click the `.bat` files.

### 1. Start the Backend (Terminal 1)
In **PowerShell** (note the `.\` prefix):
```powershell
.\run_backend.ps1
```
*(or `.\run_backend.bat`)*

* Or in **Command Prompt (cmd)**:
```cmd
run_backend.bat
```
- **Backend URL:** http://localhost:8000
- **Interactive Swagger API Docs:** http://localhost:8000/docs
- **ReDoc Documentation:** http://localhost:8000/redoc

---

### 2. Start the Frontend (Terminal 2)
In **PowerShell** (note the `.\` prefix):
```powershell
.\run_frontend.ps1
```
*(or `.\run_frontend.bat`)*

* Or in **Command Prompt (cmd)**:
```cmd
run_frontend.bat
```
- **Frontend Web UI:** http://localhost:3000

---

## 🛠️ Option 2: Manual Terminal Execution

If you prefer running the commands step-by-step in separate terminal windows:

### Terminal 1: FastAPI Backend

1. **Navigate to the project root directory:**
   ```powershell
   cd "c:\Users\arghy\OneDrive\Documents\HACKATHIN PROJECT\HACKATHON PROJECT\ip-sakti"
   ```

2. **Activate the Python Virtual Environment:**
   * **PowerShell:**
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   * **Command Prompt:**
     ```cmd
     .venv\Scripts\activate.bat
     ```

3. **Set the Python Path & Start Uvicorn:**
   * **PowerShell:**
     ```powershell
     $env:PYTHONPATH = "backend"
     python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
     ```
   * **Command Prompt:**
     ```cmd
     set PYTHONPATH=backend
     python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
     ```

---

### Terminal 2: Next.js Frontend

1. **Navigate to the `frontend` directory:**
   ```powershell
   cd "c:\Users\arghy\OneDrive\Documents\HACKATHIN PROJECT\HACKATHON PROJECT\ip-sakti\frontend"
   ```

2. **(First-time only) Install frontend dependencies:**
   ```powershell
   npm install
   ```

3. **Start the Next.js development server:**
   ```powershell
   npm run dev
   ```

4. **Access the application in your browser:**
   Open [http://localhost:3000](http://localhost:3000)

---

## 📦 First-Time Setup & Prerequisites

If setting up the repository from scratch or on a new machine:

### 1. Python Environment Setup (Backend)
```powershell
# From the ip-sakti directory:
python -m venv .venv
.\.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Statutory Knowledge Base & Database Initialization (Optional)
The project comes with a pre-configured SQLite database (`ipsakti.db`). To re-ingest official statutory documents:
```powershell
$env:PYTHONPATH = "backend"
python scripts/ingest.py
```

To run the 100-question automated RAG benchmark:
```powershell
python scripts/evaluate.py
```

---

## 🐳 Option 3: Docker Compose (All-in-One)

If Docker Desktop is installed:
```powershell
# Start all containers (Postgres, pgvector, Backend, Frontend)
docker compose up -d

# Stop all containers
docker compose down
```

---

## 🔧 Useful URLs & Endpoints Summary

| Service | URL | Description |
|---|---|---|
| **Frontend Web UI** | [http://localhost:3000](http://localhost:3000) | Main User Interface (Chat, Discovery Wizard, Comparison) |
| **Backend API Root** | [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health) | API Health Check Endpoint |
| **API Swagger UI** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive API exploration and testing |
| **API ReDoc** | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Clean API documentation |

---

## ⚠️ Troubleshooting & FAQs

### 1. PowerShell Script Execution Policy Error
If running `.ps1` scripts gives an execution policy error, run this once in PowerShell:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### 2. `'npm' is not recognized` Error
Ensure Node.js is installed or ensure `C:\Program Files\nodejs` is in your PATH environment variable. The `run_frontend.ps1` and `run_frontend.bat` scripts already include this automatically.

### 3. Port Already in Use (Port 8000 or 3000)
- Find process using port:
  ```powershell
  Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess
  ```
- Terminate if needed or change the port in `.env` and `frontend/package.json`.
