@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0instalar.ps1"
if errorlevel 1 (
  echo.
  echo Algo salio mal. Revisa el mensaje de arriba o pidele ayuda a quien te compartio Kiara.
)
pause
