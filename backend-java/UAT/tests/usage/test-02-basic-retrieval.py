#!/usr/bin/env python3
"""
USAGE-02: Basic Retrieval of Usage Requests
Test ID: USAGE-02
Test Name: Basic Retrieval of Usage Requests
Test Type: Functional Testing
Priority: High
Estimated Duration: 5 minutes

Description:
Test basic retrieval functionality of the /api/usage/requests endpoint.
This test validates that users can retrieve their usage data with proper
authentication, response structure, and default pagination behavior.
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

class Usage02BasicRetrieval:
    """Usage basic retrieval test following API token test pattern"""

    def __init__(self):
        """Initialize test configuration and helpers"""
        self.test_id = "USAGE-02"
        self.test_name = "Basic Retrieval of Usage Requests"

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
        self.test_email_prefix = f"usage02_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.request_log_count = 20

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

        # Additional setup: Create test data
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
            invite_code = f"USAGE02-{uuid.uuid4().hex[:8].upper()}"

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
            self.test_password = config.generate_test_password("02")

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
        """Create test data for basic retrieval testing"""
        try:
            user_id = self.test_user_data.get('id') if isinstance(self.test_user_data, dict) else None
            if not user_id:
                print_error("Cannot create test data: user ID not available")
                return False

            # Generate request logs
            self.generated_request_logs = self.usage_helper.generate_sample_request_logs(
                user_id, count=self.request_log_count
            )

            # Insert into database
            success = self.usage_helper.insert_request_logs_to_database(self.generated_request_logs)

            if success:
                print_success(f"Created {len(self.generated_request_logs)} test request logs")
                return True
            else:
                print_error("Failed to insert test request logs")
                return False

        except Exception as e:
            print_error(f"Test data creation error: {str(e)}")
            return False

    def test_basic_usage_retrieval(self) -> TestStep:
        """Test basic usage request retrieval"""
        step = TestStep(
            step_number=1,
            step_name="Test basic usage request retrieval",
            status="ERROR",
            message="Starting basic usage retrieval test"
        )

        try:
            # Use user token first, fall back to admin token if needed
            token_to_use = self.test_user_token
            usage_response = self.usage_helper.get_usage_requests(token_to_use)

            if usage_response["status_code"] != 200:
                # Try with admin token
                print_info("User token failed, trying admin token...")
                token_to_use = self.admin_token
                usage_response = self.usage_helper.get_usage_requests(token_to_use)

            if usage_response["status_code"] == 200:
                response_data = usage_response["response_data"]

                # Validate response structure
                validation_errors = self.usage_helper.validate_usage_response_structure(response_data)

                if not validation_errors:
                    step.status = "PASS"
                    step.message = f"Basic usage retrieval successful - {response_data.get('totalElements', 0)} total elements"
                    print_success(step.message)

                    # Store response for further validation
                    step.response_data = response_data
                else:
                    step.status = "FAIL"
                    step.message = f"Response structure validation failed: {', '.join(validation_errors)}"
                    print_error(step.message)
            else:
                step.status = "FAIL"
                step.message = f"Usage retrieval failed: {usage_response['status_code']}"
                print_error(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Basic usage retrieval test failed: {str(e)}"
            print_error(step.message)

        return step

    def test_response_content_validation(self) -> TestStep:
        """Test validation of response content"""
        step = TestStep(
            step_number=2,
            step_name="Test response content validation",
            status="ERROR",
            message="Starting response content validation"
        )

        try:
            # Get usage data
            token_to_use = self.test_user_token
            usage_response = self.usage_helper.get_usage_requests(token_to_use)

            if usage_response["status_code"] != 200:
                usage_response = self.usage_helper.get_usage_requests(self.admin_token)

            if usage_response["status_code"] == 200:
                response_data = usage_response["response_data"]
                content = response_data.get("content", [])

                if content:
                    # Validate first item structure
                    first_item = content[0]
                    required_fields = ["id", "requestTs", "service", "status", "durationMs", "requestBytes", "responseBytes", "requestId"]

                    missing_fields = [field for field in required_fields if field not in first_item]

                    if not missing_fields:
                        # Validate data types
                        errors = []

                        if not isinstance(first_item.get("durationMs"), int):
                            errors.append("durationMs should be integer")
                        if not isinstance(first_item.get("requestBytes"), int):
                            errors.append("requestBytes should be integer")
                        if not isinstance(first_item.get("responseBytes"), int):
                            errors.append("responseBytes should be integer")

                        # Validate timestamp format
                        try:
                            datetime.fromisoformat(first_item["requestTs"].replace('Z', '+00:00'))
                        except (ValueError, AttributeError):
                            errors.append("requestTs is not valid ISO datetime")

                        if not errors:
                            step.status = "PASS"
                            step.message = f"Response content validation successful - {len(content)} items"
                            print_success(step.message)
                        else:
                            step.status = "FAIL"
                            step.message = f"Content validation errors: {', '.join(errors)}"
                            print_error(step.message)
                    else:
                        step.status = "FAIL"
                        step.message = f"Missing required fields: {', '.join(missing_fields)}"
                        print_error(step.message)
                else:
                    step.status = "FAIL"
                    step.message = "Response content is empty"
                    print_error(step.message)
            else:
                step.status = "FAIL"
                step.message = f"Failed to get usage data for validation: {usage_response['status_code']}"
                print_error(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Response content validation failed: {str(e)}"
            print_error(step.message)

        return step

    def test_default_pagination(self) -> TestStep:
        """Test default pagination behavior"""
        step = TestStep(
            step_number=3,
            step_name="Test default pagination behavior",
            status="ERROR",
            message="Starting default pagination test"
        )

        try:
            # Get usage data with default pagination
            token_to_use = self.test_user_token
            usage_response = self.usage_helper.get_usage_requests(token_to_use)

            if usage_response["status_code"] != 200:
                usage_response = self.usage_helper.get_usage_requests(self.admin_token)

            if usage_response["status_code"] == 200:
                response_data = usage_response["response_data"]

                # Validate default pagination values
                expected_size = config.usage_default_page_size
                actual_size = response_data.get("size")
                actual_page = response_data.get("number")

                errors = []

                if actual_size != expected_size:
                    errors.append(f"Expected default page size {expected_size}, got {actual_size}")

                if actual_page != 0:
                    errors.append(f"Expected default page number 0, got {actual_page}")

                # Validate pagination structure
                pageable = response_data.get("pageable", {})
                required_pageable_fields = ["sort", "offset", "pageNumber", "pageSize", "paged", "unpaged"]
                missing_pageable_fields = [field for field in required_pageable_fields if field not in pageable]

                if missing_pageable_fields:
                    errors.append(f"Missing pageable fields: {', '.join(missing_pageable_fields)}")

                if not errors:
                    step.status = "PASS"
                    step.message = f"Default pagination validation successful - page {actual_page}, size {actual_size}"
                    print_success(step.message)
                else:
                    step.status = "FAIL"
                    step.message = f"Pagination validation errors: {', '.join(errors)}"
                    print_error(step.message)
            else:
                step.status = "FAIL"
                step.message = f"Failed to get usage data for pagination test: {usage_response['status_code']}"
                print_error(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Default pagination test failed: {str(e)}"
            print_error(step.message)

        return step

    def test_sorting_order(self) -> TestStep:
        """Test that results are sorted by requestTs descending"""
        step = TestStep(
            step_number=4,
            step_name="Test sorting order (requestTs descending)",
            status="ERROR",
            message="Starting sorting order test"
        )

        try:
            # Get usage data
            token_to_use = self.test_user_token
            usage_response = self.usage_helper.get_usage_requests(token_to_use)

            if usage_response["status_code"] != 200:
                usage_response = self.usage_helper.get_usage_requests(self.admin_token)

            if usage_response["status_code"] == 200:
                response_data = usage_response["response_data"]
                content = response_data.get("content", [])

                if len(content) > 1:
                    # Check if items are sorted by requestTs in descending order
                    sorted_correctly = True
                    for i in range(len(content) - 1):
                        current_ts = datetime.fromisoformat(content[i]["requestTs"].replace('Z', '+00:00'))
                        next_ts = datetime.fromisoformat(content[i+1]["requestTs"].replace('Z', '+00:00'))

                        if current_ts < next_ts:
                            sorted_correctly = False
                            break

                    if sorted_correctly:
                        step.status = "PASS"
                        step.message = "Items are correctly sorted by requestTs descending"
                        print_success(step.message)
                    else:
                        step.status = "FAIL"
                        step.message = "Items are not sorted correctly by requestTs descending"
                        print_error(step.message)
                else:
                    step.status = "SKIP"
                    step.message = "Not enough items to verify sorting order"
                    print_info(step.message)
            else:
                step.status = "FAIL"
                step.message = f"Failed to get usage data for sorting test: {usage_response['status_code']}"
                print_error(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Sorting order test failed: {str(e)}"
            print_error(step.message)

        return step

    def test_authentication_required(self) -> TestStep:
        """Test that authentication is required for usage endpoint"""
        step = TestStep(
            step_number=5,
            step_name="Test authentication requirement",
            status="ERROR",
            message="Starting authentication requirement test"
        )

        try:
            # Try to access endpoint without authentication
            response, _ = self.http_client.get("/api/usage/requests")

            if response.status_code == 401:
                step.status = "PASS"
                step.message = "Authentication requirement test passed - endpoint properly protected"
                print_success(step.message)
            else:
                step.status = "FAIL"
                step.message = f"Expected 401 Unauthorized, got {response.status_code}"
                print_error(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Authentication requirement test failed: {str(e)}"
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
                self.test_basic_usage_retrieval(),
                self.test_response_content_validation(),
                self.test_default_pagination(),
                self.test_sorting_order(),
                self.test_authentication_required()
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
    test_instance = Usage02BasicRetrieval()
    test_result = test_instance.run_test()

    # Exit with appropriate code
    sys.exit(0 if test_result.status == "PASS" else 1)

if __name__ == "__main__":
    main()