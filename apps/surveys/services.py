"""Survey services: sessions and completion processing."""
import logging

from django.db import transaction
from django.utils import timezone

from apps.rewards.models import Reward
from apps.rewards.services import RewardService

from .models import Survey, SurveyCompletion, SurveyProvider, SurveySession

logger = logging.getLogger(__name__)


@transaction.atomic
def start_session(user, survey: Survey, *, ip=None) -> SurveySession:
    return SurveySession.objects.create(user=user, survey=survey, ip_address=ip)


def survey_url(survey: Survey, user, session: SurveySession) -> str:
    from apps.surveys.providers.base import load_adapter

    adapter = load_adapter(survey.provider)
    return adapter.get_survey_url(survey, user, session)


@transaction.atomic
def process_completion(provider: SurveyProvider, payload: dict, headers: dict | None = None):
    """Idempotent survey completion ingestion (provider postback)."""
    from apps.surveys.providers.base import load_adapter

    adapter = load_adapter(provider)
    if not adapter.validate_signature(payload, headers):
        logger.warning("Invalid survey postback signature from %s", provider.code)
        return None, False

    normalized = adapter.process_postback(payload, headers)

    existing = SurveyCompletion.objects.filter(
        provider=provider, external_completion_id=normalized.external_completion_id
    ).first()
    if existing is not None:
        return existing, False

    session = (
        SurveySession.objects.select_related("user", "survey")
        .filter(survey__provider=provider, survey__external_id=normalized.survey_external_id, status=SurveySession.Status.STARTED)
        .order_by("-started_at")
        .first()
    )
    if session is None:
        logger.info("Survey completion without matching session: %s", normalized.external_completion_id)
        return None, False

    survey = session.survey
    user = session.user

    completion = SurveyCompletion.objects.create(
        user=user,
        survey=survey,
        session=session,
        provider=provider,
        external_completion_id=normalized.external_completion_id,
        payout=normalized.payout or survey.payout,
        user_reward=0,
        status=SurveyCompletion.Status.PENDING,
        raw_payload=normalized.raw,
    )

    if normalized.status != "approved":
        completion.status = SurveyCompletion.Status.REJECTED
        completion.save(update_fields=["status", "updated_at"])
        session.status = SurveySession.Status.DISQUALIFIED
        session.finished_at = timezone.now()
        session.save(update_fields=["status", "finished_at", "updated_at"])
        return completion, True

    reward, _ = RewardService.award(
        user=user,
        source=Reward.Source.SURVEY,
        source_reference=str(completion.id),
        gross_revenue=completion.payout,
        context={
            "provider_code": provider.code,
            "campaign_type": "survey",
            "country": getattr(user, "country", "") or "",
            "survey_id": str(survey.id),
        },
    )

    completion.reward = reward
    completion.user_reward = reward.user_reward
    completion.status = SurveyCompletion.Status.APPROVED
    completion.save(update_fields=["reward", "user_reward", "status", "updated_at"])

    session.status = SurveySession.Status.COMPLETED
    session.finished_at = timezone.now()
    session.save(update_fields=["status", "finished_at", "updated_at"])

    from apps.automation.services import emit_event

    emit_event(
        "SURVEY_COMPLETED",
        user,
        {"survey_id": str(survey.id), "completion_id": str(completion.id)},
    )
    return completion, True
