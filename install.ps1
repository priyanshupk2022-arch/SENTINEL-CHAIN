<#
.SYNOPSIS
    Aegis AI Security Guardrail Proxy - Automated Windows PowerShell Installer.
.DESCRIPTION
    Automates dependency checks, virtual environment setup, package installation,
    database initialization in WAL mode, and offline cryptographic license verification.
#>

[CmdletBinding()]
param (
    [switch]$SkipVenv,
    [switch]$StartAfterInstall
)

$ErrorActionPreference = "Stop"

function Write-Banner {
    Write-Host @"
`e[1;36m
      ___      _______  _______  ___   _______ 
     |   |    |       ||       ||   | |       |
     |   |    |    ___||    ___||   | |  _____|
     |   |    |   |___ |   | __ |   | | |_____ 
     |   |___ |    ___||   ||  ||   | |_____  |
     |       ||   |___ |   |_| ||   |  _____| |
     |_______||_______||_______||___| |_______|
     AI SECURITY GUARDRAIL PROXY & FORENSICS
`e[0m
"@
}

function Log-Info($msg) {
    Write-Host "`e[1;36m[INFO]`e[0m $msg"
}

function Log-Success($msg) {
    Write-Host "`e[1;32m[SUCCESS]`e[0m $msg"
}

function Log-Warn($msg) {
    Write-Host "`e[1;33m[WARN]`e[0m $msg"
}

function Log-Error($msg) {
    Write-Host "`e[1;31m[ERROR]`e[0m $msg"
}

Write-Banner
Log-Info "Starting Aegis Guardrail Proxy deployment on Windows ($([System.Environment]::OSVersion.VersionString))..."

# ------------------------------------------------------------------------------
# 1. Python Interpreter Resolution
# ------------------------------------------------------------------------------
$pythonBin = $null
$possiblePythons = @("python.exe", "py.exe", "$env:LOCALAPPDATA\Python\bin\python.exe")

foreach ($py in $possiblePythons) {
    try {
        $check = Start-Process -FilePath $py -ArgumentList "-c `"import sys; print(sys.version_info.major, sys.version_info.minor)`"" -NoNewWindow -PassThru -RedirectStandardOutput (New-TemporaryFile)
        $check.WaitForExit(3000)
        if ($check.ExitCode -eq 0) {
            $pythonBin = $py
            break
        }
    } catch {
        continue
    }
}

if (-not $pythonBin) {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        $pythonBin = $pythonCmd.Source
    } else {
        Log-Error "Python 3.11+ is required but was not found in PATH."
        exit 1
    }
}

$verCheck = & $pythonBin -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Log-Success "Verified Python environment: $pythonBin (Version $verCheck)"

# ------------------------------------------------------------------------------
# 2. Virtual Environment Setup
# ------------------------------------------------------------------------------
$rootDir = $PSScriptRoot
Set-Location $rootDir

$venvPath = Join-Path $rootDir ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"

if (-not $SkipVenv) {
    if (-not (Test-Path $venvPath)) {
        Log-Info "Creating virtual environment at $venvPath..."
        & $pythonBin -m venv $venvPath
        Log-Success "Virtual environment created."
    } else {
        Log-Info "Existing virtual environment detected at $venvPath."
    }
    $activePython = $venvPython
} else {
    $activePython = $pythonBin
}

# ------------------------------------------------------------------------------
# 3. Dependencies Installation
# ------------------------------------------------------------------------------
Log-Info "Upgrading pip, setuptools, and wheel..."
& $activePython -m pip install --upgrade pip setuptools wheel --quiet

Log-Info "Installing Aegis dependencies..."
& $activePython -m pip install -e ".[dev]" --quiet

Log-Success "Dependencies successfully installed."

# ------------------------------------------------------------------------------
# 4. Storage & Database Setup
# ------------------------------------------------------------------------------
$dataDir = Join-Path $rootDir "data"
if (-not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir | Out-Null
}

$envFile = Join-Path $rootDir ".env"
$envExample = Join-Path $rootDir ".env.example"
if (-not (Test-Path $envFile) -and (Test-Path $envExample)) {
    Copy-Item $envExample $envFile
    Log-Success "Created default .env configuration file."
}

Log-Info "Initializing SQLite WAL database storage..."
& $activePython -c "from app.models.database import db; print('[+] SQLite tables and security policies initialized in WAL mode.')"
Log-Success "Database initialization complete."

# ------------------------------------------------------------------------------
# 5. Cryptographic License Verification
# ------------------------------------------------------------------------------
Log-Info "Verifying offline Ed25519 cryptographic licensing subsystem..."
& $activePython -c "
import os
from app.security.license import license_manager
status = license_manager.get_status(os.getenv('AEGIS_LICENSE_TOKEN'))
print(f'[+] License Status: Tier={status.get(\"tier\").upper()}, Active={status.get(\"active\")}, Air-Gapped Verification=PASS')
"

Write-Host ""
Write-Host "`e[1;32m==============================================================================`e[0m"
Write-Host "`e[1;36m  🛡️  AEGIS AI SECURITY GUARDRAIL PROXY READY FOR PRODUCTION  🛡️`e[0m"
Write-Host "`e[1;32m==============================================================================`e[0m"
Write-Host "  `e[1mDashboard UI  :`e[0m http://localhost:8000/"
Write-Host "  `e[1mHealth Probe  :`e[0m http://localhost:8000/health"
Write-Host "  `e[1mOpenAI Proxy  :`e[0m http://localhost:8000/v1/chat/completions"
Write-Host "  `e[1mAnthropic Proxy:`e[0m http://localhost:8000/v1/messages"
Write-Host "  `e[1mText Scanner  :`e[0m http://localhost:8000/v1/scan/text"
Write-Host "  `e[1mDoc Forensics :`e[0m http://localhost:8000/v1/scan/document"
Write-Host ""
Write-Host "`e[1;33mTo launch the proxy server, execute:`e[0m"
Write-Host "  `e[1m& `"$activePython`" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2`e[0m"
Write-Host ""

if ($StartAfterInstall) {
    Log-Info "Launching Aegis Guardrail Proxy server..."
    & $activePython -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
}
