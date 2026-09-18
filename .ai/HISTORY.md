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
- Added earning-catalog APIs: `GET /api/v1/games/` (active games),
  `GET /api/v1/offers/` (only offers the user is eligible for, via the shared
  eligibility engine; tracking URLs never exposed) and `GET /api/v1/surveys/`
  (active surveys). 7 new tests (55 total).
- Added money-movement APIs: `GET/POST /api/v1/withdrawals/` (fund reservation
  via the service layer), `GET/POST /api/v1/withdrawals/methods/` (ownership
  enforced) and `GET/POST /api/v1/deposits/`; added a `manual` payment
  provider adapter for development/testing. 10 new tests (65 total).
- Added notifications API (list, unread filter, mark read, read-all, unread
  count) and the game session API (start/report event/end) that the Game SDK
  will call; ending a session runs server-side validation and pays rewards.
  12 new tests (77 total).
- Added the Game SDK (`static/game-sdk/game-sdk.js` iframe side +
  `game-host.js` platform side with source/origin validation), the player page
  (`/play/<slug>/`), development asset serving (`/games/<slug>/<asset>` with
  path-traversal protection), and the first playable game
  `games/tap-target/` with its own documentation. Added
  `manage.py seed_reference_game` to create the game + starter rule.
  7 new tests (84 total).
- Implemented the NOWPayments adapter (real HTTP client, HMAC-SHA512 IPN
  verification, status mapping, PKR→USD invoice conversion with the stored
  rate). Payouts intentionally raise `NotImplementedError` until payout API
  verification. Setup + sandbox checklist in `docs/integrations/NOWPAYMENTS.md`.
  8 tests (92 total). Live verification pending credentials.
- Added the server-rendered frontend: base layout + navigation, auth pages
  (login/register/logout with Django forms), dashboard (balances, recent
  rewards), wallet, transaction history, games/offers/surveys catalogs,
  withdraw page (payout methods + request form), deposit page (payment
  instructions) and alerts. Fixed a class-shadowing bug where the page login
  view inherited from the DRF login view. 19 new tests (111 total).
- Added the admin operations UI (`/admin-panel/`, staff only): metrics
  dashboard (users, provider revenue, rewards by currency, open withdrawals,
  user liability, open fraud events) and the withdrawal review queue with
  approve/pay/reject actions, all audit-logged via `AuditLog`. 7 tests
  (118 total).
- Added admin user management (search, detail, freeze/unfreeze, granular
  restrictions, audited balance adjustments via a ledger `ADJUSTMENT`
  transaction) and the configuration center (editable `PlatformSetting`
  values with `ConfigurationVersion` history + audit, feature-flag toggles).
  7 tests (125 total).
- Added admin provider management: per-provider enable/disable for CPA,
  survey, payment and ad providers, manual offer/survey sync buttons, and
  emergency kill switches (`GAMES_ENABLED`, `OFFERS_ENABLED`,
  `SURVEYS_ENABLED`, `DEPOSITS_ENABLED`, `WITHDRAWALS_ENABLED`) enforced in
  the services and catalog views. 7 tests (132 total).
- Added ad serving (ADR-013 house-first): weighted rotation, frequency caps
  (per hour / per day / minimum interval), impression recording, click
  tracking with redirect (`/ads/click/<impression>/`), an ad slot partial
  rendered on the dashboard and games pages, and
  `manage.py seed_ad_placements`. Ad clicks are never rewarded. 7 tests
  (139 total).
- Added the KYC flow: user submission page (`/kyc/`) with basic and full
  levels, private document uploads, resubmission rules, and the admin review
  queue (`/admin-panel/kyc/`) with approve/reject and audit logging.
  7 tests (146 total).
- Added CSV reports (`apps/reports`): users, financial/rewards, withdrawals
  and offer conversions, generated by a Celery-safe task and exposed on the
  admin reports page with 24-hour expiry. 4 tests (150 total).
- Added i18n: language switcher in the header, an Urdu catalogue for the
  navigation/dashboard strings, automatic RTL direction (`dir="rtl"` + RTL
  styles), and a pure-Python `.po`→`.mo` compiler
  (`scripts/compile_messages.py`) so translations build without gettext.
  3 tests (153 total).
- Completed the earning actions: the offers page now has a Start action that
  records an `OfferClick` and redirects to the provider tracking URL tagged
  with the click id as `subid`; the surveys page has Start, which creates a
  `SurveySession` and redirects to the provider URL. 5 tests (158 total).
