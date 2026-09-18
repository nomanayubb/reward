# DATABASE_RULES

## Money and precision

- Use `apps.common.fields.money_field` → `NUMERIC(20,8)`.
- Nullable money fields have **no default** (NULL = not configured). Never
  give a nullable limit/amount a `0` default — it changes semantics (this bug
  once clamped every reward to zero).
- Never use `float` for money or points.

## Ledger invariants

- `LedgerEntry` rows are immutable (update/delete raise).
- A `LedgerTransaction`'s entries sum to zero; enforced by
  `post_transaction`.
- `WalletAccount.balance` is a cache; recompute with
  `ledger.services.account_balance` when verifying.
- Every external financial event uses a unique `idempotency_key`.

## Constraints over checks

Prefer database constraints for correctness:

- `unique(provider, external_conversion_id)` on conversions.
- `unique(provider, external_id)` on payment transactions.
- `unique(wallet, type, currency)` on wallet accounts.
- Partial unique `(source, source_reference, user)` on rewards where
  `source_reference <> ''`.
- `unique(offer)` on `CampaignQuota`.

Application checks alone are race-prone.

## Migrations

- Generate with `makemigrations`; never hand-edit applied migrations.
- Data migrations for backfills; keep them idempotent.
- Add indexes with new query patterns; check with `EXPLAIN ANALYZE`.

## JSON fields

Use `JSONField` for provider payloads, conditions, configs, metadata — not for
anything queried relationally or constrained.

## Audit and retention

`adminpanel.AuditLog` and `ledger.LedgerEntry` are append-only. Do not add
cascading deletes that would remove financial history; use `PROTECT`/`SET_NULL`
deliberately.
