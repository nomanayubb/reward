# MASTER PROJECT DOCUMENTATION

A map of the system — not a copy of the source. For current status see
`.ai/STATE.md`; for remaining work see `.ai/TASKS.md`.

## Project

Reward Platform — configurable rewards, gaming, surveys and CPA platform.

## Technology

- Backend: Python 3.11 / Django 5.1 / DRF
- Database: PostgreSQL (SQLite only for dev/tests)
- Cache/broker: Redis
- Background jobs: Celery + django-celery-beat
- Web server: Nginx + Gunicorn (Uvicorn ASGI available)
- Storage: S3-compatible object storage (local filesystem in dev)
- Deployment: Docker Compose (db, redis, web, worker, beat, nginx)

## Architecture

```
Users → Frontend (templates + DRF API) → Django
     → Domain services → PostgreSQL / Redis / External providers
```

Layering: view/api/webhook/task → service → model. Provider-specific code
lives only in `apps/*/providers/`.

## Core modules (`apps/`)

`accounts`, `users`, `wallets`, `ledger`, `rewards`, `payments`, `deposits`,
`withdrawals`, `games`, `surveys`, `offers`, `cpa`, `advertising`, `bonuses`,
`referrals`, `fraud`, `risk`, `kyc`, `notifications`, `automation`,
`analytics`, `reports`, `cms`, `seo`, `support`, `adminpanel`.

## Financial architecture

- `ledger.LedgerTransaction` + immutable `ledger.LedgerEntry` rows.
- Entries sum to zero; corrections are reversals.
- `WalletAccount.balance` is a cached projection; `account_balance()` computes
  from entries.
- Money is `NUMERIC(20,8)` via `apps.common.fields.money_field`.
- Platform counterparty: system wallet (`system@reward-platform.local`).
- Idempotency keys: `reward:{id}:pending`, `reward:{id}:approve`,
  `withdrawal:{id}:reserve|payout|refund`, `deposit:{id}`, `reversal:{txn}`.

## Reward flow

```
Provider conversion / game session / survey completion / bonus / referral
  → RewardRule resolution (priority, scope, payout conditions)
  → calculate_reward (percentage | fixed | points | multiplier | cap)
  → Reward (pending) + ledger: platform cash → user pending
  → approval (auto after 30 min or admin) → pending → cash / points
  → reversal compensates via ledger
```

## Game flow

```
GameSession (server token) → SDK events (telemetry) → end_session
  → server validation (duration, score conditions, cooldown, caps)
  → RewardService.award_fixed → ledger
```

Games live in `games/<slug>/` with their own `documentation/`; see
`docs/integrations/GAME_INTEGRATION.md`.

## CPA architecture

Provider interface (`apps/cpa/providers/base.py`):

```
get_offers() / track_click() / process_postback() /
validate_signature() / validate_conversion() /
get_campaign_status() / get_reporting_data()
```

Postback: `POST /api/v1/postbacks/<provider_code>/` → signature → duplicate
check → eligibility → reward → quota bump → `OFFER_CONVERTED` event.

## Survey architecture

`apps/surveys/providers/base.py` interface; catalog sync; session + completion
ingestion; idempotent on (`provider`, `external_completion_id`).

## Payment architecture

`apps/payments/providers/base.py`: `create_payment`, `check_payment`,
`verify_webhook`, `parse_webhook`, `create_payout`.

Deposits: `CREATED → AWAITING_PAYMENT → PAYMENT_DETECTED → CONFIRMING →
CONFIRMED` (+ FAILED/EXPIRED/REFUNDED).
Withdrawals: `REQUESTED → UNDER_REVIEW → APPROVED → PROCESSING → PAID`
(+ FAILED/REJECTED/CANCELLED). Funds reserved on request (cash → locked).

## Authentication

Custom email-based user model with Argon2 hashing, email/phone verification
flags, 2FA fields, sessions/devices, granular restrictions. DRF endpoints are
planned (stubs today).

## Fraud / risk

`FraudEvent` signals (VPN/proxy/TOR/emulator/multi-account/device reuse/rapid
conversion/...), risk score 0–100 (low/medium/high/critical), `RiskRule`
actions (allow, rate-limit, hold, verify, disable offers/withdrawals, freeze,
alert). Restrictions are granular and can expire.

## Automation

`Trigger → conditions → actions` rules over an internal event bus
(`emit_event`). Executions logged; failures never roll back money.

## Admin

Django admin registered for every model; `adminpanel` provides RBAC
(`Role`/`Permission`), runtime `PlatformSetting`, `ConfigurationVersion`,
`FeatureFlag` and immutable `AuditLog`. Custom admin UI is future work.

## Integrations status

| Integration | Status |
| --- | --- |
| NOWPayments (crypto) | adapter implemented; sandbox verification pending credentials |
| EasyPaisa (local) | interface only |
| CPA networks | interface only |
| Survey providers | interface only |
| Game SDK | implemented (`static/game-sdk/`); reference game `tap-target` |
| Email/SMS | Django email backend wired; SMS logs only |

## Environment variables

See `.env.example`. Never commit production credentials.

## Deployment

Dev: `python manage.py runserver` (SQLite fallback).
Prod: Docker Compose (Nginx + Gunicorn + PostgreSQL + Redis + Celery), HTTPS,
games on a separate origin, admin on a protected host.

## Current state / tasks

See `.ai/STATE.md` and `.ai/TASKS.md`.
