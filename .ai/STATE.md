# CURRENT PROJECT STATE

Updated: 2026-09-18

## Current Phase

Phase 1 — Core Foundation: **complete**
Phase 2 — Games / Surveys / Offers: **core services implemented, adapters + UI pending**

## Current Focus

Repository + AI development protocol are in place. Next: user-facing REST API.

## Completed

- Django project + config package (base/development/production/test)
- PostgreSQL/Redis/Celery configuration (SQLite + locmem fallback in dev)
- Custom user model (`accounts.User`) + Argon2
- All 26 domain apps with models, admin registrations, migrations
- Immutable double-entry ledger (locking, idempotency, reversals)
- Wallets (cash/points/bonus/pending/locked/withdrawable/deposit) + system wallet
- Reward engine (rule resolution, calculation, pending → approved lifecycle)
- Offers: eligibility engine, quotas, clicks, conversions, postbacks
- Surveys: sessions, completions, provider interface
- Games: sessions, server-side validation, reward rules
- Deposits/withdrawals services with full state machines and fund reservation
- CPA / survey / payment provider adapter interfaces
- Fraud/risk scoring, restrictions, automation event bus, notifications
- Celery tasks (offers, surveys, rewards, deposits, fraud, analytics)
- Postback + payment webhook endpoints; OpenAPI schema + Swagger UI
- Django admin registered for every model
- 11 critical business-rule tests passing
- Docs: PRD, DRD, ARCHITECTURE, DATABASE + `docs/integrations/*`
- AI development protocol: `.ai/` memory, `AGENTS.md`, check scripts,
  GitHub Actions CI, docs folder structure
- Git repository initialized; initial commit created

## In Progress

- (none)

## Next

1. Implement user-facing REST API (auth/register/login/me, wallet, ledger,
   offers, withdrawals, notifications) — start with `apps/accounts` auth
2. Build Game SDK + first game package
3. Implement real provider adapters (CPA, survey, NOWPayments, EasyPaisa)
4. Frontend templates (homepage, earn pages, wallet, withdraw, dashboard)
5. Admin configuration UI beyond Django admin

## Known Problems

- Business API endpoints are empty stubs (only schema/docs/callbacks exist)
- No real provider adapters implemented yet (interfaces only)
- No frontend templates yet
- `ruff` reports 321 findings (no config yet) — `scripts/project-check` fails
  at the lint step until configured/fixed

## Important Decisions

- PostgreSQL is the production database (SQLite dev/test only)
- Redis is cache + Celery broker
- Ledger is the financial source of truth; balances are cached projections
- Provider integrations use adapters only
- Reward rules are database configuration, not code
- Games run isolated (sandboxed iframe, separate origin in production)
- Development follows `AGENTS.md` (read memory → one task → test → document →
  commit → push)

## Current Git

Branch: main
Last known commit: 5e29c59
Remote: origin — https://github.com/nomanayubb/reward.git
Working tree: clean
