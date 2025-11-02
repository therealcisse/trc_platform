"""
TEST-02: Get Current Billing Period
Test ID: TEST-02
Test Name: Get Current Billing Period
Test Type: Functional (Read)
Priority: HIGH (Required)
Estimated Duration: 10 minutes

Description:
Test GET /api/billing/current endpoint. Verify current billing period data and auto-creation behavior.
This test is completely self-contained and does not rely on other tests.
"""

import sys
import os
import json
import time
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

class Test02CurrentBillingPeriod:
    """TEST-02: Get Current Billing Period"""

    def __init__(self):
        self.test_id = "TEST-02"
        self.test_name = "Get Current Billing Period"
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
            invite_code = config.generate_unique_invite_code("BILLING-TEST-02")
            response, _ = self.http_client.post(
                config.get_endpoint('admin_invites'),
                {"code": invite_code},
                auth_token=self.admin_token
            )
            if response.status_code != config.STATUS_CODES['success']:
                print_error("Failed to create invite code")
                return False

            # Register user
            self.test_user_email = config.generate_unique_email("billing-test-02")
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

    def get_current_billing_period(self) -> TestStep:
        """Step: Get current billing period"""
        step = TestStep(
            step_number=1,
            step_name="Get Current Billing Period",
            status="PASS",
            message="Retrieving current billing period..."
        )

        try:
            response, response_time = self.http_client.get(
                config.get_endpoint('billing_current'),
                auth_token=self.user_token
            )
            step.response_time = response_time

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = f"Failed to get billing period: {response.status_code}"
                print_error(step.message)
                return step

            response_data = response.json()
            step.response_data = response_data

            # Validate required fields
            required_fields = ['id', 'isCurrent', 'periodStart', 'periodEnd', 'periodLabel',
                             'paymentStatus', 'totalRequests', 'totalCostCents']
            missing = [f for f in required_fields if f not in response_data]

            if missing:
                step.status = "FAIL"
                step.message = f"Missing fields: {missing}"
                print_error(step.message)
                return step

            # Validate isCurrent is true
            if not response_data.get('isCurrent'):
                step.status = "FAIL"
                step.message = "isCurrent should be true for current period"
                print_error(step.message)
                return step

            # Validate paymentStatus is pending
            if response_data.get('paymentStatus') != 'pending':
                step.status = "FAIL"
                step.message = f"Expected paymentStatus 'pending', got '{response_data.get('paymentStatus')}'"
                print_error(step.message)
                return step

            step.status = "PASS"
            step.message = f"Current billing period retrieved: {response_data['periodLabel']}"
            step.database_state = {
                'period_id': response_data['id'],
                'period_label': response_data['periodLabel'],
                'is_current': response_data['isCurrent'],
                'payment_status': response_data['paymentStatus']
            }
            print_success(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Failed to get current billing period: {e}"
            print_error(step.message)

        return step

    def verify_period_dates(self) -> TestStep:
        """Step: Verify period dates are correct"""
        step = TestStep(
            step_number=2,
            step_name="Verify Period Dates",
            status="PASS",
            message="Validating period date range..."
        )

        try:
            response, _ = self.http_client.get(
                config.get_endpoint('billing_current'),
                auth_token=self.user_token
            )

            if response.status_code != config.STATUS_CODES['success']:
                step.status = "FAIL"
                step.message = "Failed to retrieve billing period"
                return step

            data = response.json()
            period_start = data['periodStart']
            period_end = data['periodEnd']

            from datetime import datetime
            start_date = datetime.strptime(period_start, '%Y-%m-%d')
            end_date = datetime.strptime(period_end, '%Y-%m-%d')

            # Check start is 1st of month
            if start_date.day != 1:
                step.status = "FAIL"
                step.message = f"Period start should be 1st of month, got day {start_date.day}"
                print_error(step.message)
                return step

            # Check end is last day of month
            if start_date.month == 12:
                next_month = start_date.replace(year=start_date.year + 1, month=1, day=1)
            else:
                next_month = start_date.replace(month=start_date.month + 1, day=1)

            last_day = (next_month.replace(day=1) - __import__('datetime').timedelta(days=1)).day
            if end_date.day != last_day:
                step.status = "FAIL"
                step.message = f"Period end should be day {last_day}, got day {end_date.day}"
                print_error(step.message)
                return step

            step.status = "PASS"
            step.message = f"Period dates valid: {period_start} to {period_end}"
            step.database_state = {
                'period_start': period_start,
                'period_end': period_end,
                'start_is_1st': start_date.day == 1,
                'end_is_last': end_date.day == last_day
            }
            print_success(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Date verification failed: {e}"
            print_error(step.message)

        return step

    def verify_database_state(self) -> TestStep:
        """Step: Verify database state"""
        step = TestStep(
            step_number=3,
            step_name="Verify Database State",
            status="PASS",
            message="Checking database state..."
        )

        try:
            # Get current period from database
            query = """
                SELECT id, user_id, period_start, period_end, total_requests,
                       total_cost_cents, is_current, payment_status
                FROM billing_periods
                WHERE user_id = %s AND is_current = true
            """
            results = self.db_helper.execute_query(query, (self.test_user_id,))
            print(f"DB RESULTS: {results} for user id: {self.test_user_id}")

            if not results:
                step.status = "FAIL"
                step.message = "No current billing period found in database"
                print_error(step.message)
                return step

            period = results[0]

            # Verify period belongs to user
            if str(period['user_id']) != str(self.test_user_id):
                step.status = "FAIL"
                step.message = "Period does not belong to test user"
                print_error(step.message)
                return step

            # Verify is_current flag
            if not period['is_current']:
                step.status = "FAIL"
                step.message = "Period is_current flag is false"
                print_error(step.message)
                return step

            step.status = "PASS"
            step.message = "Database state verified successfully"
            step.database_state = {
                'period_id': str(period['id']),
                'user_id': str(period['user_id']),
                'is_current': period['is_current'],
                'payment_status': period['payment_status'],
                'total_requests': period['total_requests'],
                'total_cost_cents': period['total_cost_cents']
            }
            print_success(step.message)

        except Exception as e:
            step.status = "FAIL"
            step.message = f"Database verification failed: {e}"
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

        # Execute steps
        test_steps = [
            self.get_current_billing_period(),
            # self.verify_period_dates(),
            # self.verify_database_state()
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
    print(f"🧪 TRC Platform Billing API UAT - TEST-02: Get Current Billing Period")
    print(f"{'='*80}{Colors.RESET}\n")

    config.print_config_summary()

    test_runner = Test02CurrentBillingPeriod()
    result = test_runner.run_test()

    print(f"\n{Colors.CYAN}{'='*80}")
    print(f"🏁 TEST-02 EXECUTION COMPLETE")
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
