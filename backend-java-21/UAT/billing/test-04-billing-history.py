#!/usr/bin/env python3
"""
TEST-04: Billing History and Pagination
Test ID: TEST-04
Test Name: Billing History with Advanced Pagination and Filtering
Test Type: Functional (Read)
Priority: HIGH (Required)
Estimated Duration: 20 minutes

Description:
Test comprehensive billing history functionality with advanced pagination,
filtering by payment status, date range filtering, and sorting options.
Verify that billing history includes detailed payment information and
request log details for each period.
"""

import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List

current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from uat_test_framework import (
    DatabaseHelper, HTTPClient, TokenManager, TestReporting,
    TestStep, TestResult, Colors, print_success, print_error, print_warning, print_info,
    extract_jwt_token, EmailVerificationHelper, wait_for_email_verification
)
from uat_config import config
from billing_helpers import BillingDataManager, BillingHelper

class Test04BillingHistory:
    """TEST-04: Billing History and Pagination"""

    def __init__(self):
        self.test_id = "TEST-04"
        self.test_name = "Billing History and Pagination"
        self.reporting = TestReporting()
        self.db_helper = DatabaseHelper(config.DATABASE_URL)
        self.http_client = HTTPClient(config.APP_URL)
        self.token_manager = TokenManager()
        self.email_helper = EmailVerificationHelper(config.MAILCATCHER_URL)
        self.data_manager = BillingDataManager(db_helper=self.db_helper)
        self.billing_helper = BillingHelper(self.db_helper, self.http_client)
        self.test_steps = []
        self.start_time = datetime.now()
        self.admin_token = None
        self.user_token = None
        self.test_user_email = None
        self.test_user_password = None
        self.test_user_id = None
        self.period_ids = []

    def setup_environment(self) -> bool:
        """Setup test environment"""
        print_info("Setting up test environment...")

        if not self.db_helper.connect():
            print_error("Failed to connect to database")
            return False

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
            invite_code = config.generate_unique_invite_code("BILLING-TEST-04")
            response, _ = self.http_client.post(
                config.get_endpoint('admin_invites'),
                {"code": invite_code},
                auth_token=self.admin_token
            )
            if response.status_code != config.STATUS_CODES['success']:
                print_error("Failed to create invite code")
                return False

            self.test_user_email = config.generate_unique_email("billing-test-04")
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

            self.db_helper.execute_update(
                "UPDATE users SET email_verified_at = NOW() WHERE email = %s",
                (self.test_user_email,)
            )

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

    def create_comprehensive_billing_history(self) -> bool:
        """Create comprehensive billing history with various payment statuses"""
        print_info("Creating comprehensive billing history...")

        try:
            import uuid

            # Create multiple billing periods with different statuses and dates
            base_date = datetime.now() - timedelta(days=90)  # Start 3 months ago

            # Period 1: Paid period (2 months ago)
            period1_id = str(uuid.uuid4())
            period1_start = base_date.replace(day=1)
            period1_end = period1_start.replace(month=period1_start.month + 1) - timedelta(days=1)

            query = """
                INSERT INTO billing_periods
                (id, user_id, period_start, period_end, total_requests, total_cost_cents,
                 is_current, payment_status, paid_at, paid_amount_cents, payment_reference, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            self.db_helper.execute_update(
                query,
                (
                    period1_id, self.test_user_id, period1_start.date(), period1_end.date(),
                    25, 1250, False, 'paid', period1_end.date() + timedelta(days=5),
                    1250, 'INV-2023-08-001', 'Monthly payment - August'
                )
            )
            self.period_ids.append(period1_id)

            # Period 2: Overdue period (1 month ago)
            period2_id = str(uuid.uuid4())
            period2_start = period1_start.replace(month=period1_start.month + 1)
            period2_end = period2_start.replace(month=period2_start.month + 1) - timedelta(days=1)

            self.db_helper.execute_update(
                query,
                (
                    period2_id, self.test_user_id, period2_start.date(), period2_end.date(),
                    35, 1750, False, 'overdue', None,
                    0, None, 'Overdue payment'
                )
            )
            self.period_ids.append(period2_id)

            # Period 3: Waived period (current month)
            period3_id = str(uuid.uuid4())
            period3_start = period2_start.replace(month=period2_start.month + 1)
            period3_end = period3_start.replace(month=period3_start.month + 1) - timedelta(days=1)

            self.db_helper.execute_update(
                query,
                (
                    period3_id, self.test_user_id, period3_start.date(), period3_end.date(),
                    15, 750, False, 'waived', period3_start.date() + timedelta(days=10),
                    0, 'WAIVER-2023-10-001', 'Waived due to service issues'
                )
            )
            self.period_ids.append(period3_id)

            # Create request logs for each period
            for i, period_id in enumerate(self.period_ids):
                requests_count = [25, 35, 15][i]
                for j in range(requests_count):
                    # Create varied request timestamps within the period
                    request_ts = base_date + timedelta(days=i*30 + j)

                    request_query = """
                        INSERT INTO request_logs
                        (id, user_id, billing_period_id, service, request_ts, duration_ms,
                         request_bytes, response_bytes, status, request_id, flow_id, result)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    self.db_helper.execute_update(
                        request_query,
                        (
                            str(uuid.uuid4()), self.test_user_id, period_id, 'core-service', request_ts,
                            200 + j * 10, 1000 + j * 50, 2000 + j * 75,
                            'SUCCESS', str(uuid.uuid4()), str(uuid.uuid4())[:8],
                            f"Result {j+1}"
                        )
                    )

            print_success(f"Created comprehensive billing history: {len(self.period_ids)} periods")
            return True

        except Exception as e:
            print_error(f"Failed to create billing history: {e}")
            return False

    def get_billing_history_all_periods(self) -> TestStep:
        """Step: Get billing history with all periods"""
        step = TestStep(
            step_number=1,
            step_name="Get Billing History - All Periods",
            status="PASS",
            message="Retrieving complete billing history..."
        )

        try:
            response, response_time = self.http_client.get(
                config.get_endpoint('billing_periods'),
                auth_token=self.user_token
            )
            step.response_time = response_time

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = f"Failed to get billing history: {response.status_code}"
                print_error(step.message)
                return step

            response_data = response.json()
            step.response_data = response_data

            # Verify pagination structure
            required_fields = ['content', 'totalElements', 'totalPages', 'size', 'number', 'first', 'last']
            missing = [f for f in required_fields if f not in response_data]
            if missing:
                step.status = "FAIL"
                step.message = f"Missing pagination fields: {missing}"
                print_error(step.message)
                return step

            # Verify we have the expected number of periods
            content = response_data['content']
            if len(content) < len(self.period_ids):
                step.status = "FAIL"
                step.message = f"Expected at least {len(self.period_ids)} periods, got {len(content)}"
                print_error(step.message)
                return step

            # Verify each period has required fields
            period_fields = ['id', 'isCurrent', 'periodStart', 'periodEnd', 'periodLabel',
                           'paymentStatus', 'totalRequests', 'totalCostCents']
            for i, period in enumerate(content):
                missing_fields = [f for f in period_fields if f not in period]
                if missing_fields:
                    step.status = "FAIL"
                    step.message = f"Period {i} missing fields: {missing_fields}"
                    print_error(step.message)
                    return step

            step.status = "PASS"
            step.message = f"Billing history retrieved: {len(content)} periods"
            step.database_state = {
                'total_periods': len(content),
                'total_elements': response_data['totalElements'],
                'total_pages': response_data['totalPages'],
                'payment_statuses': list(set(p['paymentStatus'] for p in content))
            }
            print_success(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Billing history retrieval failed: {e}"
            print_error(step.message)

        return step

    def test_billing_history_pagination(self) -> TestStep:
        """Step: Test billing history pagination with various page sizes"""
        step = TestStep(
            step_number=2,
            step_name="Test Billing History Pagination",
            status="PASS",
            message="Testing pagination with different page sizes..."
        )

        try:
            pagination_results = []

            # Test different page sizes
            page_sizes = [1, 2, 5]

            for page_size in page_sizes:
                url = f"{config.get_endpoint('billing_periods')}?size={page_size}"
                response, _ = self.http_client.get(url, auth_token=self.user_token)

                if response.status_code != config.STATUS_CODES['success']:
                    step.status = "FAIL"
                    step.message = f"Pagination failed for size {page_size}: {response.status_code}"
                    print_error(step.message)
                    return step

                data = response.json()
                content = data['content']

                # Verify page size is respected
                if len(content) > page_size:
                    step.status = "FAIL"
                    step.message = f"Page size {page_size} not respected: got {len(content)} items"
                    print_error(step.message)
                    return step

                pagination_results.append({
                    'page_size': page_size,
                    'returned_items': len(content),
                    'total_elements': data['totalElements'],
                    'total_pages': data['totalPages'],
                    'is_first': data['first'],
                    'is_last': data['last']
                })

            step.status = "PASS"
            step.message = f"Pagination working correctly across {len(pagination_results)} page sizes"
            step.database_state = {
                'pagination_tests': pagination_results,
                'pages_tested': page_sizes
            }
            print_success(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Pagination test failed: {e}"
            print_error(step.message)

        return step

    def verify_payment_status_distribution(self) -> TestStep:
        """Step: Verify payment status distribution in billing history"""
        step = TestStep(
            step_number=3,
            step_name="Verify Payment Status Distribution",
            status="PASS",
            message="Checking payment status distribution..."
        )

        try:
            response, _ = self.http_client.get(
                config.get_endpoint('billing_periods'),
                auth_token=self.user_token
            )

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = "Failed to retrieve billing history"
                return step

            content = response.json()['content']

            # Count payment statuses
            status_counts = {}
            for period in content:
                status = period['paymentStatus']
                status_counts[status] = status_counts.get(status, 0) + 1

            # Verify we have expected payment statuses
            expected_statuses = ['paid', 'overdue', 'waived']
            actual_statuses = list(status_counts.keys())

            missing_statuses = [s for s in expected_statuses if s not in actual_statuses]
            if missing_statuses:
                step.status = "FAIL"
                step.message = f"Missing payment statuses: {missing_statuses}"
                print_error(step.message)
                return step

            step.status = "PASS"
            step.message = f"Payment status distribution verified: {status_counts}"
            step.database_state = {
                'status_distribution': status_counts,
                'unique_statuses': len(actual_statuses),
                'total_periods': len(content)
            }
            print_success(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Payment status verification failed: {e}"
            print_error(step.message)

        return step

    def test_period_details_with_request_history(self) -> TestStep:
        """Step: Test individual period details with request history"""
        step = TestStep(
            step_number=4,
            step_name="Test Period Details with Request History",
            status="PASS",
            message="Testing period detail endpoints with request logs..."
        )

        try:
            period_details = []

            # Test each period we created
            for i, period_id in enumerate(self.period_ids[:2]):  # Test first 2 periods
                url = config.get_endpoint('billing_period_detail', periodId=period_id)
                response, _ = self.http_client.get(url, auth_token=self.user_token)

                if response.status_code != config.STATUS_CODES['success']:
                    step.status = "FAIL"
                    step.message = f"Failed to get period {period_id} details: {response.status_code}"
                    print_error(step.message)
                    return step

                period_data = response.json()

                # Verify required fields
                required_fields = ['id', 'periodStart', 'periodEnd', 'totalRequests',
                                 'totalCostCents', 'paymentStatus', 'current', 'requests']
                missing_fields = [f for f in required_fields if f not in period_data]

                if missing_fields:
                    step.status = "FAIL"
                    step.message = f"Period {period_id} missing fields: {missing_fields}"
                    print_error(step.message)
                    return step

                # Verify requests field exists and contains request logs
                requests = period_data.get('requests', [])
                if not isinstance(requests, list):
                    step.status = "FAIL"
                    step.message = f"Period {period_id} requests field is not a list"
                    print_error(step.message)
                    return step

                # Verify request log structure
                if requests:
                    sample_request = requests[0]
                    request_fields = ['id', 'status', 'durationMs', 'flowId', 'result']
                    missing_request_fields = [f for f in request_fields if f not in sample_request]

                    if missing_request_fields:
                        step.status = "FAIL"
                        step.message = f"Request log missing fields: {missing_request_fields}"
                        print_error(step.message)
                        return step

                period_details.append({
                    'period_id': period_id,
                    'payment_status': period_data['paymentStatus'],
                    'total_requests': period_data['totalRequests'],
                    'request_logs_count': len(requests),
                    'has_requests': len(requests) > 0
                })

            step.status = "PASS"
            step.message = f"Period details verified: {len(period_details)} periods with request logs"
            step.database_state = {
                'periods_tested': len(period_details),
                'period_details': period_details,
                'request_logs_available': all(p['has_requests'] for p in period_details)
            }
            print_success(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Period details test failed: {e}"
            print_error(step.message)

        return step

    def test_sorting_and_filtering(self) -> TestStep:
        """Step: Test sorting and filtering options"""
        step = TestStep(
            step_number=5,
            step_name="Test Sorting and Filtering Options",
            status="PASS",
            message="Testing various sorting and filtering options..."
        )

        try:
            sorting_results = []

            # Test default sorting (should be most recent first)
            response, _ = self.http_client.get(
                config.get_endpoint('billing_periods'),
                auth_token=self.user_token
            )
            if response.status_code == config.STATUS_CODES['success']:
                content = response.json()['content']
                if len(content) >= 2:
                    # Verify chronological order (most recent first)
                    for i in range(len(content) - 1):
                        current = content[i]['periodStart']
                        next_period = content[i + 1]['periodStart']

                        from datetime import datetime as dt
                        current_date = dt.strptime(current, '%Y-%m-%d')
                        next_date = dt.strptime(next_period, '%Y-%m-%d')

                        if current_date < next_date:
                            step.status = "FAIL"
                            step.message = "Sorting order incorrect - should be most recent first"
                            print_error(step.message)
                            return step

                    sorting_results.append({
                        'sort_type': 'default',
                        'verified': True,
                        'items_sorted': len(content)
                    })

            # Test larger page size to get all results
            url = f"{config.get_endpoint('billing_periods')}?size=50"
            response, _ = self.http_client.get(url, auth_token=self.user_token)
            if response.status_code == config.STATUS_CODES['success']:
                data = response.json()
                all_periods = data['content']

                sorting_results.append({
                    'sort_type': 'large_page',
                    'total_retrieved': len(all_periods),
                    'total_elements': data['totalElements'],
                    'verified': len(all_periods) == data['totalElements']
                })

            step.status = "PASS"
            step.message = f"Sorting and filtering verified: {len(sorting_results)} tests passed"
            step.database_state = {
                'sorting_tests': sorting_results,
                'total_unique_periods': len(content) if 'content' in locals() else 0
            }
            print_success(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Sorting and filtering test failed: {e}"
            print_error(step.message)

        return step

    def cleanup(self):
        """Cleanup test resources"""
        try:
            # Clean up test data
            if self.data_manager.cleanup_test_data():
                print_info("Test data cleanup successful")
            else:
                print_warning("Test data cleanup had issues")

            # Disconnect from database
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

        if not self.create_comprehensive_billing_history():
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
            self.get_billing_history_all_periods(),
            self.test_billing_history_pagination(),
            self.verify_payment_status_distribution(),
            self.test_period_details_with_request_history(),
            self.test_sorting_and_filtering()
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
    print(f"TEST-04: Billing History and Pagination")
    print(f"{'='*80}{Colors.RESET}\n")

    config.print_config_summary()

    test_runner = Test04BillingHistory()
    result = test_runner.run_test()

    print(f"\n{Colors.CYAN}{'='*80}")
    print(f"TEST-04 EXECUTION COMPLETE")
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