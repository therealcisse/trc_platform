"""Management command to set or show the cost per request in cents."""

from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError

from core.models import Settings


class Command(BaseCommand):
    help = "Set or show the cost per request (in cents)"

    def add_arguments(self, parser):
        parser.add_argument(
            "cents",
            nargs="?",
            type=int,
            help="New cost per request in cents (e.g., 150)",
        )

    def handle(self, *args, **options):
        settings = Settings.get_settings()
        cents = options.get("cents")

        # If no value provided, show current setting
        if cents is None:
            self.stdout.write(
                f"Current cost per request (cents): {settings.cost_per_request_cents}"
            )
            return

        # Validate input
        if cents < 0:
            raise CommandError("cents must be a non-negative integer")

        # Update setting
        settings.cost_per_request_cents = cents
        settings.save(update_fields=["cost_per_request_cents", "updated_at"])

        # Invalidate cached settings so change takes immediate effect
        cache.delete("app_settings")

        dollars = cents / 100.0
        self.stdout.write(
            self.style.SUCCESS(f"Cost per request updated to {cents} cents (${dollars:.2f}).")
        )
