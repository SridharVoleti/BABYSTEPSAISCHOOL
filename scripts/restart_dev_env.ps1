#!/usr/bin/env pwsh
<#
2025-10-17: Utility script to restart backend, frontend, and TTS warmup services
Authors: Sridhar
Contact: sridhar@babystepsdigitalschool.com
#>

[CmdletBinding()]
param(
    [switch]$SkipWarmup,
    [switch]$NoBackend,
    [switch]$NoFrontend
)

$ErrorActionPreference = 'Stop'

function Write-Step {
    param([string]$Message)
    Write-Host "[restart-dev] $Message" -ForegroundColor Cyan
}

function Write-WarningStep {
    param([string]$Message)
    Write-Host "[restart-dev] $Message" -ForegroundColor Yellow
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptRoot '..')
$backendDir = Join-Path $projectRoot 'backend'
$frontendDir = Join-Path $projectRoot 'frontend'

if (-not (Test-Path $backendDir)) {
    throw "Backend directory not found at $backendDir"
}
if (-not (Test-Path $frontendDir)) {
    throw "Frontend directory not found at $frontendDir"
}

Write-Step "Project root resolved to $projectRoot"

function Stop-ProcessIfRunning {
    param(
        [string]$ProcessName,
        [string]$Description,
        [scriptblock]$Filter = $null
    )

    try {
        $instances = @()
        if ($Filter) {
            $instances = Get-CimInstance Win32_Process -Filter "Name = '$ProcessName'" | Where-Object $Filter
        } else {
            $instances = Get-Process -Name $ProcessName -ErrorAction Stop
        }

        if ($instances.Count -gt 0) {
            Write-Step "Stopping $Description ($($instances.Count) instance(s))"
            foreach ($proc in $instances) {
                try {
                    if ($proc -is [System.Diagnostics.Process]) {
                        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
                    } else {
                        Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
                    }
                } catch {
                    $procId = if ($proc -is [System.Diagnostics.Process]) { $proc.Id } else { $proc.ProcessId }
                    Write-WarningStep ("Unable to stop {0} process with ID {1}: {2}" -f $Description, $procId, $_)
                }
            }
        }
    } catch {
        if ($_.FullyQualifiedErrorId -ne 'NoProcessFoundForGivenName,Microsoft.PowerShell.Commands.GetProcessCommand') {
            Write-WarningStep "Failed to query $Description processes: $_"
        }
    }
}

Write-Step 'Stopping existing dev servers'
Stop-ProcessIfRunning -ProcessName 'node.exe' -Description 'Node.js dev server'
Stop-ProcessIfRunning -ProcessName 'python.exe' -Description 'Django server' -Filter { $_.CommandLine -like '*manage.py*runserver*' }
Stop-ProcessIfRunning -ProcessName 'python.exe' -Description 'TTS warmup job' -Filter { $_.CommandLine -like '*tts_service*' }
Start-Sleep -Seconds 1

if (-not $NoBackend) {
    Write-Step 'Starting backend (Django) server'
    $activate = @"
if (Test-Path .venv\Scripts\Activate.ps1) {
    . .venv\Scripts\Activate.ps1
} elseif (Test-Path venv\Scripts\Activate.ps1) {
    . venv\Scripts\Activate.ps1
}
"@
    $backendCommand = @"
Set-Location `"$backendDir`"
$activate
python manage.py runserver 0.0.0.0:8000
"@
    Start-Process powershell -ArgumentList '-NoExit','-Command',$backendCommand -WindowStyle Normal -WorkingDirectory $backendDir
} else {
    Write-WarningStep 'Skipping backend restart per flag'
}

if (-not $NoFrontend) {
    Write-Step 'Starting frontend (React) dev server'
    $frontendCommand = @"
Set-Location `"$frontendDir`"
npm start
"@
    Start-Process powershell -ArgumentList '-NoExit','-Command',$frontendCommand -WindowStyle Normal -WorkingDirectory $frontendDir
} else {
    Write-WarningStep 'Skipping frontend restart per flag'
}

if (-not $SkipWarmup -and -not $NoBackend) {
    Write-Step 'Running TTS warmup check'
    $warmupCode = @'
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()
from apps.ai_services.tts_service import tts_service
status = "READY" if tts_service and getattr(tts_service, "tts", None) else "UNAVAILABLE"
print(f"TTS service status: {status}")
'@
    try {
        Push-Location $backendDir
        Invoke-Expression $activate
        python -c $warmupCode
    } catch {
        Write-WarningStep "TTS warmup check failed: $_"
    } finally {
        Pop-Location
    }
} else {
    Write-WarningStep 'Skipping TTS warmup (per flag or backend disabled)'
}

Write-Step 'Restart sequence initiated. Check newly opened PowerShell windows for server logs.'
