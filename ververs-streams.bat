@echo off
rem Ververst de lijst met streams in cams.js. Duurt enkele minuten tot ongeveer een kwartier.
cd /d "%~dp0"
python ververs-streams.py
pause
