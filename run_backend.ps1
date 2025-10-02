# PowerShell script to run the backend server

Write-Host "Starting InstaDocs Knowledge Base Backend Server..." -ForegroundColor Green
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

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "Note: .env file not found. Using defaults (sentence-transformers)" -ForegroundColor Yellow
    Write-Host "To use OpenAI, copy .env.example to .env and add your API key" -ForegroundColor Yellow
    Write-Host ""
}

# Start backend
Write-Host "Starting FastAPI server on http://localhost:8000" -ForegroundColor Green
Write-Host "API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

python -m uvicorn backend.main:app --reload --host localhost --port 8000
