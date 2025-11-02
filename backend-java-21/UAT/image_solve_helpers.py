#!/usr/bin/env python3
"""
Image Solve Helpers for TRC Platform UAT Testing
Provides utilities for testing /api/core/solve endpoint
including image processing, validation, and test scenario management
"""

import sys
import os
import json
import uuid
import time
import base64
import mimetypes
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from pathlib import Path
import psycopg2
import psycopg2.extras
import requests
from datetime import datetime, timedelta

# Import UAT framework
from uat_framework import (
    DatabaseHelper, HTTPClient, TokenManager, TestReporting,
    TestStep, TestResult, Colors, print_success, print_error, print_warning, print_info,
    extract_jwt_token, wait_for_email_verification, EmailVerificationHelper
)

# Import configuration
from uat_config import config

@dataclass
class SolveResponseData:
    """Test data structure for solve response validation"""
    request_id: str
    result: str
    duration_ms: int
    timings: Dict[str, int]
    status_code: int
    response_time: float
    raw_response: Dict[str, Any]

@dataclass
class ImageTestData:
    """Test data structure for image test files"""
    filename: str
    filepath: str
    expected_answer: str
    file_size: int
    mime_type: str

class ImageHelper:
    """Helper class for image solve testing operations"""

    def __init__(self, db_helper: DatabaseHelper = None, http_client: HTTPClient = None):
        self.db_helper = db_helper or DatabaseHelper(config.database_url)
        self.http_client = http_client or HTTPClient(config.app_url)
        self.image_dir = Path(__file__).parent / "tests" / "image_solve" / "images"

    def get_test_images(self) -> List[ImageTestData]:
        """
        Get all test images from the images directory
        Parses filename pattern {number}_a{answer}.png to extract expected answers
        """
        images = []

        if not self.image_dir.exists():
            print_error(f"Image directory not found: {self.image_dir}")
            return images

        for image_file in self.image_dir.glob("*.png"):
            try:
                # Parse filename to extract expected answer
                # Pattern: {number}_a{answer}.png
                # Example: 002_a14.png -> expected_answer = "14"
                # Special case: 000__a10.png -> expected_answer = "10"
                stem = image_file.stem

                if "_a" in stem:
                    parts = stem.split("_a")
                    if len(parts) == 2:
                        expected_answer = parts[1]
                        # Handle special case of double underscore
                        if expected_answer.startswith("_"):
                            expected_answer = expected_answer[1:]
                    else:
                        print_warning(f"Unexpected filename format: {image_file.name}")
                        continue
                else:
                    print_warning(f"Filename does not contain expected answer pattern: {image_file.name}")
                    continue

                # Get file info
                file_size = image_file.stat().st_size
                mime_type, _ = mimetypes.guess_type(str(image_file))
                mime_type = mime_type or "image/png"

                image_data = ImageTestData(
                    filename=image_file.name,
                    filepath=str(image_file),
                    expected_answer=expected_answer,
                    file_size=file_size,
                    mime_type=mime_type
                )
                images.append(image_data)

            except Exception as e:
                print_error(f"Error processing image {image_file.name}: {e}")
                continue

        # Sort by filename for consistent ordering
        images.sort(key=lambda x: x.filename)
        print_info(f"Loaded {len(images)} test images from {self.image_dir}")
        return images

    def create_image_test_user(self, admin_token: str, run_id: str = None) -> TestStep:
        """
        Create a dedicated test user for image solve testing
        Follows the same pattern as usage domain testing
        """
        step = TestStep(
            step_number=1,
            step_name="Create Image Test User",
            status="PASS",
            message="Create test user with invite code for image solve testing"
        )

        try:
            if not run_id:
                run_id = str(uuid.uuid4())[:8]

            # Generate unique user details using config
            test_email = config.generate_unique_email("image-solve")
            test_password = "TestPassword123!"
            test_first_name = "Image"
            test_last_name = f"Solve-{run_id}"

            # Create invite code with admin token (billing module pattern)
            test_code = config.generate_unique_invite_code("IMG-SOLVE-TEST")
            invite_code_data = {"code": test_code}

            invite_response, invite_response_time = self.http_client.post(
                config.get_endpoint('admin_invites'),
                invite_code_data,
                auth_token=admin_token
            )

            if invite_response.status_code not in [config.STATUS_CODES['success'], config.STATUS_CODES['created']]:
                step.status = "FAIL"
                step.message = f"Failed to create invite code: {invite_response.status_code}"
                return step

            invite_code = test_code
            print_success(f"Created invite code: {invite_code}")

            # Register new user with invite code (billing module pattern)
            user_data = {
                "email": test_email,
                "password": test_password,
                "confirmPassword": test_password,
                "inviteCode": invite_code,
                "userAcceptedTerms": True,
                "userAcknowledgedDisclaimer": True
            }

            register_response, register_response_time = self.http_client.post(
                config.get_endpoint('user_register'),
                user_data
            )

            if register_response.status_code not in [config.STATUS_CODES['accepted'], config.STATUS_CODES['created']]:
                step.status = "FAIL"
                step.message = f"Failed to register user: {register_response.status_code}"
                return step

            user_info = register_response.json()
            print_success(f"Registered test user: {test_email}")

            # Login with new user to get JWT token (billing module pattern)
            login_data = {
                "email": test_email,
                "password": test_password
            }

            login_response, login_response_time = self.http_client.post(
                config.get_endpoint('login'),
                login_data
            )

            if login_response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = f"Failed to login user: {login_response.status_code}"
                return step

            jwt_token = extract_jwt_token(login_response.json()['token'])
            print_success("Obtained JWT token for test user")

            # Store test user information for cleanup
            step.result = {
                "user_email": test_email,
                "user_password": test_password,
                "user_id": user_info["id"],
                "jwt_token": jwt_token,
                "invite_code": invite_code,
                "run_id": run_id
            }

            step.status = "PASS"
            print_success("Image test user created successfully")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception creating image test user: {e}"

        return step

    def create_api_token_for_user(self, jwt_token: str, token_name: str = "image-solve-test") -> TestStep:
        """
        Create API token for the test user using their JWT token
        The image solve endpoint requires API token authentication
        """
        step = TestStep(
            step_number=2,
            step_name="Create API Token",
            status="PASS",
            message="Creating API token..."
        )

        try:
            # Create API token with expiration
            token_data = {
                "name": token_name,
                "expiresAt": (datetime.now() + timedelta(hours=2)).isoformat() + "Z"
            }

            print_info(f"Creating API token with data: {token_data}")
            print_info(f"API token endpoint: {config.get_endpoint('api_tokens')}")
            print_info(f"Using JWT token: {jwt_token[:20]}...")

            token_response, token_response_time = self.http_client.post(
                config.get_endpoint('api_tokens'),
                token_data,
                auth_token=jwt_token
            )

            print_info(f"API token response status: {token_response.status_code}")
            print_info(f"API token response body: '{token_response.text}'")

            if token_response.status_code not in [config.STATUS_CODES['success'], config.STATUS_CODES['created']]:
                step.status = "FAIL"
                step.message = f"Failed to create API token: {token_response.status_code} - {token_response.text}"
                return step

            result = token_response.json()
            api_token = result["token"]
            token_id = result["id"]

            print_success(f"Created API token: {token_name} ({token_id})")

            step.result = {
                "api_token": api_token,
                "token_id": token_id,
                "token_name": token_name
            }

            step.status = "PASS"
            print_success("API token created successfully")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception creating API token: {e}"

        return step

    def upload_and_solve(self, image_path: str, api_token: str) -> TestStep:
        """
        Upload image to /api/core/solve endpoint and get solution
        Uses API token authentication (not JWT)
        """
        step = TestStep(
            step_number=3,
            step_name="Upload and Solve Image",
            status="PASS",
            message=f"Solve math problem in image: {Path(image_path).name}"
        )

        try:
            # Prepare multipart form data
            if not os.path.exists(image_path):
                step.status = "FAIL"
                step.message = f"Image file not found: {image_path}"
                return step

            # Custom image upload with API token authentication
            # Since HTTPClient doesn't support multipart uploads, we need custom handling
            try:
                # Open image file for binary upload
                with open(image_path, 'rb') as image_file:
                    files = {
                        'file': (
                            os.path.basename(image_path),
                            image_file,
                            'image/png',
                        )
                    }

                    # Use API token in Authorization header (note: X-API-Key for API tokens)
                    headers = {
                        'Authorization': f"Bearer {api_token}",
                    }

                    start_time = time.time()
                    response = requests.post(
                        f"{self.http_client.base_url}/api/core/solve",
                        files=files,
                        headers=headers,
                        timeout=60  # 60 second timeout for image processing
                    )
                    response_time = time.time() - start_time

                # Parse response
                response_data = {
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "headers": dict(response.headers),
                    "raw_response": response.text
                }

                if response.status_code == 200:
                    try:
                        json_data = response.json()
                        response_data["data"] = json_data

                        # Validate response structure
                        if "requestId" in json_data and "result" in json_data:
                            solve_data = SolveResponseData(
                                request_id=json_data.get("requestId"),
                                result=json_data.get("result"),
                                duration_ms=json_data.get("durationMs", 0),
                                timings=json_data.get("timings", {}),
                                status_code=response.status_code,
                                response_time=response_time,
                                raw_response=json_data
                            )

                            step.result = {
                                "solve_response": solve_data,
                                "http_response": response_data
                            }

                            step.status = "PASS"
                            print_success(f"Image solved successfully: {json_data.get('result')}")

                        else:
                            step.status = "FAIL"
                            step.message = f"Invalid response structure: {json_data}"

                    except json.JSONDecodeError as e:
                        step.status = "FAIL"
                        step.message = f"Failed to parse JSON response: {e}"

                else:
                    step.status = "FAIL"
                    step.message = f"HTTP error {response.status_code}: {response.text}"
                    response_data["data"] = {"error": response.text}
                    step.result = {"http_response": response_data}

            except requests.exceptions.Timeout:
                step.status = "FAIL"
                step.message = f"Request timeout after 60 seconds"

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception uploading and solving image: {e}"

        except requests.exceptions.RequestException as e:
            step.status = "FAIL"
            step.message = f"Request exception: {e}"

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception uploading and solving image: {e}"

        return step

    def validate_solve_response(self, solve_response: SolveResponseData, expected_answer: str) -> TestStep:
        """
        Validate solve response against expected answer
        """
        step = TestStep(
            step_number=4,
            step_name="Validate Solve Response",
            status="PASS",
            message=f"Validate response matches expected answer: {expected_answer}"
        )

        try:
            validations = []

            # Validate result matches expected answer
            actual_result = solve_response.result.strip()
            if actual_result == expected_answer.strip():
                validations.append("✓ Result matches expected answer")
                step.status = "PASS"
            else:
                validations.append(f"✗ Result mismatch: expected '{expected_answer}', got '{actual_result}'")
                step.status = "FAIL"

            # Validate response structure
            if solve_response.request_id:
                validations.append("✓ Request ID present")
            else:
                validations.append("✗ Missing request ID")
                step.status = "FAIL"

            if solve_response.duration_ms is not None and solve_response.duration_ms >= 0:
                validations.append("✓ Duration present and valid")
            else:
                validations.append("✗ Invalid or missing duration")
                step.status = "FAIL"

            if isinstance(solve_response.timings, dict):
                validations.append("✓ Timings present")
            else:
                validations.append("✗ Missing or invalid timings")
                step.status = "FAIL"

            # Validate performance
            if solve_response.response_time < 60:
                validations.append("✓ Response time under 60 seconds")
            else:
                validations.append(f"⚠ Slow response time: {solve_response.response_time:.2f}s")

            step.result = {
                "expected_answer": expected_answer,
                "actual_result": actual_result,
                "validations": validations,
                "solve_response": solve_response
            }

            if step.is_success():
                print_success(f"Validation passed: {expected_answer}")
            else:
                print_error(f"Validation failed: expected {expected_answer}, got {actual_result}")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception validating solve response: {e}"

        return step

    def cleanup_image_test_data(self, user_email: str = None, user_id: str = None,
                              api_token_id: str = None, invite_code: str = None) -> TestStep:
        """
        Clean up test data including user, API tokens, and related data
        Follows foreign key constraints properly
        """
        step = TestStep(
            step_number=5,
            step_name="Cleanup Image Test Data",
            status="PASS",
            message="Cleaning up test data..."
        )

        try:
            cleanup_results = []

            # Cleanup API token first (foreign key to user)
            if api_token_id:
                try:
                    # Note: API tokens don't have a direct delete endpoint in the current API
                    # They expire automatically, so we just log the cleanup
                    cleanup_results.append(f"API token {api_token_id} marked for expiration")
                    print_info(f"API token cleanup: {api_token_id}")
                except Exception as e:
                    cleanup_results.append(f"API token cleanup failed: {e}")

            # Cleanup request logs for this user
            if user_id:
                try:
                    self.db_helper.execute_query(
                        "DELETE FROM request_logs WHERE user_id = %s",
                        (user_id,)
                    )
                    cleanup_results.append(f"Request logs deleted for user {user_id}")
                except Exception as e:
                    cleanup_results.append(f"Request logs cleanup failed: {e}")

            # Cleanup API tokens from database for this user
            if user_id:
                try:
                    self.db_helper.execute_query(
                        "DELETE FROM api_tokens WHERE user_id = %s",
                        (user_id,)
                    )
                    cleanup_results.append(f"API tokens deleted for user {user_id}")
                except Exception as e:
                    cleanup_results.append(f"Database API token cleanup failed: {e}")

            # Cleanup billing periods for this user
            if user_id:
                try:
                    self.db_helper.execute_query(
                        "DELETE FROM billing_periods WHERE user_id = %s",
                        (user_id,)
                    )
                    cleanup_results.append(f"Billing periods deleted for user {user_id}")
                except Exception as e:
                    cleanup_results.append(f"Billing periods cleanup failed: {e}")

            # Cleanup invite code
            if invite_code:
                try:
                    self.db_helper.execute_query(
                        "DELETE FROM invite_codes WHERE code = %s",
                        (invite_code,)
                    )
                    cleanup_results.append(f"Invite code deleted: {invite_code}")
                except Exception as e:
                    cleanup_results.append(f"Invite code cleanup failed: {e}")

            # Cleanup user
            if user_id:
                try:
                    self.db_helper.execute_query(
                        "DELETE FROM users WHERE id = %s",
                        (user_id,)
                    )
                    cleanup_results.append(f"User deleted: {user_id}")
                except Exception as e:
                    cleanup_results.append(f"User cleanup failed: {e}")

            step.result = {
                "cleanup_results": cleanup_results,
                "user_email": user_email,
                "user_id": user_id,
                "api_token_id": api_token_id,
                "invite_code": invite_code
            }

            step.status = "PASS"
            print_success("Image test data cleanup completed")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception during cleanup: {e}"

        return step

    def verify_billing_integration(self, user_id: str, request_id: str = None) -> TestStep:
        """
        Verify that image solve requests are properly logged and billed
        """
        step = TestStep(
            step_number=6,
            step_name="Verify Billing Integration",
            status="PASS",
            message="Check request logs and billing integration"
        )

        try:
            verifications = []

            # Check request logs for this user
            if user_id:
                query = """
                    SELECT request_id, service, status, duration_ms, request_bytes,
                           response_bytes, created_at, billing_period_id
                    FROM request_logs
                    WHERE user_id = %s AND service = 'core.image_solve'
                    ORDER BY created_at DESC
                    LIMIT 10
                """

                logs = self.db_helper.execute_query(query, (user_id,))

                if logs:
                    verifications.append(f"✓ Found {len(logs)} image solve request logs")

                    # Check specific request if provided
                    if request_id:
                        matching_logs = [log for log in logs if log['request_id'] == request_id]
                        if matching_logs:
                            verifications.append(f"✓ Found specific request log: {request_id}")
                        else:
                            verifications.append(f"✗ Request log not found: {request_id}")
                            step.status = "FAIL"

                    # Verify log structure
                    for log in logs[:3]:  # Check first 3 logs
                        if log.get('service') == 'core.image_solve':
                            verifications.append(f"✓ Service field correct: {log['service']}")
                        if log.get('status') in ['SUCCESS', 'ERROR']:
                            verifications.append(f"✓ Status valid: {log['status']}")
                        if log.get('billing_period_id'):
                            verifications.append(f"✓ Billing period assigned")
                        else:
                            verifications.append("⚠ No billing period assigned")
                else:
                    verifications.append("✗ No image solve request logs found")
                    step.status = "FAIL"

            # Check billing periods for this user
            if user_id:
                billing_query = """
                    SELECT id, status, total_cost, total_requests, start_date, end_date
                    FROM billing_periods
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                    LIMIT 5
                """

                billing_periods = self.db_helper.execute_query(billing_query, (user_id,))

                if billing_periods:
                    verifications.append(f"✓ Found {len(billing_periods)} billing periods")
                else:
                    verifications.append("⚠ No billing periods found")

            step.result = {
                "verifications": verifications,
                "user_id": user_id,
                "request_id": request_id
            }

            if step.status != "FAIL":
                step.status = "PASS"
                print_success("Billing integration verified")
            else:
                print_error("Billing integration verification failed")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception verifying billing integration: {e}"

        return step
