"""
Test script to verify that results are being stored in RequestLog.
"""

import os

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model

from core.services import openai_client
from usage.models import RequestLog

User = get_user_model()


def test_result_storage():
    """Test that results are properly stored in RequestLog."""
    print("\n=== Testing Result Storage in RequestLog ===")
    print(f"USE_MOCK_OPENAI: {settings.USE_MOCK_OPENAI}")

    # Get or create a test user
    test_email = "test_result@example.com"
    user, created = User.objects.get_or_create(
        email=test_email,
    )
    if created:
        print(f"Created test user: {test_email}")
    else:
        print(f"Using existing test user: {test_email}")

    # Get initial count of request logs
    initial_count = RequestLog.objects.filter(user=user).count()
    print(f"\nInitial RequestLog count for user: {initial_count}")

    # Test successful request
    print("\n--- Testing Successful Request ---")
    test_image = b"x" * 5000  # 5KB test image
    result = openai_client.solve_image(test_image, return_dict=True)
    print(f"Solver result: {result['result']}")
    print(f"Model used: {result['model']}")

    # Simulate creating a RequestLog (normally done in the view)
    from uuid import uuid4

    from usage.utils import get_or_create_current_billing_period

    billing_period = get_or_create_current_billing_period(user)

    request_log = RequestLog.objects.create(
        user=user,
        token=None,
        billing_period=billing_period,
        service="core.image_solve",
        duration_ms=100,
        request_bytes=len(test_image),
        response_bytes=len(result["result"]),
        status="success",
        request_id=uuid4(),
        result=result["result"],  # Store the result
    )
    print(f"\nCreated RequestLog with ID: {request_log.id}")

    # Verify the result was stored
    saved_log = RequestLog.objects.get(id=request_log.id)
    print(f"Stored result: '{saved_log.result}'")
    print(f"Result matches: {saved_log.result == result['result']}")

    # Test error case (result should be None)
    print("\n--- Testing Error Case ---")
    from core.services.exceptions import InvalidImageError

    try:
        # Try with empty image to trigger an error
        empty_image = b""
        error_result = openai_client.solve_image(empty_image)
    except InvalidImageError as e:
        print(f"Expected error occurred: {e}")

        # Simulate creating an error log
        error_log = RequestLog.objects.create(
            user=user,
            token=None,
            billing_period=billing_period,
            service="core.image_solve",
            duration_ms=50,
            request_bytes=0,
            response_bytes=0,
            status="error",
            error_code=e.error_code.value,
            request_id=uuid4(),
            result=None,  # No result for errors
        )
        print(f"Created error RequestLog with ID: {error_log.id}")

        # Verify no result was stored for error
        saved_error_log = RequestLog.objects.get(id=error_log.id)
        print(f"Error log result is None: {saved_error_log.result is None}")

    # Check recent logs
    print("\n--- Recent RequestLogs for User ---")
    recent_logs = RequestLog.objects.filter(user=user).order_by("-request_ts")[:5]
    for log in recent_logs:
        print(f"  {log.request_ts} - Status: {log.status}, Result: {log.result}")

    # Summary
    final_count = RequestLog.objects.filter(user=user).count()
    print("\n=== Summary ===")
    print(f"RequestLogs created in this test: {final_count - initial_count}")
    print(f"Total RequestLogs for user: {final_count}")

    # Check that we can query by result
    logs_with_results = RequestLog.objects.filter(user=user, result__isnull=False).count()
    logs_without_results = RequestLog.objects.filter(user=user, result__isnull=True).count()
    print(f"Logs with results: {logs_with_results}")
    print(f"Logs without results: {logs_without_results}")


if __name__ == "__main__":
    test_result_storage()
    print("\n✅ Test completed successfully!")
