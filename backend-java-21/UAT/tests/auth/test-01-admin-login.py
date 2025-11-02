"""
TEST-01: Admin Authentication and Bootstrap Login
Test ID: TEST-01
Test Name: Admin Authentication and Bootstrap Login
Test Type: Functional Authentication
Priority: High
Estimated Duration: 5 minutes

Description:
Validate that the bootstrap super admin user can successfully authenticate
with the system and receive a valid JWT token with admin privileges.
"""

import sys
import os
import jwt
import time
import json
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
    extract_jwt_token, extract_json_field, format_timestamp, format_response_time
)
from auth_helpers import AuthHelper, AuthDataManager
# Configuration will be loaded from framework config

class Test01AdminLogin:
    """Test-01: Admin Authentication"""

    def __init__(self):
        self.test_id = "TEST-01"
        self.test_name = "Admin Authentication and Bootstrap Login"
        self.reporting = TestReporting()
        self.db_helper = DatabaseHelper(config.DATABASE_URL)
        self.http_client = HTTPClient(config.APP_URL)
        self.token_manager = TokenManager()
        self.test_steps = []
        self.start_time = datetime.now()

    def setup_environment(self) -> bool:
        """Setup and verify test environment"""
        print_info("Setting up test environment...")

        # Initialize database connection
        if not self.db_helper.connect():
            print_error("Failed to connect to database")
            return False

        # Verify application health
        try:
            response, response_time = self.http_client.get(config.ENDPOINTS['health'])
            if response.status_code != 200:
                print_error(f"Application health check failed: {response.status_code}")
                return False
            print_success(f"Application health check passed ({format_response_time(response_time)})")
        except Exception as e:
            print_error(f"Failed to connect to application: {e}")
            return False

        print_success("Environment setup completed successfully")
        return True

    def verify_bootstrap_admin_exists(self) -> TestStep:
        """Step: Verify bootstrap admin user exists in database"""
        step = TestStep(
            step_number=1,
            step_name="Verify Bootstrap Admin User Exists",
            status="PASS",
            message="Starting verification..."
        )

        try:
            # Check admin user in database
            print_info(f"DEBUG: Executing query: {config.DB_QUERIES['check_admin_user']}")
            print_info(f"DEBUG: With parameter: {config.ADMIN_EMAIL}")
            admin_users = self.db_helper.execute_query(
                config.DB_QUERIES['check_admin_user'],
                (config.ADMIN_EMAIL,)
            )

            if not admin_users:
                step.status = "FAIL"
                step.message = f"Bootstrap admin user not found: {config.ADMIN_EMAIL}"
                return step

            admin_user = admin_users[0]
            print_info(f"DEBUG: Raw admin_user from database: {admin_user}")
            print_info(f"DEBUG: Admin user type: {type(admin_user)}")
            print_info(f"DEBUG: Admin user keys: {list(admin_user.keys())}")

            expected_id = config.ADMIN_USER_ID
            actual_id = admin_user['id']

            if actual_id != expected_id:
                step.status = "FAIL"
                step.message = f"Admin user ID mismatch. Expected: {expected_id}, Actual: {actual_id}"
                return step

            if not admin_user['is_staff']:
                step.status = "FAIL"
                step.message = f"Admin user is_staff flag is False for: {config.ADMIN_EMAIL}"
                return step

            step.status = "PASS"
            step.message = f"Bootstrap admin user verified: {config.ADMIN_EMAIL}"
            step.database_state = {
                'user_id': admin_user['id'],
                'email': admin_user['email'],
                'is_staff': admin_user['is_staff'],
                'email_verified_at': admin_user['email_verified_at']
            }

            print_success(f"✓ Bootstrap admin user verified: {config.ADMIN_EMAIL}")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Database verification failed: {e}"
            print_error(f"Database verification failed: {e}")

        return step

    def admin_login_authentication(self) -> TestStep:
        """Step: Authenticate with bootstrap admin credentials"""
        step = TestStep(
            step_number=2,
            step_name="Admin Login Authentication",
            status="PASS",
            message="Starting admin authentication..."
        )

        try:
            # Prepare login request
            login_data = {
                "email": config.ADMIN_EMAIL,
                "password": config.ADMIN_PASSWORD
            }

            step.request_data = login_data

            # Make login request
            response, response_time = self.http_client.post(
                config.ENDPOINTS['admin_login'],
                login_data
            )

            step.response_time = response_time

            # Check response status
            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = f"Login failed with status {response.status_code}: {response.text}"
                print_error(f"Login failed: {response.status_code} - {response.text}")
                return step

            # Parse response
            try:
                response_data = response.json()
                step.response_data = response_data
            except json.JSONDecodeError:
                step.status = "FAIL"
                step.message = "Invalid JSON response from login endpoint"
                print_error("Invalid JSON response from login endpoint")
                return step

            # Validate required fields
            required_fields = config.REQUIRED_RESPONSE_FIELDS['login']
            missing_fields = [field for field in required_fields if field not in response_data]

            if missing_fields:
                step.status = "FAIL"
                step.message = f"Missing required fields in response: {missing_fields}"
                print_error(f"Missing required fields: {missing_fields}")
                return step

            # Validate response data
            user_id = response_data['id']
            email = response_data['email']
            token = response_data['token']

            if email != config.ADMIN_EMAIL:
                step.status = "FAIL"
                step.message = f"Email mismatch. Expected: {config.ADMIN_EMAIL}, Actual: {email}"
                print_error(f"Email mismatch: {email}")
                return step

            if user_id != config.ADMIN_USER_ID:
                step.status = "FAIL"
                step.message = f"User ID mismatch. Expected: {config.ADMIN_USER_ID}, Actual: {user_id}"
                print_error(f"User ID mismatch: {user_id}")
                return step

            # Validate JWT token format
            if not self.token_manager.validate_jwt_format(token):
                step.status = "FAIL"
                step.message = "Invalid JWT token format in response"
                print_error("Invalid JWT token format")
                return step

            # Store token for later use (in-memory only)
            self.token_manager.store_token('admin', token)

            step.status = "PASS"
            step.message = f"Admin authentication successful ({format_response_time(response_time)})"
            step.database_state = {
                'user_id': user_id,
                'email': email,
                'token_stored': True,
                'token_length': len(token)
            }

            print_success(f"✓ Admin authentication successful ({format_response_time(response_time)})")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Admin authentication failed: {e}"
            print_error(f"Admin authentication failed: {e}")

        return step

    def validate_jwt_token(self) -> TestStep:
        """Step: Verify JWT token is properly formatted and contains expected data"""
        step = TestStep(
            step_number=3,
            step_name="Validate JWT Token",
            status="PASS",
            message="Starting JWT token validation..."
        )

        try:
            # Get stored admin token
            admin_token = self.token_manager.get_token('admin')
            if not admin_token:
                step.status = "FAIL"
                step.message = "Admin token not found in storage"
                print_error("Admin token not found in storage")
                return step

            # Basic format validation
            if not self.token_manager.validate_jwt_format(admin_token):
                step.status = "FAIL"
                step.message = "Admin token has invalid JWT format"
                print_error("Invalid JWT format")
                return step

            # Check token expiration (basic check)
            print_info(f"Validating admin token: {admin_token[:50]}...")
            if self.token_manager.is_token_expired(admin_token):
                step.status = "FAIL"
                step.message = "Admin token is expired"
                print_error("Token is expired")
                return step

            # Try to decode token (without signature verification for structure)
            try:
                decoded = jwt.decode(admin_token, algorithms=[config.JWT_ALGORITHM], options={"verify_signature": False})

                step.response_data = {
                    'decoded_token': decoded
                }

                # Validate token claims
                subject = decoded.get('sub')
                if subject != config.ADMIN_USER_ID:
                    step.status = "FAIL"
                    step.message = f"Token subject mismatch. Expected: {config.ADMIN_USER_ID}, Actual: {subject}"
                    print_error(f"Token subject mismatch: {subject}")
                    return step

                # Check if token has expiration
                exp = decoded.get('exp')
                if not exp:
                    step.status = "FAIL"
                    step.message = "Token missing expiration claim"
                    print_error("Token missing expiration")
                    return step

                # Check if token has issued time
                iat = decoded.get('iat')
                if not iat:
                    step.status = "FAIL"
                    step.message = "Token missing issued-at claim"
                    print_error("Token missing issued-at")
                    return step

                # Validate expiration is reasonable (should be in the future)
                current_time = time.time()
                if exp <= current_time:
                    step.status = "FAIL"
                    step.message = "Token expiration is in the past"
                    print_error("Token expiration is in the past")
                    return step

                # Validate issued time is recent (within last 5 minutes)
                time_diff = current_time - iat
                if time_diff > 300:  # 5 minutes
                    step.status = "WARN"
                    step.message = f"Token issued time is quite old: {time_diff:.0f} seconds ago"
                    print_warning(f"Token issued time is old: {time_diff:.0f} seconds")

            except jwt.DecodeError as e:
                step.status = "FAIL"
                step.message = f"Failed to decode JWT token: {e}"
                print_error(f"Failed to decode JWT: {e}")
                return step

            step.status = "PASS"
            step.message = "JWT token validation successful"
            step.database_state = {
                'token_valid': True,
                'token_subject': subject,
                'token_expires': datetime.fromtimestamp(exp).isoformat(),
                'token_issued': datetime.fromtimestamp(iat).isoformat(),
                'time_until_expiry': f"{(exp - current_time) / 3600:.1f} hours"
            }

            print_success("✓ JWT token validation successful")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"JWT token validation failed: {e}"
            print_error(f"JWT token validation failed: {e}")

        return step

    def test_admin_token_usage(self) -> TestStep:
        """Step: Test token works with a protected admin endpoint"""
        step = TestStep(
            step_number=4,
            step_name="Test Admin Token Usage",
            status="PASS",
            message="Testing admin token with protected endpoint..."
        )

        try:
            # Get stored admin token
            admin_token = self.token_manager.get_token('admin')
            if not admin_token:
                step.status = "FAIL"
                step.message = "Admin token not found for usage test"
                print_error("Admin token not found for usage test")
                return step

            # Test with admin invites endpoint
            response, response_time = self.http_client.get(
                config.ENDPOINTS['admin_invites'],
                auth_token=admin_token
            )

            step.response_time = response_time

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = f"Admin token rejected with status {response.status_code}: {response.text}"
                print_error(f"Admin token rejected: {response.status_code}")
                return step

            # Try to parse response
            try:
                response_data = response.json()
                step.response_data = response_data

                # Validate it's a paginated response
                if 'content' not in response_data or 'pageable' not in response_data:
                    step.status = "FAIL"
                    step.message = "Response doesn't contain expected pagination structure"
                    print_error("Invalid pagination response structure")
                    return step

                invite_count = len(response_data.get('content', []))
                total_elements = response_data.get('pageable', {}).get('totalElements', 0)

            except json.JSONDecodeError:
                step.status = "FAIL"
                step.message = "Invalid JSON response from admin endpoint"
                print_error("Invalid JSON response from admin endpoint")
                return step

            step.status = "PASS"
            step.message = f"Admin token usage test successful ({format_response_time(response_time)})"
            step.database_state = {
                'endpoint_accessible': True,
                'invite_count': invite_count,
                'total_invites': total_elements,
                'response_structure_valid': True
            }

            print_success(f"✓ Admin token usage test successful ({format_response_time(response_time)})")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Admin token usage test failed: {e}"
            print_error(f"Admin token usage test failed: {e}")

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
            self.verify_bootstrap_admin_exists(),
            self.admin_login_authentication(),
            self.validate_jwt_token(),
            self.test_admin_token_usage()
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
    print(f"🧪 TRC Platform UAT - {Colors.YELLOW}TEST-01: Admin Authentication")
    print(f"{'='*80}")
    print(f"{'='*80}{Colors.RESET}\n")

    # Print configuration
    config.print_config_summary()

    # Run test
    test_runner = Test01AdminLogin()
    result = test_runner.run_test()

    # Print summary
    print(f"\n{Colors.CYAN}{'='*80}")
    print(f"🏁 TEST-01 EXECUTION COMPLETE")
    print(f"{'='*80}{Colors.RESET}")
    print(f"Status: {Colors.GREEN if result.is_success() else Colors.RED}{result.status}{Colors.RESET}")
    print(f"Duration: {result.total_time:.2f} seconds")
    print(f"Steps: {result.passed_steps}/{result.total_steps} passed")

    if result.is_success():
        print_success("Admin authentication test completed successfully!")
        print_info("Admin token is available for subsequent tests")
    else:
        print_error("Admin authentication test failed!")
        print_warning("Check test logs and application status")

    return result.is_success()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
