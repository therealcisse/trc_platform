#!/usr/bin/env python3
"""
TRC Platform Consolidated UAT Test Suite Runner
Execute all UAT tests across all domains with comprehensive reporting
"""

import sys
import os
import time
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add current directory to Python path for imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Import UAT framework
from uat_framework import (
    TestReporting, TestResult,
    Colors, print_success, print_error, print_warning, print_info
)

class ConsolidatedUATTestSuite:
    """Consolidated UAT Test Suite Runner for all domains"""

    def __init__(self):
        self.suite_start_time = datetime.now()
        self.reporting = TestReporting()
        self.test_results = []
        self.test_domains = {
            'auth': {
                'name': 'Authentication',
                'description': 'User registration, login, and email verification',
                'path': current_dir / 'tests' / 'auth'
            },
            'api_token': {
                'name': 'API Token',
                'description': 'API token creation, management, and revocation',
                'path': current_dir / 'tests' / 'api_token'
            },
            'billing': {
                'name': 'Billing',
                'description': 'Usage tracking, billing periods, and payment management',
                'path': current_dir / 'tests' / 'billing'
            },
            'usage': {
                'name': 'Usage',
                'description': 'Usage request tracking and API endpoint testing',
                'path': current_dir / 'tests' / 'usage'
            },
            'image_solve': {
                'name': 'Image Solve',
                'description': 'Image-based math problem solving and API validation',
                'path': current_dir / 'tests' / 'image_solve'
            }
        }

        # Define all available tests across domains
        self.available_tests = [
            # Auth Tests
            {
                'id': 'AUTH-01',
                'name': 'Admin Login',
                'script': 'test-01-admin-login.py',
                'domain': 'auth',
                'priority': 1,
                'required': True,
                'description': 'Verify admin login functionality'
            },
            {
                'id': 'AUTH-02',
                'name': 'User Registration with Invite Code',
                'script': 'test-02-user-registration.py',
                'domain': 'auth',
                'priority': 2,
                'required': True,
                'description': 'Test user registration with invite codes'
            },
            {
                'id': 'AUTH-03',
                'name': 'Email Verification Flow',
                'script': 'test-03-email-verification.py',
                'domain': 'auth',
                'priority': 3,
                'required': True,
                'description': 'Complete email verification workflow'
            },
            {
                'id': 'AUTH-04',
                'name': 'User Login and JWT Management',
                'script': 'test-04-user-login.py',
                'domain': 'auth',
                'priority': 4,
                'required': True,
                'description': 'Test user authentication and JWT handling'
            },
            {
                'id': 'AUTH-05',
                'name': 'Password Change Functionality',
                'script': 'test-05-password-change.py',
                'domain': 'auth',
                'priority': 5,
                'required': True,
                'description': 'Test password change workflow'
            },
            {
                'id': 'AUTH-06',
                'name': 'Email Resend Verification',
                'script': 'test-06-email-resend.py',
                'domain': 'auth',
                'priority': 6,
                'required': True,
                'description': 'Test email resend functionality'
            },
            {
                'id': 'AUTH-07',
                'name': 'Account Management',
                'script': 'test-07-account-management.py',
                'domain': 'auth',
                'priority': 7,
                'required': True,
                'description': 'Test account management features'
            },

            # API Token Tests
            {
                'id': 'TOKEN-01',
                'name': 'User Registration for API Token Testing',
                'script': 'test-01-user-registration.py',
                'domain': 'api_token',
                'priority': 1,
                'required': True,
                'description': 'Create dedicated user for API token testing'
            },
            {
                'id': 'TOKEN-02',
                'name': 'API Token Creation',
                'script': 'test-02-api-token-creation.py',
                'domain': 'api_token',
                'priority': 2,
                'required': True,
                'description': 'Create API tokens with various configurations'
            },
            {
                'id': 'TOKEN-03',
                'name': 'API Token Authentication',
                'script': 'test-03-api-token-auth.py',
                'domain': 'api_token',
                'priority': 3,
                'required': True,
                'description': 'Test API token authentication'
            },
            {
                'id': 'TOKEN-04',
                'name': 'API Token Listing',
                'script': 'test-04-list-api-tokens.py',
                'domain': 'api_token',
                'priority': 4,
                'required': True,
                'description': 'Test API token listing functionality'
            },
            {
                'id': 'TOKEN-05',
                'name': 'API Token Revocation',
                'script': 'test-05-revoke-api-token.py',
                'domain': 'api_token',
                'priority': 5,
                'required': True,
                'description': 'Test API token revocation'
            },
            {
                'id': 'TOKEN-06',
                'name': 'API Token Security',
                'script': 'test-06-api-token-security.py',
                'domain': 'api_token',
                'priority': 6,
                'required': True,
                'description': 'Test API token security features'
            },
            {
                'id': 'TOKEN-07',
                'name': 'API Token Expiration',
                'script': 'test-07-api-token-expiration.py',
                'domain': 'api_token',
                'priority': 7,
                'required': True,
                'description': 'Test API token expiration handling'
            },

            # Billing Tests
            {
                'id': 'BILL-01',
                'name': 'User Registration for Billing Testing',
                'script': 'test-01-user-registration.py',
                'domain': 'billing',
                'priority': 1,
                'required': True,
                'description': 'Create dedicated user for billing testing'
            },
            {
                'id': 'BILL-02',
                'name': 'Current Billing Period',
                'script': 'test-02-current-billing-period.py',
                'domain': 'billing',
                'priority': 2,
                'required': True,
                'description': 'Test current billing period functionality'
            },
            {
                'id': 'BILL-03',
                'name': 'List Billing Periods',
                'script': 'test-03-list-billing-periods.py',
                'domain': 'billing',
                'priority': 3,
                'required': True,
                'description': 'Test billing period listing'
            },
            {
                'id': 'BILL-04',
                'name': 'Billing Period Details',
                'script': 'test-04-billing-period-details.py',
                'domain': 'billing',
                'priority': 4,
                'required': True,
                'description': 'Test billing period details with request logs'
            },
            {
                'id': 'BILL-05',
                'name': 'Usage Summary',
                'script': 'test-05-usage-summary.py',
                'domain': 'billing',
                'priority': 5,
                'required': True,
                'description': 'Test usage summary statistics'
            },
            {
                'id': 'BILL-06',
                'name': 'Admin List Periods',
                'script': 'test-06-admin-list-periods.py',
                'domain': 'billing',
                'priority': 6,
                'required': True,
                'description': 'Test admin billing period listing'
            },
            {
                'id': 'BILL-07',
                'name': 'Admin Mark Period Paid',
                'script': 'test-07-admin-mark-paid.py',
                'domain': 'billing',
                'priority': 7,
                'required': True,
                'description': 'Test admin mark period as paid'
            },
            {
                'id': 'BILL-08',
                'name': 'Admin Mark Period Overdue',
                'script': 'test-08-admin-mark-overdue.py',
                'domain': 'billing',
                'priority': 8,
                'required': True,
                'description': 'Test admin mark period as overdue'
            },
            {
                'id': 'BILL-09',
                'name': 'Admin Mark Period Waived',
                'script': 'test-09-admin-mark-waived.py',
                'domain': 'billing',
                'priority': 9,
                'required': True,
                'description': 'Test admin mark period as waived'
            },
            {
                'id': 'BILL-10',
                'name': 'Billing Period Lifecycle',
                'script': 'test-10-billing-period-lifecycle.py',
                'domain': 'billing',
                'priority': 10,
                'required': True,
                'description': 'Test complete billing period lifecycle'
            },
            {
                'id': 'BILL-11',
                'name': 'Cost Calculation Verification',
                'script': 'test-11-cost-calculation.py',
                'domain': 'billing',
                'priority': 11,
                'required': True,
                'description': 'Verify billing cost calculations'
            },
            # Usage Tests
            {
                'id': 'USAGE-01',
                'name': 'User Setup for Usage Testing',
                'script': 'test-01-user-setup.py',
                'domain': 'usage',
                'priority': 12,
                'required': True,
                'description': 'Create test user with usage request data'
            },
            {
                'id': 'USAGE-02',
                'name': 'Basic Usage Requests Retrieval',
                'script': 'test-02-basic-retrieval.py',
                'domain': 'usage',
                'priority': 13,
                'required': True,
                'description': 'Test basic usage endpoint functionality'
            },
            {
                'id': 'USAGE-03',
                'name': 'Date Filtering Validation',
                'script': 'test-03-date-filtering.py',
                'domain': 'usage',
                'priority': 14,
                'required': True,
                'description': 'Test date filtering capabilities'
            },
            {
                'id': 'USAGE-04',
                'name': 'Pagination Testing',
                'script': 'test-04-pagination.py',
                'domain': 'usage',
                'priority': 15,
                'required': True,
                'description': 'Test pagination functionality'
            },
            {
                'id': 'USAGE-05',
                'name': 'Data Security and Isolation',
                'script': 'test-05-data-security.py',
                'domain': 'usage',
                'priority': 16,
                'required': True,
                'description': 'Test user data isolation and security'
            },
            {
                'id': 'USAGE-06',
                'name': 'Error Handling and Edge Cases',
                'script': 'test-06-error-handling.py',
                'domain': 'usage',
                'priority': 17,
                'required': True,
                'description': 'Test error handling and edge cases'
            },
            # Image Solve Tests
            {
                'id': 'IMG-01',
                'name': 'User Setup for Image Solve Testing',
                'script': 'test-01-user-setup.py',
                'domain': 'image_solve',
                'priority': 18,
                'required': True,
                'description': 'Create test user with API token for image solve testing'
            },
            {
                'id': 'IMG-02',
                'name': 'Basic Image Solve Functionality',
                'script': 'test-02-basic-solve.py',
                'domain': 'image_solve',
                'priority': 19,
                'required': True,
                'description': 'Test basic image solving functionality with API token authentication'
            },
            {
                'id': 'IMG-03',
                'name': 'Response Structure Validation',
                'script': 'test-03-response-validation.py',
                'domain': 'image_solve',
                'priority': 20,
                'required': True,
                'description': 'Validate solve response structure and timing data completeness'
            },
            {
                'id': 'IMG-04',
                'name': 'Error Handling and Edge Cases',
                'script': 'test-04-error-handling.py',
                'domain': 'image_solve',
                'priority': 21,
                'required': True,
                'description': 'Test error handling and edge cases for image solve endpoint'
            },
            {
                'id': 'IMG-05',
                'name': 'Billing Integration Verification',
                'script': 'test-05-billing-integration.py',
                'domain': 'image_solve',
                'priority': 22,
                'required': True,
                'description': 'Verify billing integration for image solve requests'
            },
            {
                'id': 'IMG-06',
                'name': 'Comprehensive Image Suite Test',
                'script': 'test-06-comprehensive-suite.py',
                'domain': 'image_solve',
                'priority': 23,
                'required': True,
                'description': 'Comprehensive test of all available images with performance metrics'
            }
        ]

    def filter_tests(self, domain: str = None, test_filter: str = None) -> List[Dict[str, Any]]:
        """Filter tests based on domain and search criteria"""
        filtered_tests = self.available_tests

        # Filter by domain
        if domain and domain != 'all':
            filtered_tests = [test for test in filtered_tests if test['domain'] == domain]

        # Filter by search term
        if test_filter:
            search_term = test_filter.lower()
            filtered_tests = [
                test for test in filtered_tests
                if search_term in test['id'].lower() or
                   search_term in test['name'].lower() or
                   search_term in test['description'].lower()
            ]

        # Sort by priority
        filtered_tests.sort(key=lambda x: x['priority'])
        return filtered_tests

    def discover_tests(self) -> List[Dict[str, Any]]:
        """Discover actual test files in the filesystem"""
        discovered_tests = []

        for domain_key, domain_info in self.test_domains.items():
            domain_path = domain_info['path']
            if not domain_path.exists():
                print_warning(f"Domain path not found: {domain_path}")
                continue

            for test_file in domain_path.glob('test-*.py'):
                test_info = {
                    'id': f"{domain_key.upper()}-{test_file.stem.split('-')[-1]}",
                    'name': test_file.stem.replace('-', ' ').title(),
                    'script': test_file.name,
                    'domain': domain_key,
                    'path': test_file,
                    'priority': 999,  # Default priority for discovered tests
                    'required': False,
                    'description': f"Discovered test in {domain_info['name']}"
                }
                discovered_tests.append(test_info)

        return discovered_tests

    def execute_test(self, test_config: Dict[str, Any]) -> TestResult:
        """Execute a single test using subprocess for better isolation"""
        test_start_time = datetime.now()
        test_script = test_config['script']
        domain = test_config['domain']

        # Build full path to test script
        test_path = self.test_domains[domain]['path'] / test_script

        if not test_path.exists():
            return TestResult(
                test_id=test_config['id'],
                test_name=test_config['name'],
                status='ERROR',
                total_steps=0,
                passed_steps=0,
                failed_steps=1,
                skipped_steps=0,
                error_steps=0,
                total_time=0.0,
                start_time=test_start_time,
                end_time=datetime.now()
            )

        print(f"\n{'='*80}")
        print(f"🧪 EXECUTING {test_config['id']}: {test_config['name']}")
        print(f"📁 Domain: {self.test_domains[domain]['name']}")
        print(f"📄 Script: {test_script}")
        print(f"📝 Description: {test_config['description']}")
        print(f"{'='*80}")

        try:
            import subprocess
            import signal

            # Change to the test directory and run the test
            test_dir = str(test_path.parent)
            test_file = str(test_path.name)

            # Use subprocess to run the test with proper isolation
            # Run from UAT root directory but specify the test path
            uat_root = Path(__file__).parent

            # Set up environment with proper Python path
            env = os.environ.copy()
            env['PYTHONPATH'] = str(uat_root)

            result = subprocess.run(
                ['uv', 'run', 'python', str(test_path.relative_to(uat_root))],
                cwd=str(uat_root),
                env=env,
                capture_output=False,  # Show output in real-time
                text=True,
                timeout=300  # 5 minute timeout per test
            )

            end_time = datetime.now()
            duration = (end_time - test_start_time).total_seconds()

            # Determine test status based on exit code
            if result.returncode == 0:
                status = 'PASS'
                passed_steps = 1
                failed_steps = 0
                print_success(f"✓ {test_config['id']}: {status}")
            else:
                status = 'FAIL'
                passed_steps = 0
                failed_steps = 1
                print_error(f"✗ {test_config['id']}: {status} (exit code: {result.returncode})")

            return TestResult(
                test_id=test_config['id'],
                test_name=test_config['name'],
                status=status,
                total_steps=1,
                passed_steps=passed_steps,
                failed_steps=failed_steps,
                skipped_steps=0,
                error_steps=0,
                total_time=duration,
                start_time=test_start_time,
                end_time=end_time
            )

        except subprocess.TimeoutExpired:
            print_error(f"Test {test_config['id']} timed out after 5 minutes")
            end_time = datetime.now()
            duration = (end_time - test_start_time).total_seconds()

            return TestResult(
                test_id=test_config['id'],
                test_name=test_config['name'],
                status='ERROR',
                total_steps=1,
                passed_steps=0,
                failed_steps=0,
                skipped_steps=0,
                error_steps=1,
                total_time=duration,
                start_time=test_start_time,
                end_time=end_time
            )

        except Exception as e:
            print_error(f"Test execution failed: {e}")
            end_time = datetime.now()
            duration = (end_time - test_start_time).total_seconds()

            return TestResult(
                test_id=test_config['id'],
                test_name=test_config['name'],
                status='ERROR',
                total_steps=1,
                passed_steps=0,
                failed_steps=0,
                skipped_steps=0,
                error_steps=1,
                total_time=duration,
                start_time=test_start_time,
                end_time=end_time
            )

    def print_test_plan(self, tests: List[Dict[str, Any]]):
        """Print the test execution plan"""
        print(f"\n{'='*80}")
        print(f"📋 TEST EXECUTION PLAN")
        print(f"{'='*80}")

        # Group by domain
        domains = {}
        for test in tests:
            domain = test['domain']
            if domain not in domains:
                domains[domain] = []
            domains[domain].append(test)

        for domain_key, domain_tests in domains.items():
            domain_info = self.test_domains[domain_key]
            print(f"\n🏷️  {domain_info['name']} ({domain_key.upper()})")
            print(f"   {domain_info['description']}")
            print(f"   Tests: {len(domain_tests)}")

            for test in domain_tests:
                required_marker = "✓" if test['required'] else "○"
                print(f"   {required_marker} {test['id']}: {test['name']}")

    def generate_summary_report(self, results: List[TestResult]):
        """Generate comprehensive test report"""
        end_time = datetime.now()
        total_duration = (end_time - self.suite_start_time).total_seconds()

        total_tests = len(results)
        passed_tests = sum(1 for result in results if result.is_success())
        failed_tests = total_tests - passed_tests

        print(f"\n{'='*80}")
        print(f"{'='*80}")
        print(f"📊 CONSOLIDATED UAT TEST EXECUTION REPORT")
        print(f"{'='*80}")
        print(f"{'='*80}\n")

        print(f"📅 Date: {self.suite_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Duration: {total_duration:.2f} seconds")
        print(f"{'='*80}")
        print(f"📊 Tests Total: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "N/A")
        print(f"{'='*80}\n")

        # Group results by domain
        domain_results = {}
        for result in results:
            # Extract domain from test ID
            if '-' in result.test_id:
                domain = result.test_id.split('-')[0].lower()
                if domain not in domain_results:
                    domain_results[domain] = []
                domain_results[domain].append(result)

        # Print domain-specific summaries
        for domain_key, domain_results_list in domain_results.items():
            if domain_key in self.test_domains:
                domain_info = self.test_domains[domain_key]
                domain_passed = sum(1 for r in domain_results_list if r.is_success())
                domain_total = len(domain_results_list)

                print(f"🏷️  {domain_info['name']}: {domain_passed}/{domain_total} tests passed")

        print(f"\n{'='*80}")

        # Print failed tests
        failed_results = [r for r in results if not r.is_success()]
        if failed_results:
            print(f"❌ FAILED TESTS:")
            for result in failed_results:
                print(f"   • {result.test_id}: {result.test_name}")
        else:
            print(f"🎉 ALL TESTS PASSED!")

        print(f"{'='*80}")
        print(f"{'='*80}\n")

    def run_tests(self, domain: str = None, test_filter: str = None, dry_run: bool = False) -> int:
        """Run the test suite"""
        print_success("TRC Platform Consolidated UAT Test Suite")
        print_info(f"Suite started at: {self.suite_start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Filter tests
        selected_tests = self.filter_tests(domain, test_filter)

        if not selected_tests:
            print_error("No tests found matching the specified criteria")
            return 1

        # Print test plan
        self.print_test_plan(selected_tests)

        if dry_run:
            print_info("Dry run completed. No tests executed.")
            return 0

        # Execute tests
        print(f"\n🚀 EXECUTING {len(selected_tests)} TESTS...")

        for i, test_config in enumerate(selected_tests, 1):
            print(f"\n📍 Progress: {i}/{len(selected_tests)}")

            try:
                result = self.execute_test(test_config)
                self.test_results.append(result)

            except Exception as e:
                print_error(f"Failed to execute test {test_config['id']}: {e}")

                error_result = TestResult(
                    test_id=test_config['id'],
                    test_name=test_config['name'],
                    status='ERROR',
                    total_steps=0,
                    passed_steps=0,
                    failed_steps=0,
                    skipped_steps=0,
                    error_steps=1,
                    total_time=0.0,
                    start_time=datetime.now(),
                    end_time=datetime.now()
                )
                self.test_results.append(error_result)

        # Generate summary report
        self.generate_summary_report(self.test_results)

        # Return exit code based on results
        failed_count = sum(1 for result in self.test_results if not result.is_success())
        return 1 if failed_count > 0 else 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="TRC Platform Consolidated UAT Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --all                    # Run all tests
  %(prog)s --domain auth           # Run only auth tests
  %(prog)s --domain api_token     # Run only API token tests
  %(prog)s --domain billing       # Run only billing tests
  %(prog)s --domain usage         # Run only usage tests
  %(prog)s --domain image_solve   # Run only image solve tests
  %(prog)s --filter "user"         # Run tests containing "user"
  %(prog)s --filter TOKEN-01       # Run specific test
  %(prog)s --filter IMG-01         # Run specific image solve test
  %(prog)s --dry-run              # Show test plan without executing
        """
    )

    parser.add_argument(
        '--domain', '-d',
        choices=['auth', 'api_token', 'billing', 'usage', 'image_solve', 'all'],
        default='all',
        help='Specify domain to test (default: all)'
    )

    parser.add_argument(
        '--filter', '-f',
        help='Filter tests by ID, name, or description'
    )

    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Show test plan without executing tests'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # Create and run test suite
    test_suite = ConsolidatedUATTestSuite()

    try:
        exit_code = test_suite.run_tests(
            domain=args.domain,
            test_filter=args.filter,
            dry_run=args.dry_run
        )
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_warning("\nTest execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print_error(f"Test suite execution failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()