# DRD — Detailed Requirements & Domain Design

Companion to `PRD.md`. This document defines the rules the code must enforce.
When a rule changes, update this file in the same change.

---

## 1. Domain map

```
USER
 ├── WALLET ──────────── LEDGER_ENTRY (immutable)
 ├── GAME_SESSION ────── GAME_EVENT
 ├── SURVEY_SESSION ──── SURVEY_COMPLETION
 ├── OFFER_CLICK ─────── OFFER_CONVERSION ── OFFER_POSTBACK
 ├── DEPOSIT ─────────── PAYMENT_TRANSACTION
 ├── WITHDRAWAL ──────── PAYMENT_TRANSACTION
 ├── REFERRAL ────────── REFERRAL_CONVERSION
 ├── BONUS ───────────── BONUS_CLAIM
 ├── KYC_VERIFICATION
 ├── RISK_PROFILE ────── RISK_SCORE / FRAUD_EVENT
 └── RESTRICTIONS / DEVICES / SESSIONS / NOTIFICATIONS
```

## 2. Ledger rules (apps/ledger)

- **L1** Every financial event creates a `LedgerTransaction` with ≥2
  `LedgerEntry` rows that **sum to zero** (double entry). Enforced in
  `post_transaction`.
- **L2** Entries are immutable: update raises `ValidationError`, delete is
  forbidden. Corrections are `REVERSAL` transactions.
- **L3** `WalletAccount.balance` is a cached representation updated only inside
  the locked ledger transaction. The ledger is the source of truth
  (`account_balance()` recomputes).
- **L4** Concurrency: rows are locked with `select_for_update()` before balance
  changes.
- **L5** Idempotency: `LedgerTransaction.idempotency_key` is unique. Re-posting
  the same key returns the existing transaction (`created=False`).
- **L6** Money is `Decimal` / `NUMERIC(20,8)`. No floats anywhere.
- **L7** Reversal: `reverse_transaction()` creates the compensating transaction,
  marks the original `REVERSED` and links `reverses`.

## 3. Wallet rules (apps/wallets)

- **W1** Account types: `cash`, `points`, `bonus`, `pending`, `locked`,
  `withdrawable`, `deposit`. One account per (wallet, type, currency).
- **W2** Points use currency `POINTS`; money uses `USD`/`PKR`.
- **W3** The platform (system user `system@reward-platform.local`) is the
  counterparty account for all user movements. The system user cannot log in.
- **W4** `total_liability()` sums user-owed buckets for the finance dashboard.

## 4. Reward engine (apps/rewards)

- **R1** All user credits flow through `RewardService`
  (`award`, `award_fixed`, `approve`, `hold`, `reject`, `reverse`).
- **R2** Rule resolution: first active `RewardRule` by `priority`, matching
  `source`, `provider_code`, `campaign_type`, `country`, `user_tier`, and
  `conditions` (`min_payout`/`max_payout`).
- **R3** Calculation supports: `user_percentage`, `fixed_cash`,
  `points_percentage`, `fixed_points`, `multiplier`, `max_user_reward`.
- **R4** `cash <= 0 and points <= 0` → `RewardError` (misconfiguration must be
  visible, never silently zero).
- **R5** Flow: award credits the **pending** bucket; approve moves pending →
  cash/points; reject reverses pending; reverse compensates approved entries.
- **R6** Idempotency: one reward per (`source`, `source_reference`, `user`).
- **R7** Profitability guard: if `user_reward > gross_revenue`, log a warning
  (admin UI must also warn before saving such a rule).
- **R8** Pending rewards auto-approve after 30 minutes unless the rule sets
  `requires_manual_approval` or the reward is held.

## 5. Games (apps/games)

- **G1** Each game lives in `games/<slug>/` with its own docs; the platform
  never imports game code.
- **G2** Sessions have a server-issued `session_token`; the client can only
  report events, not rewards.
- **G3** `end_session` validates duration ≥ `game.min_session_seconds` and rule
  conditions (`min_score`, `min_duration_seconds`) server-side.
- **G4** Per-rule cooldown (`cooldown_hours`), `daily_max`, `monthly_max`
  enforced against ended sessions.
- **G5** Sessions below the minimum duration are `INVALIDATED` (anti-cheat).
- **G6** Games are served from an isolated origin/iframe sandbox in production;
  no cookies, tokens or wallet APIs are exposed to game JavaScript.

