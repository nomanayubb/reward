# TASKS

## P0 — Foundation

- [x] Initialize Django project
- [x] Configure settings (base/development/production/test)
- [x] Configure PostgreSQL (dev SQLite fallback)
- [x] Configure Redis / cache
- [x] Configure Celery + beat
- [x] Custom user model (email, Argon2)
- [x] Wallet + wallet accounts
- [x] Immutable ledger (locking, idempotency, reversals)
- [x] Reward engine (rules, calculation, lifecycle)
- [x] Admin registrations for all models
- [x] Critical business-rule tests (11 passing)
- [x] AI development protocol (.ai memory, AGENTS.md, scripts)
- [x] Ruff configuration (project-check passes end-to-end)
- [ ] Extra test coverage: deposits, postback end-to-end, quotas/eligibility,
      true parallel concurrency, points ledger
- [x] Auth API (register/login/logout/me) + 8 tests
- [x] Wallet + ledger read endpoints (`/wallets/summary/`, `/ledger/transactions/`) + 8 tests
- [x] PKR migration (ADR-015): slice 1 multi-currency wallets + per-currency ledger check
- [x] PKR migration: slice 2 exchange-rate service + USD→PKR reward conversion
- [x] PKR migration: slice 3 withdrawal/deposit limits + fees in PKR
- [x] PKR migration: slice 4 API/tests/docs updates
- [x] Offers / surveys / games listing endpoints
- [x] Withdrawal request/list endpoints (+ payout methods)
- [x] Deposit create/list endpoints (+ manual provider adapter)
- [x] Notifications endpoints (list, read, read-all, unread count)
- [x] Frontend templates (home, earn, wallet, withdraw, dashboard, alerts, auth)

## P1 — Games

- [x] Game / category / session / event models
- [x] Server-side session validation + reward rules
- [x] Game session / event / end API (Game SDK server side)
- [x] Game SDK (`static/game-sdk/`)
- [x] Game iframe wrapper view + origin checks
- [x] First game package (`games/tap-target/` + docs)
- [ ] Game player page + reward rules display

## P2 — Offers / CPA

- [x] Provider interface + normalized types
- [x] Offer model with compliance flags
- [x] Click tracking + conversions + postbacks
- [x] Eligibility engine + campaign quotas
- [x] Idempotency on (provider, external_conversion_id)
- [ ] First real CPA provider adapter
- [ ] Second CPA provider adapter
- [ ] Offer list/detail API + pages
- [ ] Provider reconciliation job

## P3 — Surveys

- [x] Provider interface + normalized types
- [x] Survey model, sessions, completions
- [x] Idempotent completion processing
- [ ] First real survey provider adapter
- [ ] Survey wall API + pages

## P4 — Payments

- [x] Payment provider interface
- [x] Deposit + withdrawal services and state machines
- [x] Webhook endpoint + signature hook
- [ ] NOWPayments adapter (code implemented + IPN tests; sandbox verification pending credentials)
- [ ] EasyPaisa adapter (real, subject to merchant availability)
- [ ] Reconciliation + payment proof workflow (admin UI)
- [ ] Payout automation for hybrid/auto modes

## P5 — Fraud / Risk

- [x] FraudEvent + RiskRule + RiskScore models
- [x] Scoring + automated restriction actions
- [x] Device reuse / rapid conversion sweep
- [ ] IP reputation integration (VPN/proxy/TOR)
- [ ] Velocity checks on withdrawals/deposits
- [ ] Fraud admin queue

## P6 — Admin

- [x] Django admin registered for all models
- [x] RBAC models, settings, feature flags, audit log
- [x] Admin dashboard (metrics)
- [x] Withdrawal review queue UI (approve / pay / reject + audit)
- [x] Configuration center UI (settings + versioning + audit)
- [x] User management UI (freeze, restrictions, balance adjustments)
- [ ] Provider management + kill switches UI

## P7 — SEO / CMS

- [x] Models (pages, versions, blog, SEO config)
- [ ] Public pages + sitemaps
- [ ] Blog rendering
- [ ] Structured data + performance budget

## P8 — Production

- [x] Dockerfile + docker-compose + Nginx config
- [x] CI (GitHub Actions: check, migrations, tests; lint currently non-blocking)
- [ ] HTTPS + domain/security headers verification
- [ ] Monitoring/alerting
- [ ] Backups + restore drill
- [ ] Load testing
- [ ] Security audit (OWASP)

## P9 — Advertising

- [x] Models: providers, campaigns, placements, impressions, clicks
- [x] Frequency caps + weighted rotation fields
- [ ] Ad rendering/placement service + rotation logic
- [ ] Frequency-cap enforcement at serve time
- [ ] House ads / direct sponsorship (first monetization, no policy risk)
- [ ] Ad-network integration (PropellerAds/Adsterra/Monetag — verify each campaign policy)
- [ ] Google AdSense only on SEO content pages — never on reward/game pages
      (incentivized clicks violate policy; see DECISIONS.md ADR-013)
- [ ] Ad admin UI + reporting
