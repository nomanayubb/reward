# PROJECT RULES

**Do not rediscover the project. Continue the project.**

## Rule 1 — Read Before Modifying

Before modifying the project, read:

```
.ai/GOAL.md
.ai/RULES.md
.ai/STATE.md
.ai/TASKS.md
```

Then read only the documentation relevant to the task. Do not unnecessarily
read the entire repository.

## Rule 2 — Preserve Existing Functionality

Never rewrite or replace working systems without a specific reason. Prefer
small, isolated changes. Before changing shared infrastructure, inspect all
known consumers.

## Rule 3 — Understand Before Editing

Before modifying a file: inspect it, understand its dependencies, identify
callers, identify tests, then make the smallest safe change. Never modify code
based only on its filename.

## Rule 4 — No Fake Implementations

Never create fake payment confirmations, CPA conversions, survey completions,
wallet credits, withdrawal approvals or provider responses. If an integration
is unavailable, implement the interface and clearly mark the integration as
incomplete.

## Rule 5 — Money Uses Decimal

Never use floating point for financial amounts. Use `Decimal` / `NUMERIC`.
Use `apps.common.fields.money_field`. Nullable money fields must not receive a
`0` default (NULL means "not configured").

## Rule 6 — Ledger Is the Financial Source of Truth

Never directly manipulate financial balances without an auditable ledger
transaction. Never delete financial history. Use reversals/adjustments.
`WalletAccount.balance` is a cache, not the truth.

## Rule 7 — External Webhooks Must Be Idempotent

Every provider conversion/payment callback must safely handle duplicate
callbacks using unique external identifiers and database constraints.

## Rule 8 — Provider Adapters

External providers must be isolated behind provider interfaces/adapters
(`apps/*/providers/`). Do not spread provider-specific logic through
views/templates/models.

## Rule 9 — Security

Never hard-code secrets, commit API keys/passwords, expose private payment
data, disable CSRF, or bypass authentication/authorization. Use environment
variables. See `.ai/SECURITY_RULES.md`.

## Rule 10 — Tests

Every meaningful backend feature must have appropriate tests. Bug fixes should
add a regression test when practical. Critical invariants live in
`tests/test_critical_flows.py`.

## Rule 11 — Documentation

When behavior changes, update the relevant documentation. Do not allow
documentation to become misleading. Module contracts live in
`apps/<module>/README.md`; product/domain docs live in `docs/`.

## Rule 12 — Git

After a coherent successful change:

1. inspect `git status`
2. inspect `git diff`
3. run tests
4. commit
5. push

Never commit secrets. Never use destructive git commands unless explicitly
authorized.

## Rule 13 — Git Commit Quality

Use descriptive conventional commits:

```
feat(wallet): add withdrawal reservation
fix(offers): prevent duplicate conversion rewards
docs(cpa): document provider adapter
refactor(games): isolate game event service
test(wallet): add concurrent withdrawal test
```

## Rule 14 — Don't Mix Unrelated Changes

One logical change per commit whenever practical. Do not combine payment
changes, UI redesign, unrelated refactoring and documentation cleanup into one
giant commit.

## Rule 15 — Don't Overengineer Early

Build the simplest architecture that satisfies the current requirement while
preserving clear extension points. Do not add infrastructure merely because it
may someday be useful.

## Rule 16 — Performance

Prefer database indexes, `select_related`, `prefetch_related`, pagination,
caching, asynchronous jobs and bulk operations. Avoid N+1 queries.

## Rule 17 — AI Context Efficiency

Do not repeatedly read the entire repository. Use `.ai/STATE.md`,
`.ai/TASKS.md`, `.ai/MASTER.md` to understand the current project, then
inspect only files relevant to the current task.

## Rule 18 — Update Project Memory

At the end of every meaningful session update `.ai/STATE.md` and
`.ai/HISTORY.md`. Write the session conversation log in
`.ai/sessions/YYYY-MM-DD-<topic>.md` (user requests, actions, decisions,
blockers — append-only). Update `.ai/TASKS.md` when task status changes.
Update `.ai/MASTER.md` when architecture/integration behavior changes.
Update `.ai/REQUIREMENTS.md` when requirement status changes. Record
architecture decisions in `.ai/DECISIONS.md`.

## Rule 19 — Stop on Ambiguity

If an implementation decision could materially affect financial accounting,
security, data integrity, provider compliance, authentication or payment
processing, do not silently guess. Explain the ambiguity and choose the safest
documented behavior only when it is clearly inferable.

## Rule 20 — Never Optimize by Removing Safety

Speed means efficient engineering. It does not mean skipping tests,
migrations, validation, security, accounting controls or provider
verification.

## Detailed rule files

- `.ai/CODING_RULES.md` — layering, style, naming, errors, tests
- `.ai/DATABASE_RULES.md` — precision, constraints, migrations, immutability
- `.ai/SECURITY_RULES.md` — secrets, webhooks, auth, games, data protection
- `.ai/REWARD_RULES.md` — reward engine invariants and configuration
- `.ai/ARCHITECTURE.md` — condensed system architecture
