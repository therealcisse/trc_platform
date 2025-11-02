#!/usr/bin/env python3
"""
USAGE-04: Pagination Testing
Test ID: USAGE-04
Test Name: Pagination Testing
Test Type: Functional Testing
Priority: High
Estimated Duration: 8 minutes

Description:
Test pagination functionality of the /api/usage/requests endpoint including
different page sizes, page numbers, boundary conditions, and pagination metadata.
"""

import sys
import os
import json
import uuid
from pathlib import Path
from datetime import datetime
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

class Usage04Pagination:
    """Usage pagination test following API token test pattern"""

    def __init__(self):
        """Initialize test configuration and helpers"""
        self.test_id = "USAGE-04"
        self.test_name = "Pagination Testing"

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
        self.test_email_prefix = f"usage04_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.request_log_count = 60  # More data for pagination testing

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

        # Additional setup: Create test data for pagination
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
            invite_code = f"USAGE04-{uuid.uuid4().hex[:8].upper()}"

            # Set expiration to 7 days from now
            from datetime import datetime, timedelta
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
            self.test_password = config.generate_test_password("04")

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
        """Create test data for pagination testing"""
        try:
            user_id = self.test_user_data.get('id') if isinstance(self.test_user_data, dict) else None
            if not user_id:
                print_error("Cannot create test data: user ID not available")
                return False

            # Generate more request logs for pagination testing
            self.generated_request_logs = self.usage_helper.generate_sample_request_logs(
                user_id, count=self.request_log_count
            )

            # Insert into database
            success = self.usage_helper.insert_request_logs_to_database(self.generated_request_logs)

            if success:
                print_success(f"Created {len(self.generated_request_logs)} test request logs for pagination")
                return True
            else:
                print_error("Failed to insert test request logs")
                return False

        except Exception as e:
            print_error(f"Test data creation error: {str(e)}")
            return False

    def test_default_pagination(self) -> TestStep:
        """Test default pagination parameters"""
        step = TestStep(
            step_number=1,
            step_name="Test default pagination parameters",
            status="ERROR",
            message="Starting default pagination test"
        )

        try:
            token_to_use = self.test_user_token
            usage_response = self.usage_helper.get_usage_requests(token_to_use)

            if usage_response["status_code"] != 200:
                usage_response = self.usage_helper.get_usage_requests(self.admin_token)

            if usage_response["status_code"] == 200:
                response_data = usage_response["response_data"]

                # Validate default pagination
                expected_size = config.usage_default_page_size
                actual_size = response_data.get("size")
                actual_page = response_data.get("number")

                validation_errors = self.usage_helper.validate_pagination(response_data, expected_page=0, expected_size=expected_size)

                if not validation_errors:
                    step.status = "PASS"
                    step.message = f"Default pagination working - page {actual_page}, size {actual_size}, {response_data.get('totalElements', 0)} total elements"
                    print_success(step.message)
                else:
                    step.status = "FAIL"
                    step.message = f"Default pagination validation failed: {', '.join(validation_errors)}"
                    print_error(step.message)
            else:
                step.status = "FAIL"
                step.message = f"Default pagination test failed: {usage_response['status_code']}"
                print_error(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Default pagination test failed: {str(e)}"
            print_error(step.message)

        return step

    def test_custom_page_size(self) -> TestStep:
        """Test custom page size"""
        step = TestStep(
            step_number=2,
            step_name="Test custom page size",
            status="ERROR",
            message="Starting custom page size test"
        )

        try:
            test_size = 10
            token_to_use = self.test_user_token
            usage_response = self.usage_helper.get_usage_requests(token_to_use, page=0, size=test_size)

            if usage_response["status_code"] != 200:
                usage_response = self.usage_helper.get_usage_requests(self.admin_token, page=0, size=test_size)

            if usage_response["status_code"] == 200:
                response_data = usage_response["response_data"]

                validation_errors = self.usage_helper.validate_pagination(response_data, expected_page=0, expected_size=test_size)

                if not validation_errors:
                    actual_elements = response_data.get("numberOfElements", 0)
                    step.status = "PASS"
                    step.message = f"Custom page size working - size {test_size}, {actual_elements} elements returned"
                    print_success(step.message)
                else:
                    step.status = "FAIL"
                    step.message = f"Custom page size validation failed: {', '.join(validation_errors)}"
                    print_error(step.message)
            else:
                step.status = "FAIL"
                step.message = f"Custom page size test failed: {usage_response['status_code']}"
                print_error(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Custom page size test failed: {str(e)}"
            print_error(step.message)

        return step

    def test_page_navigation(self) -> TestStep:
        """Test page navigation"""
        step = TestStep(
            step_number=3,
            step_name="Test page navigation",
            status="ERROR",
            message="Starting page navigation test"
        )

        try:
            token_to_use = self.test_user_token
            page_size = 15

            # Get first page
            page0_response = self.usage_helper.get_usage_requests(token_to_use, page=0, size=page_size)
            if page0_response["status_code"] != 200:
                page0_response = self.usage_helper.get_usage_requests(self.admin_token, page=0, size=page_size)

            if page0_response["status_code"] != 200:
                step.status = "FAIL"
                step.message = f"Failed to get first page: {page0_response['status_code']}"
                print_error(step.message)
                return step

            page0_data = page0_response["response_data"]
            total_elements = page0_data.get("totalElements", 0)

            if total_elements > page_size:
                # Get second page if there are enough elements
                page1_response = self.usage_helper.get_usage_requests(token_to_use, page=1, size=page_size)
                if page1_response["status_code"] != 200:
                    page1_response = self.usage_helper.get_usage_requests(self.admin_token, page=1, size=page_size)

                if page1_response["status_code"] == 200:
                    page1_data = page1_response["response_data"]

                    # Validate that pages are different
                    page0_ids = [item.get("id") for item in page0_data.get("content", [])]
                    page1_ids = [item.get("id") for item in page1_data.get("content", [])]

                    if page0_ids and page1_ids and set(page0_ids).isdisjoint(set(page1_ids)):
                        step.status = "PASS"
                        step.message = f"Page navigation working - page 0 ({len(page0_ids)} items), page 1 ({len(page1_ids)} items)"
                        print_success(step.message)
                    else:
                        step.status = "FAIL"
                        step.message = "Pages contain overlapping or empty content"
                        print_error(step.message)
                else:
                    step.status = "FAIL"
                    step.message = f"Failed to get second page: {page1_response['status_code']}"
                    print_error(step.message)
            else:
                step.status = "SKIP"
                step.message = f"Not enough data for multi-page test ({total_elements} elements, page size {page_size})"
                print_info(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Page navigation test failed: {str(e)}"
            print_error(step.message)

        return step

    def test_boundary_conditions(self) -> TestStep:
        """Test pagination boundary conditions"""
        step = TestStep(
            step_number=4,
            step_name="Test pagination boundary conditions",
            status="ERROR",
            message="Starting boundary conditions test"
        )

        try:
            token_to_use = self.test_user_token
            boundary_tests = []

            # Test very small page size
            small_size = 1
            response = self.usage_helper.get_usage_requests(token_to_use, page=0, size=small_size)
            if response["status_code"] != 200:
                response = self.usage_helper.get_usage_requests(self.admin_token, page=0, size=small_size)

            if response["status_code"] == 200:
                data = response["response_data"]
                if data.get("numberOfElements") == small_size:
                    boundary_tests.append("Small page size (1) - OK")
                else:
                    boundary_tests.append(f"Small page size (1) - Expected {small_size}, got {data.get('numberOfElements')}")

            # Test page beyond available data
            total_elements_response = self.usage_helper.get_usage_requests(token_to_use, page=0, size=1)
            if total_elements_response["status_code"] != 200:
                total_elements_response = self.usage_helper.get_usage_requests(self.admin_token, page=0, size=1)

            if total_elements_response["status_code"] == 200:
                total_elements = total_elements_response["response_data"].get("totalElements", 0)
                beyond_page = (total_elements // 1) + 1  # Page beyond available data

                beyond_response = self.usage_helper.get_usage_requests(token_to_use, page=beyond_page, size=1)
                if beyond_response["status_code"] != 200:
                    beyond_response = self.usage_helper.get_usage_requests(self.admin_token, page=beyond_page, size=1)

                if beyond_response["status_code"] == 200:
                    beyond_data = beyond_response["response_data"]
                    if beyond_data.get("numberOfElements", 0) == 0:
                        boundary_tests.append("Page beyond data - OK (empty)")
                    else:
                        boundary_tests.append(f"Page beyond data - Expected empty, got {beyond_data.get('numberOfElements')} items")

            # Test max page size
            max_size = config.usage_max_page_size
            max_response = self.usage_helper.get_usage_requests(token_to_use, page=0, size=max_size)
            if max_response["status_code"] != 200:
                max_response = self.usage_helper.get_usage_requests(self.admin_token, page=0, size=max_size)

            if max_response["status_code"] == 200:
                max_data = max_response["response_data"]
                boundary_tests.append(f"Max page size ({max_size}) - OK ({max_data.get('numberOfElements')} items)")

            if all("OK" in test for test in boundary_tests):
                step.status = "PASS"
                step.message = f"Boundary conditions passed: {'; '.join(boundary_tests)}"
                print_success(step.message)
            else:
                step.status = "FAIL"
                step.message = f"Boundary condition failures: {'; '.join(boundary_tests)}"
                print_error(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Boundary conditions test failed: {str(e)}"
            print_error(step.message)

        return step

    def test_pagination_metadata(self) -> TestStep:
        """Test pagination metadata completeness"""
        step = TestStep(
            step_number=5,
            step_name="Test pagination metadata completeness",
            status="ERROR",
            message="Starting pagination metadata test"
        )

        try:
            token_to_use = self.test_user_token
            usage_response = self.usage_helper.get_usage_requests(token_to_use, page=0, size=10)

            if usage_response["status_code"] != 200:
                usage_response = self.usage_helper.get_usage_requests(self.admin_token, page=0, size=10)

            if usage_response["status_code"] == 200:
                response_data = usage_response["response_data"]

                # Check required pagination fields
                required_fields = [
                    "content", "pageable", "last", "totalPages",
                    "totalElements", "size", "number", "sort",
                    "first", "numberOfElements", "empty"
                ]

                missing_fields = [field for field in required_fields if field not in response_data]

                # Check pageable structure
                pageable = response_data.get("pageable", {})
                required_pageable_fields = ["sort", "offset", "pageNumber", "pageSize", "paged", "unpaged"]
                missing_pageable_fields = [field for field in required_pageable_fields if field not in pageable]

                if not missing_fields and not missing_pageable_fields:
                    # Validate data consistency
                    total_elements = response_data.get("totalElements", 0)
                    total_pages = response_data.get("totalPages", 0)
                    page_size = response_data.get("size", 0)
                    number_of_elements = response_data.get("numberOfElements", 0)

                    consistency_errors = []

                    if page_size > 0 and total_pages != ((total_elements + page_size - 1) // page_size):
                        consistency_errors.append("totalPages calculation mismatch")

                    if number_of_elements > page_size:
                        consistency_errors.append("numberOfElements exceeds page size")

                    if not consistency_errors:
                        step.status = "PASS"
                        step.message = f"Pagination metadata complete and consistent - {total_elements} total elements, {total_pages} pages"
                        print_success(step.message)
                    else:
                        step.status = "FAIL"
                        step.message = f"Pagination metadata inconsistency: {', '.join(consistency_errors)}"
                        print_error(step.message)
                else:
                    step.status = "FAIL"
                    missing_all = missing_fields + [f"pageable.{field}" for field in missing_pageable_fields]
                    step.message = f"Missing pagination metadata: {', '.join(missing_all)}"
                    print_error(step.message)
            else:
                step.status = "FAIL"
                step.message = f"Pagination metadata test failed: {usage_response['status_code']}"
                print_error(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Pagination metadata test failed: {str(e)}"
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
                self.test_default_pagination(),
                self.test_custom_page_size(),
                self.test_page_navigation(),
                self.test_boundary_conditions(),
                self.test_pagination_metadata()
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
    test_instance = Usage04Pagination()
    test_result = test_instance.run_test()

    # Exit with appropriate code
    sys.exit(0 if test_result.status == "PASS" else 1)

if __name__ == "__main__":
    main()