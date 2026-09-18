# Starts the reward platform dev server on the project's fixed port (8010).
# Port 8000 is reserved for another project on this machine — never use it.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\scripts\dev.ps1
param(
    [string]$Bind = "127.0.0.1",
    [int]$Port = 8010
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)

$busy = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($busy) {
    $owner = (Get-Process -Id $busy[0].OwningProcess -ErrorAction SilentlyContinue).ProcessName
    Write-Host "Port $Port is already in use (PID $($busy[0].OwningProcess), $owner)." -ForegroundColor Yellow
    Write-Host "Stop that process first, or use another port with -Port." -ForegroundColor Yellow
    exit 1
}

Write-Host "Starting reward platform on http://${Bind}:${Port}/" -ForegroundColor Green
python manage.py runserver "${Bind}:${Port}"
