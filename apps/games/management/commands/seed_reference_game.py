"""Seed the reference game (tap-target) with a starter reward rule.

Usage: python manage.py seed_reference_game
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.games.models import Game, GameRewardRule


class Command(BaseCommand):
    help = "Create/update the reference tap-target game and a starter reward rule."

    def handle(self, *args, **options):
        game, created = Game.objects.update_or_create(
            slug="tap-target",
            defaults={
                "title": "Tap Target",
                "description": "Tap the circles before they vanish. You have 30 seconds.",
                "entry_path": "game.html",
                "status": Game.Status.ACTIVE,
                "min_session_seconds": 10,
                "is_featured": True,
            },
        )

        _, rule_created = GameRewardRule.objects.get_or_create(
            game=game,
            name="Starter: score 5 -> 5 points",
            defaults={
                "conditions": {"min_score": 5},
                "mode": GameRewardRule.Mode.POINTS,
                "points": Decimal("5"),
                "cooldown_hours": 0,
                "daily_max": 5,
                "monthly_max": 50,
            },
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"tap-target {'created' if created else 'updated'}; "
                f"reward rule {'created' if rule_created else 'already present'}"
            )
        )
