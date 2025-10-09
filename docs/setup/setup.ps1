# Moda Crypto Setup Script for Windows PowerShell
# Run this script from the moda-crypto root directory

Write-Host "🚀 Moda Crypto Setup Script for Windows" -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Green

# Check if we're in the right directory
if (-not (Test-Path "backend") -or -not (Test-Path "frontend")) {
    Write-Host "❌ Please run this script from the moda-crypto root directory" -ForegroundColor Red
    exit 1
}

# Function to check if a command exists
function Test-Command($command) {
    try {
        Get-Command $command -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}

# Check prerequisites
Write-Host "🔍 Checking prerequisites..." -ForegroundColor Yellow

# Check Python
if (Test-Command python) {
    $pythonVersion = python --version
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
}
else {
    Write-Host "❌ Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check Node.js
if (Test-Command node) {
    $nodeVersion = node --version
    Write-Host "✅ Node.js $nodeVersion" -ForegroundColor Green
}
else {
    Write-Host "❌ Node.js is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check npm
if (Test-Command npm) {
    $npmVersion = npm --version
    Write-Host "✅ npm $npmVersion" -ForegroundColor Green
}
else {
    Write-Host "❌ npm is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Setup environment files
Write-Host "`n📝 Setting up environment files..." -ForegroundColor Yellow

# Backend .env
if ((Test-Path "backend\.env.example") -and -not (Test-Path "backend\.env")) {
    Copy-Item "backend\.env.example" "backend\.env"
    Write-Host "✅ Created backend\.env from .env.example" -ForegroundColor Green
    Write-Host "⚠️  Please edit backend\.env with your API keys and Firebase credentials" -ForegroundColor Yellow
}
elseif (Test-Path "backend\.env") {
    Write-Host "✅ backend\.env already exists" -ForegroundColor Green
}

# Frontend .env.local
if ((Test-Path "frontend\.env.example") -and -not (Test-Path "frontend\.env.local")) {
    Copy-Item "frontend\.env.example" "frontend\.env.local"
    Write-Host "✅ Created frontend\.env.local from .env.example" -ForegroundColor Green
    Write-Host "⚠️  Please edit frontend\.env.local with your Firebase configuration" -ForegroundColor Yellow
}
elseif (Test-Path "frontend\.env.local") {
    Write-Host "✅ frontend\.env.local already exists" -ForegroundColor Green
}

# Setup Python backend
Write-Host "`n🐍 Setting up Python backend..." -ForegroundColor Yellow

Set-Location backend

# Create virtual environment
if (-not (Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Virtual environment created" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
}
else {
    Write-Host "✅ Virtual environment already exists" -ForegroundColor Green
}

# Install requirements
if (Test-Path "requirements.txt") {
    Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
    .\venv\Scripts\pip install -r requirements.txt
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Python dependencies installed" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Failed to install Python dependencies" -ForegroundColor Red
        exit 1
    }
}
else {
    Write-Host "❌ requirements.txt not found" -ForegroundColor Red
    exit 1
}

Set-Location ..

# Setup Node.js frontend
Write-Host "`n⚛️  Setting up Node.js frontend..." -ForegroundColor Yellow

Set-Location frontend

# Install npm dependencies
if (Test-Path "package.json") {
    Write-Host "Installing Node.js dependencies..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Node.js dependencies installed" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Failed to install Node.js dependencies" -ForegroundColor Red
        exit 1
    }
}
else {
    Write-Host "❌ package.json not found" -ForegroundColor Red
    exit 1
}

Set-Location ..

# Print next steps
Write-Host "`n🎉 Setup completed!" -ForegroundColor Green
Write-Host "`n📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Configure your API keys:" -ForegroundColor White
Write-Host "   - Edit backend\.env with your Firebase and external API credentials" -ForegroundColor Gray
Write-Host "   - Edit frontend\.env.local with your Firebase project configuration" -ForegroundColor Gray

Write-Host "`n2. Start the development servers:" -ForegroundColor White
Write-Host "   Backend:" -ForegroundColor Gray
Write-Host "     cd backend" -ForegroundColor Gray
Write-Host "     .\venv\Scripts\activate" -ForegroundColor Gray
Write-Host "     uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" -ForegroundColor Gray

Write-Host "`n   Frontend (in a new PowerShell window):" -ForegroundColor Gray
Write-Host "     cd frontend" -ForegroundColor Gray
Write-Host "     npm run dev" -ForegroundColor Gray

Write-Host "`n3. Access the application:" -ForegroundColor White
Write-Host "   - Frontend: http://localhost:3000" -ForegroundColor Gray
Write-Host "   - Backend API: http://localhost:8000" -ForegroundColor Gray
Write-Host "   - API Documentation: http://localhost:8000/docs" -ForegroundColor Gray

Write-Host "`n📚 Additional resources:" -ForegroundColor Cyan
Write-Host "   - README.md for detailed setup instructions" -ForegroundColor Gray
Write-Host "   - Firebase Console for database management" -ForegroundColor Gray
Write-Host "   - API documentation for endpoint details" -ForegroundColor Gray

Write-Host "`nPress any key to continue..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")