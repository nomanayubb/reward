"""Celery tasks for the games module."""
from celery import shared_task  # noqa: F401

# Background jobs are defined here. Financial tasks must be idempotent.
