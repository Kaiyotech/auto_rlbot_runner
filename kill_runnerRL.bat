@echo off

REM Attempt to kill by window title first
taskkill /f /fi "WINDOWTITLE eq RLBOT RUNNER" >nul 2>&1

REM Check for successful termination based on errorlevel
if errorlevel 1 (
    echo "Process with 'RLBOT RUNNER' window title not found. Attempting PID fallback..."
   REM Process with the window title not found or termination failed. Fall back to PID.
   for /f %%i in (runner_pid.txt) do set RUNNER_PID=%%i

   if not defined RUNNER_PID (
       echo "Runner PID not found! Restart may not work correctly."
   ) else (
       taskkill /F /PID %RUNNER_PID%
   )
) else (
    echo "Process with 'RLBOT RUNNER' window title terminated."
)

REM Rest of your logic
taskkill /f /im RocketLeague.exe 
timeout /t 15 > nul
start "RLBOT RUNNER" cmd /k "call .\venv\Scripts\activate.bat & python runner.py"
