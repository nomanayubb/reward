"""Celery tasks for report generation."""
import logging

from celery import shared_task

from .models import ReportJob
from .services import generate_report

logger = logging.getLogger(__name__)


@shared_task
def run_report_job(job_id: str):
    """Generate a report job. Safe to retry: the file is rewritten."""
    job = ReportJob.objects.filter(pk=job_id).first()
    if job is None:
        logger.warning("Report job %s not found", job_id)
        return {"error": "job_not_found"}

    job.status = ReportJob.Status.RUNNING
    job.save(update_fields=["status", "updated_at"])

    try:
        generate_report(job)
    except Exception as exc:
        job.status = ReportJob.Status.FAILED
        job.error = str(exc)[:255]
        job.save(update_fields=["status", "error", "updated_at"])
        raise

    return {"job_id": str(job.id), "status": job.status}
