"""
TEST-09: Period Status Transitions
Test ID: TEST-09
Test Name: Period Status Transitions (Pending -> Paid)
Test Type: Functional (Status Update)
Priority: HIGH (Required)
Estimated Duration: 15 minutes

Description:
Test billing period status transitions within the same month.
Verify that periods can be marked as paid while remaining current until the month changes.
This test is completely self-contained and does not rely on other tests.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from uat_framework import (
    DatabaseHelper, HTTPClient, TokenManager, TestReporting,
    TestStep, TestResult, Colors, print_success, print_error, print_warning, print_info
)
from billing_helpers import BillingHelper, BillingDataManager
# Configuration will be loaded from framework config

class Test09PeriodStatusTransitions:
    """TEST-09: Period Status Transitions"""

    def __init__(self):
        self.test_id = "TEST-09"
        self.test_name = "Period Status Transitions"
        self.reporting = TestReporting()
        self.db_helper = DatabaseHelper(config.DATABASE_URL)
        self.http_client = HTTPClient(config.APP_URL)
        self.test_steps = []
        self.start_time = datetime.now()
        self.admin_token = None
        self.user_token = None
        self.test_user_id = None
        self.period_id = None

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
                return False
            self.admin_token = response.json()['token']
            print_success("Admin authentication successful")
        except Exception as e:
            print_error(f"Admin auth failed: {e}")
            return False
        print_success("Environment setup completed")
        return True

    def create_test_user(self) -> bool:
        """Create test user"""
        print_info("Creating test user...")
        try:
            invite_code = config.generate_unique_invite_code("BILLING-TEST-09")
            response, _ = self.http_client.post(
                config.get_endpoint('admin_invites'),
                {"code": invite_code},
                auth_token=self.admin_token
            )
            if response.status_code != config.STATUS_CODES['success']:
                return False

            test_user_email = config.generate_unique_email("billing-test-09")
            test_user_password = "SecurePassword123!"

            response, _ = self.http_client.post(
                config.get_endpoint('user_register'),
                {
                    "email": test_user_email,
                    "password": test_user_password,
                    "confirmPassword": test_user_password,
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
                {"email": test_user_email, "password": test_user_password}
            )
            if response.status_code != config.STATUS_CODES['success']:
                return False

            response_data = response.json()
            self.user_token = response_data['token']
            self.test_user_id = response_data['id']
            print_success(f"Test user created: {test_user_email}")
            return True
        except Exception as e:
            print_error(f"User creation failed: {e}")
            return False

    def get_current_period(self) -> bool:
        """Get current period"""
        try:
            # First, ensure current billing period exists by calling the API
            response, _ = self.http_client.get(
                config.get_endpoint('billing_current'),
                auth_token=self.user_token
            )
            if response.status_code != config.STATUS_CODES['success']:
                print_error(f"Failed to get current billing period: {response.status_code}")
                return False

            query = "SELECT id FROM billing_periods WHERE user_id = %s AND is_current = true"
            results = self.db_helper.execute_query(query, (self.test_user_id,))
            if not results:
                return False
            self.period_id = results[0]['id']
            print_success(f"Current period ID: {self.period_id}")
            return True
        except Exception as e:
            print_error(f"Failed to get period: {e}")
            return False

    def verify_period_created_pending(self) -> TestStep:
        """Step: Verify period created in pending state"""
        step = TestStep(step_number=1, step_name="Period Created Pending", status="PASS", message="...")
        try:
            query = "SELECT payment_status, is_current FROM billing_periods WHERE id = %s"
            results = self.db_helper.execute_query(query, (self.period_id,))
            if not results:
                step.status = "FAIL"
                return step

            period = results[0]
            if period['payment_status'] != 'pending' or not period['is_current']:
                step.status = "FAIL"
                step.message = f"Status: {period['payment_status']}, current: {period['is_current']}"
                print_error(step.message)
                return step

            step.status = "PASS"
            step.message = "Period created with pending status"
            print_success(step.message)
        except Exception as e:
            step.status = "FAIL"
            step.message = str(e)
            print_error(str(e))
        return step

    def transition_period_to_paid(self) -> TestStep:
        """Step: Transition period to paid"""
        step = TestStep(step_number=2, step_name="Transition to Paid", status="PASS", message="...")
        try:
            url = f"{config.get_endpoint('admin_billing_mark_paid').format(periodId=self.period_id)}"
            mark_paid_data = {
                "paidAmountCents": 1000,  # $10.00 in cents
                "paymentReference": "TEST-09-LIFECYCLE-REF",
                "notes": "Test payment for TEST-09 lifecycle"
            }
            response, _ = self.http_client.post(url, mark_paid_data, auth_token=self.admin_token)

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = f"Mark paid failed: {response.status_code}"
                print_error(step.message)
                return step

            step.status = "PASS"
            step.message = "Period marked as paid"
            print_success(step.message)
        except Exception as e:
            step.status = "FAIL"
            step.message = str(e)
            print_error(str(e))
        return step

    def verify_period_paid_status(self) -> TestStep:
        """Step: Verify period status changed to paid"""
        step = TestStep(step_number=3, step_name="Verify Paid Status", status="PASS", message="...")
        try:
            query = "SELECT payment_status FROM billing_periods WHERE id = %s"
            results = self.db_helper.execute_query(query, (self.period_id,))
            if not results or results[0]['payment_status'] != 'paid':
                step.status = "FAIL"
                step.message = f"Status: {results[0]['payment_status'] if results else 'not found'}"
                print_error(step.message)
                return step

            step.status = "PASS"
            step.message = "Period status verified as paid"
            print_success(step.message)
        except Exception as e:
            step.status = "FAIL"
            step.message = str(e)
            print_error(str(e))
        return step

    def verify_period_remains_current(self) -> TestStep:
        """Step: Verify paid period remains current in same month"""
        step = TestStep(step_number=4, step_name="Period Remains Current", status="PASS", message="...")
        try:
            query = "SELECT is_current FROM billing_periods WHERE id = %s"
            results = self.db_helper.execute_query(query, (self.period_id,))

            if not results or not results[0]['is_current']:
                step.status = "FAIL"
                step.message = "Paid period should remain current within same month"
                print_error(step.message)
                return step

            step.status = "PASS"
            step.message = "Paid period correctly remains current"
            print_success(step.message)
        except Exception as e:
            step.status = "FAIL"
            step.message = str(e)
            print_error(str(e))
        return step

    def verify_user_sees_paid_status(self) -> TestStep:
        """Step: Verify user can see paid status via API"""
        step = TestStep(step_number=5, step_name="User Sees Paid Status", status="PASS", message="...")
        try:
            response, _ = self.http_client.get(
                config.get_endpoint('billing_current'),
                auth_token=self.user_token
            )

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = f"Failed to get current period: {response.status_code}"
                print_error(step.message)
                return step

            data = response.json()

            if data.get('paymentStatus') != 'paid':
                step.status = "FAIL"
                step.message = f"User sees status '{data.get('paymentStatus')}', expected 'paid'"
                print_error(step.message)
                return step

            if not data.get('isCurrent'):
                step.status = "FAIL"
                step.message = "User sees period as not current, but it should be current"
                print_error(step.message)
                return step

            step.status = "PASS"
            step.message = "User sees correct paid status and current flag"
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

        if not self.setup_environment() or not self.create_test_user() or not self.get_current_period():
            result = TestResult(
                test_id=self.test_id, test_name=self.test_name, status="ERROR",
                total_steps=0, passed_steps=0, failed_steps=0, skipped_steps=0, error_steps=1,
                total_time=0, start_time=self.start_time
            )
            self.reporting.add_test_result(result)
            return result

        test_steps = [
            self.verify_period_created_pending(),
            self.transition_period_to_paid(),
            self.verify_period_paid_status(),
            self.verify_period_remains_current(),
            self.verify_user_sees_paid_status()
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
    print(f"TEST-09: Period Lifecycle")
    print(f"{'='*80}{Colors.RESET}\n")

    config.print_config_summary()

    test_runner = Test09PeriodStatusTransitions()
    result = test_runner.run_test()

    print(f"\n{Colors.CYAN}{'='*80}")
    print(f"TEST-09 EXECUTION COMPLETE")
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
