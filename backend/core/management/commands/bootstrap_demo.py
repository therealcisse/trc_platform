from datetime import UTC, datetime, timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from core.models import Settings
from customers.models import ApiToken, InviteCode

User = get_user_model()


class Command(BaseCommand):
    help = "Bootstrap demo data for the application"

    def handle(self, *args: Any, **options: Any) -> None:
        self.stdout.write("Creating demo data...")

        # Create Settings
        settings, created = Settings.objects.get_or_create(
            pk=1,
            defaults={
                "cost_per_request_cents": 100,
                "openai_model": "gpt-vision",
                "openai_timeout_s": 30,
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS("✓ Created Settings"))
        else:
            self.stdout.write("Settings already exists")

        # Create admin user
        admin_email = "admin@example.com"
        if not User.objects.filter(email=admin_email).exists():
            User.objects.create_superuser(email=admin_email, password="admin123")
            self.stdout.write(
                self.style.SUCCESS(f"✓ Created admin user: {admin_email} (password: admin123)")
            )
        else:
            self.stdout.write(f"Admin user {admin_email} already exists")

        # Create unused invite code
        unused_code = "DEMO1234"
        if not InviteCode.objects.filter(code=unused_code).exists():
            InviteCode.objects.create(
                code=unused_code, is_active=True, expires_at=datetime.now(UTC) + timedelta(days=30)
            )
            self.stdout.write(self.style.SUCCESS(f"✓ Created unused invite code: {unused_code}"))
        else:
            self.stdout.write(f"Invite code {unused_code} already exists")

        # Create verified user
        user_email = "user@example.com"
        if not User.objects.filter(email=user_email).exists():
            user = User.objects.create_user(
                email=user_email, password="user123", email_verified_at=datetime.now(UTC)
            )

            # Create API token for the user
            full_token, token_prefix, token_hash = ApiToken.generate_token()
            ApiToken.objects.create(
                user=user, name="Demo Token", token_prefix=token_prefix, token_hash=token_hash
            )

            self.stdout.write(
                self.style.SUCCESS(f"✓ Created verified user: {user_email} (password: user123)")
            )
            self.stdout.write(self.style.SUCCESS(f"✓ Created API token: {full_token}"))
            self.stdout.write(self.style.WARNING("  Save this token, it will not be shown again!"))
        else:
            self.stdout.write(f"User {user_email} already exists")

        self.stdout.write(self.style.SUCCESS("\n✅ Demo data created successfully!"))
