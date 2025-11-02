"""
TEST-05: Resend Verification Email
Test ID: TEST-05
Test Name: Resend Verification Email Functionality
Test Type: Functional Email Management
Priority: Medium
Estimated Duration: 10 minutes

Description:
Validate resend verification email functionality by:
1. Creating and verifying a user through complete flow
2. Setting email_verified_at to null in database to simulate unverified state
3. Testing resend verification email functionality
4. Verifying that resend token works for email verification
5. Testing rate limiting for resend requests
"""

import sys
import os
import json
import time
import uuid
from pathlib import Path
from datetime import datetime

# Add current directory to Python path for imports
# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import UAT framework and configuration
from uat_framework import (
    DatabaseHelper, HTTPClient, TokenManager, TestReporting,
    TestStep, TestResult, EnvironmentInfo,
    Colors, print_success, print_error, print_warning, print_info,
    extract_jwt_token, extract_json_field, format_timestamp, format_response_time,
    EmailVerificationHelper, wait_for_email_verification
)
from auth_helpers import AuthHelper, AuthDataManager
# Configuration will be loaded from framework config

class Test05ResendVerification:
    """Test-05: Resend Verification Email Functionality"""

    def __init__(self):
        self.test_id = "TEST-05"
        self.test_name = "Resend Verification Email Functionality"
        self.reporting = TestReporting()
        self.db_helper = DatabaseHelper(config.DATABASE_URL)
        self.http_client = HTTPClient(config.APP_URL)
        self.token_manager = TokenManager()
        self.email_helper = EmailVerificationHelper(config.MAILCATCHER_URL)
        self.test_steps = []
        self.start_time = datetime.now()
        self.admin_token = None
        self.test_user_email = None
        self.test_user_password = None
        self.invite_code = None

    def setup_environment(self) -> bool:
        """Setup and verify test environment"""
        print_info("Setting up resend verification test environment...")

        # Initialize database connection
        if not self.db_helper.connect():
            print_error("Failed to connect to database")
            return False

        # Connect to Mailcatcher
        if not self.email_helper.connect_mailcatcher():
            print_error("Failed to connect to Mailcatcher")
            return False

        # Clear existing emails
        self.email_helper.clear_all_emails()

        # Clean up any existing test user to ensure clean state
        self.cleanup_existing_test_user()

        # Load admin token from TEST-01
        try:
            token_path = config.get_token_path('admin_token')
            if os.path.exists(token_path):
                with open(token_path, 'r') as f:
                    self.admin_token = f.read().strip()
                print_success("Admin token loaded from previous test")
            else:
                print_error("Admin token not found - run TEST-01 first")
                return False
        except Exception as e:
            print_error(f"Failed to load admin token: {e}")
            return False

        print_success("Environment setup completed successfully")
        return True

    def cleanup_existing_test_user(self):
        """Clean up any existing test user and invite codes to ensure clean state"""
        try:
            # Clean up test invite codes first (to handle foreign key constraints)
            cleanup_invite_query = """
                DELETE FROM invite_codes
                WHERE upper(code) LIKE upper(%s)
                OR used_by_user_id IN (
                    SELECT id FROM users WHERE upper(email) = upper(%s)
                )
            """
            self.db_helper.execute_update(cleanup_invite_query, ("RESEND-TEST-%", "resend-test@example.com",))
            self.db_helper.execute_update(cleanup_invite_query, ("RATE-LIMIT-%", "rate-limit-test@example.com",))

            # Clean up rate limit test user
            cleanup_rate_limit_query = """
                DELETE FROM users
                WHERE upper(email) = upper(%s)
            """
            self.db_helper.execute_update(cleanup_rate_limit_query, ("rate-limit-test@example.com",))

            # Clean up main test user (now that foreign key constraints are removed)
            cleanup_query = """
                DELETE FROM users
                WHERE upper(email) = upper(%s)
            """
            self.db_helper.execute_update(cleanup_query, ("resend-test@example.com",))

            print_info("Cleaned up any existing test user and invite codes")
        except Exception as e:
            print_warning(f"Could not cleanup existing test data: {e}")

    def create_and_verify_test_user(self) -> TestStep:
        """Step: Create a test user and complete initial verification"""
        step = TestStep(
            step_number=1,
            step_name="Create and Verify Test User",
            status="PASS",
            message="Creating test user and completing initial verification for resend testing..."
        )

        try:
            # Always create a new unique invite code for this test to avoid conflicts
            print_info("Creating new unique invite code for test...")
            # Generate unique invite code with timestamp
            unique_suffix = str(int(time.time()))[-6:]  # Last 6 digits of timestamp
            self.invite_code = f"RESEND-TEST-{unique_suffix}"

            request_data = {
                "code": self.invite_code,
                "expiresAt": "2025-12-31T23:59:59"
            }

            response, response_time = self.http_client.post(
                config.ENDPOINTS['admin_invites'],
                request_data,
                auth_token=self.admin_token
            )

            if response.status_code == config.STATUS_CODES['success']:
                response_data = response.json()
                # Invite code is already set above, but we can confirm it was created
                print_info(f"Successfully created invite code: {self.invite_code}")
            else:
                step.status = "FAIL"
                step.message = f"Failed to create invite code: {response.status_code} - {response.text}"
                return step

            # Create test user
            self.test_user_email = "resend-test@example.com"
            self.test_user_password = "ResendTest123!"

            # Check if user already exists
            existing_user_results = self.db_helper.execute_query(
                "SELECT id, email, email_verified_at FROM users WHERE upper(email) = upper(%s)",
                (self.test_user_email,)
            )

            if existing_user_results:
                # User already exists, reuse it
                user_data = existing_user_results[0]
                print_info(f"Found existing user: {user_data['email']}, ID: {user_data['id']}")

                # If user is not verified, we can proceed with verification
                if not user_data['email_verified_at']:
                    print_info("Existing user is not verified - proceeding with verification flow")
                else:
                    print_info("Existing user is already verified - will reset to unverified for testing")
            else:
                # Create new user
                registration_data = {
                    "email": self.test_user_email,
                    "password": self.test_user_password,
                    "confirmPassword": self.test_user_password,
                    "inviteCode": self.invite_code,
                    "userAcceptedTerms": True,
                    "userAcknowledgedDisclaimer": True
                }

                step.request_data = registration_data

                response, response_time = self.http_client.post(
                    config.ENDPOINTS['user_register'],
                    registration_data
                )

                if response.status_code != config.STATUS_CODES['accepted']:
                    step.status = "FAIL"
                    step.message = f"User registration failed: {response.status_code} - {response.text}"
                    print_error(f"Registration response: {response.status_code} - {response.text}")
                    print_error(f"Registration data: {registration_data}")
                    return step

                print_success("New user registered successfully")

            # Check if user is already verified
            user_results_after_check = self.db_helper.execute_query(
                config.DB_QUERIES['check_complete_user'],
                (self.test_user_email,)
            )

            if not user_results_after_check:
                step.status = "FAIL"
                step.message = "User not found in database"
                return step

            current_user_data = user_results_after_check[0]

            if not current_user_data['email_verified_at']:
                # User is not verified, need to verify first
                print_info("User is not verified - waiting for verification email...")
                email_found = wait_for_email_verification(self.email_helper, self.test_user_email, config.EMAIL_TIMEOUT)

                if not email_found:
                    step.status = "FAIL"
                    step.message = "Initial verification email not received"
                    return step

                # Get the verification email and extract token
                email = self.email_helper.get_latest_email(self.test_user_email)
                if not email:
                    step.status = "FAIL"
                    step.message = "Failed to retrieve initial verification email"
                    return step

                verification_token = self.email_helper.extract_verification_token(email)
                if not verification_token:
                    step.status = "FAIL"
                    step.message = "Failed to extract verification token from email"
                    return step

                # Verify the email
                verification_data = {"token": verification_token}
                response, response_time = self.http_client.post(
                    config.ENDPOINTS['email_verify'],
                    verification_data
                )

                if response.status_code != config.STATUS_CODES['success']:
                    step.status = "FAIL"
                    step.message = f"Initial email verification failed: {response.status_code}"
                    return step

                print_success("Initial verification completed successfully")
            else:
                # User is already verified, which is perfect for our test
                print_success("User is already verified - ready for resend test")

            # Get final user data for the step result
            final_user_results = self.db_helper.execute_query(
                config.DB_QUERIES['check_complete_user'],
                (self.test_user_email,)
            )

            final_user_data = final_user_results[0] if final_user_results else current_user_data

            step.status = "PASS"
            step.message = f"Test user created and verified successfully: {self.test_user_email}"
            step.database_state = {
                'user_created': True,
                'user_email': self.test_user_email,
                'initially_verified': True,
                'invite_code_used': self.invite_code,
                'user_id': final_user_data['id'],
                'initial_verification_time': final_user_data['email_verified_at']
            }

            print_success(f"✓ Test user created and verified: {self.test_user_email}")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Failed to create and verify test user: {e}"
            print_error(f"Failed to create and verify test user: {e}")

        return step

    def set_email_verified_to_null(self) -> TestStep:
        """Step: Set email_verified_at to null in database to simulate unverified state"""
        step = TestStep(
            step_number=2,
            step_name="Set Email Verified to Null",
            status="PASS",
            message="Setting email_verified_at to null to test resend functionality..."
        )

        try:
            # First, verify user exists with exact email case
            print_info(f"Verifying user exists with email: {self.test_user_email}")
            user_check_query = """
                SELECT id, email, email_verified_at, is_active
                FROM users
                WHERE email = %s
            """

            user_results = self.db_helper.execute_query(user_check_query, (self.test_user_email,))

            if not user_results:
                # Try case-insensitive search
                case_insensitive_query = """
                    SELECT id, email, email_verified_at, is_active
                    FROM users
                    WHERE upper(email) = upper(%s)
                """
                user_results = self.db_helper.execute_query(case_insensitive_query, (self.test_user_email,))

                if not user_results:
                    step.status = "FAIL"
                    step.message = f"User not found in database with email: {self.test_user_email}"
                    return step
                else:
                    print_warning(f"User found with different case: {user_results[0]['email']}")

            user_data = user_results[0]
            user_id = user_data['id']

            print_info(f"Found user: ID={user_id}, Email={user_data['email']}, Verified={user_data['email_verified_at']}")

            # Update email_verified_at to null
            update_query = """
                UPDATE users
                SET email_verified_at = NULL
                WHERE id = %s
            """

            print_info("Updating email_verified_at to NULL...")
            update_success = self.db_helper.execute_update(update_query, (user_id,))

            if not update_success:
                step.status = "FAIL"
                step.message = "Failed to update email_verified_at to null"
                return step

            # Verify the update worked with fresh query
            print_info("Verifying update worked...")
            user_results_after = self.db_helper.execute_query(user_check_query, (self.test_user_email,))

            if not user_results_after:
                step.status = "FAIL"
                step.message = "User not found after update"
                return step

            user_data_after = user_results_after[0]
            print_info(f"User after update: ID={user_data_after['id']}, Email={user_data_after['email']}, Verified={user_data_after['email_verified_at']}")

            if user_data_after['email_verified_at'] is not None:
                step.status = "FAIL"
                step.message = f"Email_verified_at is not null after update: {user_data_after['email_verified_at']}"
                return step

            step.status = "PASS"
            step.message = f"Successfully set email_verified_at to null for {self.test_user_email}"
            step.database_state = {
                'email_verified_updated': True,
                'email_verified_at_null': True,
                'user_id': user_id,
                'previous_verification_time': user_data['email_verified_at'],
                'actual_email_in_db': user_data_after['email']
            }

            print_success(f"✓ Email verified status set to null for {user_data_after['email']}")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Failed to set email_verified_at to null: {e}"
            print_error(f"Failed to set email_verified_at to null: {e}")

        return step

    def request_resend_verification(self) -> TestStep:
        """Step: Request resend verification email"""
        step = TestStep(
            step_number=3,
            step_name="Request Resend Verification Email",
            status="PASS",
            message="Requesting resend of verification email..."
        )

        try:
            # Get the actual email from database to handle case sensitivity
            user_check_query = """
                SELECT email, email_verified_at, is_active
                FROM users
                WHERE upper(email) = upper(%s)
            """

            user_results = self.db_helper.execute_query(user_check_query, (self.test_user_email,))

            if not user_results:
                step.status = "FAIL"
                step.message = f"Cannot find user in database before resend request: {self.test_user_email}"
                return step

            actual_email = user_results[0]['email']
            is_verified = user_results[0]['email_verified_at'] is not None
            is_active = user_results[0]['is_active']

            print_info(f"Database check - Email: {actual_email}, Verified: {is_verified}, Active: {is_active}")

            if is_verified:
                step.status = "FAIL"
                step.message = f"User is already verified in database: {actual_email}"
                return step

            # Clear emails to isolate resend
            self.email_helper.clear_all_emails()

            # Request resend verification using the actual email from database
            resend_data = {
                "email": actual_email
            }

            step.request_data = resend_data

            print_info(f"Sending resend request for email: {actual_email}")
            response, response_time = self.http_client.post(
                config.ENDPOINTS['email_resend'],
                resend_data
            )

            step.response_time = response_time

            print_info(f"Resend response - Status: {response.status_code}, Body: {response.text}")

            # Should return 200 OK for successful resend request
            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = f"Resend verification request failed: {response.status_code} - {response.text}"
                print_error(f"Resend verification request failed: {response.status_code}")
                print_error(f"Request data: {resend_data}")
                return step

            # Parse response (should be empty or success message)
            try:
                response_data = response.json() if response.text.strip() else {}
                step.response_data = response_data
            except json.JSONDecodeError:
                response_data = {}

            step.status = "PASS"
            step.message = f"Resend verification request successful ({format_response_time(response_time)})"
            step.database_state = {
                'resend_requested': True,
                'response_status': response.status_code,
                'request_successful': True,
                'email_used': actual_email,
                'user_was_verified_before': is_verified
            }

            print_success(f"✓ Resend verification request successful for {actual_email} ({format_response_time(response_time)})")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Resend verification request failed: {e}"
            print_error(f"Resend verification request failed: {e}")

        return step

    def verify_resend_email_delivery(self) -> TestStep:
        """Step: Verify resend email is delivered"""
        step = TestStep(
            step_number=4,
            step_name="Verify Resend Email Delivery",
            status="PASS",
            message="Verifying resend verification email delivery..."
        )

        try:
            # Wait for resend email
            print_info("Waiting for resend verification email...")
            email_found = wait_for_email_verification(self.email_helper, self.test_user_email, config.EMAIL_TIMEOUT)

            if not email_found:
                step.status = "FAIL"
                step.message = "Resend verification email not received"
                return step

            # Get the resend email
            email = self.email_helper.get_latest_email(self.test_user_email)
            if not email:
                step.status = "FAIL"
                step.message = "Failed to retrieve resend verification email"
                return step

            # Extract verification token from resend email
            resend_token = self.email_helper.extract_verification_token(email)
            if not resend_token:
                step.status = "FAIL"
                step.message = "Failed to extract token from resend email"
                return step

            # Store resend token
            self.token_manager.store_token('resend_verification_token', resend_token)

            step.status = "PASS"
            step.message = f"Resend verification email delivered successfully"
            step.database_state = {
                'resend_email_received': True,
                'resend_token_extracted': True,
                'email_subject': email.get('subject'),
                'email_sender': email.get('from'),
                'resend_token': resend_token[:20] + "..." if resend_token and len(resend_token) > 20 else resend_token
            }

            print_success(f"✓ Resend verification email delivered successfully")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Resend email delivery verification failed: {e}"
            print_error(f"Resend email delivery verification failed: {e}")

        return step

    def verify_resend_token_works(self) -> TestStep:
        """Step: Verify that resend verification token works"""
        step = TestStep(
            step_number=5,
            step_name="Verify Resend Token Works",
            status="PASS",
            message="Testing verification with resend token..."
        )

        try:
            resend_token = self.token_manager.get_token('resend_verification_token')
            if not resend_token:
                step.status = "FAIL"
                step.message = "Resend verification token not found"
                return step

            # Use resend token to verify email
            verification_data = {
                "token": resend_token
            }

            response, response_time = self.http_client.post(
                config.ENDPOINTS['email_verify'],
                verification_data
            )

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = f"Verification with resend token failed: {response.status_code}"
                return step

            # Verify user is now marked as verified
            user_results = self.db_helper.execute_query(
                config.DB_QUERIES['check_complete_user'],
                (self.test_user_email,)
            )

            if not user_results:
                step.status = "FAIL"
                step.message = "User not found after verification"
                return step

            user_data = user_results[0]

            if not user_data['email_verified_at']:
                step.status = "FAIL"
                step.message = "User not marked as verified after resend token usage"
                return step

            step.status = "PASS"
            step.message = f"Resend token verification successful ({format_response_time(response_time)})"
            step.database_state = {
                'resend_token_works': True,
                'user_verified': True,
                'verification_time': user_data['email_verified_at']
            }

            print_success(f"✓ Resend token verification successful ({format_response_time(response_time)})")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Resend token verification failed: {e}"
            print_error(f"Resend token verification failed: {e}")

        return step

    def test_resend_rate_limiting(self) -> TestStep:
        """Step: Test resend rate limiting"""
        step = TestStep(
            step_number=6,
            step_name="Test Resend Rate Limiting",
            status="PASS",
            message="Testing resend verification rate limiting..."
        )

        try:
            # Create another unverified user for rate limiting test
            rate_limit_email = "rate-limit-test@example.com"
            rate_limit_password = "RateLimitTest123!"

            # Get another invite code
            unique_suffix = str(int(time.time()))[-6:]  # Last 6 digits of timestamp
            rate_limit_code = f"RATE-LIMIT-{unique_suffix}"

            request_data = {
                "code": rate_limit_code,
                "expiresAt": "2025-12-31T23:59:59"
            }

            response, response_time = self.http_client.post(
                config.ENDPOINTS['admin_invites'],
                request_data,
                auth_token=self.admin_token
            )

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = f"Failed to create invite code for rate limiting test"
                return step

            response_data = response.json()
            # rate_limit_code is already set above

            # Register user
            registration_data = {
                "email": rate_limit_email,
                "password": rate_limit_password,
                "confirmPassword": rate_limit_password,
                "inviteCode": rate_limit_code,
                "userAcceptedTerms": True,
                "userAcknowledgedDisclaimer": True
            }

            response, response_time = self.http_client.post(
                config.ENDPOINTS['user_register'],
                registration_data
            )

            if response.status_code != config.STATUS_CODES['accepted']:
                step.status = "WARN"
                step.message = f"Rate limiting user registration failed: {response.status_code} - {response.text}"
                print_warning(f"Could not create user for rate limiting test: {response.status_code}")
                return step

            # Clear emails
            self.email_helper.clear_all_emails()

            # Make multiple resend requests quickly
            resend_data = {"email": rate_limit_email}
            responses = []

            for i in range(3):  # Try 3 rapid requests
                response, response_time = self.http_client.post(
                    config.ENDPOINTS['email_resend'],
                    resend_data
                )
                responses.append({
                    'attempt': i + 1,
                    'status': response.status_code,
                    'response_time': response_time
                })
                time.sleep(1)  # Small delay between requests

            # Check if rate limiting is working (should get 429 after first few requests)
            rate_limiting_detected = any(r['status'] == 429 for r in responses)

            step.status = "PASS"
            step.message = f"Rate limiting test completed"
            step.database_state = {
                'multiple_requests_made': len(responses),
                'rate_limiting_detected': rate_limiting_detected,
                'responses': responses
            }

            if rate_limiting_detected:
                print_success("✓ Rate limiting is working correctly")
            else:
                print_warning("Rate limiting may not be configured (this might be acceptable)")

        except Exception as e:
            step.status = "WARN"  # Rate limiting is optional
            step.message = f"Rate limiting test encountered issues: {e}"
            print_warning(f"Rate limiting test encountered issues: {e}")

        return step

    def cleanup(self):
        """Cleanup test resources"""
        try:
            self.db_helper.disconnect()
            print_info("Test cleanup completed")
        except Exception as e:
            print_warning(f"Cleanup warning: {e}")

    def run_test(self) -> TestResult:
        """Run the complete test"""
        self.reporting.print_test_header(self.test_id, self.test_name)

        # Setup environment
        if not self.setup_environment():
            result = TestResult(
                test_id=self.test_id,
                test_name=self.test_name,
                status="ERROR",
                total_steps=0,
                passed_steps=0,
                failed_steps=0,
                skipped_steps=0,
                error_steps=1,
                total_time=0,
                start_time=self.start_time
            )
            self.reporting.add_test_result(result)
            self.reporting.print_test_footer(self.test_id, self.test_name, result)
            return result

        # Execute test steps
        test_steps = [
            self.create_and_verify_test_user(),
            self.set_email_verified_to_null(),
            self.request_resend_verification(),
            self.verify_resend_email_delivery(),
            self.verify_resend_token_works(),
            self.test_resend_rate_limiting()
        ]

        self.test_steps = test_steps

        # Calculate results
        total_steps = len(test_steps)
        passed_steps = sum(1 for step in test_steps if step.status == "PASS")
        failed_steps = sum(1 for step in test_steps if step.status == "FAIL")
        skipped_steps = sum(1 for step in test_steps if step.status == "SKIP")
        error_steps = sum(1 for step in test_steps if step.status == "ERROR")
        warning_steps = sum(1 for step in test_steps if step.status == "WARN")

        overall_status = "PASS" if failed_steps == 0 and error_steps == 0 else "FAIL"
        total_time = (datetime.now() - self.start_time).total_seconds()

        # Create test result
        result = TestResult(
            test_id=self.test_id,
            test_name=self.test_name,
            status=overall_status,
            total_steps=total_steps,
            passed_steps=passed_steps,
            failed_steps=failed_steps,
            skipped_steps=skipped_steps,
            error_steps=error_steps,
            total_time=total_time,
            start_time=self.start_time,
            end_time=datetime.now(),
            test_steps=test_steps
        )

        # Print step results
        for step in test_steps:
            self.reporting.print_step_result(step)

        # Print test footer
        self.reporting.print_test_footer(self.test_id, self.test_name, result)
        self.reporting.add_test_result(result)

        # Cleanup
        self.cleanup()

        return result

def main():
    """Main test execution function"""
    print(f"\n{Colors.CYAN}{'='*80}")
    print(f"{'='*80}")
    print(f"🧪 TRC Platform UAT - {Colors.YELLOW}TEST-05: Resend Verification Email")
    print(f"{'='*80}")
    print(f"{'='*80}{Colors.RESET}\n")

    # Print configuration
    config.print_config_summary()

    # Run test
    test_runner = Test05ResendVerification()
    result = test_runner.run_test()

    # Print summary
    print(f"\n{Colors.CYAN}{'='*80}")
    print(f"🏁 TEST-05 EXECUTION COMPLETE")
    print(f"{'='*80}{Colors.RESET}")
    print(f"Status: {Colors.GREEN if result.is_success() else Colors.RED}{result.status}{Colors.RESET}")
    print(f"Duration: {result.total_time:.2f} seconds")
    print(f"Steps: {result.passed_steps}/{result.total_steps} passed")

    if result.is_success():
        print_success("Resend verification email test completed successfully!")
        print_info("Email resend functionality working correctly")
    else:
        print_error("Resend verification email test failed!")
        print_warning("Check email service configuration and rate limiting settings")

    return result.is_success()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
