# CURRENT PROJECT STATE

Updated: 2026-09-18

## Current Phase

Phase 1 — Core Foundation: **complete**
Phase 2 — Games / Surveys / Offers: **core services implemented, adapters + UI pending**

## Current Focus

Adopting the AI development protocol (`.ai/` memory system, `AGENTS.md`,
scripts, Git) and then implementing the user-facing REST API.

## Completed

- Django project + config package (base/development/production/test)
- PostgreSQL/Redis/Celery configuration (SQLite + locmem fallback in dev)
- Custom user model (`accounts.User`) + Argon2
- All 26 domain apps created with models, admin registrations, migrations
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
- Postback + payment webhook endpoints
- Django admin registered for every model
- 11 critical business-rule tests passing
- Docs: PRD, DRD, ARCHITECTURE, DATABASE, GAME_INTEGRATION, CPA_INTEGRATION

## In Progress

- AI development protocol setup (this session)

## Next

1. Implement user-facing REST API (auth/register/login/me, wallet, ledger,
   offers, withdrawals, notifications)
2. Build Game SDK + first game package
3. Implement real provider adapters (CPA, survey, NOWPayments, EasyPaisa)
4. Frontend templates (homepage, earn pages, wallet, withdraw, dashboard)
5. Admin configuration UI beyond Django admin

## Known Problems

- Business API endpoints are empty stubs (only schema/docs/callbacks exist)
- No real provider adapters implemented yet (interfaces only)
- No frontend templates yet
- Git repository not initialized until 2026-09-18 (no remote configured yet)
- Git push not possible until a remote is added

## Important Decisions

- PostgreSQL is the production database (SQLite dev/test only)
- Redis is cache + Celery broker
- Ledger is the financial source of truth; balances are cached projections
- Provider integrations use adapters only
- Reward rules are database configuration, not code
- Games run isolated (sandboxed iframe, separate origin in production)

## Current Git

Branch: main (to be initialized)
Remote: none configured
Working tree: n/a
