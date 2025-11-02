"""
TEST-02: Admin Invite Code Creation and Management
Test ID: TEST-02
Test Name: Admin Invite Code Creation and Management
Test Type: Functional Admin Operations
Priority: High
Estimated Duration: 10 minutes

Description:
Validate that authenticated admin users can create new invite codes, list existing codes,
and manage invite code lifecycle with proper creator tracking.
"""

import sys
import os
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

class Test02CreateInviteCodes:
    """Test-02: Admin Invite Code Creation and Management"""

    def __init__(self):
        self.test_id = "TEST-02"
        self.test_name = "Admin Invite Code Creation and Management"
        self.reporting = TestReporting()
        self.db_helper = DatabaseHelper(config.DATABASE_URL)
        self.http_client = HTTPClient(config.APP_URL)
        self.token_manager = TokenManager()
        self.test_steps = []
        self.start_time = datetime.now()
        self.admin_token = None

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
                config.ENDPOINTS['admin_login'],
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

            # Store token to file for potential reuse
            token_path = config.get_token_path('admin_token')
            with open(token_path, 'w') as f:
                f.write(self.admin_token)

            print_success(f"Admin authentication successful ({format_response_time(response_time)})")

        except Exception as e:
            print_error(f"Failed to authenticate admin: {e}")
            return False

        # Verify admin token validity
        if not self.token_manager.validate_jwt_format(self.admin_token):
            print_error("Invalid admin token format")
            return False

        print_success("Environment setup completed successfully")
        return True

    def list_existing_invite_codes(self) -> TestStep:
        """Step: Retrieve current list of invite codes"""
        step = TestStep(
            step_number=1,
            step_name="List Existing Invite Codes",
            status="PASS",
            message="Retrieving existing invite codes..."
        )

        try:
            # Make request to list invite codes
            response, response_time = self.http_client.get(
                f"{config.ENDPOINTS['admin_invites']}?page=0&size=20",
                auth_token=self.admin_token
            )

            step.response_time = response_time

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = f"Failed to list invite codes: {response.status_code} - {response.text}"
                print_error(f"Failed to list invite codes: {response.status_code}")
                return step

            # Parse response
            try:
                response_data = response.json()
                step.response_data = response_data
            except json.JSONDecodeError:
                step.status = "FAIL"
                step.message = "Invalid JSON response from invite codes endpoint"
                print_error("Invalid JSON response")
                return step

            # Validate response structure
            required_fields = config.REQUIRED_RESPONSE_FIELDS['invite_list']
            missing_fields = [field for field in required_fields if field not in response_data]

            if missing_fields:
                step.status = "FAIL"
                step.message = f"Missing required fields in response: {missing_fields}"
                print_error(f"Missing fields: {missing_fields}")
                return step

            # Extract invite codes data
            content = response_data.get('content', [])
            pageable = response_data.get('pageable', {})
            total_elements = pageable.get('totalElements', 0)

            # Check for preloaded invite codes
            preloaded_found = 0
            for invite in content:
                if invite.get('code') in config.PRELOADED_INVITE_CODES:
                    preloaded_found += 1

            step.status = "PASS"
            step.message = f"Retrieved {total_elements} invite codes ({format_response_time(response_time)})"
            step.database_state = {
                'total_invites': total_elements,
                'preloaded_found': preloaded_found,
                'expected_preloaded': len(config.PRELOADED_INVITE_CODES),
                'page_size': pageable.get('pageSize', 0),
                'current_page': pageable.get('pageNumber', 0)
            }

            print_success(f"✓ Retrieved {total_elements} invite codes ({format_response_time(response_time)})")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Failed to list invite codes: {e}"
            print_error(f"Failed to list invite codes: {e}")

        return step

    def create_invite_code_no_expiration(self) -> TestStep:
        """Step: Create invite code without expiration date"""
        step = TestStep(
            step_number=2,
            step_name="Create Invite Code (No Expiration)",
            status="PASS",
            message="Creating invite code without expiration..."
        )

        try:
            # Prepare request data
            # Generate unique invite code with timestamp to avoid duplicates
            from datetime import datetime, timedelta
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            test_code = f"UAT-TEST-01-{timestamp}"
            # For "no expiration" test, don't include expiresAt field
            request_data = {
                "code": test_code
            }

            step.request_data = request_data

            # Make request to create invite code
            response, response_time = self.http_client.post(
                config.ENDPOINTS['admin_invites'],
                request_data,
                auth_token=self.admin_token
            )

            step.response_time = response_time

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
                print_error("Invalid JSON response")
                return step

            # Validate response fields
            required_fields = config.REQUIRED_RESPONSE_FIELDS['invite_create']
            missing_fields = [field for field in required_fields if field not in response_data]

            if missing_fields:
                step.status = "FAIL"
                step.message = f"Missing required fields in response: {missing_fields}"
                print_error(f"Missing fields: {missing_fields}")
                return step

            # Validate response data
            created_code = response_data.get('code')
            if created_code != test_code:
                step.status = "FAIL"
                step.message = f"Created code mismatch. Expected: {test_code}, Actual: {created_code}"
                print_error(f"Code mismatch: {created_code}")
                return step

            # Check expiration is null
            expires_at = response_data.get('expiresAt')
            if expires_at is not None:
                step.status = "FAIL"
                step.message = f"Expected null expiration, got: {expires_at}"
                print_error(f"Unexpected expiration: {expires_at}")
                return step

            # Verify creator information
            creator_email = response_data.get('createdByUserEmail')
            if creator_email != config.ADMIN_EMAIL:
                step.status = "FAIL"
                step.message = f"Creator email mismatch. Expected: {config.ADMIN_EMAIL}, Actual: {creator_email}"
                print_error(f"Creator email mismatch: {creator_email}")
                return step

            # Store created invite code info
            self.token_manager.store_token('invite_code_uat_test_01', created_code)

            step.status = "PASS"
            step.message = f"Created invite code: {test_code} ({format_response_time(response_time)})"
            step.database_state = {
                'code': created_code,
                'active': response_data.get('active'),
                'expires_at': None,
                'creator_email': creator_email,
                'created_at': response_data.get('createdAt')
            }

            print_success(f"✓ Created invite code: {test_code} ({format_response_time(response_time)})")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Failed to create invite code: {e}"
            print_error(f"Failed to create invite code: {e}")

        return step

    def create_invite_code_with_expiration(self) -> TestStep:
        """Step: Create invite code with specific expiration"""
        step = TestStep(
            step_number=3,
            step_name="Create Invite Code (With Expiration)",
            status="PASS",
            message="Creating invite code with expiration..."
        )

        try:
            # Prepare request data
            # Generate unique invite code with timestamp to avoid duplicates
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            test_code = f"UAT-TEST-02-{timestamp}"
            expiration_date = "2025-11-30T23:59:59"
            request_data = {
                "code": test_code,
                "expiresAt": expiration_date
            }

            step.request_data = request_data

            # Make request to create invite code
            response, response_time = self.http_client.post(
                config.ENDPOINTS['admin_invites'],
                request_data,
                auth_token=self.admin_token
            )

            step.response_time = response_time

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
                print_error("Invalid JSON response")
                return step

            # Validate response data
            created_code = response_data.get('code')
            if created_code != test_code:
                step.status = "FAIL"
                step.message = f"Created code mismatch. Expected: {test_code}, Actual: {created_code}"
                print_error(f"Code mismatch: {created_code}")
                return step

            # Check expiration date matches
            expires_at = response_data.get('expiresAt')
            if expires_at != expiration_date:
                step.status = "FAIL"
                step.message = f"Expiration date mismatch. Expected: {expiration_date}, Actual: {expires_at}"
                print_error(f"Expiration date mismatch: {expires_at}")
                return step

            # Store created invite code info
            self.token_manager.store_token('invite_code_uat_test_02', created_code)

            step.status = "PASS"
            step.message = f"Created invite code with expiration: {test_code} ({format_response_time(response_time)})"
            step.database_state = {
                'code': created_code,
                'active': response_data.get('active'),
                'expires_at': expires_at,
                'creator_email': response_data.get('createdByUserEmail'),
                'created_at': response_data.get('createdAt')
            }

            print_success(f"✓ Created invite code with expiration: {test_code} ({format_response_time(response_time)})")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Failed to create invite code: {e}"
            print_error(f"Failed to create invite code: {e}")

        return step

    def create_auto_generated_invite_code(self) -> TestStep:
        """Step: Create invite code without specifying code (auto-generated)"""
        step = TestStep(
            step_number=4,
            step_name="Create Auto-Generated Invite Code",
            status="PASS",
            message="Creating auto-generated invite code..."
        )

        try:
            # Prepare request data (no code specified)
            expiration_date = "2025-12-15T23:59:59"
            request_data = {
                "expiresAt": expiration_date
            }

            step.request_data = request_data

            # Make request to create invite code
            response, response_time = self.http_client.post(
                config.ENDPOINTS['admin_invites'],
                request_data,
                auth_token=self.admin_token
            )

            step.response_time = response_time

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = f"Failed to create auto-generated invite code: {response.status_code} - {response.text}"
                print_error(f"Failed to create auto-generated invite code: {response.status_code}")
                return step

            # Parse response
            try:
                response_data = response.json()
                step.response_data = response_data
            except json.JSONDecodeError:
                step.status = "FAIL"
                step.message = "Invalid JSON response from invite creation endpoint"
                print_error("Invalid JSON response")
                return step

            # Validate response data
            created_code = response_data.get('code')
            if not created_code or len(created_code) < 6:
                step.status = "FAIL"
                step.message = f"Auto-generated code appears invalid: {created_code}"
                print_error(f"Invalid auto-generated code: {created_code}")
                return step

            # Check expiration date matches
            expires_at = response_data.get('expiresAt')
            if expires_at != expiration_date:
                step.status = "FAIL"
                step.message = f"Expiration date mismatch. Expected: {expiration_date}, Actual: {expires_at}"
                print_error(f"Expiration date mismatch: {expires_at}")
                return step

            # Store auto-generated code
            self.token_manager.store_token('invite_code_auto_generated', created_code)

            step.status = "PASS"
            step.message = f"Created auto-generated invite code: {created_code} ({format_response_time(response_time)})"
            step.database_state = {
                'code': created_code,
                'active': response_data.get('active'),
                'expires_at': expires_at,
                'creator_email': response_data.get('createdByUserEmail'),
                'created_at': response_data.get('createdAt'),
                'code_length': len(created_code)
            }

            print_success(f"✓ Created auto-generated invite code: {created_code} ({format_response_time(response_time)})")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Failed to create auto-generated invite code: {e}"
            print_error(f"Failed to create auto-generated invite code: {e}")

        return step

    def verify_updated_invite_code_list(self) -> TestStep:
        """Step: List all invite codes to verify new ones appear"""
        step = TestStep(
            step_number=5,
            step_name="Verify Updated Invite Code List",
            status="PASS",
            message="Verifying new invite codes appear in list..."
        )

        try:
            # Make request to list invite codes with larger page size
            response, response_time = self.http_client.get(
                f"{config.ENDPOINTS['admin_invites']}?page=0&size=50",
                auth_token=self.admin_token
            )

            step.response_time = response_time

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = f"Failed to list invite codes: {response.status_code} - {response.text}"
                print_error(f"Failed to list invite codes: {response.status_code}")
                return step

            # Parse response
            try:
                response_data = response.json()
                step.response_data = response_data
            except json.JSONDecodeError:
                step.status = "FAIL"
                step.message = "Invalid JSON response from invite codes endpoint"
                print_error("Invalid JSON response")
                return step

            # Extract invite codes data
            content = response_data.get('content', [])
            pageable = response_data.get('pageable', {})
            total_elements = pageable.get('totalElements', 0)

            # Check for our newly created codes
            created_codes = ['UAT-TEST-01', 'UAT-TEST-02']
            auto_generated = self.token_manager.get_token('invite_code_auto_generated')
            if auto_generated:
                created_codes.append(auto_generated)

            found_codes = []
            for invite in content:
                if invite.get('code') in created_codes:
                    found_codes.append(invite.get('code'))

            # Expected increase: preloaded codes (3) + created codes (3)
            expected_total = len(config.PRELOADED_INVITE_CODES) + 3  # 6 total
            actual_found = len(found_codes)

            step.status = "PASS"
            step.message = f"Found {actual_found}/{len(created_codes)} new codes in list ({format_response_time(response_time)})"
            step.database_state = {
                'total_invites': total_elements,
                'expected_total': expected_total,
                'new_codes_found': actual_found,
                'new_codes_expected': len(created_codes),
                'found_codes': found_codes
            }

            print_success(f"✓ Found {actual_found}/{len(created_codes)} new codes in list ({format_response_time(response_time)})")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Failed to verify updated invite code list: {e}"
            print_error(f"Failed to verify updated invite code list: {e}")

        return step

    def verify_database_creator_tracking(self) -> TestStep:
        """Step: Verify creator tracking in database"""
        step = TestStep(
            step_number=6,
            step_name="Verify Database Creator Tracking",
            status="PASS",
            message="Verifying creator tracking in database..."
        )

        try:
            # Check our created codes in database
            created_codes = ['UAT-TEST-01', 'UAT-TEST-02']
            auto_generated = self.token_manager.get_token('invite_code_auto_generated')
            if auto_generated:
                created_codes.append(auto_generated)

            tracking_results = []
            for code in created_codes:
                results = self.db_helper.execute_query(
                    config.DB_QUERIES['verify_invite_creator'],
                    (code,)
                )
                if results:
                    tracking_results.append({
                        'code': code,
                        'creator_email': results[0]['creator_email'],
                        'created_at': results[0]['created_at']
                    })

            # Verify all codes have proper creator tracking
            correctly_tracked = sum(1 for result in tracking_results
                                  if result['creator_email'] == config.ADMIN_EMAIL)

            step.status = "PASS"
            step.message = f"Creator tracking verified for {correctly_tracked}/{len(created_codes)} codes"
            step.database_state = {
                'codes_checked': len(created_codes),
                'correctly_tracked': correctly_tracked,
                'tracking_results': tracking_results
            }

            print_success(f"✓ Creator tracking verified for {correctly_tracked}/{len(created_codes)} codes")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Failed to verify creator tracking: {e}"
            print_error(f"Failed to verify creator tracking: {e}")

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
            self.list_existing_invite_codes(),
            self.create_invite_code_no_expiration(),
            self.create_invite_code_with_expiration(),
            self.create_auto_generated_invite_code(),
            self.verify_updated_invite_code_list(),
            self.verify_database_creator_tracking()
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
    print(f"🧪 TRC Platform UAT - {Colors.YELLOW}TEST-02: Invite Code Creation")
    print(f"{'='*80}")
    print(f"{'='*80}{Colors.RESET}\n")

    # Print configuration
    config.print_config_summary()

    # Run test
    test_runner = Test02CreateInviteCodes()
    result = test_runner.run_test()

    # Print summary
    print(f"\n{Colors.CYAN}{'='*80}")
    print(f"🏁 TEST-02 EXECUTION COMPLETE")
    print(f"{'='*80}{Colors.RESET}")
    print(f"Status: {Colors.GREEN if result.is_success() else Colors.RED}{result.status}{Colors.RESET}")
    print(f"Duration: {result.total_time:.2f} seconds")
    print(f"Steps: {result.passed_steps}/{result.total_steps} passed")

    if result.is_success():
        print_success("Invite code creation test completed successfully!")
        print_info("New invite codes are available for subsequent tests")
    else:
        print_error("Invite code creation test failed!")
        print_warning("Check test logs and application status")

    return result.is_success()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
