"""
Create billing periods for existing users.
Run once after implementing the billing system.
"""

from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from usage.utils import get_or_create_current_billing_period

User = get_user_model()


class Command(BaseCommand):
    help = "Create current billing periods for all active users"

    def handle(self, *args: Any, **options: Any) -> None:
        users = User.objects.filter(is_active=True)
        count = 0

        for user in users:
            get_or_create_current_billing_period(user)
            count += 1
            self.stdout.write(f"Created/updated billing period for {user.email}")

        self.stdout.write(self.style.SUCCESS(f"Processed {count} users"))
