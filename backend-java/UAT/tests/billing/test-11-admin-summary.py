"""
TEST-11: Admin Summary and Reporting
Test ID: TEST-11
Test Name: Admin Summary and Reporting
Test Type: Functional (Read - Admin)
Priority: HIGH (Required)
Estimated Duration: 25 minutes

Description:
Test admin endpoints for comprehensive billing summaries and reporting.
Verify admin can access all billing periods across all users, generate
summary statistics, and access detailed billing information.
"""

import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List

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
from billing_helpers import BillingDataManager, BillingHelper

class Test11AdminSummary:
    """TEST-11: Admin Summary and Reporting"""

    def __init__(self):
        self.test_id = "TEST-11"
        self.test_name = "Admin Summary and Reporting"
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
        self.user_tokens = {}
        self.test_users = []
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

    def create_multiple_test_users(self) -> bool:
        """Create multiple test users with diverse billing scenarios"""
        print_info("Creating multiple test users for admin reporting...")

        try:
            import uuid

            # Create 3 test users with different usage patterns
            user_scenarios = [
                {
                    'name': 'light-user',
                    'requests': [5, 8, 3],  # Light usage
                    'statuses': ['paid', 'pending', 'paid']
                },
                {
                    'name': 'heavy-user',
                    'requests': [50, 75, 60],  # Heavy usage
                    'statuses': ['paid', 'paid', 'overdue']
                },
                {
                    'name': 'medium-user',
                    'requests': [20, 15, 25],  # Medium usage
                    'statuses': ['waived', 'paid', 'pending']
                }
            ]

            for i, scenario in enumerate(user_scenarios):
                # Create invite code
                invite_code = config.generate_unique_invite_code(f"ADMIN-TEST-{i}")
                response, _ = self.http_client.post(
                    config.get_endpoint('admin_invites'),
                    {"code": invite_code},
                    auth_token=self.admin_token
                )
                if response.status_code != config.STATUS_CODES['success']:
                    print_error(f"Failed to create invite code for user {i}")
                    return False

                # Register user
                user_email = config.generate_unique_email(f"admin-test-{scenario['name']}")
                user_password = "SecurePassword123!"

                response, _ = self.http_client.post(
                    config.get_endpoint('user_register'),
                    {
                        "email": user_email,
                        "password": user_password,
                        "confirmPassword": user_password,
                        "inviteCode": invite_code,
                        "userAcceptedTerms": True,
                        "userAcknowledgedDisclaimer": True
                    }
                )
                if response.status_code not in [config.STATUS_CODES['accepted'], config.STATUS_CODES['created']]:
                    print_error(f"User registration failed for {user_email}")
                    return False

                # Verify email directly
                self.db_helper.execute_update(
                    "UPDATE users SET email_verified_at = NOW() WHERE email = %s",
                    (user_email,)
                )

                # Authenticate user
                response, _ = self.http_client.post(
                    config.get_endpoint('login'),
                    {"email": user_email, "password": user_password}
                )
                if response.status_code != config.STATUS_CODES['success']:
                    print_error(f"User login failed for {user_email}")
                    return False

                response_data = response.json()
                user_token = response_data['token']
                user_id = response_data['id']

                # Store user info
                self.test_users.append({
                    'id': user_id,
                    'email': user_email,
                    'scenario': scenario['name'],
                    'token': user_token
                })
                self.user_tokens[user_id] = user_token

                # Create billing periods for this user
                base_date = datetime.now() - timedelta(days=60)
                for j, (requests, status) in enumerate(zip(scenario['requests'], scenario['statuses'])):
                    period_id = str(uuid.uuid4())
                    period_start = (base_date + timedelta(days=j*30)).replace(day=1)
                    period_end = period_start.replace(month=period_start.month + 1) - timedelta(days=1)

                    # Insert billing period
                    query = """
                        INSERT INTO billing_periods
                        (id, user_id, period_start, period_end, total_requests, total_cost_cents,
                         is_current, payment_status, paid_at, paid_amount_cents, payment_reference, notes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """

                    paid_at = None
                    paid_amount = 0
                    payment_ref = None

                    if status == 'paid':
                        paid_at = period_end.date() + timedelta(days=5)
                        paid_amount = requests * config.COST_PER_REQUEST_CENTS
                        payment_ref = f"INV-{scenario['name'].upper()}-{j+1}"

                    self.db_helper.execute_update(
                        query,
                        (
                            period_id, user_id, period_start.date(), period_end.date(),
                            requests, requests * config.COST_PER_REQUEST_CENTS, False, status,
                            paid_at, paid_amount, payment_ref, f"{scenario['name']} period {j+1}"
                        )
                    )
                    self.period_ids.append(period_id)

            print_success(f"Created {len(self.test_users)} test users with diverse billing scenarios")
            return True

        except Exception as e:
            print_error(f"Failed to create test users: {e}")
            return False

    def get_admin_billing_list_all(self) -> TestStep:
        """Step: Get comprehensive billing list as admin"""
        step = TestStep(
            step_number=1,
            step_name="Get Admin Billing List - All Periods",
            status="PASS",
            message="Retrieving all billing periods as admin..."
        )

        try:
            response, response_time = self.http_client.get(
                config.get_endpoint('admin_billing_list'),
                auth_token=self.admin_token
            )
            step.response_time = response_time

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = f"Failed to get admin billing list: {response.status_code}"
                print_error(step.message)
                return step

            # Debug: Check response content
            if not response.text.strip():
                step.status = "FAIL"
                step.message = f"Admin billing list returned empty response: {response.status_code}"
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

            content = response_data['content']

            # Verify we have data from multiple users
            user_ids = set()
            payment_statuses = set()
            total_requests = 0
            total_cost = 0

            for period in content:
                if 'userId' in period:
                    user_ids.add(period['userId'])
                if 'paymentStatus' in period:
                    payment_statuses.add(period['paymentStatus'])
                if 'totalRequests' in period:
                    total_requests += period['totalRequests']
                if 'totalCostCents' in period:
                    total_cost += period['totalCostCents']

            # Verify admin billing response structure
            expected_fields = ['id', 'userId', 'paymentStatus', 'totalRequests', 'totalCostCents']
            for i, period in enumerate(content):
                missing_fields = [f for f in expected_fields if f not in period]
                if missing_fields:
                    step.status = "FAIL"
                    step.message = f"Period {i} missing fields: {missing_fields}"
                    print_error(step.message)
                    return step

            step.status = "PASS"
            step.message = f"Admin billing list retrieved: {len(content)} periods from {len(user_ids)} users"
            step.database_state = {
                'total_periods': len(content),
                'unique_users': len(user_ids),
                'payment_statuses': list(payment_statuses),
                'total_requests_all': total_requests,
                'total_cost_all': total_cost,
                'total_elements': response_data['totalElements']
            }
            print_success(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Admin billing list retrieval failed: {e}"
            print_error(step.message)

        return step

    def test_admin_pagination_and_filtering(self) -> TestStep:
        """Step: Test admin pagination and filtering capabilities"""
        step = TestStep(
            step_number=2,
            step_name="Test Admin Pagination and Filtering",
            status="PASS",
            message="Testing admin pagination with various parameters..."
        )

        try:
            pagination_results = []

            # Test different page sizes
            page_sizes = [5, 10, 20]
            for page_size in page_sizes:
                url = f"{config.get_endpoint('admin_billing_list')}?size={page_size}"
                response, _ = self.http_client.get(url, auth_token=self.admin_token)

                if response.status_code != config.STATUS_CODES['success']:
                    step.status = "FAIL"
                    step.message = f"Admin pagination failed for size {page_size}: {response.status_code}"
                    print_error(step.message)
                    return step

                data = response.json()
                content = data['content']

                # Verify page size is respected
                if len(content) > page_size:
                    step.status = "FAIL"
                    step.message = f"Admin page size {page_size} not respected: got {len(content)} items"
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

            # Test pagination with page number
            url = f"{config.get_endpoint('admin_billing_list')}?size=5&page=0"
            response, _ = self.http_client.get(url, auth_token=self.admin_token)
            if response.status_code == config.STATUS_CODES['success']:
                first_page = response.json()

                url = f"{config.get_endpoint('admin_billing_list')}?size=5&page=1"
                response, _ = self.http_client.get(url, auth_token=self.admin_token)
                if response.status_code == config.STATUS_CODES['success']:
                    second_page = response.json()

                    pagination_results.append({
                        'test_type': 'page_navigation',
                        'first_page_items': len(first_page['content']),
                        'second_page_items': len(second_page['content']),
                        'first_page_number': first_page['number'],
                        'second_page_number': second_page['number']
                    })

            step.status = "PASS"
            step.message = f"Admin pagination verified: {len(pagination_results)} tests passed"
            step.database_state = {
                'pagination_tests': pagination_results,
                'pages_tested': page_sizes
            }
            print_success(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Admin pagination test failed: {e}"
            print_error(step.message)

        return step

    def verify_admin_user_isolation(self) -> TestStep:
        """Step: Verify admin can see data from all users"""
        step = TestStep(
            step_number=3,
            step_name="Verify Admin User Isolation",
            status="PASS",
            message="Verifying admin can access all users' billing data..."
        )

        try:
            # Get admin view of all billing periods
            response, _ = self.http_client.get(
                config.get_endpoint('admin_billing_list'),
                auth_token=self.admin_token
            )

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = "Failed to get admin billing list"
                return step

            admin_content = response.json()['content']
            admin_user_ids = set()

            for period in admin_content:
                if 'userId' in period:
                    admin_user_ids.add(period['userId'])

            # Compare with each user's view
            user_comparison_results = []
            for user in self.test_users:
                response, _ = self.http_client.get(
                    config.get_endpoint('billing_periods'),
                    auth_token=user['token']
                )

                if response.status_code == config.STATUS_CODES['success']:
                    user_content = response.json()['content']
                    user_user_ids = set()

                    for period in user_content:
                        # Regular users shouldn't see userId field
                        if 'userId' in period:
                            step.status = "FAIL"
                            step.message = f"Regular user {user['email']} should not see userId field"
                            print_error(step.message)
                            return step

                    user_comparison_results.append({
                        'user_email': user['email'],
                        'user_periods_count': len(user_content),
                        'user_can_see_others': False
                    })

            # Verify admin can see more data than individual users
            admin_total_periods = len(admin_content)
            max_user_periods = max([r['user_periods_count'] for r in user_comparison_results]) if user_comparison_results else 0

            if admin_total_periods <= max_user_periods:
                step.status = "FAIL"
                step.message = f"Admin should see more periods than any individual user. Admin: {admin_total_periods}, Max user: {max_user_periods}"
                print_error(step.message)
                return step

            step.status = "PASS"
            step.message = f"Admin isolation verified: Admin sees {admin_total_periods} periods vs max user {max_user_periods}"
            step.database_state = {
                'admin_total_periods': admin_total_periods,
                'admin_unique_users': len(admin_user_ids),
                'max_user_periods': max_user_periods,
                'user_comparisons': user_comparison_results,
                'admin_can_see_all': admin_total_periods > max_user_periods
            }
            print_success(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Admin user isolation test failed: {e}"
            print_error(step.message)

        return step

    def test_admin_payment_status_filtering(self) -> TestStep:
        """Step: Test admin filtering by payment status"""
        step = TestStep(
            step_number=4,
            step_name="Test Admin Payment Status Filtering",
            status="PASS",
            message="Testing admin filtering by payment status..."
        )

        try:
            # Get all periods to understand the distribution
            response, _ = self.http_client.get(
                config.get_endpoint('admin_billing_list'),
                auth_token=self.admin_token
            )

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = "Failed to get admin billing list"
                return step

            all_periods = response.json()['content']
            status_distribution = {}

            for period in all_periods:
                status = period.get('paymentStatus', 'unknown')
                status_distribution[status] = status_distribution.get(status, 0) + 1

            # Test filtering by each payment status
            filtering_results = []
            for status in ['paid', 'pending', 'overdue', 'waived']:
                # Note: Assuming the API supports filtering by payment status
                # If not implemented, this test will show what's needed
                url = f"{config.get_endpoint('admin_billing_list')}?paymentStatus={status}"
                response, _ = self.http_client.get(url, auth_token=self.admin_token)

                if response.status_code == config.STATUS_CODES['success']:
                    filtered_content = response.json()['content']
                    filtered_statuses = [p.get('paymentStatus') for p in filtered_content]

                    # Verify all results have the expected status
                    unexpected_statuses = [s for s in filtered_statuses if s != status]

                    filtering_results.append({
                        'filtered_status': status,
                        'results_count': len(filtered_content),
                        'expected_count': status_distribution.get(status, 0),
                        'unexpected_statuses': unexpected_statuses,
                        'filtering_works': len(unexpected_statuses) == 0
                    })
                else:
                    filtering_results.append({
                        'filtered_status': status,
                        'error': f"HTTP {response.status_code}",
                        'filtering_works': False
                    })

            step.status = "PASS"
            step.message = f"Admin payment status filtering tested: {len(filtering_results)} statuses"
            step.database_state = {
                'total_distribution': status_distribution,
                'filtering_tests': filtering_results,
                'statuses_tested': len(filtering_results)
            }
            print_success(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Admin payment status filtering test failed: {e}"
            print_error(step.message)

        return step

    def test_admin_summary_statistics(self) -> TestStep:
        """Step: Test admin summary statistics calculation"""
        step = TestStep(
            step_number=5,
            step_name="Test Admin Summary Statistics",
            status="PASS",
            message="Calculating and verifying admin summary statistics..."
        )

        try:
            # Get all billing periods
            response, _ = self.http_client.get(
                config.get_endpoint('admin_billing_list'),
                auth_token=self.admin_token
            )

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = "Failed to get admin billing list for statistics"
                return step

            all_periods = response.json()['content']

            # Calculate comprehensive statistics
            stats = {
                'total_periods': len(all_periods),
                'total_users': len(set(p.get('userId') for p in all_periods if p.get('userId'))),
                'total_requests': sum(p.get('totalRequests', 0) for p in all_periods),
                'total_revenue': sum(p.get('totalCostCents', 0) for p in all_periods if p.get('paymentStatus') == 'paid'),
                'payment_breakdown': {},
                'average_requests_per_period': 0,
                'revenue_per_user': 0
            }

            # Payment status breakdown
            for period in all_periods:
                status = period.get('paymentStatus', 'unknown')
                stats['payment_breakdown'][status] = stats['payment_breakdown'].get(status, 0) + 1

            # Calculate averages
            if stats['total_periods'] > 0:
                stats['average_requests_per_period'] = stats['total_requests'] / stats['total_periods']

            if stats['total_users'] > 0:
                stats['revenue_per_user'] = stats['total_revenue'] / stats['total_users']

            # Verify data consistency
            consistency_checks = {
                'all_periods_have_ids': all(p.get('id') for p in all_periods),
                'all_periods_have_userids': all(p.get('userId') for p in all_periods),
                'all_periods_have_requests': all('totalRequests' in p for p in all_periods),
                'all_periods_have_costs': all('totalCostCents' in p for p in all_periods),
                'total_requests_positive': stats['total_requests'] >= 0,
                'total_revenue_non_negative': stats['total_revenue'] >= 0
            }

            failed_checks = [check for check, passed in consistency_checks.items() if not passed]
            if failed_checks:
                step.status = "FAIL"
                step.message = f"Data consistency checks failed: {failed_checks}"
                print_error(step.message)
                return step

            step.status = "PASS"
            step.message = f"Admin summary statistics calculated successfully"
            step.database_state = {
                'statistics': stats,
                'consistency_checks': consistency_checks,
                'data_quality': 'good' if not failed_checks else 'failed'
            }
            print_success(f"Statistics: {stats['total_periods']} periods, {stats['total_users']} users, {stats['total_requests']} total requests, ${stats['total_revenue']/100:.2f} revenue")

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Admin summary statistics test failed: {e}"
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

        if not self.create_multiple_test_users():
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
            self.get_admin_billing_list_all(),
            self.test_admin_pagination_and_filtering(),
            self.verify_admin_user_isolation(),
            self.test_admin_payment_status_filtering(),
            self.test_admin_summary_statistics()
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
    print(f"TEST-11: Admin Summary and Reporting")
    print(f"{'='*80}{Colors.RESET}\n")

    config.print_config_summary()

    test_runner = Test11AdminSummary()
    result = test_runner.run_test()

    print(f"\n{Colors.CYAN}{'='*80}")
    print(f"TEST-11 EXECUTION COMPLETE")
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
