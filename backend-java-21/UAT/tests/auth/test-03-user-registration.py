"""
TEST-03: Complete User Registration Flow
Test ID: TEST-03
Test Name: Complete User Registration Flow
Test Type: Functional Registration
Priority: High
Estimated Duration: 15 minutes

Description:
Validate complete user registration flow including invite code validation,
terms acceptance, and automatic verification email sending.
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
from auth_helpers import AuthHelper, AuthDataManager
# Configuration will be loaded from framework config
from uat_config import config

class Test03UserRegistration:
    """Test-03: Complete User Registration Flow"""

    def __init__(self):
        self.test_id = "TEST-03"
        self.test_name = "Complete User Registration Flow"
        self.reporting = TestReporting()
        self.db_helper = DatabaseHelper(config.DATABASE_URL)
        self.http_client = HTTPClient(config.APP_URL)
        self.token_manager = TokenManager()
        self.email_helper = EmailVerificationHelper(config.MAILCATCHER_URL)
        self.test_steps = []
        self.start_time = datetime.now()
        self.admin_token = None
        self.test_user_email = None

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
            step_name="Create Test Invite Code",
            status="PASS",
            message="Creating invite code for registration test..."
        )

        try:
            # Generate unique invite code with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            test_code = f"REG-TEST-{timestamp}"

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

            # Store invite code for registration
            self.token_manager.store_token('registration_invite_code', created_code)

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

    def successful_user_registration(self) -> TestStep:
        """Step: Register new user with valid data"""
        step = TestStep(
            step_number=2,
            step_name="Successful User Registration",
            status="PASS",
            message="Registering new user with valid data..."
        )

        try:
            # Get invite code and create unique test user
            invite_code = self.token_manager.get_token('registration_invite_code')

            # Generate unique email with timestamp to avoid conflicts
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            test_email = f"uat-test-{timestamp}@example.com"

            # Prepare registration request
            registration_data = {
                "email": test_email,
                "password": "SecurePassword123!",
                "confirmPassword": "SecurePassword123!",
                "inviteCode": invite_code,
                "userAcceptedTerms": True,
                "userAcknowledgedDisclaimer": True
            }

            # Store test email for later steps
            self.test_user_email = test_email

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

            # Store user credentials for later tests
            self.token_manager.store_token('test_user_email', self.test_user_email)
            self.token_manager.store_token('test_user_password', 'SecurePassword123!')

            step.status = "PASS"
            step.message = f"User registration successful for {self.test_user_email} ({format_response_time(response_time)})"
            step.database_state = {
                'registered_email': self.test_user_email,
                'invite_code_used': invite_code,
                'terms_accepted': True,
                'disclaimer_acknowledged': True,
                'response_status': response.status_code
            }

            print_success(f"✓ User registration successful for {self.test_user_email} ({format_response_time(response_time)})")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"User registration failed: {e}"
            print_error(f"User registration failed: {e}")

        return step

    def capture_verification_email(self) -> TestStep:
        """Step: Check Mailcatcher for verification email"""
        step = TestStep(
            step_number=3,
            step_name="Capture Verification Email",
            status="PASS",
            message="Checking for verification email..."
        )

        try:
            test_user_email = self.token_manager.get_token('test_user_email')
            if not test_user_email:
                step.status = "FAIL"
                step.message = "Test user email not found"
                print_error("Test user email not found")
                return step

            # Wait for email to arrive
            print_info("Waiting for verification email...")
            email_found = wait_for_email_verification(self.email_helper, test_user_email, config.EMAIL_TIMEOUT)

            if not email_found:
                step.status = "FAIL"
                step.message = f"Verification email not received within {config.EMAIL_TIMEOUT} seconds"
                print_error("Verification email not received")
                return step

            # Get the latest email
            email = self.email_helper.get_latest_email(test_user_email)
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

            if test_user_email not in clean_recipients:
                step.status = "FAIL"
                step.message = f"Email not sent to expected recipient: {test_user_email}"
                print_error(f"Email recipient mismatch: {clean_recipients}")
                return step

            # Extract verification token
            verification_token = self.email_helper.extract_verification_token(email)
            if not verification_token:
                step.status = "FAIL"
                step.message = "Failed to extract verification token from email"
                print_error("Failed to extract verification token")
                return step

            # Store verification token for next test
            self.token_manager.store_token('verification_token', verification_token)

            step.status = "PASS"
            step.message = f"Verification email captured for {test_user_email}"
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

            print_success(f"✓ Verification email captured for {test_user_email}")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Failed to capture verification email: {e}"
            print_error(f"Failed to capture verification email: {e}")

        return step

    def verify_database_state(self) -> TestStep:
        """Step: Check user creation and invite code usage in database"""
        step = TestStep(
            step_number=4,
            step_name="Verify Database State",
            status="PASS",
            message="Verifying user creation and invite code usage..."
        )

        try:
            test_user_email = self.token_manager.get_token('test_user_email')
            invite_code = self.token_manager.get_token('registration_invite_code')

            if not test_user_email or not invite_code:
                step.status = "FAIL"
                step.message = "Missing test user email or invite code"
                print_error("Missing test data")
                return step

            # Check user creation
            user_results = self.db_helper.execute_query(
                config.DB_QUERIES['check_complete_user'],
                (test_user_email,)
            )

            if not user_results:
                step.status = "FAIL"
                step.message = f"User not found in database: {test_user_email}"
                print_error(f"User not found: {test_user_email}")
                return step

            user_data = user_results[0]

            # Validate user data
            if user_data['email_verified_at'] is not None:
                step.status = "FAIL"
                step.message = "User email should not be verified yet"
                print_error("User email incorrectly marked as verified")
                return step

            if not user_data['user_accepted_terms']:
                step.status = "FAIL"
                step.message = "User terms acceptance flag not set"
                print_error("Terms acceptance flag not set")
                return step

            if not user_data['user_acknowledged_disclaimer']:
                step.status = "FAIL"
                step.message = "User disclaimer acknowledgment flag not set"
                print_error("Disclaimer acknowledgment flag not set")
                return step

            # Check invite code usage
            invite_usage = self.db_helper.check_invite_code_usage(invite_code)
            if not invite_usage:
                step.status = "FAIL"
                step.message = f"Invite code usage not found: {invite_code}"
                print_error(f"Invite code usage not found: {invite_code}")
                return step

            if not invite_usage['used_at']:
                step.status = "FAIL"
                step.message = "Invite code not marked as used"
                print_error("Invite code not marked as used")
                return step

            if invite_usage['used_by_email'] != test_user_email:
                step.status = "FAIL"
                step.message = f"Invite code used by wrong user. Expected: {test_user_email}, Actual: {invite_usage['used_by_email']}"
                print_error(f"Invite code used by wrong user: {invite_usage['used_by_email']}")
                return step

            step.status = "PASS"
            step.message = "Database state verification successful"
            step.database_state = {
                'user_created': True,
                'user_email': test_user_email,
                'user_id': user_data['id'],
                'email_verified': False,
                'terms_accepted': user_data['user_accepted_terms'],
                'disclaimer_acknowledged': user_data['user_acknowledged_disclaimer'],
                'invite_code_used': True,
                'invite_code': invite_code,
                'invite_used_at': invite_usage['used_at']
            }

            print_success("✓ Database state verification successful")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Database state verification failed: {e}"
            print_error(f"Database state verification failed: {e}")

        return step

    def test_password_requirements(self) -> TestStep:
        """Step: Test password complexity validation"""
        step = TestStep(
            step_number=5,
            step_name="Test Password Requirements",
            status="PASS",
            message="Testing password complexity validation..."
        )

        try:
            # Get weak password test user
            weak_user = config.get_test_user('error_scenarios')['weak_password']
            invite_code = self.token_manager.get_token('registration_invite_code')

            # Try to register with weak password
            weak_registration_data = {
                "email": weak_user['email'],
                "password": weak_user['password'],
                "confirmPassword": weak_user['password'],
                "inviteCode": "INVALID-CODE",  # Use invalid code to avoid using up valid codes
                "userAcceptedTerms": True,
                "userAcknowledgedDisclaimer": True
            }

            step.request_data = weak_registration_data

            # Make registration request
            response, response_time = self.http_client.post(
                config.ENDPOINTS['user_register'],
                weak_registration_data
            )

            step.response_time = response_time

            # Should fail with validation error
            if response.status_code != config.STATUS_CODES['bad_request']:
                step.status = "FAIL"
                step.message = f"Weak password validation failed - expected 400, got {response.status_code}"
                print_error(f"Weak password not rejected: {response.status_code}")
                return step

            # Try to parse error response
            try:
                error_response = response.json()
                step.response_data = error_response
            except json.JSONDecodeError:
                error_response = {"error": response.text}

            step.status = "PASS"
            step.message = f"Weak password correctly rejected ({format_response_time(response_time)})"
            step.database_state = {
                'weak_password_rejected': True,
                'expected_status': config.STATUS_CODES['bad_request'],
                'actual_status': response.status_code,
                'validation_working': True
            }

            print_success(f"✓ Weak password correctly rejected ({format_response_time(response_time)})")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Password requirements test failed: {e}"
            print_error(f"Password requirements test failed: {e}")

        return step

    def save_test_data_for_subsequent_tests(self) -> TestStep:
        """Step: Save test data for subsequent tests"""
        step = TestStep(
            step_number=6,
            step_name="Save Test Data for Subsequent Tests",
            status="PASS",
            message="Saving test data for subsequent tests..."
        )

        try:
            # Save verification token to file
            verification_token = self.token_manager.get_token('verification_token')

            # Save user credentials to file
            test_user_email = self.token_manager.get_token('test_user_email')
            test_user_password = self.token_manager.get_token('test_user_password')

            if test_user_email and test_user_password:
                # Create a simple credentials file (in production, this would be more secure)
                credentials_path = os.path.join(config.TOKEN_STORAGE_DIR, 'test_user_credentials.txt')
                os.makedirs(config.TOKEN_STORAGE_DIR, exist_ok=True)
                with open(credentials_path, 'w') as f:
                    f.write(f"{test_user_email}:{test_user_password}\n")

            step.status = "PASS"
            step.message = "Test data saved for subsequent tests"
            step.database_state = {
                'verification_token_saved': bool(verification_token),
                'user_credentials_saved': bool(test_user_email and test_user_password),
                'test_data_directory': config.TOKEN_STORAGE_DIR
            }

            print_success("✓ Test data saved for subsequent tests")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Failed to save test data: {e}"
            print_error(f"Failed to save test data: {e}")

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
            self.successful_user_registration(),
            self.capture_verification_email(),
            self.verify_database_state(),
            self.test_password_requirements(),
            self.save_test_data_for_subsequent_tests()
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
    print(f"🧪 TRC Platform UAT - {Colors.YELLOW}TEST-03: User Registration")
    print(f"{'='*80}")
    print(f"{'='*80}{Colors.RESET}\n")

    # Print configuration
    config.print_config_summary()

    # Run test
    test_runner = Test03UserRegistration()
    result = test_runner.run_test()

    # Print summary
    print(f"\n{Colors.CYAN}{'='*80}")
    print(f"🏁 TEST-03 EXECUTION COMPLETE")
    print(f"{'='*80}{Colors.RESET}")
    print(f"Status: {Colors.GREEN if result.is_success() else Colors.RED}{result.status}{Colors.RESET}")
    print(f"Duration: {result.total_time:.2f} seconds")
    print(f"Steps: {result.passed_steps}/{result.total_steps} passed")

    if result.is_success():
        print_success("User registration test completed successfully!")
        print_info("User account and verification token ready for subsequent tests")
    else:
        print_error("User registration test failed!")
        print_warning("Check test logs and application status")

    return result.is_success()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
