# Factory Intelligence Copilot - one-command local launch (Windows PowerShell)
# Starts the FastAPI backend (port 8000) and the React dashboard (port 5173).

$root = $PSScriptRoot

Write-Host "Starting backend (FastAPI + live simulation)..." -ForegroundColor Cyan
$backend = Start-Process -PassThru -WindowStyle Normal powershell -ArgumentList @(
  "-NoExit", "-Command",
  "cd '$root\backend'; .\venv\Scripts\Activate.ps1; uvicorn app.main:app --host 127.0.0.1 --port 8000"
)

Start-Sleep -Seconds 3

Write-Host "Starting frontend (Vite dev server)..." -ForegroundColor Cyan
$frontend = Start-Process -PassThru -WindowStyle Normal powershell -ArgumentList @(
  "-NoExit", "-Command",
  "cd '$root\frontend'; npm run dev"
)

Write-Host ""
Write-Host "Backend:  http://127.0.0.1:8000/api/health" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host ""
Write-Host "Close the two opened PowerShell windows to stop the servers."
