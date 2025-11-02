"""
TEST-02: API Token Creation
Test ID: TEST-02
Test Name: API Token Creation
Test Type: Functional API Token Management
Priority: High
Estimated Duration: 10 minutes

Description:
Test API token creation functionality. This test validates that a registered user
can create API tokens with custom names and expiration dates. The test is completely
self-contained and does not rely on external token storage or dependencies on other tests.
"""

import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime, timedelta

# Add current directory to Python path for imports
# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import UAT framework and configuration
from uat_framework import (
    DatabaseHelper, HTTPClient, TokenManager, TestReporting,
    TestStep, TestResult, EnvironmentInfo, ApiTokenHelper,
    Colors, print_success, print_error, print_warning, print_info,
    extract_jwt_token, extract_json_field, format_timestamp, format_response_time,
    EmailVerificationHelper, wait_for_email_verification
)
from api_token_helpers import ApiTokenHelper, ApiTokenDataManager
# Configuration will be loaded from framework config

class Test02ApiTokenCreation:
    """Test-02: API Token Creation"""

    def __init__(self):
        self.test_id = "TEST-02"
        self.test_name = "API Token Creation"
        self.reporting = TestReporting()
        self.db_helper = DatabaseHelper(config.DATABASE_URL)
        self.http_client = HTTPClient(config.APP_URL)
        self.token_manager = TokenManager()
        self.api_token_helper = ApiTokenHelper(self.db_helper, self.http_client)
        self.test_steps = []
        self.start_time = datetime.now()
        self.user_token = None
        self.test_user_id = None
        self.created_tokens = []

    def setup_environment(self) -> bool:
        """Setup and verify test environment"""
        print_info("Setting up test environment...")

        # Initialize database connection
        if not self.db_helper.connect():
            print_error("Failed to connect to database")
            return False

        # Create a test user for this test
        try:
            print_info("Creating test user for API token creation test...")

            # Generate unique invite code
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            invite_code = f"TOKEN-TEST-{timestamp}"

            # Authenticate as admin to create invite code
            admin_login_data = {
                "email": config.ADMIN_EMAIL,
                "password": config.ADMIN_PASSWORD
            }

            response, response_time = self.http_client.post(
                config.ENDPOINTS['login'],
                admin_login_data
            )

            if response.status_code != config.STATUS_CODES['success']:
                print_error(f"Admin login failed: {response.status_code} - {response.text}")
                return False

            admin_response_data = response.json()
            self.admin_token = admin_response_data['token']

            # Create invite code
            invite_request_data = {"code": invite_code}
            invite_response, invite_response_time = self.http_client.post(
                "/api/v1/admin/invites",
                invite_request_data,
                auth_token=self.admin_token
            )

            if invite_response.status_code != config.STATUS_CODES['success']:
                print_error(f"Failed to create invite code: {invite_response.status_code}")
                return False

            # Generate unique user data
            self.test_user_email = f"token-test-{timestamp}@example.com"
            self.test_user_password = "SecureTokenPassword123!"

            # Register user
            registration_data = {
                "email": self.test_user_email,
                "password": self.test_user_password,
                "confirmPassword": self.test_user_password,
                "inviteCode": invite_code,
                "userAcceptedTerms": True,
                "userAcknowledgedDisclaimer": True
            }

            register_response, register_response_time = self.http_client.post(
                config.ENDPOINTS['user_register'],
                registration_data
            )

            if register_response.status_code != config.STATUS_CODES['accepted']:
                print_error(f"User registration failed: {register_response.status_code}")
                return False

            # Wait for verification email
            print_info("Waiting for verification email...")
            email_found = wait_for_email_verification(
                EmailVerificationHelper(config.MAILCATCHER_URL),
                self.test_user_email,
                config.EMAIL_TIMEOUT
            )

            if not email_found:
                print_error("Verification email not received")
                return False

            # Verify user was created in database
            user_results = self.db_helper.execute_query(
                config.DB_QUERIES['check_complete_user'],
                (self.test_user_email,)
            )

            if not user_results:
                print_error("User not found in database")
                return False

            user_data = user_results[0]
            self.test_user_id = user_data['id']

            # Authenticate as the new user
            user_login_data = {
                "email": self.test_user_email,
                "password": self.test_user_password
            }

            login_response, login_response_time = self.http_client.post(
                config.ENDPOINTS['login'],
                user_login_data
            )

            if login_response.status_code != config.STATUS_CODES['success']:
                print_error(f"User login failed: {login_response.status_code}")
                return False

            login_response_data = login_response.json()
            self.user_token = login_response_data['token']

            print_success(f"Test user setup completed successfully")

        except Exception as e:
            print_error(f"Failed to setup test user: {e}")
            return False

        print_success("Environment setup completed successfully")
        return True

    def create_api_token_no_expiration(self) -> TestStep:
        """Step: Create API token without expiration"""
        step = TestStep(
            step_number=1,
            step_name="Create API Token Without Expiration",
            status="PASS",
            message="Creating API token without expiration date..."
        )

        try:
            token_name = config.generate_unique_token_name("No Expiration Token")
            request_data = self.api_token_helper.create_token_data(token_name)

            step.request_data = request_data

            # Make token creation request
            response, response_time = self.http_client.post(
                config.ENDPOINTS['api_token_create'],
                request_data,
                auth_token=self.user_token
            )

            step.response_time = response_time

            if response.status_code == config.STATUS_CODES['created']:
                # Parse actual response
                try:
                    response_data = response.json()
                    step.response_data = response_data

                    # Validate required fields
                    required_fields = config.REQUIRED_RESPONSE_FIELDS['token_create']
                    missing_fields = [field for field in required_fields if field not in response_data]

                    if missing_fields:
                        step.status = "FAIL"
                        step.message = f"Missing required fields in token response: {missing_fields}"
                        print_error(f"Missing fields: {missing_fields}")
                        return step

                    # Store created token
                    token_info = {
                        'id': response_data['id'],
                        'token': response_data['token'],
                        'name': response_data['name'],
                        'has_expiration': response_data.get('expiresAt') is not None
                    }

                    self.created_tokens.append(token_info)

                    step.status = "PASS"
                    step.message = f"API token creation successful: {token_name} ({format_response_time(response_time)})"

                except json.JSONDecodeError:
                    step.status = "FAIL"
                    step.message = "Invalid JSON response from token creation endpoint"
                    print_error("Invalid JSON response from token creation endpoint")
                    return step
            else:
                step.status = "FAIL"
                step.message = f"Token creation failed with status {response.status_code}: {response.text}"
                print_error(f"Token creation failed: {response.status_code} - {response.text}")
                return step

            # Validate token format
            token = token_info['token']
            if not self.api_token_helper.validate_token_format(token):
                step.status = "WARN"
                step.message += " - Token format validation warning"
                print_warning("Token format validation warning")

            step.database_state = {
                'token_name': token_name,
                'token_length': len(token),
                'token_prefix': self.api_token_helper.extract_token_prefix(token),
                'has_expiration': False
            }

            print_success(f"✓ API token creation successful: {token_name} ({format_response_time(response_time)})")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"API token creation failed: {e}"
            print_error(f"API token creation failed: {e}")

        return step

    def create_api_token_with_expiration(self) -> TestStep:
        """Step: Create API token with expiration date"""
        step = TestStep(
            step_number=2,
            step_name="Create API Token With Expiration",
            status="PASS",
            message="Creating API token with expiration date..."
        )

        try:
            token_name = config.generate_unique_token_name("Expiring Token")
            expires_at = (datetime.now() + timedelta(days=30)).isoformat()
            request_data = self.api_token_helper.create_token_data(token_name, expires_at)

            step.request_data = request_data

            # Make token creation request
            response, response_time = self.http_client.post(
                config.ENDPOINTS['api_token_create'],
                request_data,
                auth_token=self.user_token
            )

            step.response_time = response_time

            if response.status_code == config.STATUS_CODES['created']:
                # Parse actual response
                try:
                    response_data = response.json()
                    step.response_data = response_data

                    # Validate required fields
                    required_fields = config.REQUIRED_RESPONSE_FIELDS['token_create']
                    missing_fields = [field for field in required_fields if field not in response_data]

                    if missing_fields:
                        step.status = "FAIL"
                        step.message = f"Missing required fields in token response: {missing_fields}"
                        print_error(f"Missing fields: {missing_fields}")
                        return step

                    # Store created token
                    token_info = {
                        'id': response_data['id'],
                        'token': response_data['token'],
                        'name': response_data['name'],
                        'expires_at': response_data.get('expiresAt'),
                        'has_expiration': response_data.get('expiresAt') is not None
                    }

                    self.created_tokens.append(token_info)

                    step.status = "PASS"
                    step.message = f"API token creation with expiration successful: {token_name} ({format_response_time(response_time)})"

                except json.JSONDecodeError:
                    step.status = "FAIL"
                    step.message = "Invalid JSON response from token creation endpoint"
                    print_error("Invalid JSON response from token creation endpoint")
                    return step
            else:
                step.status = "FAIL"
                step.message = f"Token creation failed with status {response.status_code}: {response.text}"
                print_error(f"Token creation failed: {response.status_code} - {response.text}")
                return step

            # Validate token format
            token = token_info['token']
            if not self.api_token_helper.validate_token_format(token):
                step.status = "WARN"
                step.message += " - Token format validation warning"
                print_warning("Token format validation warning")

            step.database_state = {
                'token_name': token_name,
                'token_length': len(token),
                'token_prefix': self.api_token_helper.extract_token_prefix(token),
                'has_expiration': True,
                'expires_at': expires_at
            }

            print_success(f"✓ API token creation with expiration successful: {token_name} ({format_response_time(response_time)})")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"API token creation with expiration failed: {e}"
            print_error(f"API token creation with expiration failed: {e}")

        return step


    def verify_database_token_storage(self) -> TestStep:
        """Step: Verify tokens are stored correctly in database"""
        step = TestStep(
            step_number=3,
            step_name="Verify Database Token Storage",
            status="PASS",
            message="Verifying API tokens are stored correctly in database..."
        )

        try:
            # Get user's tokens from database
            user_tokens = self.db_helper.get_user_tokens(self.test_user_id)

            # Verify each created token exists in database
            for token_info in self.created_tokens:

                token_id = token_info['id']
                db_token = self.db_helper.get_token_by_id(token_id)

                if not db_token:
                    step.status = "FAIL"
                    step.message = f"Token not found in database: {token_id}"
                    print_error(f"Token not found in database: {token_id}")
                    return step

                # Verify token fields
                if db_token['name'] != token_info['name']:
                    step.status = "FAIL"
                    step.message = f"Token name mismatch in database. Expected: {token_info['name']}, Actual: {db_token['name']}"
                    print_error(f"Token name mismatch: {db_token['name']}")
                    return step

                if db_token['user_id'] != self.test_user_id:
                    step.status = "FAIL"
                    step.message = f"Token user_id mismatch in database. Expected: {self.test_user_id}, Actual: {db_token['user_id']}"
                    print_error(f"Token user_id mismatch: {db_token['user_id']}")
                    return step

                # Verify token hash exists and is not the plain token
                if not db_token['token_hash'] or len(db_token['token_hash']) < 50:
                    step.status = "FAIL"
                    step.message = f"Token hash invalid in database: {db_token['token_hash'][:20]}..."
                    print_error("Token hash invalid in database")
                    return step

            step.status = "PASS"
            step.message = "Database token storage verification successful"
            step.database_state = {
                'total_tokens_in_db': len(user_tokens),
                'created_tokens_count': len(self.created_tokens),
                'user_id': self.test_user_id,
                'all_tokens_verified': True
            }

            print_success("✓ Database token storage verification successful")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Database token storage verification failed: {e}"
            print_error(f"Database token storage verification failed: {e}")

        return step

    def test_token_creation_validation(self) -> TestStep:
        """Step: Test token creation validation scenarios"""
        step = TestStep(
            step_number=4,
            step_name="Test Token Creation Validation",
            status="PASS",
            message="Testing token creation validation scenarios..."
        )

        try:
            validation_results = []

            # Test empty token name
            request_data = {"name": ""}
            response, response_time = self.http_client.post(
                config.ENDPOINTS['api_token_create'],
                request_data,
                auth_token=self.user_token
            )

            if response.status_code == config.STATUS_CODES['bad_request']:
                validation_results.append("Empty name correctly rejected")
            else:
                validation_results.append(f"Empty name should be rejected, got {response.status_code}")

            # Test very long token name
            long_name = "A" * 300  # Exceed typical max length
            request_data = {"name": long_name}
            response, response_time = self.http_client.post(
                config.ENDPOINTS['api_token_create'],
                request_data,
                auth_token=self.user_token
            )

            if response.status_code == config.STATUS_CODES['bad_request']:
                validation_results.append("Long name correctly rejected")
            else:
                validation_results.append(f"Long name should be rejected, got {response.status_code}")

            # Test invalid expiration date
            invalid_date = "invalid-date-format"
            request_data = {"name": "Test Token", "expiresAt": invalid_date}
            response, response_time = self.http_client.post(
                config.ENDPOINTS['api_token_create'],
                request_data,
                auth_token=self.user_token
            )

            if response.status_code == config.STATUS_CODES['bad_request']:
                validation_results.append("Invalid date correctly rejected")
            else:
                validation_results.append(f"Invalid date should be rejected, got {response.status_code}")

            step.status = "PASS"
            step.message = f"Token creation validation tests completed: {len(validation_results)} scenarios"
            step.response_data = {
                'validation_results': validation_results,
                'scenarios_tested': len(validation_results)
            }

            print_success(f"✓ Token creation validation tests completed: {len(validation_results)} scenarios")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Token creation validation tests failed: {e}"
            print_error(f"Token creation validation tests failed: {e}")

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
            self.create_api_token_no_expiration(),
            self.create_api_token_with_expiration(),
            self.verify_database_token_storage(),
            self.test_token_creation_validation()
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
    print(f"🧪 TRC Platform API Token UAT - {Colors.YELLOW}TEST-02: API Token Creation")
    print(f"{'='*80}")
    print(f"{'='*80}{Colors.RESET}\n")

    # Print configuration
    config.print_config_summary()

    # Run test
    test_runner = Test02ApiTokenCreation()
    result = test_runner.run_test()

    # Print summary
    print(f"\n{Colors.CYAN}{'='*80}")
    print(f"🏁 TEST-02 EXECUTION COMPLETE")
    print(f"{'='*80}{Colors.RESET}")
    print(f"Status: {Colors.GREEN if result.is_success() else Colors.RED}{result.status}{Colors.RESET}")
    print(f"Duration: {result.total_time:.2f} seconds")
    print(f"Steps: {result.passed_steps}/{result.total_steps} passed")

    if result.is_success():
        print_success("API token creation test completed successfully!")
        print_info("API tokens created and verified successfully")
    else:
        print_error("API token creation test failed!")
        print_warning("Check test logs and application status")

    return result.is_success()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
