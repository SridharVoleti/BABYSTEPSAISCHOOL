<#
.SYNOPSIS
    Starts the BabySteps Digital School development servers (frontend and backend)
.DESCRIPTION
    This script starts both the Django backend server and React frontend development server
    in separate PowerShell windows for development purposes.
#>

# Configuration
$backendDir = "D:\Sridhar\Projects\BabyStepsDigitalSchool"
$frontendDir = "D:\Sridhar\Projects\BabyStepsDigitalSchool\frontend"
$backendPort = 8000
$frontendPort = 3000

# Function to check if a port is in use
function Test-PortInUse {
    param($port)
    $tcpConnections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    return $null -ne $tcpConnections
}

# Check if required ports are available
if (Test-PortInUse -port $backendPort) {
    Write-Host "Port $backendPort is already in use. Please close any applications using this port." -ForegroundColor Red
    exit 1
}

if (Test-PortInUse -port $frontendPort) {
    Write-Host "Port $frontendPort is already in use. Please close any applications using this port." -ForegroundColor Red
    exit 1
}

# Start backend server in a new window
Write-Host "Starting Django backend server on port $backendPort..." -ForegroundColor Cyan
$backendScript = @"
cd `"$backendDir`"
if (Test-Path "venv\Scripts\Activate.ps1") {
    .\venv\Scripts\Activate.ps1
    python manage.py runserver $backendPort
} else {
    Write-Host "Virtual environment not found. Please ensure you have set up the Python virtual environment." -ForegroundColor Red
    pause
}
"@

# Start frontend in a new window
Write-Host "Starting React frontend development server on port $frontendPort..." -ForegroundColor Cyan
$frontendScript = @"
cd `"$frontendDir`"
npm start
"@

# Create temporary script files
$backendScriptPath = [System.IO.Path]::GetTempFileName() + ".ps1"
$frontendScriptPath = [System.IO.Path]::GetTempFileName() + ".ps1"

# Save scripts to temporary files
$backendScript | Out-File -FilePath $backendScriptPath -Encoding utf8
$frontendScript | Out-File -FilePath $frontendScriptPath -Encoding utf8

# Start the processes
$backendProcess = Start-Process powershell -ArgumentList "-NoExit", "-File", "`"$backendScriptPath`"" -PassThru
$frontendProcess = Start-Process powershell -ArgumentList "-NoExit", "-File", "`"$frontendScriptPath`"" -PassThru

# Clean up temporary files on exit
Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action {
    Remove-Item $event.MessageData -ErrorAction SilentlyContinue
} -MessageData @($backendScriptPath, $frontendScriptPath)

Write-Host "Servers are starting in separate windows..." -ForegroundColor Green
Write-Host "Backend: http://localhost:$backendPort" -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:$frontendPort" -ForegroundColor Yellow
Write-Host "`nPress Ctrl+C to stop both servers" -ForegroundColor Cyan

# Wait for Ctrl+C
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
}
finally {
    # Cleanup on script exit
    Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
    Write-Host "`nServers have been stopped." -ForegroundColor Green
}