# AGENTS.md — Reward Project Development Protocol

You are working inside the **Reward Project** repository.

Your responsibility is to extend the existing system safely, efficiently, and
incrementally.

The project is a production-oriented Django rewards platform containing HTML5
games, surveys, compliant offer/CPA integrations, advertisements, wallets,
rewards, deposits, withdrawals, fraud controls, analytics, and a highly
configurable administration system.

---

## 1. FIRST ACTION — LOAD PROJECT CONTEXT

At the beginning of every new session, read these files in this order:

```
.ai/GOAL.md
.ai/RULES.md
.ai/STATE.md
.ai/TASKS.md
.ai/MASTER.md
```

Then read only the module-specific documentation relevant to the task.

Do NOT scan the entire repository unnecessarily.
Do NOT reread large files unless they are relevant to the current task.

The `.ai/` documentation is the project's persistent development memory.

## 2. DETERMINE THE CURRENT TASK

Use `.ai/STATE.md` and `.ai/TASKS.md` to determine the next unfinished task.

If the user explicitly provides a different task, follow the user's task while
preserving the project's architecture and rules.

Do not silently switch to unrelated work.

## 3. INSPECT BEFORE EDITING

Before changing code:

- Find the relevant module.
- Inspect existing implementation.
- Inspect related models/services.
- Inspect relevant tests.
- Inspect relevant URLs/API endpoints.
- Inspect relevant documentation.

Understand the current implementation before modifying it.

## 4. MINIMAL CONTEXT PRINCIPLE

Do not read the whole repository. Use targeted inspection:

1. Identify relevant module.
2. Identify relevant files.
3. Read those files.
4. Trace dependencies only as required.
5. Implement the change.

Only expand the inspection scope when the dependency graph requires it.

## 5. MINIMAL CHANGE PRINCIPLE

Prefer the smallest safe implementation that completely satisfies the
requirement.

- Do not rewrite functioning systems unnecessarily.
- Do not refactor unrelated code during feature work.
- Do not introduce unnecessary dependencies.
- Do not create unnecessary abstractions.

## 6. ARCHITECTURE PRINCIPLES

- Business logic belongs in service/domain layers.
- Views/controllers must remain thin.
- Provider integrations must use adapters/interfaces.
- Financial operations must use services.
- Templates must not contain business logic.
- Client-side code must never be trusted for financial authorization.

## 7. FINANCIAL SAFETY

- Money must use `Decimal`/`NUMERIC` (`apps.common.fields.money_field`).
- Never use floating-point arithmetic for financial values.
- The immutable ledger is the source of truth.
- Never directly manipulate financial balances without an appropriate ledger
  transaction.
- Financial operations must be atomic (database transactions, row-level
  locking where necessary).
- Financial history must never be silently deleted — use reversals/adjustments.

## 8. IDEMPOTENCY

External callbacks must be idempotent. A provider may send the same event
multiple times; repeated callbacks must not generate repeated financial
rewards. Use unique external identifiers and appropriate database constraints.
Payment operations must also be designed for idempotency.

## 9. PROVIDER INTEGRATIONS

All external providers must be isolated behind provider adapters.

Never scatter provider-specific logic through views, templates, user models or
wallet models. Use a normalized internal representation. Credentials come from
environment variables or secure configuration. Never commit secrets.

## 10. OFFER COMPLIANCE

Never implement mechanisms intended to evade advertiser/provider fraud
detection or policy enforcement. Never assume that an offer is incentivizable.
Store and enforce campaign eligibility and incentive rules where provided by
the network. Only expose offers to users when the provider/campaign rules
permit the intended traffic and incentive model.

## 11. GAMES

HTML5 games are isolated applications. Game code must not receive unrestricted
access to authentication credentials, wallet internals, admin APIs or private
user data. Use controlled APIs, signed/session-bound events, origin
validation, and server-side reward verification. Never trust client-side
scores as proof of monetary rewards.

## 12. DATABASE

- Use Django migrations for schema changes.
- Do not manually alter production schema.
- Add indexes for frequently queried fields.
- Avoid N+1 queries: use `select_related`, `prefetch_related`, pagination and
  bulk operations where appropriate.

