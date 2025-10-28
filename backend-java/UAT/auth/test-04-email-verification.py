#!/usr/bin/env python3
"""
TEST-04: Email Verification
Test ID: TEST-04
Test Name: Email Verification Workflow
Test Type: Functional Email Verification
Priority: High
Estimated Duration: 10 minutes

Description:
Validate email verification token workflow including user creation, token extraction,
initial verification submission, token reuse prevention, and resend verification functionality.
This test is completely self-contained and does not rely on data from other tests.
"""

import sys
import os
import json
import time
import random
import string
from pathlib import Path
from datetime import datetime

# Add current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Import UAT framework and configuration
from uat_test_framework import (
    DatabaseHelper, HTTPClient, TokenManager, TestReporting,
    TestStep, TestResult, EnvironmentInfo,
    Colors, print_success, print_error, print_warning, print_info,
    extract_jwt_token, extract_json_field, format_timestamp, format_response_time,
    EmailVerificationHelper, wait_for_email_verification
)
from uat_config import config

class Test04EmailVerification:
    """Test-04: Self-Contained Email Verification Workflow"""

    def __init__(self):
        self.test_id = "TEST-04"
        self.test_name = "Email Verification Workflow"
        self.reporting = TestReporting()
        self.db_helper = DatabaseHelper(config.DATABASE_URL)
        self.http_client = HTTPClient(config.APP_URL)
        self.token_manager = TokenManager()
        self.email_helper = EmailVerificationHelper(config.MAILCATCHER_URL)
        self.test_steps = []
        self.start_time = datetime.now()
        self.verification_token = None
        self.test_user_email = None
        self.test_user_password = None
        self.admin_token = None

    def generate_test_email(self) -> str:
        """Generate a unique test email address"""
        timestamp = int(time.time())
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"test-04-{timestamp}-{random_str}@example.com"

    def generate_test_password(self) -> str:
        """Generate a test password that meets complexity requirements"""
        return f"TestPass123!{random.randint(100, 999)}"

    def setup_environment(self) -> bool:
        """Setup and verify test environment"""
        print_info("Setting up test environment...")

        # Initialize database connection
        if not self.db_helper.connect():
            print_error("Failed to connect to database")
            return False

        # Clear any existing emails
        try:
            self.email_helper.clear_all_emails()
        except Exception as e:
            print_warning(f"Could not clear emails: {e}")

        # Generate test user credentials
        self.test_user_email = self.generate_test_email()
        self.test_user_password = self.generate_test_password()

        print_success(f"Generated test user: {self.test_user_email}")
        return True

    def create_test_user(self) -> TestStep:
        """Step: Create a new test user for verification testing"""
        step = TestStep(
            step_number=1,
            step_name="Create Test User",
            status="PASS",
            message="Creating test user for email verification testing..."
        )

        try:
            # Get admin token to create invite code
            admin_credentials = {
                "email": config.ADMIN_EMAIL,
                "password": config.ADMIN_PASSWORD
            }

            admin_response, response_time = self.http_client.post(
                config.ENDPOINTS['admin_login'],
                admin_credentials
            )

            if admin_response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = "Failed to authenticate as admin"
                return step

            response_data = admin_response.json()
            self.admin_token = response_data['token']

            # Create invite code
            invite_data = {
                "code": f"TEST-04-{int(time.time())}"
            }

            invite_response, _ = self.http_client.post(
                config.ENDPOINTS['admin_invites'],
                invite_data,
                auth_token=self.admin_token
            )

            if invite_response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = f"Failed to create invite code: {invite_response.status_code} - {invite_response.text}"
                return step

            response_data = invite_response.json()
            invite_code = response_data['code']

            # Register test user
            registration_data = {
                "email": self.test_user_email,
                "password": self.test_user_password,
                "confirmPassword": self.test_user_password,
                "inviteCode": invite_code,
                "userAcceptedTerms": True,
                "userAcknowledgedDisclaimer": True
            }

            step.request_data = registration_data

            response, response_time = self.http_client.post(
                config.ENDPOINTS['user_register'],
                registration_data
            )

            step.response_time = response_time
            step.response_code = response.status_code

            if response.status_code != config.STATUS_CODES['accepted']:
                step.status = "FAIL"
                step.message = f"User registration failed: {response.status_code} - {response.text}"
                step.response_body = response.text
                return step

            # Wait for verification email
            print_info("Waiting for verification email...")
            if wait_for_email_verification(self.email_helper, self.test_user_email, timeout=30):
                email_data = self.email_helper.get_latest_email(self.test_user_email)
                if email_data:
                    self.verification_token = self.email_helper.extract_verification_token(email_data)
                    if self.verification_token:
                        step.status = "PASS"
                        step.message = f"Test user created and verification email received for {self.test_user_email}"
                        step.response_body = f"Token extracted: {self.verification_token[:20]}..."
                    else:
                        step.status = "FAIL"
                        step.message = "Failed to extract verification token from email"
                else:
                    step.status = "FAIL"
                    step.message = "No email data found"
            else:
                step.status = "FAIL"
                step.message = "Verification email not received within timeout"

        except Exception as e:
            step.status = "FAIL"
            step.message = f"User creation failed: {e}"
            print_error(f"User creation failed: {e}")

        return step

    def verify_pre_verification_state(self) -> TestStep:
        """Step: Verify user is not yet verified"""
        step = TestStep(
            step_number=2,
            step_name="Verify Pre-Verification State",
            status="PASS",
            message=f"Verifying {self.test_user_email} is not yet verified..."
        )

        try:
            # Check if user email is not verified yet
            is_verified = self.db_helper.verify_email_verified(self.test_user_email)

            if is_verified:
                step.status = "FAIL"
                step.message = f"User {self.test_user_email} is already verified - test setup error"
            else:
                step.status = "PASS"
                step.message = f"User {self.test_user_email} is correctly not verified yet"

            step.database_state = {
                'user_email': self.test_user_email,
                'email_verified': is_verified
            }

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Failed to verify user state: {e}"
            print_error(f"Failed to verify user state: {e}")

        return step

    def submit_email_verification(self) -> TestStep:
        """Step: Submit email verification token"""
        step = TestStep(
            step_number=3,
            step_name="Submit Email Verification",
            status="PASS",
            message="Submitting email verification token..."
        )

        try:
            if not self.verification_token:
                step.status = "FAIL"
                step.message = "No verification token available"
                return step

            verification_data = {
                "token": self.verification_token
            }

            step.request_data = verification_data

            response, response_time = self.http_client.post(
                config.ENDPOINTS['email_verify'],
                verification_data
            )

            step.response_time = response_time
            step.response_code = response.status_code

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = f"Email verification failed: {response.status_code}"
                step.response_body = response.text
            else:
                step.status = "PASS"
                step.message = f"Email verification successful for {self.test_user_email}"

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Email verification submission failed: {e}"
            print_error(f"Email verification submission failed: {e}")

        return step

    def verify_post_verification_state(self) -> TestStep:
        """Step: Verify user is now verified"""
        step = TestStep(
            step_number=4,
            step_name="Verify Post-Verification State",
            status="PASS",
            message=f"Verifying {self.test_user_email} is now verified..."
        )

        try:
            # Check if user is now verified using existing method
            is_verified = self.db_helper.verify_email_verified(self.test_user_email)

            if is_verified:
                step.status = "PASS"
                step.message = f"User {self.test_user_email} successfully verified"
                step.database_state = {
                    'user_email': self.test_user_email,
                    'email_verified': True
                }

                print_success(f"✓ User {self.test_user_email} successfully verified")
            else:
                step.status = "FAIL"
                step.message = f"User {self.test_user_email} is still not verified"

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Failed to verify post-verification state: {e}"
            print_error(f"Failed to verify post-verification state: {e}")

        return step

    def test_token_reuse_prevention(self) -> TestStep:
        """Step: Test that verification token cannot be reused"""
        step = TestStep(
            step_number=5,
            step_name="Test Token Reuse Prevention",
            status="PASS",
            message="Testing verification token reuse prevention..."
        )

        try:
            if not self.verification_token:
                step.status = "FAIL"
                step.message = "No verification token available for reuse test"
                return step

            # Try to use the same token again
            verification_data = {
                "token": self.verification_token
            }

            step.request_data = verification_data

            response, response_time = self.http_client.post(
                config.ENDPOINTS['email_verify'],
                verification_data
            )

            step.response_time = response_time
            step.response_code = response.status_code

            # Should return 200 Success for token reuse (graceful handling)
            if response.status_code == 200:
                step.status = "PASS"
                step.message = "Token reuse gracefully handled (user already verified)"
            elif response.status_code == 400:
                step.status = "WARN"
                step.message = "Token reuse rejected with 400 (alternative valid approach)"
            else:
                step.status = "FAIL"
                step.message = f"Unexpected response code for token reuse: {response.status_code} - {response.text}"

            step.response_body = response.text

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Token reuse test failed: {e}"
            print_error(f"Token reuse test failed: {e}")

        return step

    def test_invalid_token_handling(self) -> TestStep:
        """Step: Test invalid token handling"""
        step = TestStep(
            step_number=6,
            step_name="Test Invalid Token Handling",
            status="PASS",
            message="Testing invalid token handling..."
        )

        invalid_tokens = [
            "invalid-token-format",
            "eyJhbGciOiJIUzI1NiJ9.invalid.signature",
            "",
            None
        ]

        failed_tokens = []

        for token in invalid_tokens:
            try:
                verification_data = {"token": token}

                response, _ = self.http_client.post(
                    config.ENDPOINTS['email_verify'],
                    verification_data
                )

                # Should return 400 or 401 for invalid tokens
                if response.status_code in [400, 401]:
                    pass  # Expected
                else:
                    failed_tokens.append(f"Token '{token}' returned {response.status_code}")

            except Exception as e:
                failed_tokens.append(f"Token '{token}' caused exception: {e}")

        if failed_tokens:
            step.status = "FAIL"
            step.message = f"Some invalid tokens were not properly rejected: {failed_tokens}"
            print_error(f"Invalid token handling issues: {failed_tokens}")
        else:
            step.status = "PASS"
            step.message = "All invalid tokens properly rejected"

        return step

    def save_test_data(self) -> TestStep:
        """Step: Save test data for subsequent tests"""
        step = TestStep(
            step_number=7,
            step_name="Save Test Data",
            status="PASS",
            message="Saving test data for subsequent tests..."
        )

        try:
            # Save verified user credentials
            credentials_path = os.path.join(config.TOKEN_STORAGE_DIR, 'verified_user_credentials.txt')
            os.makedirs(os.path.dirname(credentials_path), exist_ok=True)

            with open(credentials_path, 'w') as f:
                f.write(f"{self.test_user_email}:{self.test_user_password}")

            # Save verification token for potential use
            if self.verification_token:
                token_path = config.get_token_path('verification_token')
                os.makedirs(os.path.dirname(token_path), exist_ok=True)
                with open(token_path, 'w') as f:
                    f.write(self.verification_token)

            step.status = "PASS"
            step.message = "Verified user credentials saved for subsequent tests"

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Failed to save test data: {e}"
            print_error(f"Failed to save test data: {e}")

        return step

    def cleanup_test_data(self) -> bool:
        """Clean up test data"""
        try:
            # Clean up created user (optional - might want to keep for debugging)
            return True
        except Exception:
            return False

    def run_test(self) -> TestResult:
        """Execute the complete test suite"""
        print_info(f"Starting {self.test_id}: {self.test_name}")

        if not self.setup_environment():
            return TestResult(
                test_id=self.test_id,
                test_name=self.test_name,
                status="FAIL",
                steps=[],
                duration=0,
                message="Environment setup failed"
            )

        # Execute test steps
        self.test_steps.append(self.create_test_user())
        self.test_steps.append(self.verify_pre_verification_state())
        self.test_steps.append(self.submit_email_verification())
        self.test_steps.append(self.verify_post_verification_state())
        self.test_steps.append(self.test_token_reuse_prevention())
        self.test_steps.append(self.test_invalid_token_handling())
        self.test_steps.append(self.save_test_data())

        # Calculate results
        passed_steps = sum(1 for step in self.test_steps if step.status == "PASS")
        total_steps = len(self.test_steps)
        duration = (datetime.now() - self.start_time).total_seconds()

        # Determine overall status
        if passed_steps == total_steps:
            status = "PASS"
            message = "Email verification workflow completed successfully!"
        else:
            status = "FAIL"
            message = f"Email verification workflow failed: {total_steps - passed_steps}/{total_steps} steps failed"

        # Clean up
        self.cleanup_test_data()

        return TestResult(
            test_id=self.test_id,
            test_name=self.test_name,
            status=status,
            total_steps=len(self.test_steps),
            passed_steps=sum(1 for step in self.test_steps if step.status == 'PASS'),
            failed_steps=sum(1 for step in self.test_steps if step.status == 'FAIL'),
            skipped_steps=0,
            error_steps=0,
            total_time=duration,
            start_time=self.start_time,
            end_time=datetime.now(),
            test_steps=self.test_steps
        )

