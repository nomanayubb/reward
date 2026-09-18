"""Scaffold a provider adapter for a new network.

Usage:
    python manage.py scaffold_provider cpa adgem --name "AdGem"
    python manage.py scaffold_provider survey cpx --name "CPX Research"
    python manage.py scaffold_provider payment easypaisa --name "EasyPaisa"

The generated file contains the full interface with TODO markers; fill it in,
add credentials to .env, then register the network in
/admin-panel/providers/ and press Test.
"""
from django.core.management.base import BaseCommand

from apps.adminpanel.scaffolding import (
    adapter_path_for,
    render_adapter,
    target_path,
)


class Command(BaseCommand):
    help = "Scaffold a provider adapter (cpa | survey | payment)."

    def add_arguments(self, parser):
        parser.add_argument("kind", choices=["cpa", "survey", "payment"])
        parser.add_argument("code", help="Network code, e.g. adgem")
        parser.add_argument("--name", default="", help="Display name")
        parser.add_argument(
            "--dry-run", action="store_true", help="Print the file instead of writing it"
        )

    def handle(self, *args, **options):
        kind = options["kind"]
        code = options["code"]
        name = options["name"] or code.replace("-", " ").title()

        content = render_adapter(kind, code, name)

        if options["dry_run"]:
            self.stdout.write(content)
            return

        path = target_path(kind, code)
        if path.exists():
            self.stderr.write(
                self.style.ERROR(f"{path} already exists — not overwriting.")
            )
            return

        path.write_text(content, encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"wrote {path}"))
        self.stdout.write(f"adapter_path = {adapter_path_for(kind, code)}")
        self.stdout.write(
            "next: fill the TODOs, add .env keys, register in "
            "/admin-panel/providers/ and press Test"
        )
