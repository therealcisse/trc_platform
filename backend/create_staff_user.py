"""
Script to create a staff user using the custom User model.
"""
import os
from datetime import UTC, datetime

import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from customers.models import User  # noqa: E402

# Create staff user
try:
    staff_user = User.objects.create_user(email="user@trc.com", password="user")
    staff_user.is_staff = False
    staff_user.is_superuser = False
    staff_user.email_verified_at = datetime.now(UTC)
    staff_user.save()

    print("✅ Staff user created successfully!")
    print(f"   Email: {staff_user.email}")
    print(f"   Is staff: {staff_user.is_staff}")
    print(f"   Is superuser: {staff_user.is_superuser}")
    print(f"   Is active: {staff_user.is_active}")
    print(f"   Email verified: {staff_user.is_email_verified}")

except Exception as e:
    if "UNIQUE constraint failed" in str(e) or "duplicate key" in str(e).lower():
        print("⚠️  User with email 'user@trc.com' already exists")
        # Try to update existing user
        try:
            staff_user = User.objects.get(email="user@trc.com")
            staff_user.is_staff = False
            staff_user.email_verified_at = datetime.now(UTC)
            staff_user.save()
            print("✅ Existing user updated to staff status")
            print(f"   Email: {staff_user.email}")
            print(f"   Is staff: {staff_user.is_staff}")
            print(f"   Is superuser: {staff_user.is_superuser}")
            print(f"   Email verified: {staff_user.is_email_verified}")
        except Exception as update_error:
            print(f"❌ Error updating user: {update_error}")
    else:
        print(f"❌ Error creating user: {e}")
