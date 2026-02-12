# 2025-12-11: Watch for file changes and run tests automatically
# Author: BabySteps Development Team
# Purpose: Automatically run tests when code changes are detected
# Usage: .\run_tests_on_change.ps1

param(
    [string]$WatchPath = ".",
    [string]$Filter = "*",
    [switch]$BackendOnly,
    [switch]$FrontendOnly
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Auto Test Runner - File Watcher" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Watching for changes in: $WatchPath" -ForegroundColor Yellow
Write-Host "Filter: $Filter" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Ctrl+C to stop watching" -ForegroundColor Gray
Write-Host ""

# Configure file watcher
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $WatchPath
$watcher.Filter = $Filter
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents = $true

# Debounce timer to avoid running tests multiple times for rapid changes
$lastRun = [DateTime]::MinValue
$debounceSeconds = 3

# Function to run tests based on changed file
function Invoke-TestsForChange {
    param([string]$changedFile)
    
    $now = Get-Date
    $timeSinceLastRun = ($now - $script:lastRun).TotalSeconds
    
    if ($timeSinceLastRun -lt $debounceSeconds) {
        Write-Host "Debouncing... (waiting for changes to settle)" -ForegroundColor Gray
        return
    }
    
    $script:lastRun = $now
    
    Write-Host ""
    Write-Host "====================" -ForegroundColor Yellow
    Write-Host "File changed: $changedFile" -ForegroundColor Yellow
    Write-Host "Running tests..." -ForegroundColor Yellow
    Write-Host "====================" -ForegroundColor Yellow
    Write-Host ""
    
    # Determine which tests to run based on file path
    $isBackendFile = $changedFile -match "\\(services|backend|tests)\\"
    $isFrontendFile = $changedFile -match "\\frontend\\"
    
    if ($BackendOnly -or ($isBackendFile -and -not $FrontendOnly)) {
        Write-Host "Running backend tests..." -ForegroundColor Cyan
        python -m pytest tests/ -v --tb=short
    }
    
    if ($FrontendOnly -or ($isFrontendFile -and -not $BackendOnly)) {
        Write-Host "Running frontend tests..." -ForegroundColor Cyan
        Push-Location frontend
        npm test -- --watchAll=false
        Pop-Location
    }
    
    if (-not $BackendOnly -and -not $FrontendOnly -and -not $isBackendFile -and -not $isFrontendFile) {
        Write-Host "Running all tests..." -ForegroundColor Cyan
        .\run_all_tests.ps1
    }
    
    Write-Host ""
    Write-Host "Tests completed. Watching for changes..." -ForegroundColor Green
    Write-Host ""
}

# Register event handlers
$onChanged = Register-ObjectEvent $watcher "Changed" -Action {
    $changedFile = $Event.SourceEventArgs.FullPath
    
    # Skip certain files/folders
    if ($changedFile -match "__pycache__|node_modules|\.git|coverage|\.pyc$") {
        return
    }
    
    # Only process Python and JavaScript/TypeScript files
    if ($changedFile -match "\.(py|js|jsx|ts|tsx)$") {
        Invoke-TestsForChange -changedFile $changedFile
    }
}

$onCreated = Register-ObjectEvent $watcher "Created" -Action {
    $changedFile = $Event.SourceEventArgs.FullPath
    
    if ($changedFile -match "\.(py|js|jsx|ts|tsx)$" -and 
        $changedFile -notmatch "__pycache__|node_modules|\.git|coverage") {
        Invoke-TestsForChange -changedFile $changedFile
    }
}

# Keep script running
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
}
finally {
    # Cleanup
    Unregister-Event -SourceIdentifier $onChanged.Name
    Unregister-Event -SourceIdentifier $onCreated.Name
    $watcher.Dispose()
    Write-Host "File watcher stopped." -ForegroundColor Yellow
}
