@echo off
setlocal

REM Always run relative to this .bat file location.
cd /d "%~dp0"

set "EXE=dist\CSProjectRunner\CSProjectRunner.exe"

echo Building latest version...
powershell -ExecutionPolicy Bypass -File "build_exe.ps1"
if errorlevel 1 (
  echo Build failed.
  exit /b 1
)

if not exist "%EXE%" (
  echo Build finished but executable not found: %EXE%
  exit /b 1
)

start "" "%EXE%"
endlocal
