# Session Logs

One file per working session: `YYYY-MM-DD-<topic>.md`.

Purpose: at the start of a new session the agent reads the latest log to see
**what was actually discussed and decided**, not just what was committed.
Detailed technical state still lives in `STATE.md` / `TASKS.md` /
`REQUIREMENTS.md` / `HISTORY.md` — this folder is the conversation record.

## Rules

- Append-only. Never edit or delete an old session log.
- Record: the user's requests (paraphrased or quoted), what the agent did,
  decisions made, blockers, and what was left open.
- Keep it factual. Do not include secrets, credentials or personal data.
- At session end: write the log **before** the final commit of the session.

## Index

| Date | Topic | File |
| --- | --- | --- |
| 2026-09-18 | Project inception, foundation build, AI protocol, auth API | `2026-09-18-project-inception.md` |
| 2026-09-18 | AdGem integration, Render production fix, generic offerwalls | `2026-09-18-adgem-and-live-deploy.md` |
