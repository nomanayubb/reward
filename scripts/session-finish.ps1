# Safe end-of-session checks (Windows PowerShell).
# Does NOT commit or push — the agent must inspect the diff and commit
# explicitly (see AGENTS.md §19 and §24).

Set-Location (Join-Path $PSScriptRoot "..")

Write-Host "==> git status"
git status --short

Write-Host ""
Write-Host "==> whitespace / conflict check"
git diff --check

Write-Host ""
Write-Host "==> project checks"
& (Join-Path $PSScriptRoot "project-check.ps1")

Write-Host ""
Write-Host "==> reminder"
Write-Host "Review the diff, update .ai/STATE.md, .ai/HISTORY.md and .ai/TASKS.md,"
Write-Host "then: git add <files>; git commit -m ""type(scope): summary""; git push"
