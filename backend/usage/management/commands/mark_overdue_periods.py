"""
Run monthly to mark unpaid periods as overdue.
Example cron: 0 0 5 * * python manage.py mark_overdue_periods
"""

from datetime import timedelta
from typing import Any

from django.core.management.base import BaseCommand
from django.utils import timezone

from usage.models import BillingPeriod


class Command(BaseCommand):
    help = "Mark unpaid billing periods as overdue"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Number of days after period end to mark as overdue",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        days = options["days"]

        # Mark periods as overdue if they ended > X days ago and are still pending
        cutoff_date = timezone.now().date() - timedelta(days=days)

        overdue_periods = BillingPeriod.objects.filter(
            period_end__lt=cutoff_date, payment_status="pending", is_current=False
        )

        count = 0
        for period in overdue_periods:
            period.mark_as_overdue()
            count += 1
            self.stdout.write(f"Marked {period} as overdue")

        self.stdout.write(self.style.SUCCESS(f"Marked {count} billing periods as overdue"))
