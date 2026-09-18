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
- KYC flow live: user submission page (`/kyc/`, basic + full levels with
  private document uploads) and the admin review queue
  (`/admin-panel/kyc/`) with approve/reject + audit. 7 tests (146 total).
- Reports live: CSV exports (users, financial/rewards, withdrawals, offers)
  generated via `apps/reports` services + Celery task, with the admin page
  `/admin-panel/reports/` (24h expiry). 4 tests (150 total).
- i18n live: language switcher, Urdu catalogue (navigation/dashboard),
  automatic RTL direction, and a pure-Python `.po`→`.mo` compiler
  (`scripts/compile_messages.py`) for machines without gettext. 3 tests
  (153 total).
- Earning actions complete: offer Start records an `OfferClick` and redirects
  to the provider tracking URL with the click id as `subid`; survey Start
  creates a `SurveySession` and redirects to the provider URL (graceful errors
  when a provider link is unavailable). 5 tests (158 total).
- Remaining-limit visibility live: offers show how many completions a user has
  left (today + lifetime + campaign) with the reset time, and exhausted offers
  appear in a "Not available right now" section with the reason; the games
  page shows plays left today and the reward per game. 6 tests (164 total).
- Direct-ads management live (`/admin-panel/ads/`): create banner/native/
  sponsorship campaigns with image upload, placements, schedule, weight and
  frequency caps; impressions/clicks/CTR stats; pause/activate with audit.
  4 tests (168 total).
- Network ad snippets supported: staff-authored HTML tags (AdSense/Adsterra/
  Monetag) render verbatim in placements, audit-logged; network tags handle
  their own clicks. 1 test (169 total).
- Multi-network console live (`/admin-panel/providers/?tab=...`): tabs for
  CPA / surveys / payments / ads plus an overview with emergency switches;
  per-network inventory counts, health, enable/disable, connection **Test**,
  manual syncs, and an "Add network" form (JSON config validated). Onboarding
  checklist in `docs/integrations/CPA_ONBOARDING.md`. 8 tests (176 total).
- Game catalog expanded: `tap-target`, `memory-match` and `snake` — each an
  original HTML5 game with its own documentation and a starter reward rule;
  `manage.py seed_reference_game` seeds all three.
- Earn hub live at `/earn/` with tabs (Games / Offers / Surveys): every tab
  shows its own activity list, and each offer exposes the full campaign rules
  (incentive policy, countries, devices, OS, reinstall, completions, remaining
  limits, campaign cap, min age, expiry) plus an offer detail page
  (`/offers/<id>/`). Catalog row builders centralized in services. 6 tests
  (182 total).
- Flexibility tooling: `docs/integrations/NETWORK_CATALOG.md` (34 catalogued
  platforms + per-network credential requirements) and
  `manage.py scaffold_provider <kind> <code>` which generates a full adapter
  stub (CPA / survey / payment) with TODOs and prints the adapter path.
  6 tests (188 total).
- Public pages live: landing page at `/` (redirects logged-in users to
  `/dashboard/`) and CMS-driven pages at `/p/<slug>/` (about, terms, privacy,
  contact, FAQ) seeded by `manage.py seed_cms_pages`; footer links on every
  page. These are the pages payment/CPA reviewers check. 6 tests (194 total).
- Free deployment path ready: `render.yaml` (Docker blueprint, production
  settings, generated SECRET_KEY, SQLite, auto-seeded) and
  `scripts/public-tunnel.ps1` (instant temporary URL via cloudflared);
  `docker/start.sh` is the container entrypoint (migrate → collectstatic →
  seed → gunicorn); production settings work without Redis.
- Own-server (no PaaS dependency) path ready: `docker-compose.prod.yml`
  (PostgreSQL + Redis + web + worker + beat + **Caddy with automatic HTTPS**),
  `docker/Caddyfile`, and the step-by-step `docs/deployment/VPS.md` guide
  (server, DNS, deploy, backups, migration from the temporary URL).
- Host-agnostic configuration: production settings are fully environment-driven
  (`ALLOWED_HOSTS`, `EXTRA_ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, optional
  Redis); the only Render-aware line is an optional hostname auto-detect that
  is ignored elsewhere. Verified with a production-settings smoke test.
- SEO live: `/robots.txt` (public pages allowed, app/admin disallowed),
  `/sitemap.xml` (landing + published CMS pages) and per-path metadata from
  `SEOConfig` (title, description, robots, canonical, OG tags) via a cached
  context processor. 5 tests (199 total).
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
2. Ad network integration, deeper analytics dashboards, reconciliation workflow
3. Remaining translations (beyond navigation) as the UI grows

## Known Problems

- NOWPayments adapter is implemented and unit-tested but **not verified against
  the live/sandbox API** — credentials required (see docs/integrations/NOWPAYMENTS.md)
- No CPA / survey / EasyPaisa adapters yet (interfaces + manual provider only)
- Ad network **accounts** and per-campaign policy verification are business
  steps (the snippet capability is built; house/direct serving is live —
  ADR-013)
- Reports run inline (switch to Celery `.delay()` once a worker is deployed)
- Urdu catalogue covers navigation/dashboard strings only
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
