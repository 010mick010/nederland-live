@echo off
rem Start Natuur Live op http://localhost:8377/?natuur (sluit dit venster om te stoppen)
cd /d "%~dp0"
start "" /b cmd /c "ping -n 2 127.0.0.1 >nul & start http://localhost:8377/?natuur"
python -m http.server 8377 --bind 127.0.0.1
