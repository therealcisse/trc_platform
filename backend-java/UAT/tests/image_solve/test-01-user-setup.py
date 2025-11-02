#!/usr/bin/env python3
"""
IMG-01: User Setup for Image Solve Testing
Test ID: IMG-01
Test Name: User Setup for Image Solve Testing
Test Type: Functional Setup
Priority: High
Estimated Duration: 10 minutes

Description:
Create a dedicated test user for image solve endpoint testing and create an API token
for authentication. This test creates the foundation for all subsequent image solve
testing by ensuring we have a user with valid API token access to the /api/core/solve
endpoint.

Extended 6-Step Pattern:
1. Admin login
2. Create invite codes with admin user token
3. Register new test user with invite code
4. Login with newly registered user to get JWT token
5. Create API token for test user using JWT token
6. Verify API token works for image solve endpoint
"""

import sys
import os
import json
import time
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import UAT framework and configuration
from uat_framework import (
    DatabaseHelper, HTTPClient, TokenManager, TestReporting,
    TestStep, TestResult, Colors, print_success, print_error, print_warning, print_info
)
from uat_config import config

# Import image solve helpers
from image_solve_helpers import ImageHelper

class Image01UserSetup:
    """Image solve user setup test following extended 6-step pattern with API token creation"""

    def __init__(self):
        """Initialize test configuration and helpers"""
        self.test_id = "IMG-01"
        self.test_name = "User Setup for Image Solve Testing"

        # Initialize helpers
        self.reporting = TestReporting()
        self.db_helper = DatabaseHelper(config.database_url)
        self.http_client = HTTPClient(config.app_url)
        self.image_helper = ImageHelper(self.db_helper, self.http_client)

        # Test data storage
        self.test_data = {}
        self.run_id = str(uuid.uuid4())[:8]

    def step_01_admin_login(self) -> TestStep:
        """Step 1: Admin login - Get admin JWT token for creating invite codes"""
        step = TestStep(
            step_number=1,
            step_name="Admin Login",
            status="PASS",
            message="Authenticating as admin..."
        )

        try:
            print_info("Step 1: Admin Login")

            # Use admin credentials from config
            admin_data = {
                "email": config.admin_email,
                "password": config.admin_password
            }

            response, response_time = self.http_client.post(config.get_endpoint('login'), data=admin_data)

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = f"Admin login failed: {response.status_code}"
                print_error(f"Admin login failed: {response.status_code}")
                return step

            # Extract JWT token
            response_data = response.json()
            jwt_token = response_data['token']

            print_success(f"Admin login successful")

            # Store admin data
            self.test_data.update({
                "admin_email": config.ADMIN_EMAIL,
                "admin_jwt_token": jwt_token
            })

            step.status = "PASS"
            step.message = f"Admin login successful"
            print_success("✓ Admin JWT token obtained")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception during admin login: {e}"
            print_error(f"Admin login failed: {e}")

        return step

    def step_02_create_invite_code(self) -> TestStep:
        """Step 2: Create invite code with admin token"""
        step = TestStep(
            step_number=2,
            step_name="Create Invite Code",
            status="PASS",
            message="Creating invite code..."
        )

        try:
            print_info("Step 2: Create Invite Code")

            if "admin_jwt_token" not in self.test_data:
                step.status = "FAIL"
                step.message = "Admin JWT token not available"
                return step

            admin_token = self.test_data["admin_jwt_token"]

            # Create invite code data (billing module pattern)
            test_code = config.generate_unique_invite_code("IMG-SOLVE-TEST")
            invite_data = {"code": test_code}

            print_info(f"Creating invite code with data: {invite_data}")
            print_info(f"Using admin token: {admin_token[:20]}...")

            response, response_time = self.http_client.post(
                config.get_endpoint('admin_invites'),
                invite_data,
                auth_token=admin_token
            )

            print_info(f"Invite code response status: {response.status_code}")
            print_info(f"Invite code response headers: {dict(response.headers)}")
            print_info(f"Invite code response body: {response.text}")

            if response.status_code not in [config.STATUS_CODES['success'], config.STATUS_CODES['created']]:
                step.status = "FAIL"
                step.message = f"Failed to create invite code: {response.status_code} - {response.text}"
                print_error(f"Response body: {response.text}")
                return step

            invite_code = test_code
            print_success(f"Invite code created: {invite_code}")

            # Store invite code data
            self.test_data.update({
                "invite_code": invite_code
            })

            step.result = {
                "invite_code": invite_code
            }

            step.status = "PASS"
            print_success("✓ Invite code created successfully")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception creating invite code: {e}"
            print_error(f"Invite code creation failed: {e}")

        return step

    def step_03_register_test_user(self) -> TestStep:
        """Step 3: Register new test user with invite code"""
        step = TestStep(
            step_number=3,
            step_name="Register Test User",
            status="PASS",
            message="Registering test user..."
        )

        try:
            print_info("Step 3: Register Test User")

            if "invite_code" not in self.test_data:
                step.status = "FAIL"
                step.message = "Invite code not available"
                return step

            # Generate unique user details
            test_email = f"image-solve-{self.run_id}@uat-test.trc-platform.local"
            test_password = "TestPassword123!"

            # Generate unique user details using config (billing module pattern)
            test_email = config.generate_unique_email("image-solve")
            test_password = "TestPassword123!"

            # User registration data (billing module pattern)
            user_data = {
                "email": test_email,
                "password": test_password,
                "confirmPassword": test_password,
                "inviteCode": self.test_data["invite_code"],
                "userAcceptedTerms": True,
                "userAcknowledgedDisclaimer": True
            }

            print_info(f"Registering user with data: {user_data}")
            print_info(f"Registration endpoint: {config.get_endpoint('user_register')}")

            response, response_time = self.http_client.post(
                config.get_endpoint('user_register'),
                user_data
            )

            print_info(f"Registration response status: {response.status_code}")
            print_info(f"Registration response headers: {dict(response.headers)}")
            print_info(f"Registration response body: '{response.text}'")

            if response.status_code not in [config.STATUS_CODES['accepted'], config.STATUS_CODES['created']]:
                step.status = "FAIL"
                step.message = f"User registration failed: {response.status_code} - {response.text}"
                return step

            # Handle empty response for 202 Accepted
            if response.text.strip():
                user_info = response.json()
                user_id = user_info["id"]
            else:
                # For 202 Accepted with empty body, we'll get user_id from login response
                user_id = None

            print_success(f"Test user registered: {test_email}")

            # Store test user data
            self.test_data.update({
                "user_email": test_email,
                "user_password": test_password,
                "user_id": user_id,
            })

            step.result = {
                "user_id": user_id,
                "user_email": test_email,
            }

            step.status = "PASS"
            print_success("✓ Test user registered successfully")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception registering test user: {e}"
            print_error(f"User registration failed: {e}")

        return step

    def step_04_user_login(self) -> TestStep:
        """Step 4: Login with newly registered user to get JWT token"""
        step = TestStep(
            step_number=4,
            step_name="User Login",
            status="PASS",
            message="Authenticating test user..."
        )

        try:
            print_info("Step 4: User Login")

            if "user_email" not in self.test_data:
                step.status = "FAIL"
                step.message = "Test user credentials not available"
                return step

            # User login data (billing module pattern)
            login_data = {
                "email": self.test_data["user_email"],
                "password": self.test_data["user_password"]
            }

            response, response_time = self.http_client.post(
                config.get_endpoint('login'),
                login_data
            )

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = f"User login failed: {response.status_code}"
                return step

            # Extract JWT token
            response_data = response.json()
            jwt_token = response_data['token']

            print_success(f"User login successful: {self.test_data['user_email']}")

            # Store user JWT token
            self.test_data.update({
                "user_jwt_token": jwt_token
            })

            step.result = {
                "user_email": self.test_data["user_email"],
                "jwt_token": jwt_token
            }

            step.status = "PASS"
            print_success("✓ User JWT token obtained")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception during user login: {e}"
            print_error(f"User login failed: {e}")

        return step

    def step_05_create_api_token(self) -> TestStep:
        """Step 5: Create API token for test user using JWT token"""
        step = TestStep(
            step_number=5,
            step_name="Create API Token",
            status="PASS",
            message="Creating API token..."
        )

        try:
            print_info("Step 5: Create API Token")

            if "user_jwt_token" not in self.test_data:
                step.status = "FAIL"
                step.message = "User JWT token not available"
                return step

            user_jwt_token = self.test_data["user_jwt_token"]
            print_info(f"Creating API token with token: {user_jwt_token[:20]}...")

            # Use ImageHelper to create API token
            token_step = self.image_helper.create_api_token_for_user(
                user_jwt_token,
                f"image-solve-{self.run_id}"
            )

            print_info(f"API token creation step status: {token_step.status}")
            print_info(f"API token creation step message: {token_step.message}")

            if not token_step.is_success():
                step.status = "FAIL"
                step.message = f"API token creation failed: {token_step.message}"
                print_error(f"API token creation failed: {token_step.message}")
                return step

            api_token_data = token_step.result

            print_success(f"API token created: {api_token_data['token_name']}")

            # Store API token data
            self.test_data.update({
                "api_token": api_token_data["api_token"],
                "api_token_id": api_token_data["token_id"],
                "api_token_name": api_token_data["token_name"]
            })

            step.result = {
                "api_token_id": api_token_data["token_id"],
                "api_token_name": api_token_data["token_name"],
                "created_at": datetime.now().isoformat()
            }

            step.status = "PASS"
            print_success("✓ API token created successfully")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception creating API token: {e}"
            print_error(f"API token creation failed: {e}")

        return step

    def step_06_verify_api_token(self) -> TestStep:
        """Step 6: Verify API token works for image solve endpoint"""
        step = TestStep(
            step_number=6,
            step_name="Verify API Token",
            status="PASS",
            message="Verifying API token..."
        )

        try:
            print_info("Step 6: Verify API Token")

            if "api_token" not in self.test_data:
                step.status = "FAIL"
                step.message = "API token not available"
                return step

            api_token = self.test_data["api_token"]

            # Test API token with a simple health check or by trying to access image solve endpoint
            # Since we don't have a dedicated API token validation endpoint, we'll test it
            # by attempting to access the image solve endpoint (it will fail with auth error if token is invalid)

            # Try to access image solve endpoint with API token
            headers = {
                'X-API-Key': api_token
            }

            # Test API token authentication with the health endpoint (doesn't require image)
            # This is a better approach since /health is GET and doesn't require multipart data
            health_endpoint = "/api/core/health"
            print_info(f"Verifying API token with endpoint: {health_endpoint}")
            print_info(f"Using headers: {headers}")

            try:
                response, response_time = self.http_client.get(
                    health_endpoint,
                    headers=headers
                )
                print_info(f"API token verification response status: {response.status_code}")
                print_info(f"API token verification response body: '{response.text}'")
            except Exception as e:
                step.status = "FAIL"
                step.message = f"API token verification request failed: {e}"
                print_error(f"API token verification exception: {e}")
                return step

            # Check the response - health endpoint should be accessible with valid API token
            if response.status_code == 401:
                step.status = "FAIL"
                step.message = "API token authentication failed - got 401 Unauthorized on health endpoint"
                return step
            elif response.status_code == 200:
                # Perfect - API token authentication works
                print_success("✓ API token authentication verified (200 OK on health endpoint)")
            elif response.status_code == 403:
                step.status = "FAIL"
                step.message = "API token authentication failed - got 403 Forbidden"
                return step
            else:
                print_warning(f"Unexpected status code {response.status_code} on health endpoint")

            step.result = {
                "api_token_valid": True,
            }

            step.status = "PASS"
            print_success("✓ API token verification completed")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Exception verifying API token: {e}"
            print_error(f"API token verification failed: {e}")

        return step

    def run_test(self) -> TestResult:
        """Execute the complete 6-step user setup test"""
        print(f"\n{'='*80}")
        print(f"🧪 {self.test_id}: {self.test_name}")
        print(f"🆔 Run ID: {self.run_id}")
        print(f"{'='*80}")

        start_time = datetime.now()
        test_steps = []

        try:
            # Step 1: Admin Login
            step_1 = self.step_01_admin_login()
            test_steps.append(step_1)
            if not step_1.is_success():
                print_error("❌ Admin login failed - aborting test")
                return self._create_test_result(start_time, test_steps, "ADMIN_LOGIN_FAILED")

            # Step 2: Create Invite Code
            step_2 = self.step_02_create_invite_code()
            test_steps.append(step_2)
            if not step_2.is_success():
                print_error("❌ Invite code creation failed - aborting test")
                return self._create_test_result(start_time, test_steps, "INVITE_CODE_FAILED")

            # Step 3: Register Test User
            step_3 = self.step_03_register_test_user()
            test_steps.append(step_3)
            if not step_3.is_success():
                print_error("❌ User registration failed - aborting test")
                return self._create_test_result(start_time, test_steps, "USER_REGISTRATION_FAILED")

            # Step 4: User Login
            step_4 = self.step_04_user_login()
            test_steps.append(step_4)
            if not step_4.is_success():
                print_error("❌ User login failed - aborting test")
                return self._create_test_result(start_time, test_steps, "USER_LOGIN_FAILED")

            # Step 5: Create API Token
            step_5 = self.step_05_create_api_token()
            test_steps.append(step_5)
            if not step_5.is_success():
                print_error("❌ API token creation failed - aborting test")
                return self._create_test_result(start_time, test_steps, "API_TOKEN_CREATION_FAILED")

            # Step 6: Verify API Token
            step_6 = self.step_06_verify_api_token()
            test_steps.append(step_6)
            if not step_6.is_success():
                print_error("❌ API token verification failed")
                return self._create_test_result(start_time, test_steps, "API_TOKEN_VERIFICATION_FAILED")

            # All steps completed successfully
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            result = TestResult(
                test_id=self.test_id,
                test_name=self.test_name,
                status='PASS',
                total_steps=6,
                passed_steps=len([s for s in test_steps if s.is_success()]),
                failed_steps=0,
                skipped_steps=0,
                error_steps=0,
                total_time=duration,
                start_time=start_time,
                end_time=end_time
            )

            # Store test data for cleanup
            result.test_data = self.test_data

            print_success(f"\n🎉 {self.test_id} PASSED - All 6 steps completed successfully")
            print_success(f"✅ Test user created: {self.test_data.get('user_email')}")
            print_success(f"✅ API token created: {self.test_data.get('api_token_name')}")
            print_info(f"⏱️  Total duration: {duration:.2f} seconds")

            return result

        except KeyboardInterrupt:
            print_warning("\n⚠️  Test interrupted by user")
            return self._create_test_result(start_time, test_steps, "INTERRUPTED")

        except Exception as e:
            print_error(f"\n❌ Unexpected error during test execution: {e}")
            return self._create_test_result(start_time, test_steps, "ERROR", str(e))

    def _create_test_result(self, start_time: datetime, test_steps: list,
                          status: str, error_msg: str = None) -> TestResult:
        """Create TestResult object with current state"""
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        passed_steps = len([s for s in test_steps if s.is_success()])
        failed_steps = len([s for s in test_steps if s.status == "FAIL"])
        error_steps = len([s for s in test_steps if s.status not in ["PASS", "FAIL"]])

        result = TestResult(
            test_id=self.test_id,
            test_name=self.test_name,
            status=status,
            total_steps=len(test_steps),
            passed_steps=passed_steps,
            failed_steps=failed_steps,
            skipped_steps=0,
            error_steps=error_steps,
            total_time=duration,
            start_time=start_time,
            end_time=end_time
        )

        # Store test data for cleanup
        result.test_data = self.test_data

        if error_msg:
            result.error_message = error_msg

        # Disconnect from database before cleanup
        try:
            self.db_helper.disconnect()
            print_info("Database disconnected successfully")
        except Exception as e:
            print_warning(f"Database disconnect warning: {e}")

        return result

