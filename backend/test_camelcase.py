#!/usr/bin/env python
"""
Test script to verify camelCase JSON conversion in Django REST Framework
"""

import os

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

import json
from datetime import date

from customers.models import User
from usage.models import BillingPeriod
from usage.serializers import CurrentBillingPeriodSerializer


def test_camelcase_conversion() -> None:
    """Test that the serializer outputs camelCase fields"""

    # Create a test user
    user, created = User.objects.get_or_create(
        email="test@example.com", defaults={"is_active": True}
    )

    # Create or get a billing period
    period, created = BillingPeriod.objects.get_or_create(
        user=user,
        period_start=date(2025, 8, 1),
        defaults={
            "period_end": date(2025, 8, 31),
            "total_requests": 42,
            "total_cost_cents": 4200,
            "is_current": True,
            "payment_status": "pending",
        },
    )

    # Create a serializer instance
    serializer = CurrentBillingPeriodSerializer(period)

    # Get the data
    data = serializer.data

    print("=" * 60)
    print("Testing CamelCase Conversion")
    print("=" * 60)

    # Test with the camelCase renderer
    from djangorestframework_camel_case.render import CamelCaseJSONRenderer  # type: ignore[import-untyped]
    from djangorestframework_camel_case.util import camelize  # type: ignore[import-untyped]

    renderer = CamelCaseJSONRenderer()

    # Convert to camelCase
    camelized_data = camelize(data)

    print("\n1. Original snake_case fields from serializer:")
    print("-" * 40)
    for key in data.keys():
        print(f"  - {key}")

    print("\n2. Converted camelCase fields:")
    print("-" * 40)
    for key in camelized_data.keys():
        print(f"  - {key}")

    print("\n3. Sample JSON output (camelCase):")
    print("-" * 40)
    json_output = json.dumps(camelized_data, indent=2, default=str)
    print(json_output)

    print("\n4. Verification:")
    print("-" * 40)

    # Check that snake_case fields are converted
    expected_conversions = {
        "period_start": "periodStart",
        "period_end": "periodEnd",
        "period_label": "periodLabel",
        "total_requests": "totalRequests",
        "total_cost_cents": "totalCostCents",
        "is_current": "isCurrent",
        "last_request_at": "lastRequestAt",
    }

    for snake, camel in expected_conversions.items():
        if snake in data:
            if camel in camelized_data:
                print(f"  ✓ {snake} -> {camel}")
            else:
                print(f"  ✗ {snake} NOT converted to {camel}")
        else:
            print(f"  - {snake} not in original data")

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

    # Clean up if we created test data
    if created:
        period.delete()
        if user.email == "test@example.com":
            user.delete()


if __name__ == "__main__":
    test_camelcase_conversion()
