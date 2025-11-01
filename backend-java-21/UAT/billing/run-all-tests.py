#!/usr/bin/env python3
"""
TRC Platform Billing API UAT Test Suite Runner
Execute all billing tests in sequence with comprehensive reporting

STUB READY FOR IMPLEMENTATION - Add remaining test imports as they are created
"""

import sys
import os
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add current directory to path
current_dir = Path(__file__).parent

from uat_test_framework import (
    TestReporting, TestResult,
    Colors, print_success, print_error, print_warning, print_info
)
from uat_config import config

class BillingUATTestSuite:
    """Billing API UAT Test Suite Runner"""

    def __init__(self):
        self.suite_start_time = datetime.now()
        self.reporting = TestReporting()
        self.test_results = []
        self.available_tests = [
            {
                'id': 'TEST-01',
                'name': 'User Registration for Billing API Testing',
                'script': 'test-01-user-registration.py',
                'priority': 1,
                'required': True,
                'tags': ['setup', 'user'],
                'description': 'Create dedicated user for billing API testing (self-contained)'
            },
            {
                'id': 'TEST-02',
                'name': 'Get Current Billing Period',
                'script': 'test-02-current-billing-period.py',
                'priority': 2,
                'required': True,
                'tags': ['billing', 'read', 'period'],
                'description': 'Test GET /api/billing/current endpoint (TO IMPLEMENT)'
            },
            {
                'id': 'TEST-03',
                'name': 'List Billing Periods',
                'script': 'test-03-list-billing-periods.py',
                'priority': 3,
                'required': True,
                'tags': ['billing', 'list', 'period'],
                'description': 'Test GET /api/billing/periods endpoint (TO IMPLEMENT)'
            },
            {
                'id': 'TEST-05',
                'name': 'Get Usage Summary',
                'script': 'test-05-usage-summary.py',
                'priority': 5,
                'required': False,
                'tags': ['usage', 'summary', 'analytics'],
                'description': 'Test GET /api/usage/summary endpoint (TO IMPLEMENT)'
            },
            {
                'id': 'TEST-06',
                'name': 'Admin List Billing Periods',
                'script': 'test-06-admin-list-periods.py',
                'priority': 6,
                'required': False,
                'tags': ['admin', 'list', 'filtering'],
                'description': 'Test GET /api/v1/admin/billing/periods endpoint (TO IMPLEMENT)'
            },
            {
                'id': 'TEST-07',
                'name': 'Admin Mark Period as Paid',
                'script': 'test-07-admin-mark-paid.py',
                'priority': 7,
                'required': True,
                'tags': ['admin', 'payment', 'paid'],
                'description': 'Test POST mark-paid endpoint (TO IMPLEMENT)'
            },
            {
                'id': 'TEST-08',
                'name': 'Admin Mark Period as Overdue',
                'script': 'test-08-admin-mark-overdue.py',
                'priority': 8,
                'required': False,
                'tags': ['admin', 'payment', 'overdue'],
                'description': 'Test POST mark-overdue endpoint (TO IMPLEMENT)'
            },
            {
                'id': 'TEST-09',
                'name': 'Admin Mark Period as Waived',
                'script': 'test-09-admin-mark-waived.py',
                'priority': 9,
                'required': False,
                'tags': ['admin', 'payment', 'waived'],
                'description': 'Test POST mark-waived endpoint (TO IMPLEMENT)'
            },
            {
                'id': 'TEST-10',
                'name': 'Billing Period Lifecycle',
                'script': 'test-10-billing-period-lifecycle.py',
                'priority': 10,
                'required': False,
                'tags': ['lifecycle', 'integration', 'payment'],
                'description': 'Test complete billing period lifecycle (TO IMPLEMENT)'
            },
        ]

    def verify_environment(self) -> bool:
        """Verify test environment is ready"""
        print_info("Verifying Billing API test environment...")

        # Check if required scripts exist
        missing_scripts = []
        for test in self.available_tests[:1]:  # At least check TEST-01
            script_path = current_dir / test['script']
            if not script_path.exists():
                missing_scripts.append(test['script'])

        if missing_scripts:
            print_error(f"Missing test scripts: {missing_scripts}")
            return False

        # Check Python dependencies
        try:
            import requests
            import psycopg2
            import jwt
            import colorama
            import bcrypt
            print_success("Python dependencies verified")
        except ImportError as e:
            print_error(f"Missing Python dependency: {e}")
            print_warning("Run: uv sync")
            return False

        # Check environment variables (optional)
        print_info(f"App URL: {config.APP_URL}")
        print_info(f"Database: {config.DATABASE_URL}")
        print_info(f"Mailcatcher: {config.MAILCATCHER_URL}")

        print_success("Environment verification completed")
        return True

    def get_tests_to_run(self, required_only: bool = False, filter_tag: str = None) -> List[Dict]:
        """Get tests to run based on filters"""
        tests = self.available_tests

        if required_only:
            tests = [t for t in tests if t['required']]
            print_info(f"Running required tests only ({len(tests)} tests)")

        if filter_tag:
            tests = [t for t in tests if filter_tag.lower() in [tag.lower() for tag in t['tags']]]
            print_info(f"Running tests with tag '{filter_tag}' ({len(tests)} tests)")

        return tests

    def run_individual_test(self, test_info: Dict[str, Any]) -> Optional[TestResult]:
        """Run an individual test script"""
        test_id = test_info['id']
        test_name = test_info['name']
        script_path = current_dir / test_info['script']

        print(f"\n{Colors.CYAN}{'='*60}")
        print(f"{'='*60}")
        print(f"🚀 EXECUTING {test_id}: {test_name}")
        print(f"{'='*60}")
        print(f"{'='*60}{Colors.RESET}")

        print_info(f"Script: {test_info['script']}")
        print_info(f"Priority: {test_info['priority']}")
        print_info(f"Required: {test_info['required']}")
        print_info(f"Tags: {', '.join(test_info['tags'])}")
        print_info(f"Description: {test_info['description']}")

        try:
            # Import and run the test module
            module_name = test_info['script'].replace('.py', '')
            spec = __import__(module_name)

            # Check if the module has a main function
            if hasattr(spec, 'main') and callable(spec.main):
                print_info(f"Running {test_id}...")
                start_time = time.time()

                # Execute the test
                success = spec.main()

                execution_time = time.time() - start_time

                # Create a basic test result
                result = TestResult(
                    test_id=test_id,
                    test_name=test_name,
                    status="PASS" if success else "FAIL",
                    total_steps=1,
                    passed_steps=1 if success else 0,
                    failed_steps=0 if success else 1,
                    skipped_steps=0,
                    error_steps=0,
                    total_time=execution_time,
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    test_steps=[]
                )

                if success:
                    print_success(f"✅ {test_id} completed successfully")
                else:
                    print_error(f"❌ {test_id} failed")

                return result
            else:
                print_error(f"Test script {test_info['script']} does not have a main() function")
                return TestResult(
                    test_id=test_id,
                    test_name=test_name,
                    status="ERROR",
                    total_steps=0,
                    passed_steps=0,
                    failed_steps=0,
                    skipped_steps=0,
                    error_steps=1,
                    total_time=0,
                    start_time=datetime.now(),
                    test_steps=[]
                )

        except ModuleNotFoundError:
            print_warning(f"Test {test_id} not yet implemented (file not found)")
            return TestResult(
                test_id=test_id,
                test_name=test_name,
                status="SKIP",
                total_steps=0,
                passed_steps=0,
                failed_steps=0,
                skipped_steps=1,
                error_steps=0,
                total_time=0,
                start_time=datetime.now(),
                test_steps=[]
            )
        except Exception as e:
            print_error(f"Failed to execute {test_id}: {e}")

            return TestResult(
                test_id=test_id,
                test_name=test_name,
                status="ERROR",
                total_steps=0,
                passed_steps=0,
                failed_steps=0,
                skipped_steps=0,
                error_steps=1,
                total_time=0,
                start_time=datetime.now(),
                test_steps=[]
            )

    def run_all_tests(self, tests: List[Dict]) -> bool:
        """Run all selected tests"""
        print(f"\n{Colors.CYAN}{'='*80}")
        print(f"{'='*80}")
        print(f"🧪 TRC PLATFORM BILLING API UAT TEST SUITE")
        print(f"{'='*80}")
        print(f"{'='*80}{Colors.RESET}\n")

        print(f"Tests to run: {len(tests)}")
        print(f"Start time: {self.suite_start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

        for test in tests:
            result = self.run_individual_test(test)
            if result:
                self.test_results.append(result)

        return self.generate_summary_report()

    def generate_summary_report(self) -> bool:
        """Generate comprehensive test report"""
        self.reporting.set_end_time()
        end_time = datetime.now()

        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.is_success())
        failed_tests = sum(1 for r in self.test_results if r.status == "FAIL")
        skipped_tests = sum(1 for r in self.test_results if r.status == "SKIP")
        error_tests = sum(1 for r in self.test_results if r.status == "ERROR")

        total_time = (end_time - self.suite_start_time).total_seconds()

        print(f"\n{Colors.CYAN}{'='*80}")
        print(f"{'='*80}")
        print(f"📊 UAT TEST EXECUTION REPORT - BILLING API")
        print(f"{'='*80}")
        print(f"{'='*80}{Colors.RESET}\n")

        print(f"Date: {self.suite_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {total_time:.2f} seconds")
        print(f"{'='*80}")
        print(f"Tests Total: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Skipped: {skipped_tests}")
        print(f"Errors: {error_tests}")
        print(f"{'='*80}")
        if total_tests > 0:
            print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"{'='*80}\n")

        # Individual test results
        for result in self.test_results:
            status_color = Colors.GREEN if result.is_success() else (Colors.YELLOW if result.status == "SKIP" else Colors.RED)
            print(f"  {result.test_id}: {result.test_name} - {status_color}{result.status}{Colors.RESET}")

            if result.status == 'FAIL':
                print(f"    ❌ FAILED")
            elif result.status == 'SKIP':
                print(f"    ⏭ SKIPPED (not yet implemented)")
            elif result.status == 'ERROR':
                print(f"    ⚠ ERROR")

            print(f"{'='*80}")

        print(f"\n{Colors.CYAN}🏁 TEST SUITE EXECUTION COMPLETE{Colors.RESET}\n")

        if failed_tests == 0 and error_tests == 0:
            print_success(f"All {passed_tests} implemented tests passed!")
            return True
        elif skipped_tests > 0 and failed_tests == 0 and error_tests == 0:
            print_warning(f"{passed_tests} tests passed, {skipped_tests} tests skipped (not implemented)")
            return True
        else:
            print_error(f"{failed_tests} tests failed, {error_tests} tests with errors")
            return False

    def run(self, required_only: bool = False, filter_tag: str = None) -> bool:
        """Run the test suite"""
        if not self.verify_environment():
            print_error("Environment verification failed")
            return False

        tests = self.get_tests_to_run(required_only, filter_tag)

        if not tests:
            print_error("No tests selected to run")
            return False

        return self.run_all_tests(tests)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='TRC Platform Billing API UAT Test Suite',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Run all tests
  python run-all-tests.py

  # Run required tests only
  python run-all-tests.py --required-only

  # Run tests with specific tag
  python run-all-tests.py --filter admin
  python run-all-tests.py --filter payment
  python run-all-tests.py --filter lifecycle
        '''
    )

    parser.add_argument(
        '--required-only',
        action='store_true',
        help='Run only required tests'
    )

    parser.add_argument(
        '--filter',
        type=str,
        help='Filter tests by tag (e.g., admin, payment, lifecycle)'
    )

    args = parser.parse_args()

    suite = BillingUATTestSuite()
    success = suite.run(required_only=args.required_only, filter_tag=args.filter)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
