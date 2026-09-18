"""Seed the standard ad placements.

Usage: python manage.py seed_ad_placements
"""
from django.core.management.base import BaseCommand

from apps.advertising.models import AdPlacement

PLACEMENTS = [
    ("homepage", "Homepage"),
    ("dashboard", "User dashboard"),
    ("games", "Games catalog"),
    ("game_player", "Game player"),
    ("offers", "Offers catalog"),
    ("surveys", "Surveys catalog"),
    ("wallet", "Wallet"),
    ("withdraw", "Withdraw page"),
]


class Command(BaseCommand):
    help = "Create the standard ad placements (idempotent)."

    def handle(self, *args, **options):
        created = 0
        for code, name in PLACEMENTS:
            _, was_created = AdPlacement.objects.get_or_create(
                code=code, defaults={"name": name}
            )
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(f"placements created: {created}"))
