"""Game services: sessions, server-side validation and reward evaluation.

Client scores are never trusted. ``end_session`` re-validates duration and
score server-side against ``GameRewardRule`` conditions before any reward is
created (docs/DRD.md §8-9, §248).
"""
import logging
import secrets

from django.db import transaction
from django.utils import timezone

from apps.rewards.models import Reward
from apps.rewards.services import RewardService

from .models import Game, GameEvent, GameRewardRule, GameSession

logger = logging.getLogger(__name__)


@transaction.atomic
def start_session(user, game: Game, *, ip=None, device_hash="") -> GameSession:
    from apps.adminpanel.settings import get_setting

    if not get_setting("GAMES_ENABLED", True):
        raise ValueError("Games are temporarily disabled.")
    if game.status != Game.Status.ACTIVE:
        raise ValueError("Game is not available.")

    today_sessions = GameSession.objects.filter(
        user=user, game=game, started_at__date=timezone.localdate()
    ).count()
    if today_sessions >= game.max_daily_sessions:
        raise ValueError("Daily session limit reached for this game.")

    return GameSession.objects.create(
        user=user,
        game=game,
        session_token=secrets.token_urlsafe(24),
        ip_address=ip,
        device_id_hash=device_hash,
    )


@transaction.atomic
def report_event(
    session: GameSession, *, event_type: str, payload: dict | None = None
) -> GameEvent:
    """Record a telemetry event from an active session (never a reward by itself)."""
    if session.status != GameSession.Status.ACTIVE:
        raise ValueError("Session is not active.")
    if not event_type:
        raise ValueError("event_type is required.")
    return GameEvent.objects.create(
        session=session, event_type=event_type[:64], payload=payload or {}
    )


def catalog_rows(user) -> list[dict]:
    """Active games with plays remaining today and a reward summary.

    Shared by the games page and the Earn hub.
    """
    from django.db.models import Count

    games = list(
        Game.objects.filter(status=Game.Status.ACTIVE)
        .select_related("category")
        .order_by("sort_order", "title")
    )
    today = timezone.localdate()
    counts = dict(
        GameSession.objects.filter(user=user, started_at__date=today)
        .values_list("game_id")
        .annotate(total=Count("id"))
    )

    rules = {}
    for rule in GameRewardRule.objects.filter(game__in=games, is_active=True).order_by(
        "game_id", "priority"
    ):
        rules.setdefault(rule.game_id, rule)

    rows = []
    for game in games:
        rule = rules.get(game.id)
        reward = ""
        if rule is not None:
            reward = (
                f"{rule.points} pts"
                if rule.mode == GameRewardRule.Mode.POINTS
                else f"{rule.cash}"
            )
        rows.append(
            {
                "game": game,
                "plays_remaining": max(0, game.max_daily_sessions - counts.get(game.id, 0)),
                "reward": reward,
            }
        )
    return rows


def _conditions_match(conditions: dict, *, duration: int, score: int | None) -> bool:
    if not conditions:
        return True
    min_score = conditions.get("min_score")
    if min_score is not None and (score is None or score < int(min_score)):
        return False
    min_duration = conditions.get("min_duration_seconds")
    return min_duration is None or duration >= int(min_duration)


@transaction.atomic
def end_session(session: GameSession, *, score: int | None = None) -> GameSession:
    """Close a session, validate it and award the best matching rule."""
    session = GameSession.objects.select_for_update().select_related("game", "user").get(pk=session.pk)
    if session.status != GameSession.Status.ACTIVE:
        return session

    now = timezone.now()
    session.ended_at = now
    session.duration_seconds = max(0, int((now - session.started_at).total_seconds()))
    session.score = score

    if session.duration_seconds < session.game.min_session_seconds:
        session.status = GameSession.Status.INVALIDATED
        session.invalid_reason = "session_too_short"
        session.save()
        return session

    session.status = GameSession.Status.ENDED
    session.save()

    rules = GameRewardRule.objects.filter(game=session.game, is_active=True).order_by("priority")
    for rule in rules:
        if not _conditions_match(rule.conditions, duration=session.duration_seconds, score=score):
            continue
        if not _rule_available(session, rule):
            continue

        RewardService.award_fixed(
            user=session.user,
            source=Reward.Source.GAME,
            source_reference=str(session.id),
            cash=rule.cash if rule.mode == GameRewardRule.Mode.CASH else 0,
            points=rule.points if rule.mode == GameRewardRule.Mode.POINTS else 0,
            context={"game_id": str(session.game_id), "rule_id": str(rule.id)},
        )
        break

    from apps.automation.services import emit_event

    emit_event("GAME_COMPLETED", session.user, {"game_id": str(session.game_id), "score": score})
    return session


def _rule_available(session: GameSession, rule: GameRewardRule) -> bool:
    from datetime import timedelta

    now = timezone.now()
    cooldown_start = now - timedelta(hours=rule.cooldown_hours)

    recent = GameSession.objects.filter(
        user=session.user, game=session.game, status=GameSession.Status.ENDED,
        ended_at__gte=cooldown_start,
    ).exclude(pk=session.pk)
    if recent.exists():
        return False

    daily = GameSession.objects.filter(
        user=session.user, game=session.game, status=GameSession.Status.ENDED,
        ended_at__date=now.date(),
    ).exclude(pk=session.pk).count()
    if daily >= rule.daily_max:
        return False

    month_count = GameSession.objects.filter(
        user=session.user, game=session.game, status=GameSession.Status.ENDED,
        ended_at__year=now.year, ended_at__month=now.month,
    ).exclude(pk=session.pk).count()
    return month_count < rule.monthly_max
