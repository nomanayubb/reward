# Architecture

## 1. System map

```
                         ┌──────────────────────┐
                         │        USERS         │
                         └──────────┬───────────┘
                                    ▼
                         ┌──────────────────────┐
                         │  DJANGO (templates +  │
                         │  DRF API /api/v1/)    │
                         └──────────┬───────────┘
        ┌───────────────┬───────────┼────────────┬───────────────┐
        ▼               ▼           ▼            ▼               ▼
     GAMES           SURVEYS      CPA          ADS           BONUSES
        │               │           │            │               │
        └───────────────┴───────────┼────────────┴───────────────┘
                                    ▼
                         ┌──────────────────────┐
                         │   REWARD ENGINE      │  apps/rewards
                         └──────────┬───────────┘
                                    ▼
                         ┌──────────────────────┐
                         │   FRAUD / RISK       │  apps/fraud, apps/risk
                         └──────────┬───────────┘
                                    ▼
                         ┌──────────────────────┐
                         │  LEDGER / WALLETS    │  apps/ledger, apps/wallets
                         └──────────┬───────────┘
                         ┌──────────┴──────────┐
                         ▼                     ▼
                     DEPOSITS             WITHDRAWALS
                         │                     │
                         ▼                     ▼
                  NOWPayments           EasyPaisa / crypto
                                   
                         ┌──────────────────────┐
                         │    ADMIN PANEL       │ apps/adminpanel
                         │  config / RBAC /     │
                         │  audit / automation  │
                         └──────────────────────┘
```

## 2. Request and service layering

```
View / API / Task / Webhook
        ↓
Service layer (business rules, transactions)
        ↓
Domain models (persistence, constraints)
```

- Views are thin: parse, authorize, call a service, serialize.
- Services own transactions, locking, idempotency and ledger calls.
- Provider-specific code lives only in adapters under
  `apps/*/providers/`.
- Templates never contain business decisions.

## 3. Module responsibilities

| Module | Owns |
| --- | --- |
| `accounts` | User model, registration, referral codes |
| `users` | Profile, security, devices, sessions, risk profile, restrictions |
| `wallets` | Wallet + accounts, system wallet, liability totals |
| `ledger` | Immutable double-entry transactions and entries |
| `rewards` | Rule resolution, calculation, award lifecycle |
| `payments` | Provider registry, payment transactions, webhooks |
| `deposits` | Deposit lifecycle and crediting |
| `withdrawals` | Method storage, request/review/pay/refund flow |
| `games` | Catalog, sessions, events, game reward rules |
| `surveys` | Provider registry, catalog, sessions, completions |
| `offers` | Offer catalog, quotas, clicks, conversions, postbacks, eligibility |
| `cpa` | CPA provider registry + adapter interfaces |
| `advertising` | Providers, campaigns, placements, impressions, clicks |
| `bonuses` | Bonus rules, issuance, claims |
| `referrals` | Referral links, conversions |
| `fraud` | Fraud events, analysis tasks |
| `risk` | Risk rules and score history |
| `kyc` | Verification records |
| `notifications` | In-app/email/SMS + templates |
| `automation` | Event bus, rule engine, executions |
| `analytics` | Daily statistics, event stream |
| `reports` | Async report jobs |
| `cms` | Pages (versioned) + blog |
| `seo` | Per-path SEO config |
| `support` | Tickets, messages, reward disputes |
| `adminpanel` | Settings, RBAC, feature flags, config versions, audit log |

## 4. Event bus

Internal events are plain strings dispatched by
`apps.automation.services.emit_event`. Automation rules subscribe by trigger.

```
OFFER_CONVERTED ──► automation rules ──► actions (credit, notify, pause, ...)
SURVEY_COMPLETED
GAME_COMPLETED
WITHDRAWAL_REQUESTED / PAID / REJECTED
DEPOSIT_CONFIRMED
USER_REGISTERED / EMAIL_VERIFIED
```

Events are dispatched after the financial transaction commits where possible;
automation failures never roll back the money movement.

## 5. Background jobs (Celery + beat)

| Task | Schedule | Purpose |
| --- | --- | --- |
| `apps.offers.tasks.sync_offers` | 15 min | Pull offers from enabled CPA providers |
| `apps.offers.tasks.recalculate_campaign_quotas` | 5 min | Reset counters, resume paused offers |
| `apps.surveys.tasks.sync_surveys` | 15 min | Pull survey catalog |
| `apps.rewards.tasks.process_pending_rewards` | 5 min | Auto-approve eligible pending rewards |
| `apps.deposits.tasks.expire_deposits` | 10 min | Expire unpaid deposits |
| `apps.fraud.tasks.run_fraud_analysis` | 30 min | Device reuse / rapid conversion sweep |
| `apps.analytics.tasks.generate_daily_statistics` | daily | KPI aggregation |

Failed financial tasks must be idempotent (ledger idempotency keys) before
retrying.

## 6. Deployment

```
Internet → Cloudflare → Nginx → Gunicorn (Django) ─┬─ PostgreSQL
                                                    ├─ Redis (cache/broker)
                                                    ├─ Celery worker
                                                    ├─ Celery beat
                                                    └─ S3-compatible storage
```

- `docker-compose.yml` runs db, redis, web, worker, beat, nginx.
- Static files are served by whitenoise/Nginx; media on object storage in
  production.
- Games should be served from a separate origin (`games.example.com`) in
  production; admin on `admin.example.com`.

## 7. Scaling path

1. Start: 1 Django app, 1 PostgreSQL, 1 Redis, 1 worker.
2. Add load balancer + N app instances (stateless app, shared DB/Redis).
3. Move analytics/events to a pipeline (ClickHouse/BigQuery) as volume grows;
   partition high-volume tables (ledger entries, game events, ad impressions,
   offer clicks) by month.
4. Provider adapters and automation make new integrations additive, not
   invasive.

## 8. Key architectural decisions

- **Modular monolith** with service-oriented boundaries (per-module
  `services.py`, `tasks.py`, `README.md` contracts) so modules can be split
  later.
- **Configurable reward engine** instead of hard-coded splits.
- **Immutable ledger** instead of mutable balances.
- **Adapter pattern** for every external network.
- **Compliance flags as data** so provider terms are enforced by code paths
  that cannot be bypassed by UI changes.
