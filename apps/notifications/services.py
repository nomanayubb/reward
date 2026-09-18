"""Notification services: in-app, email and SMS delivery."""
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template import Context, Template
from django.utils import timezone

from .models import EmailTemplate, Notification, SMSLog

logger = logging.getLogger(__name__)


def notify(
    user,
    *,
    kind: str = Notification.Kind.SYSTEM,
    title: str,
    body: str = "",
    channel: str = Notification.Channel.IN_APP,
    metadata: dict | None = None,
) -> Notification:
    notification = Notification.objects.create(
        user=user,
        kind=kind,
        channel=channel,
        title=title[:160],
        body=body,
        metadata=metadata or {},
        sent_at=None if channel != Notification.Channel.IN_APP else None,
    )
    if channel == Notification.Channel.EMAIL:
        try:
            send_mail(title, body, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
            notification.delivery_status = "sent"
        except Exception as exc:  # delivery must not break business flow
            logger.exception("Email notification failed for %s", user.pk)
            notification.delivery_status = "failed"
            notification.delivery_error = str(exc)[:255]
        notification.save(update_fields=["delivery_status", "delivery_error", "updated_at"])
    return notification


def send_email_template(
    code: str,
    user,
    *,
    context: dict | None = None,
    fallback_subject: str = "",
    fallback_body: str = "",
) -> bool:
    context = context or {}
    template = EmailTemplate.objects.filter(code=code, is_active=True).first()

    if template is not None:
        subject = Template(template.subject).render(Context(context))
        body = Template(template.html_body or template.text_body).render(Context(context))
    else:
        subject = fallback_subject or code.replace("_", " ").title()
        body = fallback_body

    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)
        return True
    except Exception:
        logger.exception("Email template '%s' failed for %s", code, user.pk)
        return False


def send_sms(user, phone: str, message: str, *, provider: str = "") -> SMSLog:
    """Record an SMS. Wire an actual gateway before enabling in production."""
    log = SMSLog.objects.create(
        user=user,
        phone=phone,
        message=message,
        provider=provider,
        status="queued",
    )
    logger.info("SMS queued for %s (provider=%s)", phone, provider or "unset")
    return log


def mark_read(user, notification_ids: list) -> int:
    return Notification.objects.filter(user=user, pk__in=notification_ids, is_read=False).update(
        is_read=True, read_at=timezone.now()
    )


def mark_all_read(user) -> int:
    return Notification.objects.filter(user=user, is_read=False).update(
        is_read=True, read_at=timezone.now()
    )