## 6. Surveys (apps/surveys)

- **S1** Provider-specific logic only in adapters
  (`apps/surveys/providers/`).
- **S2** Catalog fields: external id, title, category, country, language,
  device, estimated minutes, payout, user reward, qualification rate, caps,
  status, expiry.
- **S3** Completion requires a matching started session; otherwise ignored.
- **S4** Completions are idempotent on (`provider`, `external_completion_id`).
- **S5** Rejected/disqualified completions are stored (not paid) for analytics.

## 7. Offers / CPA (apps/offers, apps/cpa)

- **O1** Compliance flags stored per offer: `incentive_allowed`,
  `traffic_source_allowed`, `vpn_allowed`, `proxy_allowed`,
  `emulator_allowed`, `multiple_completion_allowed`, `reinstall_allowed`,
  `daily_user_limit`, `lifetime_user_limit`.
- **O2** `incentive_allowed = False` ⇒ the offer is **not** shown in the
  rewards section.
- **O3** Eligibility engine returns `ELIGIBLE | NOT_ELIGIBLE | REQUIRES_REVIEW`
  with reasons, considering: offer status/expiry, country, device, OS,
  compliance flags, campaign quotas, user completion history, daily/lifetime
  limits, user restrictions and risk score.
- **O4** Quotas (`CampaignQuota`): `daily_global_cap`, `hourly_cap`,
  `daily_user_cap`, `lifetime_user_cap`, `country_cap`. Counters roll hourly
  and daily. Hitting `daily_global_cap` sets the offer
  `PAUSED_BY_QUOTA`; it auto-resumes when counters reset.
- **O5** Postbacks: signature validation → duplicate detection → user/offer
  resolution via click id → eligibility re-check → reward → quota bump →
  event emit. Raw payloads are stored for disputes.
- **O6** Conversion idempotency is enforced by
  `unique(provider, external_conversion_id)`; replays never pay twice.
- **O7** Reversals from providers reverse the reward via the ledger; the
  original conversion row is kept.

## 8. Withdrawals (apps/withdrawals)

- **W1** State machine: `REQUESTED → UNDER_REVIEW → APPROVED → PROCESSING →
  PAID`, with `FAILED`, `REJECTED`, `CANCELLED` as terminal alternatives.
- **W2** Funds are **reserved on request**: cash → locked in one ledger
  transaction; two simultaneous requests cannot spend the same balance.
- **W3** Rejection refunds locked → cash. Payment moves locked → platform cash.
- **W4** Checks before request: withdrawals feature flag, user restriction,
  min/max, KYC threshold, cooldown, verified-method requirement (configurable),
  available balance.
- **W5** Risk level from the user's risk score; high-risk and large amounts go
  to the manual queue. Dual approval is required above
  `DUAL_APPROVAL_THRESHOLD_USD`.
- **W6** Payout mode `auto | manual | hybrid`; hybrid auto-pays below
  `AUTO_PAYOUT_MAX_USD`.
- **W7** Payment reference and proof are stored and shown to the user.

## 9. Deposits and payments (apps/deposits, apps/payments)

- **D1** Deposit states: `CREATED → AWAITING_PAYMENT → PAYMENT_DETECTED →
  CONFIRMING → CONFIRMED`, plus `FAILED`, `EXPIRED`, `REFUNDED`.
- **D2** Provider adapters implement `create_payment`, `check_payment`,
  `verify_webhook`, `parse_webhook`, `create_payout`.
- **D3** Webhooks: signature validation, idempotent transaction update, ledger
  credit exactly once (`deposit:{id}` idempotency key).
- **D4** `PaymentTransaction` unique on (`provider`, `external_id`).
- **D5** Exchange rates are stored per transaction; historical transactions are
  never recalculated with today's rate.

## 10. Fraud and risk (apps/fraud, apps/risk)

- **F1** Fraud events cover: VPN, proxy, TOR, emulator, multi-account, device
  reuse, IP reuse, cookie manipulation, fake postback, rapid conversion,
  impossible completion time, repeated install, chargeback, payment abuse,
  referral abuse.
- **F2** Risk score 0–100: ≤20 low, ≤50 medium, ≤75 high, >75 critical.
  Severity weights: low 5, medium 15, high 30, critical 60; capped at 100.
