"""
TEST-01: User Registration for API Token Testing
Test ID: TEST-01
Test Name: User Registration for API Token Testing
Test Type: Functional Registration
Priority: High
Estimated Duration: 15 minutes

Description:
Create a dedicated test user for API token testing. This test follows the same
pattern as UAT/auth test-03 but creates a specific user for API token functionality
testing. The test is completely self-contained and does not rely on external token storage.
"""

import sys
import os
import json
import time
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
from api_token_helpers import ApiTokenHelper, ApiTokenDataManager
# Configuration will be loaded from framework config

class Test01UserRegistration:
    """Test-01: User Registration for API Token Testing"""

    def __init__(self):
        self.test_id = "TEST-01"
        self.test_name = "User Registration for API Token Testing"
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
        self.test_user_id = None

    def setup_environment(self) -> bool:
        """Setup and verify test environment"""
        print_info("Setting up test environment...")

        # Initialize database connection
        if not self.db_helper.connect():
            print_error("Failed to connect to database")
            return False

        # Authenticate with default admin credentials
        try:
            login_data = {
                "email": config.ADMIN_EMAIL,
                "password": config.ADMIN_PASSWORD
            }

            response, response_time = self.http_client.post(
                config.ENDPOINTS['login'],
                login_data
            )

            if response.status_code != config.STATUS_CODES['success']:
                print_error(f"Admin login failed: {response.status_code} - {response.text}")
                return False

            response_data = response.json()
            required_fields = config.REQUIRED_RESPONSE_FIELDS['login']
            missing_fields = [field for field in required_fields if field not in response_data]

            if missing_fields:
                print_error(f"Missing required fields in login response: {missing_fields}")
                return False

            self.admin_token = response_data['token']
            self.token_manager.store_token('admin', self.admin_token)

            print_success(f"Admin authentication successful ({format_response_time(response_time)})")

        except Exception as e:
            print_error(f"Failed to authenticate admin: {e}")
            return False

        # Connect to Mailcatcher
        if not self.email_helper.connect_mailcatcher():
            print_error("Failed to connect to Mailcatcher")
            return False

        # Clear existing emails to ensure clean state
        self.email_helper.clear_all_emails()

        print_success("Environment setup completed successfully")
        return True

    def create_test_invite_code(self) -> TestStep:
        """Step: Create a fresh invite code for testing registration"""
        step = TestStep(
            step_number=1,
            step_name="Create Test Invite Code for API Token Testing",
            status="PASS",
            message="Creating invite code for registration test..."
        )

        try:
            # Generate unique invite code with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            test_code = f"API-TOKEN-{timestamp}"

            # Prepare request data for invite code creation
            request_data = {
                "code": test_code
            }

            step.request_data = request_data

            # Make request to create invite code
            response, response_time = self.http_client.post(
                "/api/v1/admin/invites",
                request_data,
                auth_token=self.admin_token
            )

            step.response_time = response_time

            # Check response status
            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = f"Failed to create invite code: {response.status_code} - {response.text}"
                print_error(f"Failed to create invite code: {response.status_code}")
                return step

            # Parse response
            try:
                response_data = response.json()
                step.response_data = response_data
            except json.JSONDecodeError:
                step.status = "FAIL"
                step.message = "Invalid JSON response from invite creation endpoint"
                print_error("Invalid JSON response from invite creation endpoint")
                return step

            # Validate required fields
            required_fields = ['id', 'code', 'active', 'createdAt']
            missing_fields = [field for field in required_fields if field not in response_data]

            if missing_fields:
                step.status = "FAIL"
                step.message = f"Missing required fields in invite response: {missing_fields}"
                print_error(f"Missing fields: {missing_fields}")
                return step

            # Validate response data
            created_code = response_data.get('code')
            if created_code != test_code:
                step.status = "FAIL"
                step.message = f"Created code mismatch. Expected: {test_code}, Actual: {created_code}"
                print_error(f"Code mismatch: {created_code}")
                return step

            if not response_data.get('active'):
                step.status = "FAIL"
                step.message = "Created invite code is not active"
                print_error("Invite code is not active")
                return step

            # Store invite code only within this test
            self.invite_code = created_code

            step.status = "PASS"
            step.message = f"Created invite code for testing: {created_code} ({format_response_time(response_time)})"
            step.database_state = {
                'code': created_code,
                'active': response_data.get('active'),
                'created_at': response_data.get('createdAt')
            }

            print_success(f"✓ Created invite code for testing: {created_code} ({format_response_time(response_time)})")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Failed to create test invite code: {e}"
            print_error(f"Failed to create test invite code: {e}")

        return step

    def register_api_token_test_user(self) -> TestStep:
        """Step: Register new user for API token testing"""
        step = TestStep(
            step_number=2,
            step_name="Register API Token Test User",
            status="PASS",
            message="Registering new user for API token testing..."
        )

        try:
            # Generate unique email with timestamp to avoid conflicts
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            self.test_user_email = f"api-token-{timestamp}@example.com"
            self.test_user_password = "SecurePassword123!"

            # Prepare registration request
            registration_data = {
                "email": self.test_user_email,
                "password": self.test_user_password,
                "confirmPassword": self.test_user_password,
                "inviteCode": self.invite_code,
                "userAcceptedTerms": True,
                "userAcknowledgedDisclaimer": True
            }

            step.request_data = registration_data

            # Make registration request
            response, response_time = self.http_client.post(
                config.ENDPOINTS['user_register'],
                registration_data
            )

            step.response_time = response_time

            if response.status_code != config.STATUS_CODES['accepted']:
                step.status = "FAIL"
                step.message = f"Registration failed with status {response.status_code}: {response.text}"
                print_error(f"Registration failed: {response.status_code} - {response.text}")
                return step

            # Check response body (should be empty for 202)
            if response.text.strip():
                try:
                    response_data = response.json()
                    step.response_data = response_data
                    step.status = "WARN"
                    step.message = f"Registration succeeded but unexpected response body: {response_data}"
                    print_warning(f"Unexpected response body: {response_data}")
                except json.JSONDecodeError:
                    step.status = "WARN"
                    step.message = "Registration succeeded but non-JSON response returned"
                    print_warning("Non-JSON response returned")

            step.status = "PASS"
            step.message = f"API token test user registration successful for {self.test_user_email} ({format_response_time(response_time)})"
            step.database_state = {
                'registered_email': self.test_user_email,
                'invite_code_used': self.invite_code,
                'terms_accepted': True,
                'disclaimer_acknowledged': True,
                'response_status': response.status_code
            }

            print_success(f"✓ API token test user registration successful for {self.test_user_email} ({format_response_time(response_time)})")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"API token test user registration failed: {e}"
            print_error(f"API token test user registration failed: {e}")

        return step

    def capture_verification_email(self) -> TestStep:
        """Step: Check Mailcatcher for verification email"""
        step = TestStep(
            step_number=3,
            step_name="Capture Verification Email for API Token User",
            status="PASS",
            message="Checking for API token user verification email..."
        )

        try:
            # Wait for email to arrive
            print_info("Waiting for verification email...")
            email_found = wait_for_email_verification(self.email_helper, self.test_user_email, config.EMAIL_TIMEOUT)

            if not email_found:
                step.status = "FAIL"
                step.message = f"Verification email not received within {config.EMAIL_TIMEOUT} seconds"
                print_error("Verification email not received")
                return step

            # Get the latest email
            email = self.email_helper.get_latest_email(self.test_user_email)
            if not email:
                step.status = "FAIL"
                step.message = "Failed to retrieve verification email"
                print_error("Failed to retrieve verification email")
                return step

            # Validate email content
            sender = email.get('sender', '')
            recipients = email.get('recipients', [])
            subject = email.get('subject', '')

            # Clean sender and recipients for comparison
            clean_sender = sender.strip('<>')
            clean_recipients = [r.strip('<>') for r in recipients]

            if config.EMAIL_FROM not in clean_sender:
                step.status = "FAIL"
                step.message = f"Email sender mismatch. Expected: {config.EMAIL_FROM}, Actual: {clean_sender}"
                print_error(f"Email sender mismatch: {clean_sender}")
                return step

            if self.test_user_email not in clean_recipients:
                step.status = "FAIL"
                step.message = f"Email not sent to expected recipient: {self.test_user_email}"
                print_error(f"Email recipient mismatch: {clean_recipients}")
                return step

            # Extract verification token
            verification_token = self.email_helper.extract_verification_token(email)
            if not verification_token:
                step.status = "FAIL"
                step.message = "Failed to extract verification token from email"
                print_error("Failed to extract verification token")
                return step

            # Store verification token only within this test
            self.verification_token = verification_token

            step.status = "PASS"
            step.message = f"Verification email captured for {self.test_user_email}"
            step.database_state = {
                'email_sender': sender,
                'email_recipients': recipients,
                'email_subject': subject,
                'verification_token_extracted': True,
                'token_length': len(verification_token)
            }

            step.response_data = {
                'email_id': email.get('id'),
                'subject': subject,
                'sender': sender,
                'recipients': recipients
            }

            print_success(f"✓ Verification email captured for {self.test_user_email}")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Failed to capture verification email: {e}"
            print_error(f"Failed to capture verification email: {e}")

        return step

    def verify_user_creation_in_database(self) -> TestStep:
        """Step: Verify user creation and invite code usage in database"""
        step = TestStep(
            step_number=4,
            step_name="Verify API Token User Creation in Database",
            status="PASS",
            message="Verifying API token user creation and invite code usage..."
        )

        try:
            # Check user creation
            user_results = self.db_helper.execute_query(
                config.DB_QUERIES['check_complete_user'],
                (self.test_user_email,)
            )

            if not user_results:
                step.status = "FAIL"
                step.message = f"API token user not found in database: {self.test_user_email}"
                print_error(f"User not found: {self.test_user_email}")
                return step

            user_data = user_results[0]
            self.test_user_id = user_data['id']

            # Validate user data
            if user_data['email_verified_at'] is not None:
                step.status = "FAIL"
                step.message = "API token user email should not be verified yet"
                print_error("User email incorrectly marked as verified")
                return step

            if not user_data['user_accepted_terms']:
                step.status = "FAIL"
                step.message = "API token user terms acceptance flag not set"
                print_error("Terms acceptance flag not set")
                return step

            if not user_data['user_acknowledged_disclaimer']:
                step.status = "FAIL"
                step.message = "API token user disclaimer acknowledgment flag not set"
                print_error("Disclaimer acknowledgment flag not set")
                return step

            # Check invite code usage
            invite_usage = self.db_helper.check_invite_code_usage(self.invite_code)
            if not invite_usage:
                step.status = "FAIL"
                step.message = f"Invite code usage not found: {self.invite_code}"
                print_error(f"Invite code usage not found: {self.invite_code}")
                return step

            if not invite_usage['used_at']:
                step.status = "FAIL"
                step.message = "Invite code not marked as used"
                print_error("Invite code not marked as used")
                return step

            if invite_usage['used_by_email'] != self.test_user_email:
                step.status = "FAIL"
                step.message = f"Invite code used by wrong user. Expected: {self.test_user_email}, Actual: {invite_usage['used_by_email']}"
                print_error(f"Invite code used by wrong user: {invite_usage['used_by_email']}")
                return step

            step.status = "PASS"
            step.message = "API token user database state verification successful"
            step.database_state = {
                'user_created': True,
                'user_email': self.test_user_email,
                'user_id': self.test_user_id,
                'email_verified': False,
                'terms_accepted': user_data['user_accepted_terms'],
                'disclaimer_acknowledged': user_data['user_acknowledged_disclaimer'],
                'invite_code_used': True,
                'invite_code': self.invite_code,
                'invite_used_at': invite_usage['used_at']
            }

            print_success("✓ API token user database state verification successful")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"API token user database state verification failed: {e}"
            print_error(f"API token user database state verification failed: {e}")

        return step

    def verify_user_can_authenticate(self) -> TestStep:
        """Step: Verify user can authenticate with credentials"""
        step = TestStep(
            step_number=5,
            step_name="Verify User Can Authenticate",
            status="PASS",
            message="Verifying that the registered user can authenticate..."
        )

        try:
            # Authenticate with the newly created user credentials
            login_data = {
                "email": self.test_user_email,
                "password": self.test_user_password
            }

            response, response_time = self.http_client.post(
                config.ENDPOINTS['login'],
                login_data
            )

            step.response_time = response_time

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = f"User authentication failed: {response.status_code} - {response.text}"
                print_error(f"User authentication failed: {response.status_code}")
                return step

            # Parse response
            try:
                response_data = response.json()
                step.response_data = response_data

                # Validate required fields
                required_fields = config.REQUIRED_RESPONSE_FIELDS['login']
                missing_fields = [field for field in required_fields if field not in response_data]

                if missing_fields:
                    step.status = "FAIL"
                    step.message = f"Missing required fields in login response: {missing_fields}"
                    print_error(f"Missing required fields: {missing_fields}")
                    return step

                # Validate response data
                user_id = response_data['id']
                email = response_data['email']
                token = response_data['token']

                if email != self.test_user_email:
                    step.status = "FAIL"
                    step.message = f"Email mismatch. Expected: {self.test_user_email}, Actual: {email}"
                    print_error(f"Email mismatch: {email}")
                    return step

                if user_id != self.test_user_id:
                    step.status = "FAIL"
                    step.message = f"User ID mismatch. Expected: {self.test_user_id}, Actual: {user_id}"
                    print_error(f"User ID mismatch: {user_id}")
                    return step

                # Store user token for potential use within this test
                self.user_token = token

                step.status = "PASS"
                step.message = f"User authentication verification successful ({format_response_time(response_time)})"
                step.database_state = {
                    'user_can_authenticate': True,
                    'authenticated_user_id': user_id,
                    'authenticated_email': email,
                    'token_received': bool(token)
                }

                print_success(f"✓ User authentication verification successful ({format_response_time(response_time)})")

            except json.JSONDecodeError:
                step.status = "FAIL"
                step.message = "Invalid JSON response from login endpoint"
                print_error("Invalid JSON response from login endpoint")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"User authentication verification failed: {e}"
            print_error(f"User authentication verification failed: {e}")

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
            self.create_test_invite_code(),
            self.register_api_token_test_user(),
            self.capture_verification_email(),
            self.verify_user_creation_in_database(),
            self.verify_user_can_authenticate()
        ]

        self.test_steps = test_steps

        # Calculate results
        total_steps = len(test_steps)
        passed_steps = sum(1 for step in test_steps if step.status == "PASS")
        failed_steps = sum(1 for step in test_steps if step.status == "FAIL")
        skipped_steps = sum(1 for step in test_steps if step.status == "SKIP")
        error_steps = sum(1 for step in test_steps if step.status == "ERROR")

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
    print(f"🧪 TRC Platform API Token UAT - {Colors.YELLOW}TEST-01: User Registration for API Token Testing")
    print(f"{'='*80}")
    print(f"{'='*80}{Colors.RESET}\n")

    # Print configuration
    config.print_config_summary()

    # Run test
    test_runner = Test01UserRegistration()
    result = test_runner.run_test()

    # Print summary
    print(f"\n{Colors.CYAN}{'='*80}")
    print(f"🏁 TEST-01 EXECUTION COMPLETE")
    print(f"{'='*80}{Colors.RESET}")
    print(f"Status: {Colors.GREEN if result.is_success() else Colors.RED}{result.status}{Colors.RESET}")
    print(f"Duration: {result.total_time:.2f} seconds")
    print(f"Steps: {result.passed_steps}/{result.total_steps} passed")

    if result.is_success():
        print_success("API token user registration test completed successfully!")
        print_info("User account created and verified for API token testing")
    else:
        print_error("API token user registration test failed!")
        print_warning("Check test logs and application status")

    return result.is_success()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
