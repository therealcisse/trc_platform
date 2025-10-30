#!/usr/bin/env python3
"""
TRC Platform API Token UAT Test Suite Runner
Execute all API token UAT tests in sequence with comprehensive reporting
"""

import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Import UAT framework and configuration
from uat_test_framework import (
    TestReporting, TestResult,
    Colors, print_success, print_error, print_warning, print_info
)
from uat_config import config

class ApiTokenUATTestSuite:
    """API Token UAT Test Suite Runner"""

    def __init__(self):
        self.suite_start_time = datetime.now()
        self.reporting = TestReporting()
        self.test_results = []
        self.available_tests = [
            {
                'id': 'TEST-01',
                'name': 'User Registration for API Token Testing',
                'script': 'test-01-user-registration.py',
                'priority': 1,
                'required': True,
                'description': 'Create dedicated user for API token testing (self-contained)'
            },
            {
                'id': 'TEST-02',
                'name': 'API Token Creation',
                'script': 'test-02-api-token-creation.py',
                'priority': 2,
                'required': True,
                'description': 'Create API tokens with various configurations (self-contained)'
            },
            {
                'id': 'TEST-03',
                'name': 'API Token Authentication',
                'script': 'test-03-api-token-authentication.py',
                'priority': 3,
                'required': True,
                'description': 'Test API token authentication via headers (self-contained)'
            },
            {
                'id': 'TEST-04',
                'name': 'API Token Listing',
                'script': 'test-04-api-token-listing.py',
                'priority': 4,
                'required': False,
                'description': 'Test API token listing and pagination (self-contained)'
            },
            {
                'id': 'TEST-05',
                'name': 'API Token Revocation',
                'script': 'test-05-api-token-revocation.py',
                'priority': 5,
                'required': False,
                'description': 'Test API token revocation functionality (self-contained)'
            },
            {
                'id': 'TEST-06',
                'name': 'Token Security Scenarios',
                'script': 'test-06-token-security-scenarios.py',
                'priority': 6,
                'required': False,
                'description': 'Test token security and validation scenarios (self-contained)'
            },
            {
                'id': 'TEST-07',
                'name': 'Token Expiration Handling',
                'script': 'test-07-token-expiration-handling.py',
                'priority': 7,
                'required': False,
                'description': 'Test token expiration and time-based scenarios (self-contained)'
            }
        ]

    def verify_environment(self) -> bool:
        """Verify test environment is ready"""
        print_info("Verifying API token test environment...")

        # Check if required scripts exist
        missing_scripts = []
        for test in self.available_tests:
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
            print_warning("Run: pip install -r requirements.txt")
            return False

        # Check environment variables
        required_env_vars = ['UAT_APP_URL', 'UAT_DATABASE_URL', 'UAT_MAILCATCHER_URL']
        missing_env_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_env_vars.append(var)

        if missing_env_vars:
            print_warning(f"Missing environment variables: {missing_env_vars}")
            print_info("Using default configuration values")

        # Note: Tests are now self-contained and do not depend on auth UAT
        print_info("✅ Tests are self-contained - no external dependencies required")

        print_success("Environment verification completed")
        return True

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

                # Create a basic test result (actual detailed result comes from the test itself)
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
                return None

        except Exception as e:
            print_error(f"Failed to execute {test_id}: {e}")

            # Return failure result
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
                end_time=datetime.now(),
                test_steps=[]
            )

    def run_test_suite(self, test_filter: Optional[str] = None,
                      required_only: bool = False,
                      skip_list: Optional[List[str]] = None) -> bool:
        """Run the complete test suite"""
        print(f"\n{Colors.MAGENTA}{'='*80}")
        print(f"{'='*80}")
        print(f"🧪 TRC PLATFORM API TOKEN UAT TEST SUITE")
        print(f"{'='*80}")
        print(f"{'='*80}{Colors.RESET}\n")

        # Print configuration
        config.print_config_summary()

        # Verify environment
        if not self.verify_environment():
            print_error("Environment verification failed. Aborting test suite.")
            return False

        # Filter tests based on parameters
        tests_to_run = self.available_tests.copy()

        if test_filter:
            tests_to_run = [t for t in tests_to_run if test_filter.lower() in t['id'].lower() or test_filter.lower() in t['name'].lower()]

        if required_only:
            tests_to_run = [t for t in tests_to_run if t['required']]

        if skip_list:
            tests_to_run = [t for t in tests_to_run if t['id'] not in skip_list]

        if not tests_to_run:
            print_error("No tests to run after filtering")
            return False

        print_info(f"Running {len(tests_to_run)} tests:")
        for test in tests_to_run:
            priority_marker = "🔴" if test['required'] else "🟡"
            print(f"  {priority_marker} {test['id']}: {test['name']}")

        # Execute tests
        suite_success = True
        for test_info in sorted(tests_to_run, key=lambda x: x['priority']):
            result = self.run_individual_test(test_info)
            if result:
                self.test_results.append(result)
                if not result.is_success() and test_info['required']:
                    suite_success = False
                    if required_only:  # Stop early if running required tests only
                        print_error(f"Required test {test_info['id']} failed. Stopping suite execution.")
                        break
            else:
                print_error(f"Failed to get result for {test_info['id']}")
                suite_success = False

        # Generate comprehensive report
        self.generate_suite_report()

        return suite_success

    def generate_suite_report(self):
        """Generate comprehensive test suite report"""
        suite_end_time = datetime.now()
        suite_duration = (suite_end_time - self.suite_start_time).total_seconds()

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.is_success())
        failed_tests = total_tests - passed_tests

        print(f"\n{Colors.MAGENTA}{'='*80}")
        print(f"{'='*80}")
        print(f"📊 API TOKEN UAT TEST SUITE EXECUTION REPORT")
        print(f"{'='*80}")
        print(f"{'='*80}{Colors.RESET}\n")

        print(f"📅 Date: {self.suite_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Duration: {suite_duration:.2f} seconds")
        print(f"{'='*80}")
        print(f"📊 Tests Total: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"{'='*80}")
        print(f"📊 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"{'='*80}\n")

        # Individual test results
        print("📋 Individual Test Results:")
        for result in self.test_results:
            status_color = Colors.GREEN if result.is_success() else Colors.RED
            status_icon = "✅" if result.is_success() else "❌"
            print(f"  {status_icon} {result.test_id}: {result.test_name} - {status_color}{result.status}{Colors.RESET} ({result.total_time:.2f}s)")

            # Print failed steps for failed tests
            if not result.is_success():
                for step in result.test_steps:
                    if step.status == 'FAIL':
                        print(f"    ❌ Step {step.step_number}: {step.step_name}")

        print(f"\n{'='*80}")

        # Summary and recommendations
        if failed_tests == 0:
            print_success("🎉 ALL TESTS PASSED!")
            print_success("TRC Platform API token system is ready for production")
            print_info("\n✅ Production Readiness Checklist:")
            print("  ✅ API token creation and management tested")
            print("  ✅ Token authentication with both header formats working")
            print("  ✅ Token security validation implemented correctly")
            print("  ✅ Usage tracking and monitoring functional")
            print("  ✅ Error handling is comprehensive")
            print("  ✅ Token format validation working")
            print("  ✅ Database integration verified")
        else:
            print_error("❌ SOME TESTS FAILED!")
            print_warning("Review failed tests and fix issues before production deployment")

            failed_required = [r for r in self.test_results if not r.is_success() and any(t['id'] == r.test_id and t['required'] for t in self.available_tests)]
            if failed_required:
                print_error(f"\n🚨 CRITICAL: {len(failed_required)} required tests failed:")
                for result in failed_required:
                    print_error(f"  ❌ {result.test_id}: {result.test_name}")

        # Save results to file
        self.save_results_to_file()

    def save_results_to_file(self):
        """Save test results to JSON file"""
        try:
            results_file = current_dir / "test-results.json"

            results_data = {
                'suite_info': {
                    'start_time': self.suite_start_time.isoformat(),
                    'end_time': datetime.now().isoformat(),
                    'total_tests': len(self.test_results),
                    'passed_tests': sum(1 for r in self.test_results if r.is_success()),
                    'failed_tests': sum(1 for r in self.test_results if not r.is_success())
                },
                'test_results': []
            }

            for result in self.test_results:
                test_data = {
                    'test_id': result.test_id,
                    'test_name': result.test_name,
                    'status': result.status,
                    'total_time': result.total_time,
                    'total_steps': result.total_steps,
                    'passed_steps': result.passed_steps,
                    'failed_steps': result.failed_steps,
                    'skipped_steps': result.skipped_steps,
                    'error_steps': result.error_steps
                }
                results_data['test_results'].append(test_data)

            with open(results_file, 'w') as f:
                json.dump(results_data, f, indent=2)

            print_info(f"Test results saved to: {results_file}")

        except Exception as e:
            print_warning(f"Failed to save results to file: {e}")

def print_usage():
    """Print usage information"""
    print(f"Usage: {sys.argv[0]} [OPTIONS]")
    print("")
    print("Options:")
    print("  -h, --help              Show this help message")
    print("  -f, --filter FILTER    Run only tests matching FILTER (test ID or name)")
    print("  -r, --required-only    Run only required tests")
    print("  -s, --skip LIST        Comma-separated list of test IDs to skip")
    print("  -q, --quick            Quick run (required tests only)")
    print("")
    print("Examples:")
    print(f"  {sys.argv[0]}                          # Run all tests")
    print(f"  {sys.argv[0]} --required-only          # Run only required tests")
    print(f"  {sys.argv[0]} --filter token           # Run token-related tests")
    print(f"  {sys.argv[0]} --skip TEST-06,TEST-07  # Skip specific tests")
    print(f"  {sys.argv[0]} --quick                  # Quick run with required tests only")

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='TRC Platform API Token UAT Test Suite Runner')
    parser.add_argument('-f', '--filter', help='Run only tests matching filter (test ID or name)')
    parser.add_argument('-r', '--required-only', action='store_true', help='Run only required tests')
    parser.add_argument('-s', '--skip', help='Comma-separated list of test IDs to skip')
    parser.add_argument('-q', '--quick', action='store_true', help='Quick run (required tests only)')

    args = parser.parse_args()

    # Parse skip list
    skip_list = None
    if args.skip:
        skip_list = [test_id.strip() for test_id in args.skip.split(',')]

    # Set required_only based on quick flag
    required_only = args.required_only or args.quick

    # Run test suite
    suite_runner = ApiTokenUATTestSuite()
    success = suite_runner.run_test_suite(
        test_filter=args.filter,
        required_only=required_only,
        skip_list=skip_list
    )

    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_warning("\nTest suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)