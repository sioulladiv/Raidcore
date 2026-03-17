$ErrorActionPreference = "Stop"

$python = ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Error "Virtual environment python not found at $python"
}

& $python -m PyInstaller --noconfirm --clean --onedir --windowed --name CSProjectRunner main.py `
  --add-data "Assets;Assets" `
  --add-data "Tiled;Tiled" `
  --add-data "data;data" `
  --add-data "config;config" `
  --add-data "Dungeon;Dungeon"

Write-Host "Build finished: dist\CSProjectRunner\CSProjectRunner.exe"
