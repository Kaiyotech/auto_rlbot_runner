@echo off

REM Attempt to kill by window title first
taskkill /fi "WINDOWTITLE eq RLBOT_RUNNER*"
echo "Attempted to kill RUNNER by name and related Python processes"


REM taskkill /f /im RocketLeague.exe
REM give stuff time to fully die
timeout /t 45 > nul
start "RLBOT_RUNNER" cmd /k "call .\venv311\Scripts\activate.bat & python runner.py"

