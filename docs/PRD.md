# PRD — Rewards Gaming, Surveys & CPA Platform

Status: v0.1 (foundation implemented)
Market: Pakistan (primary), international secondary
Stack: Django + PostgreSQL + Redis/Celery, Docker/Nginx/Gunicorn
Related docs: `DRD.md` (detailed requirements), `ARCHITECTURE.md`, `DATABASE.md`,
`integrations/GAME_INTEGRATION.md`, `integrations/CPA_INTEGRATION.md`,
`.ai/` (AI context pack)

---

## 1. Product vision

A configurable **operating system for earning activities**. Users create an
account, play HTML5 games, complete surveys, complete CPA/offerwall offers
(including incentivized app installs where the campaign permits), earn points
or cash, track every transaction, deposit where permitted and withdraw through
crypto or local Pakistani payment methods.

Administrators configure virtually everything — rewards, percentages,
conversion rates, limits, quotas, fraud rules, payment rules, commissions,
content, SEO and automations — **without modifying source code**.

## 2. Core principles

1. Everything that reasonably can be configured is configurable at runtime.
2. The **immutable ledger** is the source of truth; balances are derived/cached.
3. **Never trust the client** — no browser value, game score or client reward
   request is used for money. Server-side validation is mandatory.
4. **Provider adapters, never provider `if/else`** in views or templates.
5. **Campaign terms are data**: incentive/geo/device/VPN/emulator rules are
   stored per offer and enforced by the eligibility engine.
6. Money is exact: `NUMERIC(20,8)`, never floating point.
7. Every external event is idempotent; every financial movement is reversible
   via compensating entries, never by editing history.

## 3. User roles

| Role | Description |
| --- | --- |
| Visitor | Browsing public pages, SEO content, guides |
| User | Registered account, earns, deposits, withdraws |
| VIP user | Higher tiers with better multipliers/limits |
| Support admin | Tickets, disputes, read-mostly user views |
| Finance admin | Deposits, withdrawals, reconciliation, adjustments |
| Fraud analyst | Risk queue, fraud events, restrictions |
| Offer/Survey manager | Providers, offers, quotas, campaigns |
| Game manager | Games, reward rules, sessions |
| Content/SEO manager | CMS, blog, SEO config |
| Super admin | Everything, including roles and settings |

## 4. User-facing features

### 4.1 Account
Email/password registration, optional username, referral codes, email/phone
verification, 2FA (TOTP-ready), session management, suspicious-login alerts.

### 4.2 Earn
- **Games** — HTML5 catalog, isolated iframe execution, server-validated
  sessions, configurable reward rules (score/duration conditions, cooldowns,
  daily/monthly caps).
- **Surveys** — provider-agnostic survey wall with eligibility and risk
  filtering, session tracking, provider postback completion.
- **Offers (CPA)** — offerwall of compliant offers with full condition display,
  click tracking, provider postback conversions, quotas and compliance gating.
- **Apps** — incentivized install campaigns only where the provider permits it.
- **Bonuses** — signup, daily login, streaks, first-offer, deposit, seasonal.
- **Referrals** — referral link, tracked registrations and conversions.

### 4.3 Wallet
Separate ledgers: cash, points, bonus, pending, locked, withdrawable, deposit.
Dashboard shows available, pending, points, today/week/month/lifetime earnings
and withdrawable amount.

### 4.4 History
Full activity history with tabs (all/games/surveys/offers/apps/bonuses/
referrals/deposits/withdrawals/wallet/adjustments) and filters (date, type,
status, amount, provider, transaction ID). Every row shows source, gross
provider revenue where appropriate, user reward, status, date and transaction
ID.

### 4.5 Deposits
Crypto (NOWPayments) and local methods (EasyPaisa, subject to merchant
availability). Full deposit state machine and payment instructions.

### 4.6 Withdrawals
Method selection (EasyPaisa/JazzCash/bank/crypto), minimum/maximum checks,
KYC threshold, cooldown, risk scoring, reserve-on-request, admin review queue
with dual approval for large amounts, payment proof, full state machine.

## 5. Admin features

- Dashboard: users, revenue, user rewards, net profit, pending rewards and
  withdrawals, conversions, sessions, fraud alerts.
- Configuration center: general, currencies, points, rewards, offers, surveys,
  games, ads, payments, withdrawals, fraud, KYC, referrals, bonuses,
  notifications, SEO, security, maintenance.
- Provider management with health, sync status and kill switches.
- Reward rule builder (priority, scope, conditions, mode, caps).
- Offer compliance editor (incentive/VPN/proxy/emulator/reinstall/caps).
- Campaign quotas with automatic throttling and auto-pause.
- Fraud queue, risk rules, user restrictions (granular, temporary).
- Withdrawal queue prioritized by risk/amount/account age.
- Balance adjustments with reason + immutable audit log.
- Automation rule builder (trigger → conditions → actions).
- Reports/exports (CSV/Excel/PDF), analytics, cohort/funnel views.
- RBAC roles and permissions, 2FA mandatory for admins, audit log.
- Feature flags, maintenance mode, geo restrictions, emergency kill switches.
- CMS pages (versioned terms/privacy), blog, per-path SEO config.

## 6. Business model

The platform never hard-codes "advertiser pays $2 → user gets $1". Instead:

```
Advertiser Revenue
  → Network Revenue Event
  → Validated Conversion
  → Revenue Classification
  → Platform Share
  → User Reward Rule (percentage | fixed | points | hybrid | multiplier)
  → Fraud/Risk Validation
  → Pending Reward
  → Confirmation
  → User Wallet
```

