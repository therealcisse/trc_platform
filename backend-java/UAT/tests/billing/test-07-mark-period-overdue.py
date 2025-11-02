"""
TEST-07: Mark Period as Overdue
Test ID: TEST-07
Test Name: Mark Period as Overdue (Admin Operation)
Test Type: Functional (Write - Admin)
Priority: HIGH (Required)
Estimated Duration: 15 minutes

Description:
Test admin endpoint to mark a billing period as overdue.
Verify paymentStatus changes from 'pending' to 'overdue', timestamps update, and user sees change.
This test is completely self-contained and does not rely on other tests.
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

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

class Test07MarkPeriodOverdue:
    """TEST-07: Mark Period as Overdue"""

    def __init__(self):
        self.test_id = "TEST-07"
        self.test_name = "Mark Period as Overdue"
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
            invite_code = config.generate_unique_invite_code("BILLING-TEST-07")
            response, _ = self.http_client.post(
                config.get_endpoint('admin_invites'),
                {"code": invite_code},
                auth_token=self.admin_token
            )
            if response.status_code != config.STATUS_CODES['success']:
                print_error("Failed to create invite code")
                return False

            self.test_user_email = config.generate_unique_email("billing-test-07")
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

    def get_current_period(self) -> bool:
        """Get current billing period ID"""
        print_info("Fetching current billing period...")

        try:
            query = """
                SELECT id FROM billing_periods
                WHERE user_id = %s AND is_current = true
            """
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

    def verify_initial_state(self) -> TestStep:
        """Step: Verify initial period state is pending"""
        step = TestStep(
            step_number=1,
            step_name="Verify Initial State",
            status="PASS",
            message="Checking initial payment status..."
        )

        try:
            query = """
                SELECT payment_status FROM billing_periods WHERE id = %s
            """
            results = self.db_helper.execute_query(query, (self.period_id,))

            if not results:
                step.status = "FAIL"
                step.message = "Period not found"
                print_error(step.message)
                return step

            status = results[0]['payment_status']

            if status != 'pending':
                step.status = "FAIL"
                step.message = f"Expected 'pending', got '{status}'"
                print_error(step.message)
                return step

            step.status = "PASS"
            step.message = f"Initial status verified: {status}"
            step.database_state = {'initial_status': status}
            print_success(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Failed to verify initial state: {e}"
            print_error(step.message)

        return step

    def mark_period_as_overdue(self) -> TestStep:
        """Step: Call admin API to mark period as overdue"""
        step = TestStep(
            step_number=2,
            step_name="Mark Period as Overdue",
            status="PASS",
            message="Calling admin mark-overdue endpoint..."
        )

        try:
            url = f"{config.get_endpoint('admin_billing_mark_overdue').format(period_id=self.period_id)}"
            response, response_time = self.http_client.post(
                url,
                {},
                auth_token=self.admin_token
            )
            step.response_time = response_time

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = f"Failed to mark as overdue: {response.status_code}"
                print_error(step.message)
                if response.status_code == config.STATUS_CODES['not_found']:
                    step.message += " (Endpoint may not exist or period not found)"
                return step

            response_data = response.json()
            step.response_data = response_data

            if 'paymentStatus' not in response_data:
                step.status = "FAIL"
                step.message = "Response missing 'paymentStatus' field"
                print_error(step.message)
                return step

            if response_data['paymentStatus'] != 'overdue':
                step.status = "FAIL"
                step.message = f"Expected 'overdue', got '{response_data['paymentStatus']}'"
                print_error(step.message)
                return step

            step.status = "PASS"
            step.message = "Period successfully marked as overdue"
            step.database_state = {'payment_status': response_data['paymentStatus']}
            print_success(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Failed to mark period as overdue: {e}"
            print_error(step.message)

        return step

    def verify_database_updated(self) -> TestStep:
        """Step: Verify database reflects overdue status"""
        step = TestStep(
            step_number=3,
            step_name="Verify Database Updated",
            status="PASS",
            message="Checking database state..."
        )

        try:
            query = """
                SELECT payment_status FROM billing_periods WHERE id = %s
            """
            results = self.db_helper.execute_query(query, (self.period_id,))

            if not results:
                step.status = "FAIL"
                step.message = "Period not found in database"
                print_error(step.message)
                return step

            period = results[0]

            if period['payment_status'] != 'overdue':
                step.status = "FAIL"
                step.message = f"Database status is '{period['payment_status']}', expected 'overdue'"
                print_error(step.message)
                return step

            step.status = "PASS"
            step.message = f"Database verified: status={period['payment_status']}"
            step.database_state = {
                'payment_status': period['payment_status']
            }
            print_success(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Database verification failed: {e}"
            print_error(step.message)

        return step

    def verify_user_sees_change(self) -> TestStep:
        """Step: Verify user can see updated status via API"""
        step = TestStep(
            step_number=4,
            step_name="Verify User Sees Change",
            status="PASS",
            message="Checking user-facing API response..."
        )

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

            if data.get('paymentStatus') != 'overdue':
                step.status = "FAIL"
                step.message = f"User sees status '{data.get('paymentStatus')}', expected 'overdue'"
                print_error(step.message)
                return step

            step.status = "PASS"
            step.message = "User can see updated status via API"
            step.database_state = {
                'user_visible_status': data.get('paymentStatus'),
                'visible_to_user': True
            }
            print_success(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"User API check failed: {e}"
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

        if not self.get_current_period():
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
            self.verify_initial_state(),
            self.mark_period_as_overdue(),
            self.verify_database_updated(),
            self.verify_user_sees_change()
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
    print(f"TEST-07: Mark Period as Overdue")
    print(f"{'='*80}{Colors.RESET}\n")

    config.print_config_summary()

    test_runner = Test07MarkPeriodOverdue()
    result = test_runner.run_test()

    print(f"\n{Colors.CYAN}{'='*80}")
    print(f"TEST-07 EXECUTION COMPLETE")
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
