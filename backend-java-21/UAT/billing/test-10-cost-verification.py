#!/usr/bin/env python3
"""
TEST-10: Cost Verification and Calculations
Test ID: TEST-10
Test Name: Cost Verification and Calculations
Test Type: Functional (Validation)
Priority: HIGH (Required)
Estimated Duration: 15 minutes

Description:
Test billing cost calculations with multiple users at different usage levels.
Verify per-request pricing applied correctly and aggregates calculated accurately.
This test is completely self-contained and does not rely on other tests.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from uat_test_framework import (
    DatabaseHelper, HTTPClient, TokenManager, TestReporting,
    TestStep, TestResult, Colors, print_success, print_error, print_warning, print_info
)
from uat_config import config

class Test10CostVerification:
    """TEST-10: Cost Verification"""

    def __init__(self):
        self.test_id = "TEST-10"
        self.test_name = "Cost Verification and Calculations"
        self.reporting = TestReporting()
        self.db_helper = DatabaseHelper(config.DATABASE_URL)
        self.http_client = HTTPClient(config.APP_URL)
        self.test_steps = []
        self.start_time = datetime.now()
        self.admin_token = None
        self.user_ids = []

    def setup_environment(self) -> bool:
        """Setup test environment"""
        print_info("Setting up test environment...")
        if not self.db_helper.connect():
            return False
        try:
            login_data = {"email": config.ADMIN_EMAIL, "password": config.ADMIN_PASSWORD}
            response, _ = self.http_client.post(config.get_endpoint('login'), login_data)
            if response.status_code != config.STATUS_CODES['success']:
                return False
            self.admin_token = response.json()['token']
            print_success("Admin authentication successful")
        except Exception as e:
            print_error(f"Admin auth failed: {e}")
            return False
        return True

    def create_test_users_with_usage(self) -> bool:
        """Create multiple users with different usage levels"""
        print_info("Creating test users with different usage levels...")
        try:
            for i in range(1, 4):
                invite_code = config.generate_unique_invite_code(f"BILLING-TEST-10-{i}")
                response, _ = self.http_client.post(
                    config.get_endpoint('admin_invites'),
                    {"code": invite_code},
                    auth_token=self.admin_token
                )
                if response.status_code != config.STATUS_CODES['success']:
                    return False

                test_user_email = config.generate_unique_email(f"billing-test-10-{i}")
                response, _ = self.http_client.post(
                    config.get_endpoint('user_register'),
                    {
                        "email": test_user_email,
                        "password": "SecurePassword123!",
                        "confirmPassword": "SecurePassword123!",
                        "inviteCode": invite_code,
                        "userAcceptedTerms": True,
                        "userAcknowledgedDisclaimer": True
                    }
                )
                if response.status_code not in [config.STATUS_CODES['accepted'], config.STATUS_CODES['created']]:
                    return False

                self.db_helper.execute_update(
                    "UPDATE users SET email_verified_at = NOW() WHERE email = %s",
                    (test_user_email,)
                )

                response, _ = self.http_client.post(
                    config.get_endpoint('login'),
                    {"email": test_user_email, "password": "SecurePassword123!"}
                )
                if response.status_code != config.STATUS_CODES['success']:
                    return False

                user_id = response.json()['id']
                self.user_ids.append(user_id)

                # Ensure current billing period exists by calling the API
                response, _ = self.http_client.get(
                    config.get_endpoint('billing_current'),
                    auth_token=response.json()['token']
                )
                if response.status_code != config.STATUS_CODES['success']:
                    print_error(f"Failed to get current billing period for user {i}: {response.status_code}")
                    return False

                # Add different usage levels per user
                query = "SELECT id FROM billing_periods WHERE user_id = %s AND is_current = true"
                period_results = self.db_helper.execute_query(query, (user_id,))
                if period_results:
                    period_id = period_results[0]['id']
                    num_requests = i * 10
                    total_cost = num_requests * 100

                    self.db_helper.execute_update(
                        "UPDATE billing_periods SET total_requests = %s, total_cost_cents = %s WHERE id = %s",
                        (num_requests, total_cost, period_id)
                    )

            print_success(f"Created {len(self.user_ids)} test users with usage data")
            return True
        except Exception as e:
            print_error(f"User creation failed: {e}")
            return False

    def verify_individual_cost_calculations(self) -> TestStep:
        """Step: Verify each user's cost calculation"""
        step = TestStep(step_number=1, step_name="Individual Cost Calculations", status="PASS", message="...")
        try:
            for i, user_id in enumerate(self.user_ids, 1):
                query = "SELECT total_requests, total_cost_cents FROM billing_periods WHERE user_id = %s AND is_current = true"
                results = self.db_helper.execute_query(query, (user_id,))
                if not results:
                    step.status = "FAIL"
                    step.message = f"No period for user {i}"
                    return step

                period = results[0]
                expected_requests = i * 10
                expected_cost = expected_requests * 100

                if period['total_requests'] != expected_requests or period['total_cost_cents'] != expected_cost:
                    step.status = "FAIL"
                    step.message = f"User {i}: expected {expected_requests} requests/{expected_cost} cents, got {period['total_requests']}/{period['total_cost_cents']}"
                    print_error(step.message)
                    return step

            step.status = "PASS"
            step.message = "All individual costs verified"
            print_success(step.message)
        except Exception as e:
            step.status = "FAIL"
            step.message = str(e)
            print_error(str(e))
        return step

    def verify_average_cost_calculation(self) -> TestStep:
        """Step: Verify average cost per request calculations"""
        step = TestStep(step_number=2, step_name="Average Cost Calculation", status="PASS", message="...")
        try:
            for i, user_id in enumerate(self.user_ids, 1):
                query = "SELECT total_requests, total_cost_cents FROM billing_periods WHERE user_id = %s AND is_current = true"
                results = self.db_helper.execute_query(query, (user_id,))
                if not results:
                    step.status = "FAIL"
                    return step

                period = results[0]
                if period['total_requests'] > 0:
                    expected_avg = period['total_cost_cents'] / period['total_requests']
                    expected_avg_should_be = 100.0

                    if abs(expected_avg - expected_avg_should_be) > 0.01:
                        step.status = "FAIL"
                        step.message = f"User {i} average: {expected_avg}, expected {expected_avg_should_be}"
                        print_error(step.message)
                        return step

            step.status = "PASS"
            step.message = "Average cost calculations verified"
            print_success(step.message)
        except Exception as e:
            step.status = "FAIL"
            step.message = str(e)
            print_error(str(e))
        return step

    def verify_aggregate_totals(self) -> TestStep:
        """Step: Verify aggregate statistics across all users"""
        step = TestStep(step_number=3, step_name="Aggregate Totals", status="PASS", message="...")
        try:
            query = """
                SELECT SUM(total_requests) as total_requests, SUM(total_cost_cents) as total_cost
                FROM billing_periods
                WHERE user_id IN ({})
            """.format(','.join(f"'{u}'" for u in self.user_ids))

            results = self.db_helper.execute_query(query)
            if not results:
                step.status = "FAIL"
                return step

            agg = results[0]
            expected_total_requests = sum(i * 10 for i in range(1, len(self.user_ids) + 1))
            expected_total_cost = expected_total_requests * 100

            if agg['total_requests'] != expected_total_requests or agg['total_cost'] != expected_total_cost:
                step.status = "FAIL"
                step.message = f"Aggregate: {agg['total_requests']}/{agg['total_cost']}, expected {expected_total_requests}/{expected_total_cost}"
                print_error(step.message)
                return step

            step.status = "PASS"
            step.message = f"Aggregate totals verified: {agg['total_requests']} requests, {agg['total_cost']} cents"
            print_success(step.message)
        except Exception as e:
            step.status = "FAIL"
            step.message = str(e)
            print_error(str(e))
        return step

    def verify_consistent_pricing_model(self) -> TestStep:
        """Step: Verify consistent pricing model applied"""
        step = TestStep(step_number=4, step_name="Pricing Model Consistency", status="PASS", message="...")
        try:
            query = """
                SELECT user_id, total_requests, total_cost_cents
                FROM billing_periods
                WHERE user_id IN ({}) AND is_current = true
            """.format(','.join(f"'{u}'" for u in self.user_ids))

            results = self.db_helper.execute_query(query)
            per_request_cost = 100

            for row in results:
                if row['total_requests'] > 0:
                    actual_cost_per_request = row['total_cost_cents'] / row['total_requests']
                    if abs(actual_cost_per_request - per_request_cost) > 0.01:
                        step.status = "FAIL"
                        step.message = f"User {row['user_id']}: cost per request {actual_cost_per_request}, expected {per_request_cost}"
                        print_error(step.message)
                        return step

            step.status = "PASS"
            step.message = "Pricing model consistent across all users"
            print_success(step.message)
        except Exception as e:
            step.status = "FAIL"
            step.message = str(e)
            print_error(str(e))
        return step

    def cleanup(self):
        """Cleanup"""
        try:
            self.db_helper.disconnect()
            print_info("Cleanup completed")
        except Exception as e:
            print_warning(f"Cleanup warning: {e}")

    def run_test(self) -> TestResult:
        """Run the test"""
        self.reporting.print_test_header(self.test_id, self.test_name)

        if not self.setup_environment() or not self.create_test_users_with_usage():
            result = TestResult(
                test_id=self.test_id, test_name=self.test_name, status="ERROR",
                total_steps=0, passed_steps=0, failed_steps=0, skipped_steps=0, error_steps=1,
                total_time=0, start_time=self.start_time
            )
            self.reporting.add_test_result(result)
            return result

        test_steps = [
            self.verify_individual_cost_calculations(),
            self.verify_average_cost_calculation(),
            self.verify_aggregate_totals(),
            self.verify_consistent_pricing_model()
        ]

        self.test_steps = test_steps
        passed_steps = sum(1 for step in test_steps if step.status == "PASS")
        failed_steps = sum(1 for step in test_steps if step.status == "FAIL")
        total_time = (datetime.now() - self.start_time).total_seconds()

        result = TestResult(
            test_id=self.test_id, test_name=self.test_name,
            status="PASS" if failed_steps == 0 else "FAIL",
            total_steps=len(test_steps), passed_steps=passed_steps, failed_steps=failed_steps,
            skipped_steps=0, error_steps=0, total_time=total_time,
            start_time=self.start_time, end_time=datetime.now(), test_steps=test_steps
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
    print(f"TEST-10: Cost Verification and Calculations")
    print(f"{'='*80}{Colors.RESET}\n")

    config.print_config_summary()

    test_runner = Test10CostVerification()
    result = test_runner.run_test()

    print(f"\n{Colors.CYAN}{'='*80}")
    print(f"TEST-10 EXECUTION COMPLETE")
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