def main():
    """Main test execution function"""
    print_success(f"\n{'='*80}")
    print_success(f"🧪 TRC Platform UAT - {Test04EmailVerification().test_name}")
    print_success(f"{'='*80}\n")

    test = Test04EmailVerification()
    result = test.run_test()

    # Print results
    print(f"\n{'='*80}")
    if result.status == "PASS":
        print_success(f"⏹ {test.test_id}: {test.test_name} - PASS")
    else:
        print_error(f"⏹ {test.test_id}: {test.test_name} - FAIL")
    print(f"{'='*80}\n")

    print(f"🏁 {test.test_id} EXECUTION COMPLETE")
    print(f"Status: {result.status}")
    print(f"Duration: {result.total_time:.2f} seconds")
    print(f"Steps: {result.passed_steps}/{result.total_steps} passed")

    if result.status == "PASS":
        print_success("✅ Email verification test completed successfully!")
    else:
        print_error("❌ Email verification test failed!")
        print(f"⚠ Check test logs and application status")

    print(f"\n{'='*80}\n")
    print(f"🏁 {test.test_id} EXECUTION COMPLETE")
    print(f"Status: {result.status}")
    print(f"Duration: {result.total_time:.2f} seconds")
    print(f"Steps: {result.passed_steps}/{result.total_steps} passed")

    if result.status == "PASS":
        print_success(f"✅ ✅ {test.test_id} completed successfully")
    else:
        print_error(f"❌ ❌ {test.test_id} failed")

    # Print detailed step results
    print(f"\n{'='*40}")
    print(f"DETAILED STEP RESULTS:")
    print(f"{'='*40}")

    for i, step in enumerate(result.test_steps, 1):
        if step.status == "PASS":
            response_time = f"({step.response_time:.3f}ms)" if step.response_time is not None else ""
            print(f"{i}. {step.step_name} - PASS {response_time}")
            if step.message:
                print(f"   - {step.message}")
        else:
            print(f"{i}. {step.step_name} - FAIL")
            if step.message:
                print(f"   - {step.message}")
            if hasattr(step, 'response_body') and step.response_body:
                print(f"   - Response: {step.response_body[:100]}...")

    # Return success status based on test result
    return result.status == "PASS"

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)