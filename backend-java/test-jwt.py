#!/usr/bin/env python3
"""
Simple test to verify JWT email verification functionality
"""

import sys
import os
import time
import requests
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Import UAT framework
from uat_test_framework import (
    DatabaseHelper, HTTPClient, TokenManager, TestReporting,
    Colors, print_success, print_error, print_warning, print_info
)
from uat_config import config

def test_jwt_token_generation():
    """Test JWT token generation and validation"""
    print_info("Testing JWT email verification...")

    # Setup test environment
    db_helper = DatabaseHelper(config.DATABASE_URL)
    http_client = HTTPClient(config.APP_URL)

    if not db_helper.connect():
        print_error("Failed to connect to database")
        return False

    # Get admin token
    login_data = {
        "email": config.ADMIN_EMAIL,
        "password": config.ADMIN_PASSWORD
    }

    try:
        response = http_client.post("/api/customers/login", login_data)
        if response.status_code != 200:
            print_error(f"Admin login failed: {response.status_code}")
            return False

        admin_token = response.json().get("token")
        if not admin_token:
            print_error("No admin token received")
            return False

        print_success("Admin login successful")

        # Create invite code
        invite_data = {
            "code": f"JWT-TEST-{int(time.time())}",
            "max_uses": 1,
            "expires_at": "2025-12-31T23:59:59"
        }

        headers = {"Authorization": f"Bearer {admin_token}"}
        response = http_client.post("/api/admin/invite-codes", invite_data, headers=headers)

        if response.status_code != 201:
            print_error(f"Failed to create invite code: {response.status_code}")
            return False

        invite_code = response.json().get("code")
        print_success(f"Created invite code: {invite_code}")

        # Register a test user
        test_email = f"jwt-test-{int(time.time())}@example.com"
        registration_data = {
            "email": test_email,
            "password": "TestPassword123!",
            "confirm_password": "TestPassword123!",
            "invite_code": invite_code,
            "user_accepted_terms": True,
            "user_acknowledged_disclaimer": True
        }

        response = http_client.post("/api/customers/register", registration_data)

        if response.status_code != 202:
            print_error(f"Registration failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return False

        print_success(f"User registered: {test_email}")

        # Wait a moment for email to be sent
        time.sleep(5)

        # Check Mailcatcher for emails
        mailcatcher_response = requests.get("http://localhost:1080/messages")

        if mailcatcher_response.status_code == 200:
            messages = mailcatcher_response.json()
            print_info(f"Found {len(messages)} messages in Mailcatcher")

            if messages:
                latest_message = messages[0]  # Get the first message
                message_id = latest_message.get("id")
                print_info(f"Checking message ID: {message_id}")

                # Get message content
                message_response = requests.get(f"http://localhost:1080/messages/{message_id}.plain")
                if message_response.status_code == 200:
                    content = message_response.text
                    print_info("Email content preview:")
                    print(content[:500] + "..." if len(content) > 500 else content)

                    # Look for JWT token pattern
                    if "verify-email?token=" in content:
                        print_success("Found verification link in email")

                        # Extract token
                        import re
                        match = re.search(r'verify-email\?token=([^\s\n]+)', content)
                        if match:
                            token = match.group(1)
                            print_info(f"Token found: {token[:100]}...")

                            # Check if it's a JWT format (3 parts separated by dots)
                            if token.count('.') == 2:
                                print_success("Token is in JWT format!")
                                return True
                            else:
                                print_warning("Token is not in JWT format")
                                return False
                        else:
                            print_error("Could not extract token from email")
                            return False
                    else:
                        print_error("No verification link found in email")
                        return False
                else:
                    print_error(f"Failed to get email content: {message_response.status_code}")
                    return False
            else:
                print_error("No messages found in Mailcatcher")
                return False
        else:
            print_error(f"Failed to get messages from Mailcatcher: {mailcatcher_response.status_code}")
            return False

    except Exception as e:
        print_error(f"Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = test_jwt_token_generation()
    if success:
        print_success("JWT email verification test PASSED!")
        sys.exit(0)
    else:
        print_error("JWT email verification test FAILED!")
        sys.exit(1)