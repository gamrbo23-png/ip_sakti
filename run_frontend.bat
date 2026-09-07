@echo off
title IP-SAKTI Sahayak Frontend
echo =========================================
echo  Starting IP-SAKTI Sahayak Frontend...
echo  Web UI: http://localhost:3000
echo =========================================
set PATH=C:\Program Files\nodejs;%PATH%
cd frontend
call npm run dev
pause
