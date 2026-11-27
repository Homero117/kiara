@echo off
cd /d "%~dp0escritorio"
if not exist node_modules (
  echo Instalando Electron por primera vez...
  call npm install
)
start "" "node_modules\electron\dist\electron.exe" .
