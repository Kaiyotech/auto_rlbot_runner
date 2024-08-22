@echo off

REM Attempt to kill by window title first

for /f "tokens=*" %%a in ('tasklist /v ^| findstr /r /c:".*RLBOT_RUNNER.*"') do (
    for /f "tokens=2" %%b in ("%%a") do (
        taskkill /f /t /PID %%b
    )
)

echo "Attempted to kill RUNNER by name and related Python processes"


REM taskkill /f /im RocketLeague.exe
REM give stuff time to fully die
timeout /t 45 > nul
start "RLBOT_RUNNER" cmd /k "call .\venv311\Scripts\activate.bat & python runner.py"