- Added remaining-limit visibility: offers show today/lifetime/campaign
  completions left plus the daily reset time, exhausted offers move to a
  "Not available right now" section with reasons; the games page shows plays
  left today and the reward per game. 6 tests (164 total).
- Added direct-ads management (`/admin-panel/ads/`): create direct/house
  campaigns (banner, native, sponsorship) with image upload, placements,
  schedule, weight and frequency caps, plus impressions/clicks/CTR stats and
  pause/activate actions, all audit-logged. 4 tests (168 total).
- Added network ad snippet support: staff-authored HTML tags (AdSense/
  Adsterra/Monetag) render verbatim in placements and are audit-logged;
  network tags handle their own clicks (no internal redirect). 1 test
  (169 total).
- Added the multi-network admin console: tabs per network type (overview with
  emergency switches, CPA, surveys, payments, ads), inventory counts, health,
  enable/disable, connection tests (honest failures when adapters/credentials
  are missing), manual syncs, and an Add-network form with validated JSON
  config. Added `docs/integrations/CPA_ONBOARDING.md` (what to get from each
  network and what to send). 8 tests (176 total).
- Expanded the game catalog with two more original HTML5 games: Memory Match
  (4×4 pairs, move-efficient scoring) and Snake (20×20 grid, 90s), each with
  its own documentation and a starter reward rule; `seed_reference_game` now
  seeds all three games.
- Added the tabbed Earn hub (`/earn/`): Games / Offers / Surveys tabs, each
  showing its own catalog, with full per-offer campaign rules displayed
  (incentive policy, countries, devices/OS, reinstall, completion rules,
  remaining daily/lifetime/campaign limits, min age, expiry) and a dedicated
  offer detail page. Catalog row logic centralized in
  `games.services.catalog_rows` / `offers.services.catalog_rows`. 6 tests
  (182 total).
- Added flexibility tooling: `docs/integrations/NETWORK_CATALOG.md` (34
  platforms across offerwalls, surveys, CPA and ad networks, with the six
  credential values needed per network) and the
  `manage.py scaffold_provider` command that generates a complete adapter stub
  (CPA/survey/payment) with TODOs, refuses to overwrite, and prints the
  adapter path for the admin. 6 tests (188 total).
- Added public pages for provider review: a landing page at `/` (how it works,
  ways to earn, clear-rules section; logged-in users redirect to
  `/dashboard/`), CMS-driven pages at `/p/<slug>/` for about, terms, privacy,
  contact and FAQ, footer links on every page, and `manage.py seed_cms_pages`
  with starter content (placeholders flagged for replacement). 6 tests
  (194 total).
- Added a free deployment path: `render.yaml` blueprint (Docker, production
  settings, generated SECRET_KEY, SQLite, health check), `docker/start.sh`
  entrypoint (migrate → collectstatic → seed → gunicorn) and
  `scripts/public-tunnel.ps1` for an instant temporary public URL. Production
  settings now run without Redis (locmem fallback) and trust Render's
  hostname automatically. Deployment docs updated.
- Added the own-server (no PaaS dependency) production stack:
  `docker-compose.prod.yml` with PostgreSQL, Redis, web, Celery worker/beat and
  Caddy (automatic Let's Encrypt HTTPS), `docker/Caddyfile`, `.env` keys for
  DOMAIN/POSTGRES_*, and `docs/deployment/VPS.md` (server setup, DNS, deploy,
  backups, and the checklist for moving off a temporary URL).
- Made production settings fully host-agnostic: `ALLOWED_HOSTS` +
  `EXTRA_ALLOWED_HOSTS` + `CSRF_TRUSTED_ORIGINS` from the environment, optional
  Redis, and the Render hostname check reduced to an optional convenience that
  is ignored elsewhere. Verified with a production smoke test and the full
  suite (194 tests).
- Added SEO essentials: `/robots.txt` (allows the landing page and CMS pages,
  disallows app/admin/api paths), `/sitemap.xml` (landing page + published CMS
  pages) and per-path metadata from `SEOConfig` (title, description, robots,
  canonical, OG tags) through a cached context processor with safe defaults.
  5 tests (199 total).
- Added the AdGem integration paths: the Web Offerwall page
  (`/offers/offerwall/adgem/`, stable `u<uuid>` player id, needs only the App
  ID), offerwall postback resolution by player id with automatic offer
  provisioning and compliance gating, and the Reporting API client with a
  reconciliation service + `manage.py reconcile_provider` command (verified
  live with the dashboard token). Added the AdGem adapter's Cloudflare-safe
  User-Agent. 20 tests (223 total).

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
