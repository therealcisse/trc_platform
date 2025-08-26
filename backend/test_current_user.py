#!/usr/bin/env python
"""
Test script to verify the /customers/me endpoint returns the correct logged-in user.
"""

import os

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

import json

from django.contrib.auth import get_user_model
from django.test import Client
from django.utils import timezone as django_utils_timezone

User = get_user_model()


def test_current_user_endpoint() -> None:
    """Test that /customers/me returns the correct logged-in user."""

    client = Client()

    # Get all users
    users = User.objects.all()
    print(f"Total users in database: {users.count()}")
    for user in users:
        print(f"  - {user.email} (admin: {user.is_staff}, superuser: {user.is_superuser})")

    print("\n" + "=" * 50)

    # Test with a regular user (not admin)
    regular_users = User.objects.filter(is_staff=False, is_superuser=False)
    if not regular_users.exists():
        print("No regular users found. Creating test user...")
        test_user = User.objects.create_user(
            email="test_current@example.com", password="testpass123"
        )
        test_user.email_verified_at = django_utils_timezone.now()
        test_user.save()
        print(f"Created test user: {test_user.email}")
    else:
        test_user = regular_users.first()  # type: ignore[assignment]
        print(f"Using existing regular user: {test_user.email}")

    # Ensure the user has a verified email
    if not test_user.is_email_verified:
        print(f"   Setting email as verified for {test_user.email}")
        test_user.email_verified_at = django_utils_timezone.now()
        test_user.save()

    # Try to login with this user
    print(f"\n1. Testing login with {test_user.email}...")

    # First, ensure we can set a password for testing
    test_user.set_password("testpass123")
    test_user.save()

    login_response = client.post(
        "/api/customers/login",
        data=json.dumps({"email": test_user.email, "password": "testpass123"}),
        content_type="application/json",
    )

    if login_response.status_code == 200:
        login_data = login_response.json()
        print("   ✓ Login successful!")
        print(f"   Response: {login_data}")

        # Check session
        if client.session:
            print(f"   Session ID: {client.session.session_key}")
            print(f"   Session data keys: {list(client.session.keys())}")
            if "_auth_user_id" in client.session:
                session_user_id = client.session["_auth_user_id"]
                print(f"   Session user ID: {session_user_id}")
                session_user = User.objects.get(pk=session_user_id)
                print(f"   Session user email: {session_user.email}")

        # Now test /customers/me
        print("\n2. Testing /customers/me endpoint...")
        me_response = client.get("/api/customers/me")

        if me_response.status_code == 200:
            me_data = me_response.json()
            print("   ✓ /customers/me successful!")
            print(f"   Response: {me_data}")

            # Verify it's the correct user
            if me_data.get("email") == test_user.email:
                print("\n   ✅ SUCCESS: /customers/me returned the correct user!")
            else:
                print("\n   ❌ ERROR: /customers/me returned wrong user!")
                print(f"      Expected: {test_user.email}")
                print(f"      Got: {me_data.get('email')}")

                # Check if it returned an admin
                if me_data.get("email"):
                    returned_user = User.objects.get(email=me_data.get("email"))
                    print(f"      Returned user is_staff: {returned_user.is_staff}")
                    print(f"      Returned user is_superuser: {returned_user.is_superuser}")
        else:
            print(f"   ❌ /customers/me failed: {me_response.status_code}")
            print(f"   Response: {me_response.content.decode()}")
    else:
        print(f"   ❌ Login failed: {login_response.status_code}")
        print(f"   Response: {login_response.content.decode()}")

    # Test with admin user to see if there's session contamination
    print("\n" + "=" * 50)
    print("\n3. Testing with a new client session (admin user)...")

    admin_client = Client()
    admin_users = User.objects.filter(is_staff=True)
    if admin_users.exists():
        admin_user = admin_users.first()
        if admin_user:
            print(f"   Testing with admin: {admin_user.email}")

            # Set password for admin
            admin_user.set_password("adminpass123")
            admin_user.save()

            admin_login = admin_client.post(
                "/api/customers/login",
                data=json.dumps({"email": admin_user.email, "password": "adminpass123"}),
                content_type="application/json",
            )

            if admin_login.status_code == 200:
                print("   ✓ Admin login successful")

                admin_me = admin_client.get("/api/customers/me")
                if admin_me.status_code == 200:
                    admin_me_data = admin_me.json()
                    print(f"   Admin /me response: {admin_me_data.get('email')}")

        # Now check if original client still returns correct user
        print("\n4. Re-checking original client session...")
        me_recheck = client.get("/api/customers/me")
        if me_recheck.status_code == 200:
            recheck_data = me_recheck.json()
            if recheck_data.get("email") == test_user.email:
                print(
                    f"   ✅ Original session still returns correct user: {recheck_data.get('email')}"
                )
            else:
                print("   ❌ Session contamination detected!")
                print(f"      Expected: {test_user.email}")
                print(f"      Got: {recheck_data.get('email')}")


if __name__ == "__main__":
    test_current_user_endpoint()
