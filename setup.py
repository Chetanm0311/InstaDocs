Write-Host " Setting up InstaDocs Knowledge Base Agent..." -ForegroundColor Cyan

# Check if Python is installed
Write-Host "`n Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host " Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host " Python not found! Please install Python 3.8+ from python.org" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host "`n Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "  Virtual environment already exists. Skipping..." -ForegroundColor Yellow
} else {
    python -m venv venv
    Write-Host " Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "`n Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "`n Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip --quiet

# Install dependencies
Write-Host "`n Installing dependencies..." -ForegroundColor Yellow
Write-Host "   This may take a few minutes..." -ForegroundColor Gray

# Install in stages for better error handling
Write-Host "`n   Installing core frameworks..." -ForegroundColor Gray
pip install fastapi uvicorn[standard] python-multipart --quiet

Write-Host "   Installing document processing..." -ForegroundColor Gray
pip install PyPDF2 python-docx --quiet

Write-Host "   Installing LangChain..." -ForegroundColor Gray
pip install langchain langchain-community --quiet

Write-Host "   Installing ChromaDB..." -ForegroundColor Gray
pip install chromadb --quiet

Write-Host "   Installing sentence-transformers..." -ForegroundColor Gray
pip install sentence-transformers --quiet

Write-Host "   Installing OpenAI (optional)..." -ForegroundColor Gray
pip install openai --quiet

Write-Host "   Installing Streamlit..." -ForegroundColor Gray
pip install streamlit --quiet

Write-Host "   Installing utilities..." -ForegroundColor Gray
pip install python-dotenv pydantic --quiet

Write-Host "`n All dependencies installed!" -ForegroundColor Green

# Create necessary directories
Write-Host "`n Creating storage directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "storage/documents" | Out-Null
New-Item -ItemType Directory -Force -Path "storage/vector_db" | Out-Null
New-Item -ItemType Directory -Force -Path "storage/feedback" | Out-Null
Write-Host " Directories created" -ForegroundColor Green

# Create .env file if it doesn't exist
Write-Host "`n Checking .env configuration..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host " .env file already exists" -ForegroundColor Green
} else {
    Copy-Item ".env.example" ".env"
    Write-Host " Created .env file from template" -ForegroundColor Green
    Write-Host "`n IMPORTANT: Edit .env file and add your OpenAI API key (optional)" -ForegroundColor Yellow
    Write-Host "   Without API key, the system will use local embeddings (still works!)" -ForegroundColor Gray
}

# Test imports
Write-Host "`n🧪 Testing installations..." -ForegroundColor Yellow
$testScript = @"
import sys
try:
    import fastapi
    import chromadb
    import sentence_transformers
    import streamlit
    print(' All imports successful!')
    sys.exit(0)
except ImportError as e:
    print(f' Import failed: {e}')
    sys.exit(1)
"@

$testResult = python -c $testScript
Write-Host $testResult

Write-Host "`n" -NoNewline
Write-Host "="*60 -ForegroundColor Cyan
Write-Host " Setup Complete! " -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Cyan

Write-Host "`n Next Steps:" -ForegroundColor Yellow
Write-Host "   1. (Optional) Edit .env file with your OpenAI API key" -ForegroundColor White
Write-Host "      - System works WITHOUT API key using local models!" -ForegroundColor Gray
Write-Host "`n   2. Start the backend server:" -ForegroundColor White
Write-Host "      .\run_backend.ps1" -ForegroundColor Cyan
Write-Host "`n   3. In a NEW terminal, start the frontend:" -ForegroundColor White
Write-Host "      .\run_frontend.ps1" -ForegroundColor Cyan
Write-Host "`n   4. Open your browser to: http://localhost:8501" -ForegroundColor White

Write-Host " Tips:" -ForegroundColor Yellow
Write-Host "   - The system uses local sentence-transformers by default" -ForegroundColor Gray
Write-Host "   - Add OpenAI key for enhanced answers (optional)" -ForegroundColor Gray
Write-Host "   - Check backend API docs at: http://localhost:8000/docs" -ForegroundColor Gray

Write-Host " Happy Building!" -ForegroundColor Magenta