Examples (all admin-configurable):
- $2.00 revenue × 70/30 split → user $0.60
- $2.00 revenue × 50% → user $1.00
- Variable revenue, fixed reward $0.35
- $2.00 revenue → 100 points (at `POINTS_PER_USD = 100`)

Profitability guard: when a rule would make user reward exceed provider
revenue, the admin UI warns and requires explicit confirmation; the reward
service logs a warning.

## 7. Reward currency

- **Points** — conversion is admin configurable (`POINTS_PER_USD`, default
  100). Stored in a separate points ledger.
- **Cash** — exact USD (or configured currency) amounts.
- **Hybrid** — e.g. $0.25 cash + 50 points.

## 8. Revenue and cost model

Per campaign the platform tracks: advertiser revenue, user reward, provider
cost, payment cost, fraud loss, operational cost → net profit. Dashboards show
the breakdown, and total user withdrawable balances are tracked as a
**liability**.

## 9. Games

Games are self-contained folders (`games/<slug>/`) with their own docs. The
platform provides a sandboxed wrapper and a Game SDK. Rewards are configured
per game (conditions, mode, cooldown, daily/monthly caps). Server-side
anti-cheat validation is mandatory; untrusted client scores are never paid.

## 10. Surveys

Provider abstraction with adapters. Survey catalog stores country, language,
payout, estimated time, qualification rate, caps and status. Flow: fetch →
eligibility → risk filter → start → provider completion → postback →
verification → pending reward → approval → wallet.

## 11. CPA / offerwall

Unified Offer API. Every network gets an adapter producing normalized
offers/conversions. Compliance flags are enforced before display and before
crediting. Campaign quotas (`CampaignQuota`) enforce daily/hourly/global/user
caps; exhausted campaigns auto-pause (`PAUSED_BY_QUOTA`) and auto-resume when
caps reset.

## 12. Advertising

Ad providers (Google, direct, networks, house, affiliate) with placements
(homepage, game page, before/after game, survey, offer, dashboard, withdrawal),
weighted rotation and frequency capping. Users are never rewarded for ad clicks
unless the ad program explicitly permits it.

## 13. Payments

`PaymentProvider` + adapters for NOWPayments (crypto) and EasyPaisa (local,
subject to merchant/API verification). Deposit and withdrawal state machines,
webhook signature validation, reconciliation and payment proofs.

## 14. Fraud, risk and compliance

Rule-based detection (VPN/proxy/TOR, emulator, multi-account, device/IP reuse,
cookie manipulation, fake postbacks, rapid conversions, impossible completion
times, repeated installs, chargebacks, payment/referral abuse). Risk score
0–100 (Low/Medium/High/Critical) drives automated actions: allow, rate-limit,
hold reward, require verification, disable offers/withdrawals, freeze, alert.

Compliance posture: campaign terms are always enforced; incentivized traffic is
only surfaced when allowed; Pakistan-focused legal review of the operating
model is required before launch (AML/transaction monitoring, KYC thresholds).

## 15. Automation

Trigger → Condition → Action rules over an internal event bus:
`USER_REGISTERED`, `EMAIL_VERIFIED`, `FIRST_DEPOSIT`, `GAME_COMPLETED`,
`SURVEY_COMPLETED`, `OFFER_CONVERTED`, `WITHDRAWAL_REQUESTED/PAID/REJECTED`,
`REFERRAL_REGISTERED/CONVERTED`, `FRAUD_SCORE_CHANGED`, `CAMPAIGN_QUOTA_REACHED`,
`PROVIDER_UNAVAILABLE`, `DEPOSIT_CONFIRMED`.

Actions: credit points/cash, send email/notification/SMS, freeze, hold reward,
approve/reject withdrawal, change tier, enable/disable offer, pause campaign,
create admin alert.

## 16. SEO and CMS

Per-page SEO (title, meta, canonical, robots, OG, schema). Sitemaps. Programmatic
category pages must contain genuinely useful unique content — no doorway pages,
no misleading earning claims. CMS pages and terms are versioned; blog supports
categories, drafts and scheduling.

## 17. KPIs

DAU/WAU/MAU, retention (D1/D7/D30), ARPU, LTV, conversion rates (offer/survey),
reward cost / revenue, withdrawal rate, fraud rate, net profit, pending
liability, EPC per network.

## 18. Success criteria (MVP)

A user can register, play a game, complete a survey and an offer, receive a
provider conversion, get a pending reward, see it approved into the wallet,
request a withdrawal, have it processed by an admin, and the payment can be
reconciled — with every movement recorded in the immutable ledger.

## 19. Delivery phases

1. **Phase 1 (foundation)** — architecture, auth, users, schema, wallet +
   immutable ledger, reward engine, admin/RBAC, audit logs. *Implemented.*
2. **Phase 2** — games + SDK + game docs, survey abstraction, CPA abstraction,
   postbacks, eligibility/compliance engine. *Core implemented; adapters and
   UI pending.*
3. **Phase 3** — deposits, NOWPayments, EasyPaisa (subject to availability),
   withdrawal engine, reconciliation, fraud/risk. *Core implemented; provider
   credentials and UI pending.*
4. **Phase 4** — advertising, referrals, bonuses, VIP, automation,
   notifications, support.
5. **Phase 5** — SEO, CMS, analytics, A/B testing, performance, security
   hardening, production deployment.

## 20. Non-goals / constraints

- No fixed "download N apps" rule — limits are dynamic per campaign.
- No assumption that N offers × M users are all completable; quotas and
  provider terms govern.
- No ML-based fraud in v1 — transparent rules first.
- No unlimited MLM referral structures without legal review.
- No ad-click rewards where the network prohibits incentivized clicks.
