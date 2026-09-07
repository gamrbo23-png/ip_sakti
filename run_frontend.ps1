# Run IP-SAKTI Sahayak Next.js Frontend
$env:Path = "C:\Program Files\nodejs;" + $env:Path
Set-Location frontend
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " Starting IP-SAKTI Sahayak Frontend..." -ForegroundColor Green
Write-Host " Web UI: http://localhost:3000" -ForegroundColor Yellow
Write-Host "=========================================" -ForegroundColor Cyan

npm run dev

