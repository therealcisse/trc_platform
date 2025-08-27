"""Management command to set the application domain for email verification."""

from django.core.management.base import BaseCommand, CommandError
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

from core.models import Settings


class Command(BaseCommand):
    help = "Set the frontend application domain for email verification links"

    def add_arguments(self, parser):
        parser.add_argument(
            "domain",
            nargs="?",
            type=str,
            help="The frontend domain URL (e.g., https://app.example.com)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear the app_domain setting to use backend domain",
        )

    def handle(self, *args, **options):
        settings = Settings.get_settings()
        
        if options["clear"]:
            settings.app_domain = ""
            settings.save()
            self.stdout.write(
                self.style.SUCCESS(
                    "App domain cleared. Email verification will use backend domain."
                )
            )
            return
        
        domain = options.get("domain")
        
        if not domain:
            # Show current setting
            if settings.app_domain:
                self.stdout.write(f"Current app domain: {settings.app_domain}")
            else:
                self.stdout.write("No app domain set. Using backend domain for verification emails.")
            return
        
        # Validate URL
        validator = URLValidator()
        try:
            validator(domain)
        except ValidationError:
            raise CommandError(f"Invalid URL format: {domain}")
        
        # Ensure it's HTTPS in production
        if not domain.startswith("https://") and not domain.startswith("http://localhost"):
            self.stdout.write(
                self.style.WARNING(
                    "Warning: Using non-HTTPS URL. Consider using HTTPS for production."
                )
            )
        
        # Update setting
        settings.app_domain = domain
        settings.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f"App domain set to: {domain}\n"
                f"Email verification links will now use this domain."
            )
        )
        
        # Show example URL
        self.stdout.write(
            f"\nExample verification URL:\n  {domain}/verify-email?token=<token>"
        )
