"""
TEST-03: List Billing Periods
Test ID: TEST-03
Test Name: List Billing Periods with Pagination
Test Type: Functional (Read)
Priority: HIGH (Required)
Estimated Duration: 15 minutes

Description:
Test GET /api/billing/periods endpoint with pagination support.
Verify list returns multiple periods, pagination works correctly, and sorting is accurate.
This test is completely self-contained and does not rely on other tests.
"""

import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from uat_framework import (
    DatabaseHelper, HTTPClient, TokenManager, TestReporting,
    TestStep, TestResult, Colors, print_success, print_error, print_warning, print_info,
    extract_jwt_token, EmailVerificationHelper, wait_for_email_verification
)
from billing_helpers import BillingHelper, BillingDataManager
# Configuration will be loaded from framework config
from billing_helpers import BillingDataManager

class Test03ListBillingPeriods:
    """TEST-03: List Billing Periods with Pagination"""

    def __init__(self):
        self.test_id = "TEST-03"
        self.test_name = "List Billing Periods with Pagination"
        self.reporting = TestReporting()
        self.db_helper = DatabaseHelper(config.DATABASE_URL)
        self.http_client = HTTPClient(config.APP_URL)
        self.token_manager = TokenManager()
        self.email_helper = EmailVerificationHelper(config.MAILCATCHER_URL)
        self.data_manager = BillingDataManager()
        self.test_steps = []
        self.start_time = datetime.now()
        self.admin_token = None
        self.user_token = None
        self.test_user_email = None
        self.test_user_password = None
        self.test_user_id = None

    def setup_environment(self) -> bool:
        """Setup test environment"""
        print_info("Setting up test environment...")

        if not self.db_helper.connect():
            print_error("Failed to connect to database")
            return False

        # Authenticate as admin
        try:
            login_data = {"email": config.ADMIN_EMAIL, "password": config.ADMIN_PASSWORD}
            response, _ = self.http_client.post(config.get_endpoint('login'), login_data)

            if response.status_code != config.STATUS_CODES['success']:
                print_error(f"Admin login failed: {response.status_code}")
                return False

            self.admin_token = response.json()['token']
            self.token_manager.store_token('admin', self.admin_token)
            print_success("Admin authentication successful")

        except Exception as e:
            print_error(f"Failed to authenticate admin: {e}")
            return False

        # Connect to Mailcatcher
        if not self.email_helper.connect_mailcatcher():
            print_error("Failed to connect to Mailcatcher")
            return False

        self.email_helper.clear_all_emails()
        print_success("Environment setup completed")
        return True

    def create_test_user(self) -> bool:
        """Create dedicated test user"""
        print_info("Creating test user...")

        try:
            # Create invite code
            invite_code = config.generate_unique_invite_code("BILLING-TEST-03")
            response, _ = self.http_client.post(
                config.get_endpoint('admin_invites'),
                {"code": invite_code},
                auth_token=self.admin_token
            )
            if response.status_code != config.STATUS_CODES['success']:
                print_error("Failed to create invite code")
                return False

            # Register user
            self.test_user_email = config.generate_unique_email("billing-test-03")
            self.test_user_password = "SecurePassword123!"

            response, _ = self.http_client.post(
                config.get_endpoint('user_register'),
                {
                    "email": self.test_user_email,
                    "password": self.test_user_password,
                    "confirmPassword": self.test_user_password,
                    "inviteCode": invite_code,
                    "userAcceptedTerms": True,
                    "userAcknowledgedDisclaimer": True
                }
            )
            if response.status_code not in [config.STATUS_CODES['accepted'], config.STATUS_CODES['created']]:
                print_error("User registration failed")
                return False

            # Verify email directly
            self.db_helper.execute_update(
                "UPDATE users SET email_verified_at = NOW() WHERE email = %s",
                (self.test_user_email,)
            )

            # Authenticate user
            response, _ = self.http_client.post(
                config.get_endpoint('login'),
                {"email": self.test_user_email, "password": self.test_user_password}
            )
            if response.status_code != config.STATUS_CODES['success']:
                print_error("User login failed")
                return False

            response_data = response.json()
            self.user_token = response_data['token']
            self.test_user_id = response_data['id']
            self.token_manager.store_token('user', self.user_token)

            print_success(f"Test user created: {self.test_user_email}")
            return True

        except Exception as e:
            print_error(f"Failed to create test user: {e}")
            return False

    def create_multiple_billing_periods(self) -> bool:
        """Create multiple billing periods for pagination testing"""
        print_info("Creating multiple billing periods for pagination testing...")

        try:
            # Get current date
            today = datetime.now()

            # Create past periods (3 months back)
            for i in range(3, 0, -1):
                # Calculate period start and end
                if i == 3:
                    # 3 months ago
                    period_date = today.replace(day=1) - timedelta(days=1)
                    period_date = period_date.replace(day=1)
                else:
                    # Adjust month
                    period_date = today.replace(day=1) - timedelta(days=30 * (i - 1))
                    period_date = period_date.replace(day=1)

                # Calculate end date (last day of month)
                if period_date.month == 12:
                    next_month = period_date.replace(year=period_date.year + 1, month=1, day=1)
                else:
                    next_month = period_date.replace(month=period_date.month + 1, day=1)
                period_end = next_month - timedelta(days=1)

                # Generate UUID for billing period
                import uuid
                period_id = str(uuid.uuid4())

                # Insert period into database
                query = """
                    INSERT INTO billing_periods
                    (id, user_id, period_start, period_end, total_requests, total_cost_cents,
                     is_current, payment_status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                self.db_helper.execute_update(
                    query,
                    (
                        period_id,  # Add UUID for id
                        self.test_user_id,
                        period_date.date(),
                        period_end.date(),
                        (i * 10),  # Incrementing requests
                        (i * 100),  # Incrementing costs
                        False,  # Not current
                        'paid'  # Mark as paid
                    )
                )

            print_success("Multiple billing periods created")
            return True

        except Exception as e:
            print_error(f"Failed to create multiple periods: {e}")
            return False

    def list_all_periods(self) -> TestStep:
        """Step: List all billing periods"""
        step = TestStep(
            step_number=1,
            step_name="List All Billing Periods",
            status="PASS",
            message="Retrieving list of all billing periods..."
        )

        try:
            response, response_time = self.http_client.get(
                config.get_endpoint('billing_periods'),
                auth_token=self.user_token
            )
            step.response_time = response_time

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = f"Failed to list billing periods: {response.status_code}"
                print_error(step.message)
                return step

            response_data = response.json()
            step.response_data = response_data

            # Check response structure
            if 'content' not in response_data:
                step.status = "FAIL"
                step.message = "Response missing 'content' field"
                print_error(step.message)
                return step

            results = response_data['content']
            if not isinstance(results, list):
                step.status = "FAIL"
                step.message = "Results should be a list"
                print_error(step.message)
                return step

            # Verify each result has required fields
            required_fields = ['id', 'isCurrent', 'periodStart', 'periodEnd',
                             'periodLabel', 'paymentStatus', 'totalRequests', 'totalCostCents']
            for i, period in enumerate(results):
                missing = [f for f in required_fields if f not in period]
                if missing:
                    step.status = "FAIL"
                    step.message = f"Period {i} missing fields: {missing}"
                    print_error(step.message)
                    return step

            step.status = "PASS"
            step.message = f"Successfully retrieved {len(results)} billing periods"
            step.database_state = {
                'total_periods': len(results),
                'has_pagination': 'count' in response_data or 'next' in response_data,
                'period_ids': [p['id'] for p in results]
            }
            print_success(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Failed to list billing periods: {e}"
            print_error(step.message)

        return step

    def verify_pagination_structure(self) -> TestStep:
        """Step: Verify pagination structure"""
        step = TestStep(
            step_number=2,
            step_name="Verify Pagination Structure",
            status="PASS",
            message="Checking pagination fields..."
        )

        try:
            response, _ = self.http_client.get(
                config.get_endpoint('billing_periods'),
                auth_token=self.user_token
            )

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = "Failed to retrieve periods"
                return step

            data = response.json()

            # Check for pagination fields
            pagination_fields = ['content', 'totalElements', 'totalPages', 'size', 'number', 'first', 'last', 'sort']
            missing = [f for f in pagination_fields if f not in data]

            if missing:
                step.status = "FAIL"
                step.message = f"Missing pagination fields: {missing}"
                print_error(step.message)
                return step

            # Validate totalElements is non-negative
            if not isinstance(data['totalElements'], int) or data['totalElements'] < 0:
                step.status = "FAIL"
                step.message = f"Invalid totalElements value: {data['totalElements']}"
                print_error(step.message)
                return step

            step.status = "PASS"
            step.message = "Pagination structure valid"
            step.database_state = {
                'size': data['size'],
                'total_elements': data['totalElements'],
                'total_pages': data['totalPages'],
                'current_page': data['number'],
                'is_first': data['first'],
                'is_last': data['last'],
                'results_count': len(data['content'])
            }
            print_success(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Pagination verification failed: {e}"
            print_error(step.message)

        return step

    def test_pagination_limits(self) -> TestStep:
        """Step: Test pagination with size parameter"""
        step = TestStep(
            step_number=3,
            step_name="Test Pagination Size",
            status="PASS",
            message="Testing pagination with size parameters..."
        )

        try:
            # Get first page with size of 2
            url = f"{config.get_endpoint('billing_periods')}?size=2"
            response, _ = self.http_client.get(url, auth_token=self.user_token)

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = f"Failed to get paginated results: {response.status_code}"
                print_error(step.message)
                return step

            data = response.json()
            results = data['content']

            # Verify size is respected
            if len(results) > 2:
                step.status = "FAIL"
                step.message = f"Size not respected: got {len(results)} results, expected <= 2"
                print_error(step.message)
                return step

            # Check if next page exists
            has_next = not data['last']

            step.status = "PASS"
            step.message = f"Pagination size working correctly: returned {len(results)} items"
            step.database_state = {
                'requested_size': 2,
                'actual_results': len(results),
                'has_next_page': has_next,
                'total_elements': data['totalElements'],
                'current_page': data['number']
            }
            print_success(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Pagination limit test failed: {e}"
            print_error(step.message)

        return step

    def verify_sorting_order(self) -> TestStep:
        """Step: Verify periods are sorted correctly"""
        step = TestStep(
            step_number=4,
            step_name="Verify Sorting Order",
            status="PASS",
            message="Checking period sorting order..."
        )

        try:
            response, _ = self.http_client.get(
                config.get_endpoint('billing_periods'),
                auth_token=self.user_token
            )

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = "Failed to retrieve periods"
                return step

            results = response.json()['content']

            if len(results) < 2:
                step.status = "PASS"
                step.message = "Only one or fewer periods, sorting not testable"
                print_warning(step.message)
                return step

            # Verify periods are sorted by start date (most recent first)
            for i in range(len(results) - 1):
                current_start = results[i]['periodStart']
                next_start = results[i + 1]['periodStart']

                # Parse dates
                from datetime import datetime as dt
                current_date = dt.strptime(current_start, '%Y-%m-%d')
                next_date = dt.strptime(next_start, '%Y-%m-%d')

                if current_date < next_date:
                    step.status = "FAIL"
                    step.message = f"Sorting order incorrect: {current_start} should be >= {next_start}"
                    print_error(step.message)
                    return step

            step.status = "PASS"
            step.message = f"Periods correctly sorted by start date (most recent first)"
            step.database_state = {
                'total_sorted': len(results),
                'sorting_verified': True
            }
            print_success(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Sorting verification failed: {e}"
            print_error(step.message)

        return step

    def verify_user_isolation(self) -> TestStep:
        """Step: Verify periods belong only to current user"""
        step = TestStep(
            step_number=5,
            step_name="Verify User Isolation",
            status="PASS",
            message="Checking user data isolation..."
        )

        try:
            response, _ = self.http_client.get(
                config.get_endpoint('billing_periods'),
                auth_token=self.user_token
            )

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = "Failed to retrieve periods"
                return step

            results = response.json()['content']

            # Verify all periods belong to test user from database
            if results:
                placeholders = ','.join(['%s'] * len(results))
                query = f"""
                    SELECT DISTINCT user_id FROM billing_periods
                    WHERE id IN ({placeholders})
                """
                period_ids = [p['id'] for p in results]
                result = self.db_helper.execute_query(query, tuple(period_ids))
                if len(result) > 1:
                    step.status = "FAIL"
                    step.message = "Periods from multiple users returned"
                    print_error(step.message)
                    return step

                if result and str(result[0]['user_id']) != str(self.test_user_id):
                    step.status = "FAIL"
                    step.message = "Periods do not belong to current user"
                    print_error(step.message)
                    return step

            step.status = "PASS"
            step.message = "User isolation verified: all periods belong to current user"
            step.database_state = {
                'user_id': str(self.test_user_id),
                'periods_returned': len(results),
                'all_belong_to_user': True
            }
            print_success(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"User isolation check failed: {e}"
            print_error(step.message)

        return step

    def cleanup(self):
        """Cleanup test resources"""
        try:
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

        if not self.create_test_user():
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

        # Create multiple periods for pagination testing
        if not self.create_multiple_billing_periods():
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
            self.list_all_periods(),
            self.verify_pagination_structure(),
            self.test_pagination_limits(),
            self.verify_sorting_order(),
            self.verify_user_isolation()
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
    print(f"TEST-03: List Billing Periods with Pagination")
    print(f"{'='*80}{Colors.RESET}\n")

    config.print_config_summary()

    test_runner = Test03ListBillingPeriods()
    result = test_runner.run_test()

    print(f"\n{Colors.CYAN}{'='*80}")
    print(f"TEST-03 EXECUTION COMPLETE")
    print(f"{'='*80}{Colors.RESET}")
    print(f"Status: {Colors.GREEN if result.is_success() else Colors.RED}{result.status}{Colors.RESET}")
    print(f"Duration: {result.total_time:.2f} seconds")
    print(f"Steps: {result.passed_steps}/{result.total_steps} passed")

    if result.is_success():
        print_success("Test completed successfully!")
    else:
        print_error("Test failed!")

    return result.is_success()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
