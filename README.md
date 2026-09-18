# Rewards Gaming, Surveys & CPA Platform

Configurable rewards platform: HTML5 games, surveys, CPA/offerwall offers, multi-wallet
ledger, fraud/risk engine, configurable reward rules, deposits/withdrawals
(NOWPayments + Pakistani local payments), and a full admin back office.

- **Backend:** Python + Django, PostgreSQL, Redis + Celery
- **Frontend:** Django templates + HTMX/Alpine.js
- **Payments:** NOWPayments (crypto) + EasyPaisa (local, subject to merchant availability)
- **Deployment:** Docker + Nginx + Gunicorn + PostgreSQL + Redis
- **Market:** Pakistan

## Core principles

1. Everything configurable without code changes.
2. Immutable ledger is the source of truth — balances are derived.
3. Never trust the client for financial rewards.
4. Provider adapters, never provider `if/else` in views.
5. Campaign terms (incentive/geo/device) are stored and enforced.

## Documentation

- `docs/PRD.md` — product requirements
- `docs/DRD.md` — detailed requirements / domain design
- `docs/ARCHITECTURE.md` — system architecture
- `docs/DATABASE.md` — data model
- `.ai/` — AI context pack (project rules, coding rules, reward rules)

## Quickstart (development)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements/development.txt
copy .env.example .env          # then edit
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Docker

```bash
docker compose up --build
```
