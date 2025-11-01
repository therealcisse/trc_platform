#!/usr/bin/env python3
"""
TEST-05: Get Usage Summary
Test ID: TEST-05
Test Name: Get Usage Summary
Test Type: Functional (Read)
Priority: HIGH (Required)
Estimated Duration: 12 minutes

Description:
Test GET /api/billing/summary endpoint. Verify current period usage metrics and cost calculations.
Validate summary reflects accurate request counts and totals.
This test is completely self-contained and does not rely on other tests.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from uat_test_framework import (
    DatabaseHelper, HTTPClient, TokenManager, TestReporting,
    TestStep, TestResult, Colors, print_success, print_error, print_warning, print_info,
    extract_jwt_token, EmailVerificationHelper, wait_for_email_verification
)
from uat_config import config
from billing_helpers import BillingDataManager, BillingHelper

class Test05UsageSummary:
    """TEST-05: Get Usage Summary"""

    def __init__(self):
        self.test_id = "TEST-05"
        self.test_name = "Get Usage Summary"
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
            invite_code = config.generate_unique_invite_code("BILLING-TEST-05")
            response, _ = self.http_client.post(
                config.get_endpoint('admin_invites'),
                {"code": invite_code},
                auth_token=self.admin_token
            )
            if response.status_code != config.STATUS_CODES['success']:
                print_error("Failed to create invite code")
                return False

            self.test_user_email = config.generate_unique_email("billing-test-05")
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

    def add_usage_data(self) -> bool:
        """Add usage data to current billing period"""
        print_info("Adding usage data...")

        try:
            # First, ensure current billing period exists by calling the API
            response, _ = self.http_client.get(
                config.get_endpoint('billing_current'),
                auth_token=self.user_token
            )
            if response.status_code != config.STATUS_CODES['success']:
                print_error(f"Failed to get current billing period: {response.status_code}")
                return False

            # Get current period
            query = """
                SELECT id FROM billing_periods
                WHERE user_id = %s AND is_current = true
            """
            results = self.db_helper.execute_query(query, (self.test_user_id,))
            if not results:
                print_error("No current billing period found")
                return False

            period_id = results[0]['id']

            # Add 10 requests with costs
            total_cost = 0
            for i in range(1, 11):
                cost_cents = config.COST_PER_REQUEST_CENTS  # 50 cents per request (fixed)
                total_cost += cost_cents

                # Generate UUID for request log
                import uuid
                request_id = str(uuid.uuid4())
                flow_id = f"flow-{i}"

                query = """
                    INSERT INTO request_logs
                    (id, user_id, billing_period_id, service, request_ts, duration_ms,
                     request_bytes, response_bytes, status, request_id, flow_id)
                    VALUES (%s, %s, %s, %s, NOW(), %s, %s, %s, %s, %s, %s)
                """
                self.db_helper.execute_update(
                    query,
                    (request_id, self.test_user_id, period_id, 'core.image_solve',
                     1000 + (i * 100),  # duration_ms (increasing)
                     500,  # request_bytes
                     1000 + (i * 200),  # response_bytes (increasing)
                     'SUCCESS',  # status
                     request_id,  # request_id
                     flow_id)  # flow_id
                )

            # Update period totals
            query = """
                UPDATE billing_periods
                SET total_requests = %s, total_cost_cents = %s
                WHERE id = %s
            """
            self.db_helper.execute_update(
                query,
                (10, total_cost, period_id)
            )

            print_success(f"Added 10 requests with total cost {total_cost} cents")
            return True

        except Exception as e:
            print_error(f"Failed to add usage data: {e}")
            return False

    def get_usage_summary(self) -> TestStep:
        """Step: Get usage summary"""
        step = TestStep(
            step_number=1,
            step_name="Get Usage Summary",
            status="PASS",
            message="Retrieving usage summary..."
        )

        try:
            response, response_time = self.http_client.get(
                config.get_endpoint('usage_summary'),
                auth_token=self.user_token
            )
            step.response_time = response_time

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = f"Failed to get summary: {response.status_code}"
                print_error(step.message)
                return step

            response_data = response.json()
            step.response_data = response_data

            # Validate required fields
            required_fields = ['today', 'yesterday', 'last7Days', 'thisMonth']
            missing = [f for f in required_fields if f not in response_data]

            if missing:
                step.status = "FAIL"
                step.message = f"Missing fields: {missing}"
                print_error(step.message)
                return step

            step.status = "PASS"
            step.message = f"Usage summary retrieved: today={response_data['today']}, this month={response_data['thisMonth']}, last 7 days={response_data['last7Days']}"
            step.database_state = {
                'today_requests': response_data['today'],
                'yesterday_requests': response_data['yesterday'],
                'last_7_days_requests': response_data['last7Days'],
                'this_month_requests': response_data['thisMonth'],
                'last_request_at': response_data.get('lastRequestAt')
            }
            print_success(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Failed to get usage summary: {e}"
            print_error(step.message)

        return step

    def verify_cost_calculations(self) -> TestStep:
        """Step: Verify cost calculations"""
        step = TestStep(
            step_number=2,
            step_name="Verify Cost Calculations",
            status="PASS",
            message="Validating cost calculations..."
        )

        try:
            response, _ = self.http_client.get(
                config.get_endpoint('usage_summary'),
                auth_token=self.user_token
            )

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = "Failed to retrieve summary"
                return step

            data = response.json()

            # Validate usage data types and logical consistency
            for field in ['today', 'yesterday', 'last7Days', 'thisMonth']:
                if not isinstance(data[field], int) or data[field] < 0:
                    step.status = "FAIL"
                    step.message = f"Invalid {field}: {data[field]}"
                    print_error(step.message)
                    return step

            # Validate logical consistency: last7Days should be >= today
            if data['last7Days'] < data['today']:
                step.status = "FAIL"
                step.message = f"Logical error: last7Days ({data['last7Days']}) should be >= today ({data['today']})"
                print_error(step.message)
                return step

            # Validate logical consistency: thisMonth should be >= today
            if data['thisMonth'] < data['today']:
                step.status = "FAIL"
                step.message = f"Logical error: thisMonth ({data['thisMonth']}) should be >= today ({data['today']})"
                print_error(step.message)
                return step

            # Verify actual cost calculations in the database
            current_period = self.billing_helper.get_current_period_from_db(self.test_user_id)
            if not current_period:
                step.status = "FAIL"
                step.message = "No current billing period found"
                print_error(step.message)
                return step

            period_id = current_period['id']

            # Verify cost calculation accuracy
            cost_details = self.billing_helper.verify_period_cost_details(period_id)
            if not cost_details:
                step.status = "FAIL"
                step.message = "Failed to get cost details"
                print_error(step.message)
                return step

            if not cost_details['cost_matches']:
                step.status = "FAIL"
                step.message = f"Cost calculation mismatch: actual {cost_details['actual_cost']} cents, expected {cost_details['calculated_cost']} cents"
                print_error(step.message)
                return step

            # Verify request count consistency with usage summary
            if cost_details['total_requests'] != data['thisMonth']:
                step.status = "FAIL"
                step.message = f"Request count mismatch: billing period shows {cost_details['total_requests']}, usage summary shows {data['thisMonth']}"
                print_error(step.message)
                return step

            step.status = "PASS"
            step.message = f"Cost calculation verified: {cost_details['total_requests']} requests = {cost_details['actual_cost']} cents ({cost_details['actual_cost']//100}.{cost_details['actual_cost']%100:02d})"
            step.database_state = {
                'today': data['today'],
                'yesterday': data['yesterday'],
                'last7Days': data['last7Days'],
                'thisMonth': data['thisMonth'],
                'period_requests': cost_details['total_requests'],
                'period_cost_cents': cost_details['actual_cost'],
                'cost_calculation_correct': cost_details['cost_matches'],
                'last_request_at': data.get('lastRequestAt')
            }
            print_success(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Calculation verification failed: {e}"
            print_error(step.message)

        return step

    def test_boundary_values(self) -> TestStep:
        """Step: Test boundary values and edge cases"""
        step = TestStep(
            step_number=3,
            step_name="Test Boundary Values",
            status="PASS",
            message="Testing boundary values and edge cases..."
        )

        try:
            # Test boundary value calculations
            boundary_test_cases = [
                {"requests": 0, "expected_cost": 0, "description": "Zero requests"},
                {"requests": 1, "expected_cost": 50, "description": "Single request"},
                {"requests": 10, "expected_cost": 500, "description": "Ten requests"},
                {"requests": 100, "expected_cost": 5000, "description": "100 requests"},
                {"requests": 1000, "expected_cost": 50000, "description": "1000 requests (high volume)"},
            ]

            all_passed = True
            for test_case in boundary_test_cases:
                num_requests = test_case["requests"]
                expected_cost = test_case["expected_cost"]
                description = test_case["description"]

                actual_cost = self.billing_helper.calculate_expected_cost(num_requests)
                if actual_cost != expected_cost:
                    step.status = "FAIL"
                    step.message = f"Boundary test failed for {description}: expected {expected_cost}, got {actual_cost}"
                    print_error(step.message)
                    all_passed = False
                else:
                    print_success(f"✓ {description}: {num_requests} requests = {actual_cost} cents")

            # Test payment amount edge cases if we have a paid period
            current_period = self.billing_helper.get_current_period_from_db(self.test_user_id)
            if current_period and current_period['payment_status'] == 'paid':
                period_id = current_period['id']

                # Test payment amount edge cases
                period_details = self.billing_helper.verify_period_cost_details(period_id)
                if period_details:
                    total_cost = period_details.get('actual_cost', 0)
                    paid_amount = period_details.get('paid_amount', 0)

                    # Test: Exact payment match
                    if paid_amount == total_cost and total_cost > 0:
                        print_success(f"✓ Exact payment match: {paid_amount} cents")

                    # Test: Overpayment scenario (shouldn't happen but let's detect it)
                    if paid_amount > total_cost:
                        print_warning(f"⚠ Overpayment detected: paid {paid_amount} cents, cost {total_cost} cents")

                    # Test: Zero payment on non-zero cost (shouldn't happen)
                    if total_cost > 0 and paid_amount == 0:
                        print_warning(f"⚠ Zero payment for non-zero cost: {total_cost} cents")

            # Test extreme calculation scenarios
            extreme_values = [0, 1, 99999, 999999]
            calculation_issues = []

            for value in extreme_values:
                try:
                    cost = self.billing_helper.calculate_expected_cost(value)
                    # Verify calculation doesn't overflow
                    if cost < 0 or cost > 999999999:  # $10,000 max
                        calculation_issues.append(f"Invalid cost calculation for {value} requests: {cost}")
                except Exception as e:
                    calculation_issues.append(f"Calculation error for {value} requests: {e}")

            if calculation_issues:
                step.status = "FAIL"
                step.message = f"Boundary calculation issues: {', '.join(calculation_issues)}"
                print_error(step.message)
                all_passed = False

            if all_passed:
                step.status = "PASS"
                step.message = "Boundary value tests passed successfully"
                step.database_state = {
                    'boundary_cases_tested': len(boundary_test_cases),
                    'extreme_values_tested': len(extreme_values),
                    'calculation_issues': len(calculation_issues)
                }
                print_success(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Boundary value test failed: {e}"
            print_error(step.message)

        return step

    def verify_last_request_timestamp(self) -> TestStep:
        """Step: Verify last request timestamp"""
        step = TestStep(
            step_number=4,
            step_name="Verify Last Request Timestamp",
            status="PASS",
            message="Validating last request timestamp..."
        )

        try:
            response, _ = self.http_client.get(
                config.get_endpoint('usage_summary'),
                auth_token=self.user_token
            )

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = "Failed to retrieve summary"
                return step

            data = response.json()

            # Check if lastRequestAt exists and is valid
            last_request_at = data.get('lastRequestAt')
            if last_request_at is None:
                # This is valid if no requests have been made
                step.status = "PASS"
                step.message = "No previous requests found"
                print_success(step.message)
            else:
                # Validate timestamp format (ISO format)
                if not isinstance(last_request_at, str):
                    step.status = "FAIL"
                    step.message = f"Invalid lastRequestAt format: {last_request_at}"
                    print_error(step.message)
                    return step

                step.status = "PASS"
                step.message = f"Last request timestamp valid: {last_request_at}"
                print_success(step.message)

            step.database_state = {
                'last_request_at': last_request_at,
                'timestamp_valid': True
            }

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Timestamp verification failed: {e}"
            print_error(step.message)

        return step

    def verify_request_logs_consistency(self) -> TestStep:
        """Step: Verify usage summary matches request logs count"""
        step = TestStep(
            step_number=5,
            step_name="Verify Request Logs Consistency",
            status="PASS",
            message="Comparing with request logs..."
        )

        try:
            response, _ = self.http_client.get(
                config.get_endpoint('usage_summary'),
                auth_token=self.user_token
            )

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = "Failed to retrieve summary"
                return step

            api_data = response.json()

            # Count request logs for today from database
            from datetime import datetime
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            query = """
                SELECT COUNT(*) as count FROM request_logs
                WHERE user_id = %s AND request_ts >= %s
            """
            db_results = self.db_helper.execute_query(query, (self.test_user_id, today))

            today_db_count = db_results[0]['count'] if db_results else 0

            # Compare today's count
            if api_data['today'] != today_db_count:
                step.status = "FAIL"
                step.message = f"Today's count mismatch: API {api_data['today']} vs DB {today_db_count}"
                print_error(step.message)
                return step

            step.status = "PASS"
            step.message = f"Usage summary matches request logs: today={api_data['today']}"
            step.database_state = {
                'api_today': api_data['today'],
                'db_today': today_db_count,
                'counts_match': True,
                'total_requests': api_data['thisMonth']
            }
            print_success(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Request logs verification failed: {e}"
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

        if not self.add_usage_data():
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

        test_steps = [
            self.get_usage_summary(),
            self.verify_cost_calculations(),
            self.test_boundary_values(),
            self.verify_last_request_timestamp(),
            self.verify_request_logs_consistency()
        ]

        self.test_steps = test_steps

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

        for step in test_steps:
            self.reporting.print_step_result(step)

        self.reporting.print_test_footer(self.test_id, self.test_name, result)
        self.reporting.add_test_result(result)
        self.cleanup()

        return result

def main():
    """Main test execution"""
    print(f"\n{Colors.CYAN}{'='*80}")
    print(f"TEST-05: Get Usage Summary")
    print(f"{'='*80}{Colors.RESET}\n")

    config.print_config_summary()

    test_runner = Test05UsageSummary()
    result = test_runner.run_test()

    print(f"\n{Colors.CYAN}{'='*80}")
    print(f"TEST-05 EXECUTION COMPLETE")
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
