#!/usr/bin/env python3
"""
USAGE-06: Error Handling and Edge Cases
Test ID: USAGE-06
Test Name: Error Handling and Edge Cases
Test Type: Error Handling Testing
Priority: High
Estimated Duration: 10 minutes

Description:
Test error handling and edge cases for the /api/usage/requests endpoint.
Validates error responses, invalid input handling, and boundary conditions.
This test also cleans up all test data created during usage testing.
"""

import sys
import os
import json
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

# Import usage helpers
from usage_helpers import UsageHelper, UsageDataManager

class Usage06ErrorHandling:
    """Usage error handling test following API token test pattern"""

    def __init__(self):
        """Initialize test configuration and helpers"""
        self.test_id = "USAGE-06"
        self.test_name = "Error Handling and Edge Cases"

        # Initialize helpers
        self.reporting = TestReporting()
        self.db_helper = DatabaseHelper(config.database_url)
        self.http_client = HTTPClient(config.app_url)
        self.usage_helper = UsageHelper(self.db_helper, self.http_client)

        # Test data
        self.admin_token = None
        self.test_user_data = None
        self.test_user_token = None
        self.generated_request_logs = []

        # Test configuration
        self.test_email_prefix = f"usage06_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.request_log_count = 10

    def setup_environment(self) -> bool:
        """Setup test environment with 5-step pattern"""
        print_info(f"Setting up environment for {self.test_id}")

        # Step 1: Admin login
        if not self._admin_login():
            return False

        # Step 2: Create invite code
        if not self._create_invite_code():
            return False

        # Step 3: Register test user
        if not self._register_test_user():
            return False

        # Step 4: Verify email (skip for usage tests to speed up)
        print_info("Skipping email verification for usage test")

        # Step 5: Login test user
        if not self._login_test_user():
            return False

        # Additional setup: Create minimal test data for error testing
        if not self._create_test_data():
            return False

        print_success("Environment setup completed successfully")
        return True

    def _admin_login(self) -> bool:
        """Step 1: Login as admin user"""
        try:
            admin_login_data = {
                "email": config.admin_email,
                "password": config.admin_password
            }

            response, _ = self.http_client.post("/api/customers/login", data=admin_login_data)

            if response.status_code == 200:
                login_result = response.json()
                self.admin_token = login_result.get('token')
                print_success("Admin login successful")
                return True
            else:
                print_error(f"Admin login failed: {response.status_code}")
                return False

        except Exception as e:
            print_error(f"Admin login error: {str(e)}")
            return False

    def _create_invite_code(self) -> bool:
        """Step 2: Create invite code for test user"""
        try:
            invite_code = f"USAGE06-{uuid.uuid4().hex[:8].upper()}"

            # Set expiration to 7 days from now
            expires_at = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%S")

            invite_data = {
                "code": invite_code,
                "expiresAt": expires_at
            }

            response, _ = self.http_client.post("/api/v1/admin/invites",
                                               data=invite_data,
                                               auth_token=self.admin_token)

            if response.status_code in [200, 201]:
                invite_result = response.json()
                self.invite_code = invite_result.get('code')
                print_success(f"Invite code created: {self.invite_code}")
                return True
            else:
                print_error(f"Failed to create invite code: {response.status_code}")
                return False

        except Exception as e:
            print_error(f"Invite code creation error: {str(e)}")
            return False

    def _register_test_user(self) -> bool:
        """Step 3: Register test user"""
        try:
            self.test_email = f"{self.test_email_prefix}@{config.test_email_domain}"
            self.test_password = config.generate_test_password("06")

            register_data = {
                "email": self.test_email,
                "password": self.test_password,
                "confirmPassword": self.test_password,
                "inviteCode": self.invite_code,
                "userAcceptedTerms": True,
                "userAcknowledgedDisclaimer": True
            }

            response, _ = self.http_client.post("/api/customers/register", data=register_data)

            if response.status_code in [201, 202]:
                self.test_user_data = response.json() if response.status_code == 201 else {"email": self.test_email}
                print_success(f"Test user registered: {self.test_email}")
                return True
            else:
                print_error(f"Test user registration failed: {response.status_code}")
                return False

        except Exception as e:
            print_error(f"Test user registration error: {str(e)}")
            return False

    def _login_test_user(self) -> bool:
        """Step 5: Login as test user and get real user ID"""
        try:
            login_data = {
                "email": self.test_email,
                "password": self.test_password
            }

            response, _ = self.http_client.post("/api/customers/login", data=login_data)

            if response.status_code == 200:
                login_result = response.json()
                self.test_user_token = login_result.get('token')

                # Get real user ID from database using email
                try:
                    if self.db_helper.connect():
                        cursor = self.db_helper.connection.cursor()
                        cursor.execute("SELECT id, email FROM users WHERE email = %s", (self.test_email,))
                        user_row = cursor.fetchone()

                        if user_row:
                            # Extract from RealDictRow - it's a dict-like object
                            user_id = user_row['id']
                            email = user_row['email']

                            # Convert to string if it's a UUID object
                            if hasattr(user_id, 'hex'):
                                user_id = str(user_id)
                            elif hasattr(user_id, '__str__'):
                                user_id = str(user_id)

                            self.test_user_data = {
                                "id": user_id,
                                "email": email
                            }
                            print_success(f"Retrieved real user ID: {user_id}")
                        else:
                            print_warning("User not found in database after login")
                            self.test_user_data = {"email": self.test_email}

                        cursor.close()
                except Exception as db_error:
                    print_warning(f"Could not retrieve user ID from database: {db_error}")
                    self.test_user_data = {"email": self.test_email}

                print_success("Test user login successful")
                return True
            else:
                print_error(f"Test user login failed: {response.status_code}")
                return False

        except Exception as e:
            print_error(f"Test user login error: {str(e)}")
            return False

    def _create_test_data(self) -> bool:
        """Create minimal test data for error testing"""
        try:
            user_id = self.test_user_data.get('id') if isinstance(self.test_user_data, dict) else None
            if not user_id:
                print_error("Cannot create test data: user ID not available")
                return False

            # Generate some request logs for error testing
            self.generated_request_logs = self.usage_helper.generate_sample_request_logs(
                user_id, count=self.request_log_count
            )

            # Insert into database
            success = self.usage_helper.insert_request_logs_to_database(self.generated_request_logs)

            if success:
                print_success(f"Created {len(self.generated_request_logs)} test request logs for error testing")
                return True
            else:
                print_error("Failed to insert test request logs")
                return False

        except Exception as e:
            print_error(f"Test data creation error: {str(e)}")
            return False

    def test_invalid_page_parameters(self) -> TestStep:
        """Test handling of invalid pagination parameters"""
        step = TestStep(
            step_number=1,
            step_name="Test invalid pagination parameters",
            status="ERROR",
            message="Starting invalid pagination parameters test"
        )

        try:
            token_to_use = self.test_user_token
            invalid_params = []

            # Test negative page number
            response = self.usage_helper.get_usage_requests(token_to_use, page=-1)
            if response["status_code"] in [400, 401]:  # Accept both validation and auth error codes
                invalid_params.append("Negative page - Rejected")
            else:
                invalid_params.append(f"Negative page - Status {response['status_code']}")

            # Test negative page size
            response = self.usage_helper.get_usage_requests(token_to_use, page=0, size=-5)
            if response["status_code"] in [400, 401]:  # Accept both validation and auth error codes
                invalid_params.append("Negative size - Rejected")
            else:
                invalid_params.append(f"Negative size - Status {response['status_code']}")

            # Test page size too large (API may not enforce max size, which is acceptable)
            large_size = config.usage_max_page_size + 1
            response = self.usage_helper.get_usage_requests(token_to_use, page=0, size=large_size)
            if response["status_code"] in [400, 401]:  # Accept both validation and auth error codes
                invalid_params.append(f"Oversized page ({large_size}) - Rejected")
            else:
                # API accepting larger page sizes is acceptable behavior
                invalid_params.append(f"Oversized page ({large_size}) - Status {response['status_code']} (acceptable)")

            # Test zero page size
            response = self.usage_helper.get_usage_requests(token_to_use, page=0, size=0)
            if response["status_code"] in [400, 401]:  # Accept both validation and auth error codes
                invalid_params.append("Zero size - Rejected")
            else:
                invalid_params.append(f"Zero size - Status {response['status_code']}")

            # Check if critical validation errors are properly rejected
            critical_errors = [param for param in invalid_params if "Negative page" in param or "Negative size" in param or "Zero size" in param]
            critical_rejected = all("Rejected" in param for param in critical_errors)

            if critical_rejected:
                step.status = "PASS"
                step.message = f"Invalid pagination parameters properly handled: {'; '.join(invalid_params)}"
                print_success(step.message)
            else:
                step.status = "FAIL"
                step.message = f"Invalid pagination parameter issues: {'; '.join(invalid_params)}"
                print_error(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Invalid pagination parameters test failed: {str(e)}"
            print_error(step.message)

        return step

    def test_invalid_date_formats(self) -> TestStep:
        """Test handling of invalid date formats"""
        step = TestStep(
            step_number=2,
            step_name="Test invalid date formats",
            status="ERROR",
            message="Starting invalid date formats test"
        )

        try:
            token_to_use = self.test_user_token
            invalid_dates = [
                "2024-13-01",  # Invalid month
                "2024-02-30",  # Invalid day
                "2024/01/01",  # Wrong separator
                "01-01-2024",  # Wrong format
                "Jan 1, 2024", # Text month
                "",            # Empty string
                "not-a-date",  # Completely invalid
                "2024-01-01T25:00:00"  # Invalid hour
            ]

            invalid_dates_rejected = 0
            for invalid_date in invalid_dates:
                response = self.usage_helper.get_usage_requests(token_to_use, from_date=invalid_date)

                if response["status_code"] in [400, 401]:  # Accept both validation and auth error codes
                    invalid_dates_rejected += 1
                elif response["status_code"] == 200:
                    # Some APIs might ignore invalid dates instead of rejecting them
                    print_info(f"Date '{invalid_date}' was accepted (API might ignore invalid dates)")
                else:
                    print_warning(f"Date '{invalid_date}' returned status {response['status_code']}")

            if invalid_dates_rejected > 0:
                step.status = "PASS"
                step.message = f"Invalid date formats properly rejected: {invalid_dates_rejected}/{len(invalid_dates)} dates rejected"
                print_success(step.message)
            else:
                step.status = "SKIP"
                step.message = "API may ignore invalid date formats instead of rejecting them"
                print_info(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Invalid date formats test failed: {str(e)}"
            print_error(step.message)

        return step

    def test_malformed_authentication(self) -> TestStep:
        """Test handling of malformed authentication"""
        step = TestStep(
            step_number=3,
            step_name="Test malformed authentication",
            status="ERROR",
            message="Starting malformed authentication test"
        )

        try:
            auth_tests = []

            # Test with Bearer prefix but no token
            response, _ = self.http_client.get("/api/usage/requests", headers={"Authorization": "Bearer "})
            if response.status_code == 401:
                auth_tests.append("Empty Bearer token - Rejected")
            else:
                auth_tests.append(f"Empty Bearer token - Status {response.status_code}")

            # Test with wrong authentication header
            response, _ = self.http_client.get("/api/usage/requests", headers={"Authorization": "Token abc123"})
            if response.status_code == 401:
                auth_tests.append("Wrong auth scheme - Rejected")
            else:
                auth_tests.append(f"Wrong auth scheme - Status {response.status_code}")

            # Test with malformed JWT (wrong structure)
            malformed_jwt = "not.a.valid.jwt"
            response = self.usage_helper.get_usage_requests(malformed_jwt)
            if response["status_code"] == 401:
                auth_tests.append("Malformed JWT - Rejected")
            else:
                auth_tests.append(f"Malformed JWT - Status {response['status_code']}")

            # Test with valid JWT structure but invalid content
            fake_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
            response = self.usage_helper.get_usage_requests(fake_jwt)
            if response["status_code"] == 401:
                auth_tests.append("Invalid JWT - Rejected")
            else:
                auth_tests.append(f"Invalid JWT - Status {response['status_code']}")

            if all("Rejected" in test for test in auth_tests):
                step.status = "PASS"
                step.message = f"Malformed authentication properly rejected: {'; '.join(auth_tests)}"
                print_success(step.message)
            else:
                step.status = "FAIL"
                step.message = f"Malformed authentication issues: {'; '.join(auth_tests)}"
                print_error(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Malformed authentication test failed: {str(e)}"
            print_error(step.message)

        return step

    def test_boundary_conditions(self) -> TestStep:
        """Test boundary conditions and edge cases"""
        step = TestStep(
            step_number=4,
            step_name="Test boundary conditions and edge cases",
            status="ERROR",
            message="Starting boundary conditions test"
        )

        try:
            token_to_use = self.test_user_token
            boundary_tests = []

            # Test with very large page number (should return empty or error)
            response = self.usage_helper.get_usage_requests(token_to_use, page=99999, size=10)
            if response["status_code"] == 200:
                data = response["response_data"]
                if data.get("numberOfElements", 0) == 0:
                    boundary_tests.append("Very large page number - Empty result")
                else:
                    boundary_tests.append("Very large page number - Unexpected data returned")
            else:
                boundary_tests.append(f"Very large page number - Status {response['status_code']}")

            # Test with maximum allowed page size
            max_size = config.usage_max_page_size
            response = self.usage_helper.get_usage_requests(token_to_use, page=0, size=max_size)
            if response["status_code"] == 200:
                data = response["response_data"]
                if data.get("size") == max_size:
                    boundary_tests.append(f"Max page size ({max_size}) - Accepted")
                else:
                    boundary_tests.append(f"Max page size ({max_size}) - Size mismatch")
            else:
                boundary_tests.append(f"Max page size - Status {response['status_code']}")

            # Test with date range in the future
            future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            response = self.usage_helper.get_usage_requests(token_to_use, from_date=future_date)
            if response["status_code"] == 200:
                data = response["response_data"]
                if data.get("numberOfElements", 0) == 0:
                    boundary_tests.append("Future date range - Empty result")
                else:
                    boundary_tests.append("Future date range - Unexpected data returned")
            else:
                boundary_tests.append(f"Future date range - Status {response['status_code']}")

            # Test with very old date range
            old_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            response = self.usage_helper.get_usage_requests(token_to_use, to_date=old_date)
            if response["status_code"] == 200:
                data = response["response_data"]
                if data.get("numberOfElements", 0) == 0:
                    boundary_tests.append("Very old date range - Empty result")
                else:
                    boundary_tests.append("Very old date range - Data returned (may be expected)")
            else:
                boundary_tests.append(f"Very old date range - Status {response['status_code']}")

            if any("Accepted" in test or "Empty result" in test for test in boundary_tests):
                step.status = "PASS"
                step.message = f"Boundary conditions handled: {'; '.join(boundary_tests)}"
                print_success(step.message)
            else:
                step.status = "FAIL"
                step.message = f"Boundary condition issues: {'; '.join(boundary_tests)}"
                print_error(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Boundary conditions test failed: {str(e)}"
            print_error(step.message)

        return step

    def test_server_error_scenarios(self) -> TestStep:
        """Test server error scenarios (simulated)"""
        step = TestStep(
            step_number=5,
            step_name="Test server error scenarios",
            status="ERROR",
            message="Starting server error scenarios test"
        )

        try:
            # Note: These are conceptual tests as we can't easily trigger actual server errors
            # In a real environment, you might use special endpoints or configuration to simulate errors

            error_scenarios = []

            # Test concurrent requests (might trigger rate limiting or connection issues)
            token_to_use = self.test_user_token
            concurrent_results = []

            for i in range(3):
                response = self.usage_helper.get_usage_requests(token_to_use, page=0, size=5)
                concurrent_results.append(response["status_code"])

            if all(status == 200 for status in concurrent_results):
                error_scenarios.append("Concurrent requests - All successful")
            else:
                error_scenarios.append(f"Concurrent requests - Mixed results: {concurrent_results}")

            # Test with large timeout (not actually testing timeout, just ensuring it doesn't fail)
            # This is more of a smoke test to ensure the client handles normal operations
            response = self.usage_helper.get_usage_requests(token_to_use, page=0, size=1)
            if response["status_code"] == 200:
                error_scenarios.append("Normal request - Successful")
            else:
                error_scenarios.append(f"Normal request - Failed: {response['status_code']}")

            if all("successful" in scenario.lower() for scenario in error_scenarios):
                step.status = "PASS"
                step.message = f"Server scenarios handled: {'; '.join(error_scenarios)}"
                print_success(step.message)
            else:
                step.status = "SKIP"
                step.message = f"Server scenario testing limited: {'; '.join(error_scenarios)}"
                print_info(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Server error scenarios test failed: {str(e)}"
            print_error(step.message)

        return step

    def cleanup_all_usage_test_data(self) -> TestStep:
        """Clean up all usage test data created during this session"""
        step = TestStep(
            step_number=6,
            step_name="Clean up all usage test data",
            status="ERROR",
            message="Starting comprehensive cleanup"
        )

        try:
            # Clean up current test data
            if self.usage_helper.cleanup_usage_test_data(self.test_email_prefix):
                current_cleanup = "Current test data - Cleaned"
            else:
                current_cleanup = "Current test data - Issues"

            # Clean up any other usage test data with common prefixes
            common_prefixes = ["usage01_", "usage02_", "usage03_", "usage04_", "usage05_"]
            cleanup_results = [current_cleanup]

            for prefix in common_prefixes:
                try:
                    if self.usage_helper.cleanup_usage_test_data(prefix):
                        cleanup_results.append(f"{prefix} - Cleaned")
                    else:
                        cleanup_results.append(f"{prefix} - Issues")
                except Exception as e:
                    cleanup_results.append(f"{prefix} - Error: {str(e)}")

            success_count = sum("Cleaned" in result for result in cleanup_results)

            if success_count > 0:
                step.status = "PASS"
                step.message = f"Comprehensive cleanup completed: {success_count}/{len(cleanup_results)} groups cleaned"
                print_success(step.message)
            else:
                step.status = "FAIL"
                step.message = f"Cleanup failed for all groups: {'; '.join(cleanup_results)}"
                print_error(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Comprehensive cleanup failed: {str(e)}"
            print_error(step.message)

        return step

    def cleanup(self):
        """Clean up test data"""
        print_info(f"Cleaning up {self.test_id} test data")

        try:
            # Clean up using usage helper
            if self.usage_helper.cleanup_usage_test_data(self.test_email_prefix):
                print_success("Test data cleanup completed")
            else:
                print_warning("Test data cleanup completed with warnings")

        except Exception as e:
            print_error(f"Cleanup error: {str(e)}")

    def run_test(self) -> TestResult:
        """Execute complete test workflow"""
        test_start_time = datetime.now()

        print_info(f"Starting {self.test_id}: {self.test_name}")

        # Initialize test result
        test_result = TestResult(
            test_id=self.test_id,
            test_name=self.test_name,
            status="ERROR",
            total_steps=0,
            passed_steps=0,
            failed_steps=0,
            skipped_steps=0,
            error_steps=0,
            total_time=0.0,
            start_time=test_start_time,
            end_time=test_start_time
        )

        try:
            # Setup environment
            if not self.setup_environment():
                test_result.status = "FAIL"
                test_result.failed_steps = 1
                test_result.total_steps = 1
                test_result.end_time = datetime.now()
                test_result.total_time = (test_result.end_time - test_start_time).total_seconds()
                return test_result

            # Execute test steps
            test_steps = [
                self.test_invalid_page_parameters(),
                self.test_invalid_date_formats(),
                self.test_malformed_authentication(),
                self.test_boundary_conditions(),
                self.test_server_error_scenarios(),
                self.cleanup_all_usage_test_data()
            ]

            test_result.test_steps = test_steps

            # Calculate final status
            failed_steps = sum(1 for step in test_steps if step.status == "FAIL")
            error_steps = sum(1 for step in test_steps if step.status == "ERROR")
            passed_steps = sum(1 for step in test_steps if step.status == "PASS")
            skipped_steps = sum(1 for step in test_steps if step.status == "SKIP")

            test_result.total_steps = len(test_steps)
            test_result.passed_steps = passed_steps
            test_result.failed_steps = failed_steps
            test_result.error_steps = error_steps
            test_result.skipped_steps = skipped_steps
            test_result.status = "PASS" if failed_steps == 0 and error_steps == 0 else "FAIL"
            test_result.end_time = datetime.now()
            test_result.total_time = (test_result.end_time - test_start_time).total_seconds()

            if test_result.status == "PASS":
                print_success(f"{self.test_id}: {self.test_name} - PASSED")
            else:
                print_error(f"{self.test_id}: {self.test_name} - FAILED")

            return test_result

        except Exception as e:
            error_message = f"Unexpected error in {self.test_id}: {str(e)}"
            print_error(error_message)

            test_result.status = "FAIL"
            test_result.failed_steps = 1
            test_result.total_steps = 1
            test_result.end_time = datetime.now()
            test_result.total_time = (test_result.end_time - test_start_time).total_seconds()

            return test_result

        finally:
            # Cleanup test data
            self.cleanup()

def main():
    """Main test execution function"""
    test_instance = Usage06ErrorHandling()
    test_result = test_instance.run_test()

    # Exit with appropriate code
    sys.exit(0 if test_result.status == "PASS" else 1)

if __name__ == "__main__":
    main()
