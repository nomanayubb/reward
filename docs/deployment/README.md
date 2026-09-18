# Deployment

## Development

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements/development.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver
```

SQLite and locmem cache are used automatically when `DATABASE_URL`/`REDIS_URL`
are unset.

## Docker (staging/production)

```bash
docker compose up --build
```

Services: `db` (PostgreSQL 16), `redis` (7), `web` (Gunicorn), `worker`
(Celery), `beat` (django-celery-beat), `nginx`.

## Production requirements

- `DEBUG=False`, real `SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`.
- HTTPS termination + `SECURE_SSL_REDIRECT=True` (default in production).
- PostgreSQL and Redis reachable; object storage for media in production.
- Games served from a separate origin; admin on a protected host.
- Backups: daily PostgreSQL dump + weekly full backup, off-site, restore
  tested periodically.
- Monitoring: application logs, Celery failures, payment/webhook failures,
  HTTP error rates.

## Release checklist

1. `scripts/project-check` passes.
2. Migrations reviewed and applied.
3. `.env` updated for any new variables.
4. Static files collected (`manage.py collectstatic`).
5. Smoke test: register → earn → wallet → withdraw request.
