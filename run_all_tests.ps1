# 2025-12-11: Automated Test Runner for BabySteps Digital School
# Author: BabySteps Development Team
# Purpose: Run all automated tests (backend + frontend) and generate reports
# Usage: .\run_all_tests.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "BabySteps Digital School - Test Suite" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Track overall test results
$backendPassed = $false
$frontendPassed = $false
$startTime = Get-Date

# Function to display section header
function Write-Section {
    param([string]$title)
    Write-Host ""
    Write-Host "--------------------" -ForegroundColor Yellow
    Write-Host $title -ForegroundColor Yellow
    Write-Host "--------------------" -ForegroundColor Yellow
    Write-Host ""
}

# Function to check if command exists
function Test-Command {
    param([string]$command)
    $null = Get-Command $command -ErrorAction SilentlyContinue
    return $?
}

# Check prerequisites
Write-Section "Checking Prerequisites"

if (-not (Test-Command "python")) {
    Write-Host "ERROR: Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

if (-not (Test-Command "npm")) {
    Write-Host "ERROR: npm not found. Please install Node.js" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Python found: $(python --version)" -ForegroundColor Green
Write-Host "✓ npm found: $(npm --version)" -ForegroundColor Green

# Install/verify backend dependencies
Write-Section "Backend - Installing Dependencies"
try {
    pip install -r requirements.txt -q
    Write-Host "✓ Backend dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "⚠ Warning: Could not install backend dependencies" -ForegroundColor Yellow
}

# Install/verify frontend dependencies
Write-Section "Frontend - Installing Dependencies"
try {
    Push-Location frontend
    npm install --silent
    Write-Host "✓ Frontend dependencies installed" -ForegroundColor Green
    Pop-Location
} catch {
    Write-Host "⚠ Warning: Could not install frontend dependencies" -ForegroundColor Yellow
    Pop-Location
}

# Run backend tests
Write-Section "Running Backend Tests (pytest)"
try {
    $env:DJANGO_SETTINGS_MODULE = "backend.settings"
    python -m pytest tests/ -v --tb=short --color=yes 2>&1 | Tee-Object -Variable backendOutput
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✓ Backend tests PASSED" -ForegroundColor Green
        $backendPassed = $true
    } else {
        Write-Host ""
        Write-Host "✗ Backend tests FAILED" -ForegroundColor Red
    }
} catch {
    Write-Host ""
    Write-Host "✗ Backend tests encountered an error: $_" -ForegroundColor Red
}

# Run backend test coverage
Write-Section "Backend Test Coverage"
try {
    python -m pytest tests/ --cov=services --cov-report=term --cov-report=html:coverage_backend 2>&1 | Tee-Object -Variable coverageOutput
    Write-Host ""
    Write-Host "✓ Coverage report generated: coverage_backend/index.html" -ForegroundColor Green
} catch {
    Write-Host "⚠ Could not generate coverage report" -ForegroundColor Yellow
}

# Run frontend tests
Write-Section "Running Frontend Tests (Jest)"
try {
    Push-Location frontend
    npm test -- --watchAll=false --coverage --verbose 2>&1 | Tee-Object -Variable frontendOutput
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✓ Frontend tests PASSED" -ForegroundColor Green
        $frontendPassed = $true
    } else {
        Write-Host ""
        Write-Host "✗ Frontend tests FAILED" -ForegroundColor Red
    }
    Pop-Location
} catch {
    Write-Host ""
    Write-Host "✗ Frontend tests encountered an error: $_" -ForegroundColor Red
    Pop-Location
}

# Run Ollama reliability tests
Write-Section "Running Ollama Integration Tests"
try {
    python test_ollama_reliability.py 2>&1 | Tee-Object -Variable ollamaOutput
    Write-Host "✓ Ollama integration test completed" -ForegroundColor Green
} catch {
    Write-Host "⚠ Ollama integration test could not run" -ForegroundColor Yellow
}

# Generate test summary
$endTime = Get-Date
$duration = $endTime - $startTime

Write-Section "Test Summary"
Write-Host "Total Duration: $($duration.TotalSeconds) seconds" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend Tests:  $(if ($backendPassed) { '✓ PASSED' } else { '✗ FAILED' })" -ForegroundColor $(if ($backendPassed) { 'Green' } else { 'Red' })
Write-Host "Frontend Tests: $(if ($frontendPassed) { '✓ PASSED' } else { '✗ FAILED' })" -ForegroundColor $(if ($frontendPassed) { 'Green' } else { 'Red' })
Write-Host ""

# Overall result
if ($backendPassed -and $frontendPassed) {
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "🎉 ALL TESTS PASSED! 🎉" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    exit 0
} else {
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "❌ SOME TESTS FAILED" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please review the test output above for details." -ForegroundColor Yellow
    exit 1
}