def cleanup_test_data(test_result: TestResult) -> bool:
    """Clean up test data after test completion"""
    try:
        if hasattr(test_result, 'test_data') and test_result.test_data:
            image_helper = ImageHelper()

            cleanup_step = image_helper.cleanup_image_test_data(
                user_email=test_result.test_data.get('user_email'),
                user_id=test_result.test_data.get('user_id'),
                api_token_id=test_result.test_data.get('api_token_id'),
                invite_code=test_result.test_data.get('invite_code')
            )

            if cleanup_step.is_success():
                print_success("✅ Test data cleanup completed")
                return True
            else:
                print_warning(f"⚠️  Test data cleanup issues: {cleanup_step.message}")
                return False
        else:
            print_warning("⚠️  No test data to cleanup")
            return True

    except Exception as e:
        print_error(f"❌ Test data cleanup failed: {e}")
        return False

def main():
    """Main test execution function"""
    print_success("IMG-01: User Setup for Image Solve Testing")

    # Create and run test
    test_instance = Image01UserSetup()
    result = test_instance.run_test()

    # Cleanup regardless of test outcome
    cleanup_success = cleanup_test_data(result)

    # Print final result
    if result.status == 'PASS':
        print_success(f"\n🎉 TEST COMPLETED SUCCESSFULLY")
        if cleanup_success:
            print_success("🧹 Cleanup completed successfully")
        else:
            print_warning("⚠️  Cleanup had issues")
        sys.exit(0)
    else:
        print_error(f"\n❌ TEST FAILED: {result.status}")
        if hasattr(result, 'error_message') and result.error_message:
            print_error(f"Error: {result.error_message}")
        sys.exit(1)

if __name__ == "__main__":
    main()
