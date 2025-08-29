"""
Show billing periods for a customer given their email.
"""

from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Sum

from usage.models import BillingPeriod

User = get_user_model()


class Command(BaseCommand):
    help = "Show billing periods for a customer given their email"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "email",
            type=str,
            help="Email address of the customer",
        )
        parser.add_argument(
            "--status",
            type=str,
            choices=["pending", "paid", "overdue", "waived"],
            help="Filter by payment status",
        )
        parser.add_argument(
            "--current",
            action="store_true",
            help="Show only the current billing period",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed information including payment details",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        email: str = options["email"]
        status_filter: str | None = options.get("status")
        current_only: bool = options.get("current", False)
        verbose: bool = options.get("verbose", False)

        # Find the user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f"User with email '{email}' does not exist")

        # Build the query
        queryset = BillingPeriod.objects.filter(user=user)

        if current_only:
            queryset = queryset.filter(is_current=True)

        if status_filter:
            queryset = queryset.filter(payment_status=status_filter)

        # Get the billing periods
        periods = queryset.order_by("-period_start")

        if not periods.exists():
            self.stdout.write(self.style.WARNING(f"No billing periods found for {email}"))
            return

        # Display header
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Billing Periods for {email}"))
        self.stdout.write("=" * 80)

        # Calculate totals
        total_stats = periods.aggregate(
            total_requests=Sum("total_requests"),
            total_cost=Sum("total_cost_cents"),
            total_paid=Sum("paid_amount_cents"),
        )

        # Display each period
        for period in periods:
            self._display_period(period, verbose)

        # Display summary
        self.stdout.write("=" * 80)
        self.stdout.write(self.style.SUCCESS("Summary:"))
        self.stdout.write(f"  Total periods: {periods.count()}")
        self.stdout.write(f"  Total requests: {total_stats['total_requests'] or 0:,}")
        self.stdout.write(f"  Total cost: ${(total_stats['total_cost'] or 0) / 100:,.2f}")
        if total_stats["total_paid"]:
            self.stdout.write(f"  Total paid: ${total_stats['total_paid'] / 100:,.2f}")

        # Payment status breakdown
        status_counts = {}
        for status, label in BillingPeriod.PAYMENT_STATUS_CHOICES:
            count = periods.filter(payment_status=status).count()
            if count > 0:
                status_counts[label] = count

        if status_counts:
            self.stdout.write("\nPayment Status Breakdown:")
            for label, count in status_counts.items():
                self.stdout.write(f"  {label}: {count}")

    def _display_period(self, period: BillingPeriod, verbose: bool) -> None:
        """Display a single billing period."""
        # Main period info
        self.stdout.write("")
        self.stdout.write(f"Period: {period.period_label}")
        self.stdout.write(f"  Date range: {period.period_start} to {period.period_end}")

        if period.is_current:
            self.stdout.write(self.style.WARNING("  Status: CURRENT PERIOD"))

        # Usage stats
        self.stdout.write(f"  Requests: {period.total_requests:,}")
        self.stdout.write(f"  Cost: ${period.total_cost_cents / 100:.2f}")

        # Payment status with color coding
        status_display = f"  Payment status: {period.get_payment_status_display()}"
        if period.payment_status == "paid":
            self.stdout.write(self.style.SUCCESS(status_display))
        elif period.payment_status == "overdue":
            self.stdout.write(self.style.ERROR(status_display))
        elif period.payment_status == "waived":
            self.stdout.write(self.style.WARNING(status_display))
        else:
            self.stdout.write(status_display)

        # Verbose details
        if verbose:
            if period.paid_at:
                self.stdout.write(f"  Paid at: {period.paid_at.strftime('%Y-%m-%d %H:%M:%S')}")
            if period.paid_amount_cents is not None:
                self.stdout.write(f"  Paid amount: ${period.paid_amount_cents / 100:.2f}")
            if period.payment_reference:
                self.stdout.write(f"  Payment reference: {period.payment_reference}")
            if period.payment_notes:
                self.stdout.write(f"  Notes: {period.payment_notes}")

            # Show related request count
            request_count = period.requests.count()
            if request_count > 0:
                self.stdout.write(f"  Request log entries: {request_count}")
