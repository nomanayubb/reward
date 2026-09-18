"""Reconcile a CPA provider's report against our conversion records.

Usage:
    python manage.py reconcile_provider adgem --days 7
"""
from django.core.management.base import BaseCommand, CommandError

from apps.cpa.models import CPAProvider
from apps.offers.reconciliation import reconcile_provider


class Command(BaseCommand):
    help = "Compare a provider's reported conversions/payout against our records."

    def add_arguments(self, parser):
        parser.add_argument("provider_code", help="CPAProvider code, e.g. adgem")
        parser.add_argument("--days", type=int, default=7)

    def handle(self, *args, **options):
        provider = CPAProvider.objects.filter(code=options["provider_code"]).first()
        if provider is None:
            raise CommandError(f"No CPAProvider with code '{options['provider_code']}'.")

        result = reconcile_provider(provider, days=options["days"])

        self.stdout.write(f"Provider: {result.provider}")
        self.stdout.write(f"Period:   {result.period_start} → {result.period_end}")
        self.stdout.write("")
        self.stdout.write(f"Reported conversions: {result.reported_conversions}")
        self.stdout.write(f"Our conversions:      {result.local_conversions}")
        self.stdout.write(f"Conversion diff:      {result.conversion_difference}")
        self.stdout.write("")
        self.stdout.write(f"Reported payout (USD): {result.reported_payout}")
        self.stdout.write(f"Our payout (USD):      {result.local_payout}")
        self.stdout.write(f"Payout difference:     {result.payout_difference}")

        if result.is_balanced:
            self.stdout.write(self.style.SUCCESS("\nBalanced — no action needed."))
        else:
            self.stdout.write(
                self.style.WARNING(
                    "\nMismatch detected. Check missing/extra conversions with the "
                    "provider's dashboard before raising a dispute."
                )
            )
