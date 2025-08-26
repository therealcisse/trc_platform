#!/usr/bin/env python
"""Verify and compare July (closed) and August (current) billing periods."""

import os

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db.models import Avg, Count

from customers.models import ApiToken, User
from usage.models import BillingPeriod, RequestImage, RequestLog


def format_status(status: str) -> str:
    """Format payment status with color."""
    colors = {
        "paid": "\033[92m",  # Green
        "pending": "\033[93m",  # Yellow
        "overdue": "\033[91m",  # Red
        "waived": "\033[94m",  # Blue
    }
    reset = "\033[0m"
    color = colors.get(status, "")
    return f"{color}{status.upper()}{reset}"


def print_period_summary(period: BillingPeriod, token_name: str) -> None:
    """Print detailed summary for a billing period."""
    print(f"\n{'='*60}")
    print(f"{period.period_label} - {period.user.email}")
    print(f"{'='*60}")

    # Period info
    print("\nPeriod Details:")
    print(f"  - Range: {period.period_start} to {period.period_end}")
    print(f"  - Is Current: {'Yes' if period.is_current else 'No'}")
    print(f"  - Payment Status: {format_status(period.payment_status)}")

    if period.payment_status == "paid":
        print(
            f"  - Paid At: {period.paid_at.strftime('%Y-%m-%d %H:%M') if period.paid_at else 'N/A'}"
        )
        print(
            f"  - Amount Paid: ${period.paid_amount_cents / 100:.2f}"
            if period.paid_amount_cents
            else ""
        )
        print(f"  - Reference: {period.payment_reference}" if period.payment_reference else "")

    if period.payment_notes:
        print(f"  - Notes: {period.payment_notes}")

    # API Token info
    try:
        token = ApiToken.objects.get(name=token_name, user=period.user, revoked_at__isnull=True)
        print(f"\nAPI Token '{token_name}':")
        print(f"  - Prefix: {token.token_prefix}")
        print(f"  - Created: {token.created_at.strftime('%Y-%m-%d %H:%M')}")
        print(
            f"  - Last Used: {token.last_used_at.strftime('%Y-%m-%d %H:%M') if token.last_used_at else 'Never'}"
        )
    except ApiToken.DoesNotExist:
        print(f"\nAPI Token '{token_name}': Not found")

    # Request statistics
    requests = RequestLog.objects.filter(billing_period=period)
    total = requests.count()

    if total > 0:
        successful = requests.filter(status="success").count()
        errors = requests.filter(status="error").count()
        with_images = RequestImage.objects.filter(request_log__billing_period=period).count()

        # Calculate averages
        avg_duration = requests.aggregate(Avg("duration_ms"))["duration_ms__avg"]
        avg_request_size = requests.aggregate(Avg("request_bytes"))["request_bytes__avg"]
        avg_response_size = requests.aggregate(Avg("response_bytes"))["response_bytes__avg"]

        print("\nRequest Statistics:")
        print(f"  - Total Requests: {total}")
        print(f"  - Total Cost: ${period.total_cost_cents / 100:.2f}")
        print(f"  - Successful: {successful} ({successful*100/total:.1f}%)")
        print(f"  - Errors: {errors} ({errors*100/total:.1f}%)")
        print(
            f"  - With Images: {with_images} ({with_images*100/successful:.1f}% of successful)"
            if successful > 0
            else ""
        )

        print("\nPerformance Metrics:")
        print(f"  - Avg Duration: {avg_duration:.0f}ms")
        print(f"  - Avg Request Size: {avg_request_size/1024:.1f}KB")
        print(f"  - Avg Response Size: {avg_response_size/1024:.1f}KB")

        # Daily breakdown (first 5 days and last 5 days)
        from django.db.models.functions import TruncDate

        daily_stats = (
            requests.annotate(date=TruncDate("request_ts"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        daily_list = list(daily_stats)
        if daily_list:
            print("\nDaily Request Distribution:")
            # Show first 5 days
            for stat in daily_list[:5]:
                print(f"  - {stat['date'].strftime('%Y-%m-%d')}: {stat['count']} requests")

            if len(daily_list) > 10:
                print(f"  ... ({len(daily_list) - 10} more days)")

            # Show last 5 days if more than 5 days total
            if len(daily_list) > 5:
                for stat in daily_list[-5:]:
                    if stat not in daily_list[:5]:  # Don't repeat if already shown
                        print(f"  - {stat['date'].strftime('%Y-%m-%d')}: {stat['count']} requests")

        # Error breakdown if any
        if errors > 0:
            error_breakdown = (
                requests.filter(status="error")
                .values("error_code")
                .annotate(count=Count("id"))
                .order_by("-count")
            )
            print("\nError Breakdown:")
            for error in error_breakdown:
                print(f"  - {error['error_code']}: {error['count']} occurrences")


def main():
    print("\n" + "=" * 60)
    print("BILLING PERIODS VERIFICATION")
    print("=" * 60)

    # Get all unique users with billing periods
    users_with_periods = User.objects.filter(
        billing_periods__period_start__year=2025, billing_periods__period_start__month__in=[6, 7, 8]
    ).distinct()

    if not users_with_periods.exists():
        print("\nNo billing periods found for June, July, or August 2025.")
        print("Please run the generation scripts first:")
        print("  ./generate_june_data.sh")
        print("  ./generate_july_data.sh")
        print("  ./generate_august_data.sh")
        return

    for user in users_with_periods:
        print(f"\n\n{'#'*60}")
        print(f"USER: {user.email}")
        print(f"{'#'*60}")

        # Check June period
        try:
            june_period = BillingPeriod.objects.get(
                user=user, period_start__year=2025, period_start__month=6
            )
            print_period_summary(june_period, "JUNE")
        except BillingPeriod.DoesNotExist:
            print(f"\n{'='*60}")
            print("June 2025 - No data")
            print(f"{'='*60}")

        # Check July period
        try:
            july_period = BillingPeriod.objects.get(
                user=user, period_start__year=2025, period_start__month=7
            )
            print_period_summary(july_period, "JULY")
        except BillingPeriod.DoesNotExist:
            print(f"\n{'='*60}")
            print("July 2025 - No data")
            print(f"{'='*60}")

        # Check August period
        try:
            august_period = BillingPeriod.objects.get(
                user=user, period_start__year=2025, period_start__month=8
            )
            print_period_summary(august_period, "AUGUST")
        except BillingPeriod.DoesNotExist:
            print(f"\n{'='*60}")
            print("August 2025 - No data")
            print(f"{'='*60}")

    # Summary comparison
    print(f"\n\n{'='*60}")
    print("SUMMARY COMPARISON")
    print(f"{'='*60}")

    all_periods = BillingPeriod.objects.filter(
        period_start__year=2025, period_start__month__in=[6, 7, 8]
    ).order_by("user__email", "period_start")

    if all_periods:
        print("\nAll Billing Periods:")
        print(f"{'User':<30} {'Period':<15} {'Status':<10} {'Current':<8} {'Total':<10}")
        print("-" * 73)

        for period in all_periods:
            current = "Yes" if period.is_current else "No"
            print(
                f"{period.user.email:<30} {period.period_label:<15} {period.payment_status:<10} {current:<8} ${period.total_cost_cents/100:>8.2f}"
            )

    print("\n" + "=" * 60)
    print("Verification complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
