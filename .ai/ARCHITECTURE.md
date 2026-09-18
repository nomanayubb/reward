# ARCHITECTURE (condensed)

Full version: `docs/ARCHITECTURE.md`.

## Request path

```
view / API / webhook / celery task
        ↓
service (transaction, locking, idempotency, ledger)
        ↓
models (constraints, persistence)
```

## Money path

```
validated revenue event
  → RewardRule resolution + calculation (apps/rewards/services.py)
  → pending ledger credit (platform cash → user pending)
  → approval (pending → cash / points)
  → withdrawal reserve (cash → locked)
  → payout (locked → platform cash)
```

## Module boundaries

- `apps/ledger` — the only place balances change.
- `apps/rewards` — the only place user credits are created.
- `apps/wallets` — account provisioning + system accounts.
- `apps/offers`, `apps/surveys`, `apps/games` — activity ingestion; call
  `RewardService`; never write ledger directly.
- `apps/cpa`, `apps/surveys/providers`, `apps/payments/providers` — external
  adapters only.
- `apps/fraud`/`apps/risk` — scoring + restrictions.
- `apps/automation` — event bus + rule execution.
- `apps/adminpanel` — runtime settings, RBAC, audit, feature flags.

## Events

`apps.automation.services.emit_event("OFFER_CONVERTED", user, payload)` — see
`PROJECT_RULES.md` and `docs/DRD.md` §11.

## Background jobs

Celery beat schedule in `config/settings/base.py` (sync offers/surveys, quotas,
pending rewards, deposits expiry, fraud sweep, daily stats).

## Deployment

Docker compose: `db`, `redis`, `web` (gunicorn), `worker`, `beat`, `nginx`.
Production: PostgreSQL + Redis required, HTTPS, games on separate origin.
