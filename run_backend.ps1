# Run IP-SAKTI Sahayak FastAPI Backend
$env:PYTHONPATH = "backend"
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " Starting IP-SAKTI Sahayak Backend..." -ForegroundColor Green
Write-Host " API Docs: http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "=========================================" -ForegroundColor Cyan

.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
