"""Audit logging helper — call from every sensitive admin/service action."""
from .models import AuditLog


def log_action(
    *,
    actor=None,
    action: str,
    obj=None,
    object_type: str = "",
    object_id: str = "",
    old_value=None,
    new_value=None,
    reason: str = "",
    request=None,
) -> AuditLog:
    if obj is not None and not object_type:
        object_type = obj.__class__.__name__
        object_id = str(getattr(obj, "pk", ""))

    ip_address = None
    user_agent = ""
    if request is not None:
        ip_address = request.META.get("REMOTE_ADDR")
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:255]

    return AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        object_type=object_type,
        object_id=object_id,
        old_value=old_value,
        new_value=new_value,
        reason=reason,
        ip_address=ip_address,
        user_agent=user_agent,
    )
