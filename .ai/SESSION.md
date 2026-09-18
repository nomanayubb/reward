# CURRENT SESSION

## Objective

Adopt the AI development protocol for this repository:

- Create `.ai/` project memory (GOAL, RULES, STATE, TASKS, HISTORY, MASTER,
  DECISIONS, SESSION)
- Create root `AGENTS.md` operating protocol
- Create `scripts/project-check` and `scripts/session-finish`
- Align `docs/` structure (api, modules, integrations, deployment, security)
- Initialize Git and make the initial commit

## Files Being Modified

- `.ai/*` (new)
- `AGENTS.md` (new)
- `scripts/project-check.sh`, `scripts/project-check.ps1` (new)
- `scripts/session-finish.sh`, `scripts/session-finish.ps1` (new)
- `docs/integrations/*` (moved)
- `README.md`, `docs/PRD.md` (references)

## Requirements

- Project memory stays short (STATE < ~100 lines).
- Scripts must run the real project checks (`manage.py check`, `pytest`).
- No secrets committed; `.env` remains ignored.

## Validation

```
scripts/project-check.ps1        (or ./scripts/project-check.sh)
```

## Completion Criteria

- All `.ai/` files exist with accurate content.
- `AGENTS.md` describes the operating protocol.
- Scripts run successfully.
- Git repository initialized; initial commit created.
- Push attempted; if no remote is configured, reported honestly.

## Finalization

Update `.ai/STATE.md`, `.ai/HISTORY.md`, `.ai/TASKS.md`, then commit and push.
