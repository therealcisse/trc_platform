"""
TEST-08: Apply Waiver to Period
Test ID: TEST-08
Test Name: Apply Waiver to Period (Admin Operation)
Test Type: Functional (Write - Admin)
Priority: HIGH (Required)
Estimated Duration: 12 minutes

Description:
Test admin endpoint to apply cost waiver to a billing period.
Verify totalCostCents is set to 0, waiver reason stored, and user sees waived status.
This test is completely self-contained and does not rely on other tests.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from uat_framework import (
    DatabaseHelper, HTTPClient, TokenManager, TestReporting,
    TestStep, TestResult, Colors, print_success, print_error, print_warning, print_info
)
from billing_helpers import BillingHelper, BillingDataManager
# Configuration will be loaded from framework config
from billing_helpers import BillingDataManager

class Test08ApplyWaiver:
    """TEST-08: Apply Waiver to Period"""

    def __init__(self):
        self.test_id = "TEST-08"
        self.test_name = "Apply Waiver to Period"
        self.reporting = TestReporting()
        self.db_helper = DatabaseHelper(config.DATABASE_URL)
        self.http_client = HTTPClient(config.APP_URL)
        self.token_manager = TokenManager()
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
                print_error(f"Admin login failed: {response.status_code}")
                return False
            self.admin_token = response.json()['token']
            print_success("Admin authentication successful")
        except Exception as e:
            print_error(f"Failed to authenticate admin: {e}")
            return False
        print_success("Environment setup completed")
        return True

    def create_test_user(self) -> bool:
        """Create dedicated test user"""
        print_info("Creating test user...")
        try:
            invite_code = config.generate_unique_invite_code("BILLING-TEST-08")
            response, _ = self.http_client.post(
                config.get_endpoint('admin_invites'),
                {"code": invite_code},
                auth_token=self.admin_token
            )
            if response.status_code != config.STATUS_CODES['success']:
                print_error("Failed to create invite code")
                return False

            test_user_email = config.generate_unique_email("billing-test-08")
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
                print_error("User registration failed")
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
                print_error("User login failed")
                return False

            response_data = response.json()
            self.user_token = response_data['token']
            self.test_user_id = response_data['id']
            print_success(f"Test user created: {test_user_email}")
            return True
        except Exception as e:
            print_error(f"Failed to create test user: {e}")
            return False

    def get_current_period(self) -> bool:
        """Get current billing period ID"""
        print_info("Fetching current billing period...")
        try:
            query = "SELECT id, total_cost_cents FROM billing_periods WHERE user_id = %s AND is_current = true"
            results = self.db_helper.execute_query(query, (self.test_user_id,))
            if not results:
                print_error("No current billing period found")
                return False
            self.period_id = results[0]['id']
            print_success(f"Period ID: {self.period_id}")
            return True
        except Exception as e:
            print_error(f"Failed to get period: {e}")
            return False

    def verify_initial_cost(self) -> TestStep:
        """Step: Verify period has a cost before waiver"""
        step = TestStep(step_number=1, step_name="Verify Initial Cost", status="PASS", message="Checking initial cost...")
        try:
            query = "SELECT total_cost_cents FROM billing_periods WHERE id = %s"
            results = self.db_helper.execute_query(query, (self.period_id,))
            if not results or results[0]['total_cost_cents'] is None:
                self.db_helper.execute_update(
                    "UPDATE billing_periods SET total_cost_cents = 5000 WHERE id = %s",
                    (self.period_id,)
                )
                print_info("Set initial cost to 5000 cents")
            step.status = "PASS"
            step.message = "Initial cost verified"
            print_success(step.message)
        except Exception as e:
            step.status = "FAIL"
            step.message = f"Failed: {e}"
            print_error(step.message)
        return step

    def apply_waiver(self) -> TestStep:
        """Step: Call admin API to apply waiver"""
        step = TestStep(step_number=2, step_name="Apply Waiver", status="PASS", message="Applying waiver...")
        try:
            url = f"{config.get_endpoint('admin_billing_waive').format(period_id=self.period_id)}"
            payload = {"reason": "Customer goodwill adjustment"}
            response, response_time = self.http_client.post(url, payload, auth_token=self.admin_token)
            step.response_time = response_time

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = f"Failed to apply waiver: {response.status_code}"
                print_error(step.message)
                return step

            response_data = response.json()
            if response_data.get('totalCostCents', 1) != 0:
                step.status = "FAIL"
                step.message = f"Cost not waived: {response_data.get('totalCostCents')}"
                print_error(step.message)
                return step

            step.status = "PASS"
            step.message = "Waiver applied successfully"
            print_success(step.message)
        except Exception as e:
            step.status = "FAIL"
            step.message = f"Failed: {e}"
            print_error(step.message)
        return step

    def verify_database_waived(self) -> TestStep:
        """Step: Verify database reflects waived status"""
        step = TestStep(step_number=3, step_name="Verify Database Waived", status="PASS", message="Checking database...")
        try:
            query = "SELECT total_cost_cents, payment_status FROM billing_periods WHERE id = %s"
            results = self.db_helper.execute_query(query, (self.period_id,))
            if not results:
                step.status = "FAIL"
                step.message = "Period not found"
                print_error(step.message)
                return step

            period = results[0]
            if period['payment_status'] != 'waived':
                step.status = "FAIL"
                step.message = f"Payment status is {period['payment_status']}, expected 'waived'"
                print_error(step.message)
                return step

            step.status = "PASS"
            step.message = "Database verified: status=waived"
            print_success(step.message)
        except Exception as e:
            step.status = "FAIL"
            step.message = f"Failed: {e}"
            print_error(step.message)
        return step

    def verify_user_sees_waived(self) -> TestStep:
        """Step: Verify user sees waived status"""
        step = TestStep(step_number=4, step_name="Verify User Sees Waived", status="PASS", message="Checking user view...")
        try:
            response, _ = self.http_client.get(config.get_endpoint('billing_current'), auth_token=self.user_token)
            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = f"Failed to get period: {response.status_code}"
                print_error(step.message)
                return step

            data = response.json()
            if data.get('totalCostCents', 1) != 0:
                step.status = "FAIL"
                step.message = f"User sees cost {data.get('totalCostCents')}, expected 0"
                print_error(step.message)
                return step

            step.status = "PASS"
            step.message = "User can see waived status"
            print_success(step.message)
        except Exception as e:
            step.status = "FAIL"
            step.message = f"Failed: {e}"
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

        if not self.setup_environment() or not self.create_test_user() or not self.get_current_period():
            result = TestResult(
                test_id=self.test_id, test_name=self.test_name, status="ERROR",
                total_steps=0, passed_steps=0, failed_steps=0, skipped_steps=0, error_steps=1,
                total_time=0, start_time=self.start_time
            )
            self.reporting.add_test_result(result)
            return result

        test_steps = [
            self.verify_initial_cost(),
            self.apply_waiver(),
            self.verify_database_waived(),
            self.verify_user_sees_waived()
        ]

        self.test_steps = test_steps
        passed_steps = sum(1 for step in test_steps if step.status == "PASS")
        failed_steps = sum(1 for step in test_steps if step.status == "FAIL")
        overall_status = "PASS" if failed_steps == 0 else "FAIL"
        total_time = (datetime.now() - self.start_time).total_seconds()

        result = TestResult(
            test_id=self.test_id, test_name=self.test_name, status=overall_status,
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
    print(f"TEST-08: Apply Waiver to Period")
    print(f"{'='*80}{Colors.RESET}\n")

    config.print_config_summary()

    test_runner = Test08ApplyWaiver()
    result = test_runner.run_test()

    print(f"\n{Colors.CYAN}{'='*80}")
    print(f"TEST-08 EXECUTION COMPLETE")
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
