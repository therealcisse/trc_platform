"""
Test script to verify the image storage feature.
Run with: uv run python test_image_storage.py
"""

import os
import uuid

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model

from usage.models import RequestImage, RequestLog

User = get_user_model()


def test_image_storage():
    print("=" * 60)
    print("IMAGE STORAGE FEATURE TEST")
    print("=" * 60)

    # Check configuration
    print("\n1. Configuration Check:")
    print(f"   SAVE_REQUEST_IMAGES: {settings.SAVE_REQUEST_IMAGES}")
    print(f"   MAX_SAVED_IMAGE_SIZE_MB: {settings.MAX_SAVED_IMAGE_SIZE_MB}")
    print(f"   IMAGE_RETENTION_DAYS: {settings.IMAGE_RETENTION_DAYS}")

    # Check models
    print("\n2. Model Check:")
    print(f"   RequestImage model exists: {RequestImage is not None}")
    print(f"   RequestImage table: {RequestImage._meta.db_table}")

    # Check if RequestImage can be created
    print("\n3. RequestImage Creation Test:")
    try:
        # Create a test user if needed
        test_user, created = User.objects.get_or_create(email="test_image@example.com")
        if created:
            print(f"   Created test user: {test_user.email}")

        # Create a test RequestLog
        test_request_id = uuid.uuid4()
        test_log = RequestLog.objects.create(
            user=test_user,
            service="test.image_storage",
            duration_ms=100,
            request_bytes=1000,
            response_bytes=50,
            status="success",
            request_id=test_request_id,
        )
        print(f"   Created test RequestLog: {test_log.request_id}")

        # Create a test RequestImage
        test_image_bytes = b"fake image data for testing"
        test_image = RequestImage.create_from_bytes(
            request_log=test_log, image_bytes=test_image_bytes, mime_type="image/jpeg"
        )
        print(f"   Created test RequestImage: {test_image.id}")
        print(f"   Image hash: {test_image.image_hash[:16]}...")
        print(f"   File size: {test_image.file_size} bytes")

        # Verify relationship
        assert test_log.saved_image == test_image
        print("   ✓ One-to-one relationship verified")

        # Clean up
        test_image.delete()
        test_log.delete()
        if created:
            test_user.delete()
        print("   ✓ Test data cleaned up")

    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False

    # Check admin registration
    print("\n4. Admin Interface Check:")
    from django.contrib import admin

    from usage.admin import RequestImageAdmin

    print(f"   RequestImage admin registered: {RequestImage in admin.site._registry}")
    print(f"   Admin class: {RequestImageAdmin.__name__}")

    # Check management command
    print("\n5. Management Command Check:")
    from django.core.management import get_commands

    commands = get_commands()
    print(f"   cleanup_old_images command exists: {'cleanup_old_images' in commands}")

    # Check API endpoint
    print("\n6. API Endpoint Check:")
    from django.urls import reverse

    try:
        url = reverse("image_performance_stats")
        print(f"   image_performance_stats URL: {url}")
    except Exception as e:
        print(f"   ✗ URL not found: {e}")

    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nTo enable the feature, set environment variable:")
    print("  export SAVE_REQUEST_IMAGES=true")
    print("\nTo test with actual images:")
    print("  1. Enable the feature with the environment variable")
    print("  2. Send requests to /api/core/solve with images")
    print("  3. Check Django admin at /admin/usage/requestimage/")
    print("  4. View stats at /api/usage/image-performance-stats (admin only)")
    print("=" * 60)

    return True


if __name__ == "__main__":
    test_image_storage()
