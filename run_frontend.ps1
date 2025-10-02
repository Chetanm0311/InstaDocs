# PowerShell script to run the Streamlit frontend

Write-Host "Starting InstaDocs Knowledge Base Frontend..." -ForegroundColor Green
Write-Host ""

# Activate virtual environment if it exists
if (Test-Path ".\venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    .\venv\Scripts\Activate.ps1
} else {
    Write-Host "Warning: Virtual environment not found at .\venv" -ForegroundColor Red
    Write-Host "Please create it with: python -m venv venv" -ForegroundColor Yellow
    Write-Host ""
}

# Check if backend is running
Write-Host "Checking if backend is running..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/" -UseBasicParsing -TimeoutSec 2
    Write-Host " Backend is running!" -ForegroundColor Green
} catch {
    Write-Host " Backend is not running!" -ForegroundColor Red
    Write-Host "Please start the backend first with: .\run_backend.ps1" -ForegroundColor Yellow
    Write-Host ""
}

# Start frontend
Write-Host ""
Write-Host "Starting Streamlit frontend..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

streamlit run frontend/app.py
