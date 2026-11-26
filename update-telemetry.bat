@echo off
cd /d "%~dp0"
"%ProgramFiles%\Git\bin\bash.exe" update-telemetry.sh >> "%TEMP%\jseramn-telemetry.log" 2>&1
