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
- Ruff configured (`ruff.toml`); `scripts/project-check` passes end-to-end
  (Django check + migrations + tests + lint)
- Auth API live: `/api/v1/auth/register|login|logout|me/` with 8 tests
- Wallet + ledger read API live: `GET /api/v1/wallets/summary/`,
  `GET /api/v1/ledger/transactions/` with 8 tests (55 tests total)
- Earning catalog APIs live: `GET /api/v1/games/`, `GET /api/v1/offers/`
  (eligibility-filtered), `GET /api/v1/surveys/`
- Money movement APIs live: `GET/POST /api/v1/withdrawals/`,
  `GET/POST /api/v1/withdrawals/methods/`, `GET/POST /api/v1/deposits/`
  (manual provider adapter for development/testing)
- Notifications API live: list/unread filter, mark read, read-all, unread count
- Game session API live: start session, report event, end session (server-side
  validation + reward) — 77 tests total
- Game SDK live (`static/game-sdk/game-sdk.js` + `game-host.js`), player page
  at `/play/<slug>/`, asset serving at `/games/<slug>/<asset>`, and the first
  playable game `games/tap-target/` with its own documentation; seed command
  `manage.py seed_reference_game` — 84 tests total
- NOWPayments adapter implemented (`create_payment`, `check_payment`,
  HMAC-SHA512 IPN verification, status mapping); PKR deposits convert to USD
  with the stored rate. 8 tests (92 total). Live verification pending creds.
- Frontend live (server-rendered): base layout + nav, login/register/logout,
  dashboard, wallet, transactions, games/offers/surveys catalogs, withdraw
  (with payout methods), deposit (with instructions), alerts. 19 new tests
  (111 total).
- Admin operations UI live at `/admin-panel/` (staff only): metrics dashboard
  (users, provider revenue, rewards by currency, open withdrawals, user
  liability, fraud) and the withdrawal review queue with approve/pay/reject
  actions, audit-logged. 7 tests (118 total).
- Admin user management + configuration center live: user search/detail,
  freeze/unfreeze, granular restrictions, audited balance adjustments (ledger
  transaction + audit log), editable `PlatformSetting` values with
  `ConfigurationVersion` history, and feature-flag toggles. 7 tests
  (125 total).
- Admin provider management live: per-provider enable/disable, manual
  offer/survey syncs, and emergency kill switches (games/offers/surveys/
  deposits/withdrawals) enforced across services. 7 tests (132 total).
- Ad serving live: weighted rotation, frequency caps (hour/day/interval),
  impression + click tracking, `/ads/click/<impression>/` redirect, slots on
  the dashboard and games pages; `manage.py seed_ad_placements` creates the
  standard placements. 7 tests (139 total).
- Fixed reward-engine bugs found while building the wallet API: points were
  double-credited and duplicate points accounts existed (ADR-014)
- Currency migration (ADR-015): slices 1-2 done — multi-currency wallets,
  per-currency ledger integrity, exchange-rate service (`EXCHANGE_RATE_USD_PKR`),
  rewards pay **PKR by default** with the conversion rate stored per reward,
  wallet default currency is PKR
- Requirements traceability matrix: `.ai/REQUIREMENTS.md` (50 areas +
  integration status + decisions needed)
- Session conversation logs: `.ai/sessions/` (one append-only log per session;
  newest log read at session start)
- Git repository initialized; initial commit created

## In Progress

- (none)

## Next

1. Real provider adapters (CPA, survey, EasyPaisa) — needs network choices
   (`.ai/REQUIREMENTS.md`)
2. KYC flow UI, reports/exports, Urdu/i18n
3. Ad network integration (after per-campaign policy verification)

## Known Problems

- NOWPayments adapter is implemented and unit-tested but **not verified against
  the live/sandbox API** — credentials required (see docs/integrations/NOWPAYMENTS.md)
- No CPA / survey / EasyPaisa adapters yet (interfaces + manual provider only)
- Ad network integration not done (house/direct serving is live; networks need
  policy verification first — ADR-013)
- Test coverage gaps: postback end-to-end, quota edge cases, true parallel
  concurrency

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
