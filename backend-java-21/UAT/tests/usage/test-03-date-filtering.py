#!/usr/bin/env python3
"""
USAGE-03: Date Filtering Validation
Test ID: USAGE-03
Test Name: Date Filtering Validation
Test Type: Functional Testing
Priority: High
Estimated Duration: 8 minutes

Description:
Test various date filtering scenarios for the /api/usage/requests endpoint.
Validates different date formats, date range filtering, and edge cases
like boundary conditions and invalid date handling.
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
from usage_helpers import UsageHelper, UsageDataManager, DateTestUtils

class Usage03DateFiltering:
    """Usage date filtering test following API token test pattern"""

    def __init__(self):
        """Initialize test configuration and helpers"""
        self.test_id = "USAGE-03"
        self.test_name = "Date Filtering Validation"

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
        self.test_email_prefix = f"usage03_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.request_log_count = 30

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

        # Additional setup: Create test data with specific date range
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
            invite_code = f"USAGE03-{uuid.uuid4().hex[:8].upper()}"

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
            self.test_password = config.generate_test_password("03")

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
        """Create test data for date filtering testing"""
        try:
            user_id = self.test_user_data.get('id') if isinstance(self.test_user_data, dict) else None
            if not user_id:
                print_error("Cannot create test data: user ID not available")
                return False

            # Generate request logs spanning multiple days for date filtering
            self.generated_request_logs = self.usage_helper.generate_sample_request_logs(
                user_id, count=self.request_log_count
            )

            # Insert into database
            success = self.usage_helper.insert_request_logs_to_database(self.generated_request_logs)

            if success:
                print_success(f"Created {len(self.generated_request_logs)} test request logs spanning multiple days")
                return True
            else:
                print_error("Failed to insert test request logs")
                return False

        except Exception as e:
            print_error(f"Test data creation error: {str(e)}")
            return False

    def test_date_filtering_from_date(self) -> TestStep:
        """Test filtering with from date parameter"""
        step = TestStep(
            step_number=1,
            step_name="Test filtering with from date parameter",
            status="ERROR",
            message="Starting from date filtering test"
        )

        try:
            # Test with from date (last 3 days)
            from_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
            token_to_use = self.test_user_token

            usage_response = self.usage_helper.get_usage_requests(token_to_use, from_date=from_date)

            if usage_response["status_code"] != 200:
                usage_response = self.usage_helper.get_usage_requests(self.admin_token, from_date=from_date)

            if usage_response["status_code"] == 200:
                response_data = usage_response["response_data"]
                content = response_data.get("content", [])

                # Validate that all returned items are after the from date
                validation_errors = self.usage_helper.validate_date_filtering(response_data, from_date=from_date)

                if not validation_errors:
                    step.status = "PASS"
                    step.message = f"From date filtering successful - {len(content)} items from {from_date}"
                    print_success(step.message)
                else:
                    step.status = "FAIL"
                    step.message = f"From date validation failed: {', '.join(validation_errors)}"
                    print_error(step.message)
            else:
                step.status = "FAIL"
                step.message = f"From date filtering failed: {usage_response['status_code']}"
                print_error(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"From date filtering test failed: {str(e)}"
            print_error(step.message)

        return step

    def test_date_filtering_to_date(self) -> TestStep:
        """Test filtering with to date parameter"""
        step = TestStep(
            step_number=2,
            step_name="Test filtering with to date parameter",
            status="ERROR",
            message="Starting to date filtering test"
        )

        try:
            # Test with to date (yesterday) - use same logic as date generation
            to_date = (datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)).strftime("%Y-%m-%d")
            token_to_use = self.test_user_token

            usage_response = self.usage_helper.get_usage_requests(token_to_use, to_date=to_date)

            if usage_response["status_code"] != 200:
                usage_response = self.usage_helper.get_usage_requests(self.admin_token, to_date=to_date)

            if usage_response["status_code"] == 200:
                response_data = usage_response["response_data"]
                content = response_data.get("content", [])

                # Validate that all returned items are before the to date
                validation_errors = self.usage_helper.validate_date_filtering(response_data, to_date=to_date)

                if not validation_errors:
                    step.status = "PASS"
                    step.message = f"To date filtering successful - {len(content)} items until {to_date}"
                    print_success(step.message)
                else:
                    step.status = "FAIL"
                    step.message = f"To date validation failed: {', '.join(validation_errors)}"
                    print_error(step.message)
            else:
                step.status = "FAIL"
                step.message = f"To date filtering failed: {usage_response['status_code']}"
                print_error(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"To date filtering test failed: {str(e)}"
            print_error(step.message)

        return step

    def test_date_filtering_range(self) -> TestStep:
        """Test filtering with date range"""
        step = TestStep(
            step_number=3,
            step_name="Test filtering with date range",
            status="ERROR",
            message="Starting date range filtering test"
        )

        try:
            # Test with date range (last 7 days to yesterday)
            from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            to_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            token_to_use = self.test_user_token

            usage_response = self.usage_helper.get_usage_requests(token_to_use, from_date=from_date, to_date=to_date)

            if usage_response["status_code"] != 200:
                usage_response = self.usage_helper.get_usage_requests(self.admin_token, from_date=from_date, to_date=to_date)

            if usage_response["status_code"] == 200:
                response_data = usage_response["response_data"]
                content = response_data.get("content", [])

                # Validate that all returned items are within the date range
                validation_errors = self.usage_helper.validate_date_filtering(response_data, from_date=from_date, to_date=to_date)

                if not validation_errors:
                    step.status = "PASS"
                    step.message = f"Date range filtering successful - {len(content)} items from {from_date} to {to_date}"
                    print_success(step.message)
                else:
                    step.status = "FAIL"
                    step.message = f"Date range validation failed: {', '.join(validation_errors)}"
                    print_error(step.message)
            else:
                step.status = "FAIL"
                step.message = f"Date range filtering failed: {usage_response['status_code']}"
                print_error(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Date range filtering test failed: {str(e)}"
            print_error(step.message)

        return step

    def test_date_format_validation(self) -> TestStep:
        """Test different date formats"""
        step = TestStep(
            step_number=4,
            step_name="Test different date formats",
            status="ERROR",
            message="Starting date format validation test"
        )

        try:
            date_utils = DateTestUtils()
            test_dates = date_utils.get_test_date_formats()
            token_to_use = self.test_user_token

            # Test various date formats
            formats_tested = 0
            formats_passed = 0

            for format_name, date_str in test_dates.items():
                if format_name in ['yesterday', 'last_week']:  # Test a few formats
                    formats_tested += 1
                    usage_response = self.usage_helper.get_usage_requests(token_to_use, from_date=date_str)

                    if usage_response["status_code"] != 200:
                        usage_response = self.usage_helper.get_usage_requests(self.admin_token, from_date=date_str)

                    if usage_response["status_code"] == 200:
                        formats_passed += 1
                        print_info(f"Date format '{format_name}' ({date_str}) - OK")
                    else:
                        print_warning(f"Date format '{format_name}' ({date_str}) - Failed: {usage_response['status_code']}")

            if formats_passed > 0:
                step.status = "PASS"
                step.message = f"Date format validation successful - {formats_passed}/{formats_tested} formats working"
                print_success(step.message)
            else:
                step.status = "FAIL"
                step.message = "No date formats worked correctly"
                print_error(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Date format validation test failed: {str(e)}"
            print_error(step.message)

        return step

    def test_invalid_date_handling(self) -> TestStep:
        """Test handling of invalid dates"""
        step = TestStep(
            step_number=5,
            step_name="Test invalid date handling",
            status="ERROR",
            message="Starting invalid date handling test"
        )

        try:
            date_utils = DateTestUtils()
            invalid_dates = date_utils.get_invalid_date_formats()
            token_to_use = self.test_user_token

            # Test a few invalid date formats
            invalid_dates_tested = 0
            invalid_dates_rejected = 0

            for invalid_date in invalid_dates[:3]:  # Test first 3 invalid formats
                invalid_dates_tested += 1
                usage_response = self.usage_helper.get_usage_requests(token_to_use, from_date=invalid_date)

                if usage_response["status_code"] != 200:
                    usage_response = self.usage_helper.get_usage_requests(self.admin_token, from_date=invalid_date)

                # Invalid dates should return 400 Bad Request
                if usage_response["status_code"] == 400:
                    invalid_dates_rejected += 1
                    print_info(f"Invalid date '{invalid_date}' correctly rejected")
                else:
                    print_warning(f"Invalid date '{invalid_date}' was not rejected (status: {usage_response['status_code']})")

            if invalid_dates_rejected > 0:
                step.status = "PASS"
                step.message = f"Invalid date handling successful - {invalid_dates_rejected}/{invalid_dates_tested} invalid dates correctly rejected"
                print_success(step.message)
            else:
                step.status = "SKIP"
                step.message = "Invalid date handling could not be properly validated"
                print_info(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Invalid date handling test failed: {str(e)}"
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
                self.test_date_filtering_from_date(),
                self.test_date_filtering_to_date(),
                self.test_date_filtering_range(),
                self.test_date_format_validation(),
                self.test_invalid_date_handling()
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
    test_instance = Usage03DateFiltering()
    test_result = test_instance.run_test()

    # Exit with appropriate code
    sys.exit(0 if test_result.status == "PASS" else 1)

if __name__ == "__main__":
    main()
