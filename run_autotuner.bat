@echo off
title Autonomous Windows Performance and Tuning Tool
color 0A
:: Ensure administrator privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :RUN
) else (
    echo [!] Requesting Administrator Rights...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:RUN
cd /d "%~dp0"
echo ====================================================================
echo   LAUNCHING AUTONOMOUS PERFORMANCE AND TUNING ENGINE
echo ====================================================================
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0AutoPerformanceTuner.ps1"
pause
