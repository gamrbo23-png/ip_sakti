@echo off
title IP-SAKTI Sahayak Backend
echo =========================================
echo  Starting IP-SAKTI Sahayak Backend...
echo  API Docs: http://localhost:8000/docs
echo =========================================
set PYTHONPATH=backend
.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
