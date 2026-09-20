@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  powershell -ExecutionPolicy Bypass -File install_local.ps1
  if errorlevel 1 (
    pause
    exit /b 1
  )
)

powershell -ExecutionPolicy Bypass -File start_local.ps1
if errorlevel 1 (
  pause
)
