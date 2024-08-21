@echo off

REM Attempt to kill by window title first
taskkill /f /t /fi "WINDOWTITLE eq RLBOT RUNNER"

for /f "tokens=*" %%a in ('tasklist /v ^| findstr /r /c:"[0-9][0-9]*/[0-9][0-9]*"') do (
    for /f "tokens=2" %%b in ("%%a") do (
        taskkill /f /t /PID %%b
    )
)

for /f "tokens=*" %%a in ('tasklist /v ^| findstr /r /c:"[0-9][0-9]*\[0-9][0-9]*"') do (
    for /f "tokens=2" %%b in ("%%a") do (
        taskkill /f /t /PID %%b
    )
)

echo "Attempted to kill RUNNER by name and related Python processes"


REM taskkill /f /im RocketLeague.exe
REM timeout /t 30 > nul
start "RLBOT_RUNNER" cmd /k "call .\venv311\Scripts\activate.bat & python runner.py"

