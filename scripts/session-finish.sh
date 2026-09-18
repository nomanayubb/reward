#!/usr/bin/env bash
# Safe end-of-session checks. Does NOT commit or push — the agent must inspect
# the diff and commit explicitly (see AGENTS.md §19 and §24).
set -uo pipefail

cd "$(dirname "$0")/.."

echo "==> git status"
git status --short

echo
echo "==> whitespace / conflict check"
git diff --check

echo
echo "==> project checks"
if [ -f "scripts/project-check.sh" ]; then
    bash scripts/project-check.sh
fi

echo
echo "==> reminder"
echo "Review the diff, update .ai/STATE.md, .ai/HISTORY.md and .ai/TASKS.md,"
echo "then: git add <files> && git commit -m \"type(scope): summary\" && git push"
