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

## Own server (recommended for launch)

`docker-compose.prod.yml` + Caddy runs the full stack (Django, PostgreSQL,
Redis, Celery, automatic HTTPS) on any VPS with **no PaaS dependency**.
Step-by-step guide: **`docs/deployment/VPS.md`**.

## Free public URL (for provider review, e.g. AdGem)

You need a live URL before payment/CPA networks will approve you. Two free
options:

### Option A — Render free tier (stable URL)

1. Push the repo to GitHub (done).
2. Render dashboard → **New → Blueprint** → select this repository.
3. `render.yaml` creates a Docker web service with production settings,
   generated `SECRET_KEY`, SQLite database and auto-seeded pages/games.
4. Your URL: `https://reward-platform.onrender.com` (rename in `render.yaml` if
   the name is taken).

Caveats on the free plan: the service sleeps after ~15 minutes idle (first
visit is slow) and SQLite resets on redeploy — fine for review, not for real
traffic.

### Option B — Cloudflare Tunnel (instant, temporary URL)

```powershell
winget install --id Cloudflare.cloudflared
.\scripts\public-tunnel.ps1          # with the dev server running on :8010
```

Prints `https://<random-words>.trycloudflare.com`. The URL changes on every
restart and your PC must stay on — good for a quick demo, not for review.

### Option C — any free Django host

PythonAnywhere free tier (`username.pythonanywhere.com`) also works with the
development settings; no Redis/Postgres required.

## Docker (staging/production)

```bash
docker compose up --build
```

Services: `db` (PostgreSQL 16), `redis` (7), `web` (Gunicorn), `worker`
(Celery), `beat` (django-celery-beat), `nginx`. The container entrypoint
(`docker/start.sh`) migrates, collects static files and seeds starter content.

## Production requirements

- `DEBUG=False`, real `SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`.
- HTTPS termination + `SECURE_SSL_REDIRECT=True` (default in production).
- PostgreSQL and Redis recommended (the app falls back to SQLite + locmem if
  `DATABASE_URL`/`REDIS_URL` are unset, for small single-instance hosts).
- Object storage for media in production (KYC files are private).
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
5. Replace the `[bracketed]` placeholders in the seeded CMS pages
   (about/terms/privacy/contact) and have them reviewed by a lawyer.
6. Smoke test: register → earn → wallet → withdraw request.