## 13. PERFORMANCE

Optimize based on actual bottlenecks. Prefer efficient queries, caching,
asynchronous jobs, pagination, indexed queries and bulk processing. Do not
prematurely introduce complicated infrastructure. Do not sacrifice
correctness for micro-optimizations.

## 14. BACKGROUND TASKS

Use Celery for provider synchronization, webhook processing where appropriate,
reports, notifications, reconciliation, cleanup and scheduled automation. Do
not block web requests with long-running work.

## 15. TESTING

After meaningful changes, run the smallest relevant test suite first, then
broader tests when appropriate.

At minimum for backend changes:

```bash
python manage.py check
pytest
```

For targeted work: `pytest apps/<module>/tests/` or
`pytest tests/test_critical_flows.py`.

Bug fixes should add regression tests whenever practical.

## 16. MIGRATIONS

When models change:

```bash
python manage.py makemigrations
python manage.py migrate
```

Inspect generated migrations before applying them. Never blindly delete
migrations.

## 17. SECURITY

Never disable security mechanisms merely to make development easier.

Do not commit API keys, passwords, private keys, production credentials or
sensitive user data. Use environment variables. Validate permissions
server-side. Use CSRF protection, authentication and authorization correctly.

## 18. DOCUMENTATION

When implementation changes behavior, update the relevant documentation:

- `.ai/MASTER.md` — architecture/integration summaries
- `.ai/STATE.md` — current implementation status
- `.ai/TASKS.md` — task status
- `.ai/HISTORY.md` — completed work
- `.ai/DECISIONS.md` — important architectural decisions
- `docs/` and module `README.md` — detailed behavior

Do not put every tiny implementation detail into MASTER.md.

## 19. GIT WORKFLOW

Git is mandatory project state. After every coherent successful change:

1. `git status`
2. inspect `git diff`
3. run relevant tests
4. check for accidental files/secrets
5. update project memory files
6. `git status` again
7. commit
8. push

```bash
git status
git diff
python manage.py check
pytest
git status
git add <specific files>
git commit -m "feat(wallet): add transaction service"
git push
```

Prefer adding specific files instead of blindly using `git add .` — this
prevents accidental secrets and unrelated files from entering commits.

## 20. NEVER DESTROY USER WORK

Never use destructive commands such as `git reset --hard`, `git clean -fd` or
`git checkout .` unless the user explicitly authorizes the exact destructive
operation. Never overwrite uncommitted user changes. If unexpected changes
exist, inspect them first.

## 21. GIT PUSH

The environment is expected to have the repository's Git remote configured.
After a successful coherent change, `git push` directly.

If authentication or remote configuration prevents pushing, report the exact
problem rather than pretending the push succeeded. Never claim a commit or
push succeeded unless the command actually succeeded.

## 22. COMMIT STYLE

Use concise conventional commits:

```
feat(games): add game session service
feat(offers): add provider adapter interface
feat(wallet): implement reward ledger
fix(withdrawals): prevent duplicate reservations
fix(cpa): reject duplicate postbacks
refactor(admin): split provider configuration
test(wallet): add concurrent debit tests
docs(cpa): document postback architecture
```

## 23. ONE LOGICAL CHANGE PER COMMIT

Avoid giant commits. Good: `feat(wallet): add ledger service`, then
`test(wallet): add concurrent transaction tests`, then
`feat(rewards): connect rewards to ledger`. Bad: `update everything`.

## 24. SESSION COMPLETION PROTOCOL

Before ending a meaningful session:

1. Confirm implementation.
2. Run tests.
3. Inspect `git diff`.
4. Update `.ai/STATE.md`.
5. Update `.ai/TASKS.md`.
6. Append a concise entry to `.ai/HISTORY.md`.
7. Update `.ai/MASTER.md` if architecture/integrations changed.
8. Update `.ai/DECISIONS.md` if an architectural decision was made.
9. Commit.
10. Push.
11. Confirm final `git status`.

## 25. ERROR PROTOCOL

