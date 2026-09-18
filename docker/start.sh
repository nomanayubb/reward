#!/usr/bin/env bash
# Container entrypoint: migrate, collect static, seed starter content, serve.
# Used by Render/Railway and any host that runs the Docker image.
set -e

# Always run in production inside a container unless the host explicitly
# overrides it. Without this, `manage.py`'s development default leaks into
# gunicorn and the app would run with DEBUG=True.
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.production}"

python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Seed starter content (idempotent; safe on every boot).
python manage.py seed_cms_pages || true
python manage.py seed_reference_game || true
python manage.py seed_ad_placements || true

exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-2}" \
    --timeout 60
