"""Seed the bundled games with starter reward rules.

Usage: python manage.py seed_reference_game
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.games.models import Game, GameRewardRule

GAMES = [
    {
        "slug": "tap-target",
        "title": "Tap Target",
        "description": "Tap the circles before they vanish. You have 30 seconds.",
        "min_session_seconds": 10,
        "rule": {
            "name": "Starter: score 5 -> 5 points",
            "conditions": {"min_score": 5},
            "points": Decimal("5"),
        },
    },
    {
        "slug": "memory-match",
        "title": "Memory Match",
        "description": "Find all 8 pairs with as few moves as possible.",
        "min_session_seconds": 15,
        "rule": {
            "name": "Starter: score 100 -> 5 points",
            "conditions": {"min_score": 100},
            "points": Decimal("5"),
        },
    },
    {
        "slug": "snake",
        "title": "Snake",
        "description": "Eat the food, avoid the walls and yourself. 90 seconds.",
        "min_session_seconds": 15,
        "rule": {
            "name": "Starter: score 3 -> 5 points",
            "conditions": {"min_score": 3},
            "points": Decimal("5"),
        },
    },
]


class Command(BaseCommand):
    help = "Create/update the bundled games and their starter reward rules."

    def handle(self, *args, **options):
        for entry in GAMES:
            game, created = Game.objects.update_or_create(
                slug=entry["slug"],
                defaults={
                    "title": entry["title"],
                    "description": entry["description"],
                    "entry_path": "game.html",
                    "status": Game.Status.ACTIVE,
                    "min_session_seconds": entry["min_session_seconds"],
                    "is_featured": True,
                },
            )

            rule = entry["rule"]
            _, rule_created = GameRewardRule.objects.get_or_create(
                game=game,
                name=rule["name"],
                defaults={
                    "conditions": rule["conditions"],
                    "mode": GameRewardRule.Mode.POINTS,
                    "points": rule["points"],
                    "cooldown_hours": 0,
                    "daily_max": 5,
                    "monthly_max": 50,
                },
            )

            self.stdout.write(
                self.style.SUCCESS(
                    f"{game.slug}: game {'created' if created else 'updated'}, "
                    f"rule {'created' if rule_created else 'already present'}"
                )
            )