If a test fails: read the complete error, identify the root cause, fix the root
cause, rerun the smallest relevant test, then broader tests. Do not hide the
error. Do not weaken tests simply to make them pass. If the failure is
unrelated to the current task, document it in `.ai/STATE.md` and continue only
if doing so is safe.

## 26. MIGRATION ERROR PROTOCOL

Do not randomly delete migrations. Inspect the migration graph, database state,
migration dependencies and model changes, then resolve the actual conflict.

## 27. PROVIDER ERROR PROTOCOL

If an external provider API is unavailable: do not fabricate successful
responses. Implement graceful failure handling, record the failure, use
retries only when safe, and use idempotency for retryable financial
operations.

## 28. TOKEN/CONTEXT EFFICIENCY

Optimize development context aggressively. Do not repeatedly read the entire
repository, database schema, documentation or unrelated modules.

Context hierarchy:

```
GOAL → RULES → STATE → TASKS → MASTER → relevant module docs
     → relevant source files → relevant tests
```

Stop reading once enough information is available to safely implement the
current task.

## 29. DO NOT REIMPLEMENT EXISTING FEATURES

Before creating a utility/service/helper, search the project for an existing
implementation and reuse it. Avoid duplicate authentication, wallet, reward,
provider, notification, validation and configuration logic.

## 30. CENTRALIZE IMPORTANT BUSINESS LOGIC

Use centralized services for rewards, wallet operations, withdrawals, deposits,
provider conversions, fraud decisions and campaign eligibility. This prevents
different parts of the application from implementing different versions of the
same rule.

## 31. ADMIN CONFIGURATION

Prefer database-backed configuration for business rules that need
administrative control. Security-critical infrastructure configuration must
not be exposed as arbitrary database settings. Do not turn every constant into
a database setting unnecessarily.

## 32. FINANCIAL CHANGES

Any change affecting reward percentages, wallet balances, withdrawal rules,
deposit rules, payment processing, points conversion or financial fees requires
extra care and tests. Inspect existing financial behavior before editing.

## 33. NO FAKE COMPLETION

Never say "implemented" unless the feature actually exists.
Never say "tested" unless tests were actually run.
Never say "pushed" unless `git push` actually succeeded.
Never fabricate provider/API credentials or successful external API responses.

## 34. CURRENT STATE IS AUTHORITATIVE

`.ai/STATE.md` describes the latest known project state. If it conflicts with
source code, inspect the source code and correct STATE.md. Do not blindly trust
stale documentation.

## 35. MASTER DOCUMENTATION MAINTENANCE

MASTER.md must remain concise enough to read quickly. It summarizes
architecture, modules, integrations, financial flow, reward flow, game flow,
payment flow, important configuration and current integration status. Do not
turn it into a dump of every source file.

## 36. TASK COMPLETION

When a task is genuinely complete, change `[ ]` to `[x]` in `.ai/TASKS.md`.
If partially completed, leave it unchecked and describe the remaining work in
`.ai/STATE.md`. Never mark unfinished work as complete.

## 37. FINAL CHECK

Before considering a task complete:

- code works
- relevant tests pass
- migrations are correct
- documentation is updated
- task status is updated
- `git diff` is reviewed
- commit exists
- push succeeds
- working tree is clean or intentionally documented

Then stop. Do not perform unrelated cleanup automatically.

---

## Quick commands (this repository)

| Action | Windows (PowerShell) | POSIX |
| --- | --- | --- |
| Project checks | `.\scripts\project-check.ps1` | `./scripts/project-check.sh` |
| Session finish | `.\scripts\session-finish.ps1` | `./scripts/session-finish.sh` |
| Tests | `.\.venv\Scripts\python.exe -m pytest` | `.venv/bin/python -m pytest` |
| Django check | `.\.venv\Scripts\python.exe manage.py check` | `.venv/bin/python manage.py check` |

## Session loop

```
Read GOAL → RULES → STATE → TASKS → MASTER
  → identify ONE task → inspect relevant code only → implement → test
  → update documentation → git diff → commit → push → update STATE → end
```
