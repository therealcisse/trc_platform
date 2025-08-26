#!/usr/bin/env python
"""
Test script for the test-solve endpoint.
This script tests that the session-authenticated endpoint is working correctly.
"""

import requests
from pathlib import Path
import json

# Configuration
BASE_URL = "http://localhost:8000/api"
EMAIL = "chattest@example.com"
PASSWORD = "test123"

# Create a session to maintain cookies
session = requests.Session()

print("1. Testing login...")
login_response = session.post(
    f"{BASE_URL}/customers/login",
    json={"email": EMAIL, "password": PASSWORD}
)

if login_response.status_code == 200:
    print("   ✓ Login successful")
    user_data = login_response.json()
    print(f"   User: {user_data['email']}")
else:
    print(f"   ✗ Login failed: {login_response.status_code}")
    print(f"   Response: {login_response.text}")
    exit(1)

print("\n2. Getting CSRF token...")
# Make a GET request to get CSRF token
me_response = session.get(f"{BASE_URL}/customers/me")
if me_response.status_code == 200:
    print("   ✓ Got user info and CSRF token")
    csrf_token = session.cookies.get('csrftoken')
    print(f"   CSRF Token: {csrf_token[:20]}...")
else:
    print(f"   ✗ Failed to get user info: {me_response.status_code}")
    exit(1)

print("\n3. Testing test-solve endpoint...")
# Create a simple test image (1x1 white pixel PNG)
import base64
test_image_data = base64.b64decode(
    b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
)

# Prepare the file upload
files = {'file': ('test.png', test_image_data, 'image/png')}
headers = {}
if csrf_token:
    headers['X-CSRFToken'] = csrf_token

# Send the request
solve_response = session.post(
    f"{BASE_URL}/customers/test-solve",
    files=files,
    headers=headers
)

if solve_response.status_code == 200:
    print("   ✓ Test solve successful!")
    result = solve_response.json()
    print(f"   Request ID: {result.get('request_id')}")
    print(f"   Model: {result.get('model')}")
    print(f"   Duration: {result.get('duration_ms')}ms")
    print(f"   Is Test: {result.get('is_test')}")
    print(f"   Result preview: {result.get('result', '')[:100]}...")
else:
    print(f"   ✗ Test solve failed: {solve_response.status_code}")
    print(f"   Response: {solve_response.text}")

print("\n4. Logging out...")
logout_response = session.post(
    f"{BASE_URL}/customers/logout",
    headers={'X-CSRFToken': csrf_token} if csrf_token else {}
)
if logout_response.status_code == 204:
    print("   ✓ Logout successful")
else:
    print(f"   ✗ Logout failed: {logout_response.status_code}")

print("\nTest complete!")
