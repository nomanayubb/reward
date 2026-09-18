# DEVELOPMENT HISTORY

## 2026-09-18

### Completed

- Initialized the Django project: config package (base/development/production/
  test settings), Celery, WSGI/ASGI, Docker, Nginx, requirements, `.env.example`.
- Created all 26 domain apps with models, admin registrations and initial
  migrations (accounts, users, wallets, ledger, rewards, payments, deposits,
  withdrawals, games, surveys, offers, cpa, advertising, bonuses, referrals,
  fraud, risk, kyc, notifications, automation, analytics, reports, cms, seo,
  support, adminpanel).
- Implemented the immutable double-entry ledger with row locking, idempotency
  keys and reversal transactions.
- Implemented wallet provisioning, system (platform) wallet and liability
  totals.
- Implemented the configurable reward engine (rule resolution, calculation,
  pending → approved lifecycle, hold/reject/reverse).
- Implemented offers: eligibility engine, campaign quotas, clicks, postback
  ingestion, conversions.
- Implemented surveys (sessions/completions), games (sessions/validation),
  deposits, withdrawals, fraud/risk, automation event bus, notifications.
- Added CPA / survey / payment provider adapter interfaces.
- Added Celery tasks and beat schedule.
- Added postback and payment webhook endpoints; OpenAPI schema + Swagger UI.
- Wrote and passed 11 critical business-rule tests.
- Wrote documentation: PRD, DRD, ARCHITECTURE, DATABASE, GAME_INTEGRATION,
  CPA_INTEGRATION, plus the initial `.ai/` pack.
- Fixed a money-field default bug where nullable money fields received a `0`
  default, causing `max_user_reward` to clamp every reward to zero.

### Changed

- Established the modular monolith architecture with a service layer and
  provider adapters.
- Adopted the AI development protocol: `.ai/` project memory (GOAL, RULES,
  STATE, TASKS, HISTORY, MASTER, DECISIONS, SESSION), `AGENTS.md`, and
  `scripts/project-check` / `scripts/session-finish`.
- Aligned `.ai/TASKS.md` and `.ai/STATE.md` with the verified status
  (admin/user-app gaps, test-coverage gaps, ads status) and recorded
  ADR-013 (ad monetization policy).
- Configured `ruff` (`ruff.toml`, Django-aware rule set) and fixed all lint
  findings (import sorting, unused imports, simplifications, `StrEnum`);
  `scripts/project-check` now passes end-to-end.
- Added the auth API (`apps/accounts`: serializers, views, routes) —
  `POST /api/v1/auth/register/`, `login/`, `logout/`, `GET me/` — with 8 API
  tests (19 tests total). Registration reuses `register_user` (wallet +
  referral provisioning) and applies Django password validators.
- Added `.ai/REQUIREMENTS.md`: traceability of the master spec (50 areas) to
  done/partial/not-started, integration status (no CPA/survey/payment network
  connected yet) and the decisions needed from the product owner.
- Added `.ai/sessions/` conversation-log convention (one append-only log per
  session with requests, actions, decisions, blockers; the newest log is read
  at session start) and logged this session.
- Added wallet + ledger read APIs: `GET /api/v1/wallets/summary/` and
  `GET /api/v1/ledger/transactions/` (type/status filters, paginated,
  user-scoped) with 8 tests (27 total).
- Fixed two reward-engine bugs found while building the wallet API: points
  were credited twice (award + approve) and duplicate points accounts existed
  (USD + POINTS currency). Points now use a system pending-points holding
  account and approved-reward reversal unwinds both postings (ADR-014).
- Recorded ADR-015 (PKR-first currency model) after product-owner decision:
  direct PKR rewards, dual wallets (PKR primary / USD for crypto), points
  disabled by default, USD→PKR conversion with the rate stored per transaction.
- ADR-015 slice 1: multi-currency wallet accounts (on-demand per currency) and
  per-currency ledger integrity (each currency must balance; cross-currency
  leakage rejected) with 4 tests (31 total).
- ADR-015 slice 2: exchange-rate service (`EXCHANGE_RATE_USD_PKR`, admin-set,
  rate stored on every reward), reward engine pays **PKR by default** with
  percentage rewards converted from USD and fixed amounts already in the
  reward currency; wallet default currency is PKR; deposits/withdrawals
  default to the wallet currency; platform share is computed in the revenue
  currency. Global test cache clearing added. 42 tests total.
- ADR-015 slice 3: withdrawal limits are configured in PKR
  (`MIN/MAX_WITHDRAWAL_PKR`, `KYC_THRESHOLD_PKR`, `AUTO_PAYOUT_MAX_PKR`,
  `DUAL_APPROVAL_THRESHOLD_PKR`) and converted per wallet currency; 5 new
  limit tests (47 total). Docs updated (DRD W5/W6).
- ADR-015 slice 4 (migration complete): wallet summary returns per-currency
  buckets (`balances` list, PKR primary + USD) alongside the primary-currency
  fields; API docs updated to mark auth/wallets/ledger as live. 48 tests.

### Tests

- `python manage.py check` — no issues.
- `pytest` — 11 passed (`tests/test_critical_flows.py`).

### Git

Commit: `0e69b96` — chore: initialize reward platform foundation and AI
development protocol
Push: successful — `origin/main` at `5e29c59`
(remote: https://github.com/nomanayubb/reward.git)

### Next

Implement the user-facing REST API (auth, wallet, ledger, offers, withdrawals,
notifications).
