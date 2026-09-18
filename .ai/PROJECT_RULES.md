# PROJECT_RULES — AI context pack

Read this before changing code in this repository.

## What this project is

A configurable rewards platform (games, surveys, CPA offers) with an immutable
ledger, configurable reward engine, fraud/risk, deposits/withdrawals
(NOWPayments + Pakistani local payments) and a full admin back office.

Stack: Django 5.1 + DRF, PostgreSQL, Redis + Celery, Docker/Nginx/Gunicorn.

## Non-negotiable rules

1. **Never write business logic in views or templates.** Views parse/authorize/
   serialize; services own rules and transactions.
2. **Never touch `WalletAccount.balance` directly.** Use
   `apps.ledger.services.post_transaction` (balanced, locked, idempotent).
3. **Never hard-code reward splits.** Use `RewardRule` +
   `RewardService`. All user credits go through `RewardService`.
4. **Never add provider `if/else`.** Add an adapter under `apps/*/providers/`.
5. **Never trust client values for money** (game score, reward requests,
   conversion amounts).
6. **Money is Decimal** (`apps.common.fields.money_field`), never float.
7. **Everything configurable at runtime** goes in `PlatformSetting` (read via
   `apps.adminpanel.settings.get_setting`), not in settings constants.
8. **Idempotency keys** for every external/financial event.
9. **Corrections are reversals**, never updates/deletes of ledger or audit rows.
10. **Do not commit secrets.** `.env` is ignored; add new keys to `.env.example`.

## Where things live

- `config/settings/{base,development,production,test}.py`
- `apps/<module>/{models,services,views,urls,tasks,admin}.py` + `README.md`
  (module contract), `providers/` for adapters, `tests/`.
- `docs/` — PRD, DRD, ARCHITECTURE, DATABASE, GAME_INTEGRATION,
  CPA_INTEGRATION.
- `games/<slug>/` — self-contained HTML5 games with their own docs.
- `tests/` — cross-module tests, including `test_critical_flows.py`.

## Workflow

- Run `python manage.py check` and `pytest` after changes.
- Generate migrations with `makemigrations`; never edit the production schema
  by hand.
- Update the relevant doc (PRD/DRD/module README) in the same change as the
  behavior change.
- Follow `CODING_RULES.md`, `REWARD_RULES.md`, `DATABASE_RULES.md`,
  `SECURITY_RULES.md` in this folder.
