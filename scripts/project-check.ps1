# Standard project validation (Windows PowerShell). Run from the repository root.
$ErrorActionPreference = "Stop"

Set-Location (Join-Path $PSScriptRoot "..")

$python = Join-Path (Get-Location) ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }

Write-Host "==> Django system check"
& $python manage.py check
if (-not $?) { exit 1 }

Write-Host "==> Pending migrations"
& $python manage.py makemigrations --check --dry-run
if (-not $?) { exit 1 }

Write-Host "==> Tests"
& $python -m pytest
if (-not $?) { exit 1 }

& $python -m ruff --version *> $null
if ($?) {
    Write-Host "==> Ruff"
    & $python -m ruff check .
    if (-not $?) { exit 1 }
} else {
    Write-Host "==> Ruff not installed (skipping)"
}

Write-Host "==> All checks passed"
