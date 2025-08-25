from datetime import timedelta

from django.utils import timezone

from customers.models import User
from .models import BillingPeriod


def get_or_create_current_billing_period(user: User) -> BillingPeriod:
    """Get or create billing period for current month."""
    from .models import BillingPeriod

    today = timezone.now().date()
    period_start = today.replace(day=1)

    # Calculate period end (last day of month)
    if period_start.month == 12:
        period_end = period_start.replace(year=period_start.year + 1, month=1, day=1) - timedelta(
            days=1
        )
    else:
        period_end = period_start.replace(month=period_start.month + 1, day=1) - timedelta(days=1)

    # Mark any previous periods as not current
    BillingPeriod.objects.filter(user=user, is_current=True).update(is_current=False)

    # Get or create current period
    billing_period, created = BillingPeriod.objects.get_or_create(
        user=user,
        period_start=period_start,
        defaults={"period_end": period_end, "is_current": True},
    )

    if not created and not billing_period.is_current:
        billing_period.is_current = True
        billing_period.save(update_fields=["is_current"])

    return billing_period
