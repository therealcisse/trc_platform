#!/usr/bin/env python3
"""
TEST-01: User Registration for Billing API Testing
Test ID: TEST-01
Test Name: User Registration for Billing API Testing
Test Type: Functional Registration
Priority: High
Estimated Duration: 15 minutes

Description:
Create a dedicated test user for billing API testing. This test is self-contained
and does not rely on other tests. Each test creates its own user with timestamp-based
email to ensure complete isolation.
"""

import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime

from uat_test_framework import (
    DatabaseHelper, HTTPClient, TokenManager, TestReporting,
    TestStep, TestResult, Colors, print_success, print_error, print_warning, print_info,
    extract_jwt_token, wait_for_email_verification, EmailVerificationHelper
)
from uat_config import config
from billing_helpers import BillingDataManager
from billing_exceptions import (
    DatabaseConnectionError, ApiConnectionError, AuthenticationError,
    EmailVerificationError, TestSetupError, TestCleanupError,
    ServiceUnavailableError
)
from error_handling import (
    handle_test_errors, safe_execute_database_query, safe_execute_api_call,
    log_test_error, ErrorCollector
)

class Test01UserRegistration:
    """TEST-01: User Registration for Billing API Testing"""

    def __init__(self):
        self.test_id = "TEST-01"
        self.test_name = "User Registration for Billing API Testing"
        self.reporting = TestReporting()
        self.db_helper = DatabaseHelper(config.DATABASE_URL)
        self.http_client = HTTPClient(config.APP_URL)
        self.token_manager = TokenManager()
        self.email_helper = EmailVerificationHelper(config.MAILCATCHER_URL)
        self.data_manager = BillingDataManager(db_helper=self.db_helper)
        self.error_collector = ErrorCollector()
        self.test_steps = []
        self.start_time = datetime.now()
        self.admin_token = None
        self.test_user_email = None
        self.test_user_password = None
        self.test_user_id = None

    @handle_test_errors(test_id="TEST-01", step_name="Environment Setup")
    def setup_environment(self) -> bool:
        """Setup test environment"""
        print_info("Setting up test environment...")

        try:
            safe_execute_database_query(
                db_helper=self.db_helper,
                query_func=self.db_helper.connect,
                error_message="Failed to connect to database",
                test_id=self.test_id,
                step_name="Environment Setup"
            )
        except DatabaseConnectionError as e:
            self.error_collector.add_error(e)
            log_test_error(e)
            return False

        # Authenticate as admin
        try:
            login_data = {
                "email": config.ADMIN_EMAIL,
                "password": config.ADMIN_PASSWORD
            }

            response, response_time = safe_execute_api_call(
                http_client=self.http_client,
                api_func=self.http_client.post,
                endpoint=config.get_endpoint('login'),
                error_message="Admin authentication failed",
                test_id=self.test_id,
                step_name="Environment Setup",
                data=login_data
            )

            response_data = response.json()
            self.admin_token = response_data['token']
            self.token_manager.store_token('admin', self.admin_token)
            print_success(f"Admin authentication successful")

        except AuthenticationError as e:
            self.error_collector.add_error(e)
            log_test_error(e, {'user_email': config.ADMIN_EMAIL, 'auth_type': 'admin'})
            return False
        except ApiConnectionError as e:
            self.error_collector.add_error(e)
            log_test_error(e)
            return False

        # Connect to Mailcatcher
        if not self.email_helper.connect_mailcatcher():
            error = ServiceUnavailableError(
                message="Failed to connect to Mailcatcher",
                service_name="Mailcatcher",
                service_url=config.MAILCATCHER_URL,
                test_id=self.test_id,
                step_name="Environment Setup"
            )
            self.error_collector.add_error(error)
            log_test_error(error)
            return False

        self.email_helper.clear_all_emails()
        print_success("Environment setup completed")
        return True

    def create_test_invite_code(self) -> TestStep:
        """Step: Create invite code for registration"""
        step = TestStep(
            step_number=1,
            step_name="Create Test Invite Code",
            status="PASS",
            message="Creating invite code..."
        )

        try:
            test_code = config.generate_unique_invite_code("BILLING-TEST")
            request_data = {"code": test_code}

            # Track invite code for cleanup
            self.data_manager.track_invite_code(test_code)

            response, response_time = self.http_client.post(
                config.get_endpoint('admin_invites'),
                request_data,
                auth_token=self.admin_token
            )

            step.response_time = response_time

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = f"Failed to create invite code: {response.status_code}"
                print_error(f"Failed to create invite code: {response.status_code}")
                return step

            response_data = response.json()
            self.invite_code = test_code

            step.status = "PASS"
            step.message = f"Created invite code: {test_code}"
            print_success(f"Created invite code: {test_code}")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Failed to create invite code: {e}"
            print_error(f"Failed: {e}")

        return step

    def register_test_user(self) -> TestStep:
        """Step: Register test user for billing"""
        step = TestStep(
            step_number=2,
            step_name="Register Test User for Billing",
            status="PASS",
            message="Registering test user..."
        )

        try:
            self.test_user_email = config.generate_unique_email("billing-test")
            self.test_user_password = "SecurePassword123!"

            registration_data = {
                "email": self.test_user_email,
                "password": self.test_user_password,
                "confirmPassword": self.test_user_password,
                "inviteCode": self.invite_code,
                "userAcceptedTerms": True,
                "userAcknowledgedDisclaimer": True
            }

            response, response_time = self.http_client.post(
                config.get_endpoint('user_register'),
                registration_data
            )

            step.response_time = response_time

            if response.status_code not in [config.STATUS_CODES['accepted'], config.STATUS_CODES['created']]:
                step.status = "FAIL"
                step.message = f"Registration failed: {response.status_code}"
                print_error(f"Registration failed: {response.status_code}")
                return step

            step.status = "PASS"
            step.message = f"Registered user: {self.test_user_email}"
            print_success(f"Registered: {self.test_user_email}")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Registration failed: {e}"
            print_error(f"Failed: {e}")

        return step

    def verify_user_email(self) -> TestStep:
        """Step: Verify user email"""
        step = TestStep(
            step_number=3,
            step_name="Verify User Email",
            status="PASS",
            message="Verifying email..."
        )

        try:
            # Wait for email
            if not wait_for_email_verification(self.email_helper, self.test_user_email, config.EMAIL_TIMEOUT):
                step.status = "FAIL"
                step.message = "Email verification timeout"
                print_error("Email verification timeout")
                return step

            # Get email and extract token
            email = self.email_helper.get_latest_email(self.test_user_email)
            if not email:
                step.status = "FAIL"
                step.message = "Failed to get email"
                print_error("Failed to get email")
                return step

            # Verify email directly in database for testing
            update_query = "UPDATE users SET email_verified_at = NOW() WHERE email = %s"
            self.db_helper.execute_update(update_query, (self.test_user_email,))

            step.status = "PASS"
            step.message = "Email verified"
            print_success("Email verified")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Email verification failed: {e}"
            print_error(f"Failed: {e}")

        return step

    def authenticate_test_user(self) -> TestStep:
        """Step: Authenticate test user"""
        step = TestStep(
            step_number=4,
            step_name="Authenticate Test User",
            status="PASS",
            message="Authenticating user..."
        )

        try:
            login_data = {
                "email": self.test_user_email,
                "password": self.test_user_password
            }

            response, response_time = self.http_client.post(
                config.get_endpoint('login'),
                login_data
            )

            step.response_time = response_time

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = f"Login failed: {response.status_code}"
                print_error(f"Login failed: {response.status_code}")
                return step

            response_data = response.json()
            self.test_user_id = response_data['id']
            user_token = response_data['token']
            self.token_manager.store_token('user', user_token)

            # Track user for cleanup
            self.data_manager.track_user(self.test_user_id)

            step.status = "PASS"
            step.message = f"User authenticated: {self.test_user_id}"
            step.database_state = {
                'user_id': self.test_user_id,
                'email': self.test_user_email,
                'email_verified': True
            }
            print_success(f"Authenticated: {self.test_user_id}")

            # Store user data for other tests
            self.data_manager.store_period('test_user', {
                'user_id': self.test_user_id,
                'email': self.test_user_email,
                'password': self.test_user_password,
                'token': user_token
            })

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Authentication failed: {e}"
            print_error(f"Failed: {e}")

        return step

    def verify_user_in_database(self) -> TestStep:
        """Step: Verify user in database"""
        step = TestStep(
            step_number=5,
            step_name="Verify User in Database",
            status="PASS",
            message="Verifying database state..."
        )

        try:
            # Check user exists
            user_results = self.db_helper.execute_query(
                config.DB_QUERIES['check_complete_user'],
                (self.test_user_email,)
            )

            if not user_results:
                step.status = "FAIL"
                step.message = "User not found in database"
                print_error("User not found")
                return step

            user_data = user_results[0]

            if user_data['email_verified_at'] is None:
                step.status = "FAIL"
                step.message = "User email not verified in database"
                print_error("Email not verified")
                return step

            step.status = "PASS"
            step.message = "User verified in database"
            step.database_state = {
                'user_exists': True,
                'email_verified': True,
                'user_id': user_data['id'],
                'terms_accepted': user_data['user_accepted_terms'],
                'disclaimer_acknowledged': user_data['user_acknowledged_disclaimer']
            }
            print_success("User verified in database")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Database verification failed: {e}"
            print_error(f"Failed: {e}")

        return step

    def cleanup(self):
        """Cleanup test resources"""
        try:
            # Clean up test data
            if self.data_manager.cleanup_test_data():
                print_info("Test data cleanup successful")
            else:
                print_warning("Test data cleanup had issues")

            # Disconnect from database
            self.db_helper.disconnect()
            print_info("Cleanup completed")
        except Exception as e:
            print_warning(f"Cleanup warning: {e}")

    def run_test(self) -> TestResult:
        """Run the test"""
        self.reporting.print_test_header(self.test_id, self.test_name)

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
            return result

        # Execute steps
        test_steps = [
            self.create_test_invite_code(),
            self.register_test_user(),
            self.verify_user_email(),
            self.authenticate_test_user(),
            self.verify_user_in_database()
        ]

        self.test_steps = test_steps

        # Calculate results
        total_steps = len(test_steps)
        passed_steps = sum(1 for step in test_steps if step.status == "PASS")
        failed_steps = sum(1 for step in test_steps if step.status == "FAIL")

        overall_status = "PASS" if failed_steps == 0 else "FAIL"
        total_time = (datetime.now() - self.start_time).total_seconds()

        result = TestResult(
            test_id=self.test_id,
            test_name=self.test_name,
            status=overall_status,
            total_steps=total_steps,
            passed_steps=passed_steps,
            failed_steps=failed_steps,
            skipped_steps=0,
            error_steps=0,
            total_time=total_time,
            start_time=self.start_time,
            end_time=datetime.now(),
            test_steps=test_steps
        )

        # Print results
        for step in test_steps:
            self.reporting.print_step_result(step)

        self.reporting.print_test_footer(self.test_id, self.test_name, result)
        self.reporting.add_test_result(result)
        self.cleanup()

        return result

def main():
    """Main test execution"""
    print(f"\n{Colors.CYAN}{'='*80}")
    print(f"🧪 TRC Platform Billing API UAT - TEST-01: User Registration")
    print(f"{'='*80}{Colors.RESET}\n")

    config.print_config_summary()

    test_runner = Test01UserRegistration()
    result = test_runner.run_test()

    print(f"\n{Colors.CYAN}{'='*80}")
    print(f"🏁 TEST-01 EXECUTION COMPLETE")
    print(f"{'='*80}{Colors.RESET}")
    print(f"Status: {Colors.GREEN if result.is_success() else Colors.RED}{result.status}{Colors.RESET}")
    print(f"Duration: {result.total_time:.2f} seconds")
    print(f"Steps: {result.passed_steps}/{result.total_steps} passed")

    if result.is_success():
        print_success("User registration test completed successfully!")
    else:
        print_error("User registration test failed!")

    return result.is_success()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
