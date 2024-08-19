@echo off

REM Attempt to kill by window title first
taskkill /f /t /fi "WINDOWTITLE eq RLBOT_RUNNER"
taskkill /f /t /fi "WINDOWTITLE eq RLBOT_RUNNER"

REM Find and kill Python processes running runner.py
for /f "tokens=2 delims= " %%a in ('wmic process where "name='python.exe' and CommandLine like '%%runner.py%%'" get ProcessId /value') do (
    for /f "tokens=2 delims= " %%b in ('wmic process where "ProcessId=%%a" get ParentProcessId /value') do (
        taskkill /f /t /PID %%b >nul 2>&1
    )
    taskkill /f /t /PID %%a >nul 2>&1
)

echo "Attempted to kill RUNNER by name and related Python processes"

REM Rest of your logic
@REM taskkill /f /im RocketLeague.exe
@REM timeout /t 30 > nul
start "RLBOT_RUNNER" cmd /k "call .\venv311\Scripts\activate.bat & python runner.py"
