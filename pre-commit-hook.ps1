# 2025-12-11: Pre-commit hook to run tests before committing
# Author: BabySteps Development Team
# Purpose: Ensure all tests pass before allowing commits
# Setup: Copy to .git/hooks/pre-commit (remove .ps1 extension)

Write-Host "Running pre-commit tests..." -ForegroundColor Cyan

# Get list of changed files
$changedFiles = git diff --cached --name-only --diff-filter=ACM

$hasBackendChanges = $false
$hasFrontendChanges = $false

foreach ($file in $changedFiles) {
    if ($file -match "\.(py)$" -and $file -notmatch "tests/") {
        $hasBackendChanges = $true
    }
    if ($file -match "\.(js|jsx|ts|tsx)$" -and $file -match "frontend/") {
        $hasFrontendChanges = $true
    }
}

$testsFailed = $false

# Run backend tests if backend files changed
if ($hasBackendChanges) {
    Write-Host "Backend files changed, running backend tests..." -ForegroundColor Yellow
    python -m pytest tests/ -v --tb=short -q
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Backend tests failed!" -ForegroundColor Red
        $testsFailed = $true
    }
}

# Run frontend tests if frontend files changed
if ($hasFrontendChanges) {
    Write-Host "Frontend files changed, running frontend tests..." -ForegroundColor Yellow
    Push-Location frontend
    npm test -- --watchAll=false --silent
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Frontend tests failed!" -ForegroundColor Red
        $testsFailed = $true
    }
    Pop-Location
}

# Fail commit if tests failed
if ($testsFailed) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "COMMIT REJECTED: Tests must pass" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please fix failing tests before committing." -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "All tests passed! Proceeding with commit..." -ForegroundColor Green
exit 0
