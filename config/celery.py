"""Celery application bootstrap.

The app is imported in ``config/__init__.py`` so that ``@shared_task``
decorators are registered when Django starts.
"""
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("reward_platform")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):  # pragma: no cover - diagnostics only
    print(f"Request: {self.request!r}")
