# CODING_RULES

## Style

- Python 3.11+, 4-space indent, ~100 char lines.
- Imports: stdlib, third-party, local (blank-line separated). Prefer explicit
  imports; no wildcard imports.
- Type hints on public service functions and dataclasses.
- Docstrings on services, models and non-obvious functions: what and why.
- No comments that restate code. Comments explain business rules or gotchas.

## Layering

```
view/api/webhook/task  →  service  →  model
```

- Views: auth, parse, call service, serialize, map errors to HTTP status.
- Services: `@transaction.atomic` where money moves, `select_for_update` for
  balances, idempotency keys for external events.
- Models: fields, constraints, small helpers. No cross-module business logic.
- Tasks: thin wrappers calling services; must be safe to retry.
- Templates: rendering only — no queries with business meaning, no conditionals
  that decide money.

## Errors

- Raise domain exceptions (`RewardError`, `WithdrawalError`, `DepositError`,
  `LedgerError`) from services; views translate them to 400/409 responses.
- Never swallow exceptions silently; log with context (`user`, ids, provider).
- Automation/provider failures must not roll back money already committed.

## Naming

- Modules own plural app names; services use verb names
  (`post_transaction`, `request_withdrawal`, `process_postback`).
- Idempotency keys: `reward:{id}:pending`, `withdrawal:{id}:reserve`,
  `deposit:{id}`, `reversal:{txn_id}`, `cpa:{provider}:{conversion_id}`.

## Testing

- Every money path needs a test in `tests/` or the module's `tests/`.
- Critical invariants live in `tests/test_critical_flows.py` — extend, do not
  weaken them.
- Use `pytest` with `config.settings.test` (fast hashes, locmem cache, eager
  celery).
- Provider adapters: unit test the parser with recorded sandbox payloads.

## Dependencies

- Add packages to `requirements/base.txt` (runtime) or `development.txt`
  (tooling only). Pin minimum versions; avoid niche packages for core paths.
- Do not introduce a second framework (e.g. another ORM/task queue).