- **F3** Never auto-ban on one signal — score + evidence.
- **F4** Rules can trigger: allow, rate-limit, hold reward, require
  verification, disable offers, disable withdrawals, freeze account, alert.
- **F5** Restrictions are granular and may be temporary (`until`).

## 11. Automation (apps/automation)

- **A1** Rules are `trigger + conditions + ordered actions`, evaluated by
  priority; executions are logged with status `SUCCESS/SKIPPED/FAILED`.
- **A2** Conditions support risk thresholds, account age and payload equality.
- **A3** Actions never break the caller's transaction — failures are recorded,
  not raised.
- **A4** `max_executions_per_user` caps repeat bonuses.

## 12. Admin, RBAC and audit (apps/adminpanel)

- **AD1** Runtime settings live in `PlatformSetting`; reads fall back to
  `settings.PLATFORM_DEFAULTS`; changes create `ConfigurationVersion` rows.
- **AD2** Configuration precedence: Global → Country → Tier → Campaign → User.
- **AD3** Roles map to `Permission` codes (`withdrawals.approve`,
  `wallet.adjust`, ...). Admin 2FA is mandatory in production.
- **AD4** `AuditLog` is immutable and records actor, action, object, old/new
  value, reason, IP.
- **AD5** Feature flags gate modules (games/surveys/offers/referrals/crypto/
  easypaisa) and support percentage rollouts.
- **AD6** Emergency kill switches exist for offers, surveys, withdrawals,
  deposits, individual providers and countries.

## 13. Security requirements

- **SEC1** OWASP baseline: CSRF, XSS escaping, ORM parameterization, CSP,
  HSTS, secure cookies, clickjacking protection.
- **SEC2** Argon2 password hashing; login throttling; 2FA for admins.
- **SEC3** Rate limits: login 5/min, withdrawal 3/hour, offer click 30/min,
  postbacks provider-specific.
- **SEC4** Webhooks: signature, timestamp, replay protection, idempotency, raw
  payload storage, IP allow-list where available.
- **SEC5** Secrets only via environment variables; `.env` never committed.
- **SEC6** KYC/payment-proof files are private; served only via
  permission-checked views.
- **SEC7** Games run on a separate origin/sandbox; game JS cannot read cookies
  or call wallet/admin APIs.

## 14. Testing requirements

Critical tests (implemented in `tests/test_critical_flows.py`):

| ID | Scenario | Expected |
| --- | --- | --- |
| T1 | Same postback sent 100× | 1 reward, 99 duplicates |
| T2 | Two simultaneous withdrawal requests | only one reserves balance |
| T3 | Revenue $2, rule 40% | user $0.80 |
| T4 | Campaign cap 100/day, 101st conversion | not eligible |
| T5 | Same offer repeated beyond limits | blocked by eligibility |
| T6 | Reversal of approved reward | balance returns to prior state |
| T7 | Unbalanced ledger transaction | rejected |
| T8 | Ledger entry mutation | rejected |

Additional suites: unit (services), integration (adapters with sandbox),
API, security, payment webhooks, fraud, game sessions.

## 15. API surface

`/api/v1/` — `auth/`, `users/`, `wallets/`, `ledger/`, `rewards/`,
`payments/`, `deposits/`, `withdrawals/`, `games/`, `surveys/`, `offers/`,
`cpa/`, `advertising/`, `bonuses/`, `referrals/`, `fraud/`, `risk/`, `kyc/`,
`notifications/`, `automation/`, `analytics/`, `reports/`, `cms/`, `seo/`,
`support/`, `adminpanel/`.

Callbacks: `/api/v1/postbacks/<provider_code>/` (CPA),
`/api/v1/webhooks/<provider_code>/` (payments).

OpenAPI schema: `/api/v1/schema/`, Swagger UI: `/api/v1/docs/`.

## 16. Data retention and privacy

Financial records are retained per accounting law; fraud data and logs have
defined retention; KYC data is minimized and never retained without a
legitimate reason. Users may request export/deletion where legally applicable.
Privacy policy, terms, cookie policy and reward/withdrawal terms must be
published and versioned.

## 17. Environment configuration

See `.env.example`. Required in production: `SECRET_KEY`, `DATABASE_URL`,
`REDIS_URL`, `ALLOWED_HOSTS`, payment and provider credentials. Development
falls back to SQLite and locmem cache; production requires PostgreSQL and
Redis and refuses to run without secrets.
