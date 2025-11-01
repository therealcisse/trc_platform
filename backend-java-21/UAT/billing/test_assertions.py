#!/usr/bin/env python3
"""
Enhanced Test Assertion Helpers for Billing UAT Tests
Provides semantic, readable assertions for common test scenarios
with detailed error messages and automatic data collection.
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Tuple
from decimal import Decimal

from uat_test_framework import TestStep, Colors, print_success, print_error, print_warning, print_info
from uat_config import config

class AssertionResult:
    """Result of an assertion with detailed information"""

    def __init__(self, passed: bool, message: str, actual: Any = None,
                 expected: Any = None, details: Dict[str, Any] = None):
        self.passed = passed
        self.message = message
        self.actual = actual
        self.expected = expected
        self.details = details or {}
        self.timestamp = datetime.now()

    def __bool__(self):
        return self.passed

class AssertionHelper:
    """Base class for assertion helpers"""

    def __init__(self, context: str = ""):
        self.context = context
        self.assertions_made = []
        self.assertions_passed = 0
        self.assertions_failed = 0

    def _record_assertion(self, result: AssertionResult):
        """Record an assertion result"""
        self.assertions_made.append(result)
        if result.passed:
            self.assertions_passed += 1
        else:
            self.assertions_failed += 1

    def _format_message(self, message: str, details: Dict[str, Any] = None) -> str:
        """Format assertion message with context and details"""
        if self.context:
            message = f"[{self.context}] {message}"
        if details:
            details_str = ", ".join(f"{k}={v}" for k, v in details.items())
            message += f" ({details_str})"
        return message

    def get_summary(self) -> Dict[str, Any]:
        """Get assertion summary"""
        return {
            'total_assertions': len(self.assertions_made),
            'passed': self.assertions_passed,
            'failed': self.assertions_failed,
            'success_rate': (self.assertions_passed / len(self.assertions_made) * 100) if self.assertions_made else 0
        }

class HttpResponseAssertions(AssertionHelper):
    """Assertions for HTTP responses"""

    def __init__(self, context: str = "HTTP"):
        super().__init__(context)

    def assert_status_code(self, response, expected_status: int,
                          message: str = None) -> AssertionResult:
        """Assert HTTP response status code"""
        actual_status = response.status_code
        passed = actual_status == expected_status
        msg = message or f"Expected status {expected_status}, got {actual_status}"

        result = AssertionResult(
            passed=passed,
            message=self._format_message(msg),
            actual=actual_status,
            expected=expected_status,
            details={'response_time': getattr(response, 'response_time', None)}
        )

        self._record_assertion(result)
        return result

    def assert_success_response(self, response, message: str = None) -> AssertionResult:
        """Assert response is successful (200-299)"""
        actual_status = response.status_code
        passed = 200 <= actual_status < 300
        msg = message or f"Expected success status (2xx), got {actual_status}"

        result = AssertionResult(
            passed=passed,
            message=self._format_message(msg),
            actual=actual_status,
            expected="2xx",
            details={'response_time': getattr(response, 'response_time', None)}
        )

        self._record_assertion(result)
        return result

    def assert_json_response(self, response, message: str = None) -> AssertionResult:
        """Assert response contains valid JSON"""
        try:
            data = response.json()
            passed = True
            msg = message or "Response contains valid JSON"
            actual = "valid JSON"
        except Exception as e:
            passed = False
            msg = message or f"Invalid JSON response: {str(e)}"
            actual = f"invalid JSON: {str(e)}"

        result = AssertionResult(
            passed=passed,
            message=self._format_message(msg),
            actual=actual,
            expected="valid JSON",
            details={'status_code': response.status_code}
        )

        self._record_assertion(result)
        return result

    def assert_response_contains_fields(self, response, required_fields: List[str],
                                     message: str = None) -> AssertionResult:
        """Assert JSON response contains required fields"""
        try:
            data = response.json()
            missing_fields = [field for field in required_fields if field not in data]
            passed = len(missing_fields) == 0
            msg = message or f"Response missing fields: {missing_fields}" if missing_fields else "All required fields present"

            result = AssertionResult(
                passed=passed,
                message=self._format_message(msg),
                actual=list(data.keys()),
                expected=required_fields,
                details={'missing_fields': missing_fields, 'total_fields': len(data)}
            )

        except Exception as e:
            passed = False
            result = AssertionResult(
                passed=passed,
                message=self._format_message(f"Failed to parse JSON: {str(e)}"),
                actual=f"parse error: {str(e)}",
                expected="valid JSON"
            )

        self._record_assertion(result)
        return result

    def assert_pagination_structure(self, response, message: str = None) -> AssertionResult:
        """Assert response has proper pagination structure"""
        required_fields = ['content', 'totalElements', 'totalPages', 'size', 'number', 'first', 'last']
        return self.assert_response_contains_fields(response, required_fields, message or "Pagination structure")

class DatabaseAssertions(AssertionHelper):
    """Assertions for database operations"""

    def __init__(self, db_helper, context: str = "Database"):
        super().__init__(context)
        self.db_helper = db_helper

    def assert_record_exists(self, table: str, condition: str, params: tuple,
                           message: str = None) -> AssertionResult:
        """Assert record exists in database"""
        try:
            query = f"SELECT COUNT(*) as count FROM {table} WHERE {condition}"
            result = self.db_helper.execute_query(query, params)
            count = result[0]['count'] if result else 0
            passed = count > 0
            msg = message or f"Record exists in {table}" if passed else f"No record found in {table}"

            assertion_result = AssertionResult(
                passed=passed,
                message=self._format_message(msg),
                actual=count,
                expected="> 0",
                details={'table': table, 'condition': condition}
            )

        except Exception as e:
            assertion_result = AssertionResult(
                passed=False,
                message=self._format_message(f"Database query failed: {str(e)}"),
                actual=f"query error: {str(e)}",
                expected="successful query"
            )

        self._record_assertion(assertion_result)
        return assertion_result

    def assert_record_count(self, table: str, condition: str, params: tuple,
                          expected_count: int, message: str = None) -> AssertionResult:
        """Assert specific number of records exist"""
        try:
            query = f"SELECT COUNT(*) as count FROM {table} WHERE {condition}"
            result = self.db_helper.execute_query(query, params)
            actual_count = result[0]['count'] if result else 0
            passed = actual_count == expected_count
            msg = message or f"Expected {expected_count} records, found {actual_count}"

            assertion_result = AssertionResult(
                passed=passed,
                message=self._format_message(msg),
                actual=actual_count,
                expected=expected_count,
                details={'table': table, 'condition': condition}
            )

        except Exception as e:
            assertion_result = AssertionResult(
                passed=False,
                message=self._format_message(f"Database query failed: {str(e)}"),
                actual=f"query error: {str(e)}",
                expected="successful query"
            )

        self._record_assertion(assertion_result)
        return assertion_result

    def assert_field_equals(self, table: str, field: str, condition: str,
                          params: tuple, expected_value: Any,
                          message: str = None) -> AssertionResult:
        """Assert field value equals expected value"""
        try:
            query = f"SELECT {field} FROM {table} WHERE {condition}"
            result = self.db_helper.execute_query(query, params)
            actual_value = result[0][field] if result else None
            passed = actual_value == expected_value
            msg = message or f"Field {field} equals expected value" if passed else f"Field {field} mismatch"

            assertion_result = AssertionResult(
                passed=passed,
                message=self._format_message(msg),
                actual=actual_value,
                expected=expected_value,
                details={'table': table, 'field': field}
            )

        except Exception as e:
            assertion_result = AssertionResult(
                passed=False,
                message=self._format_message(f"Database query failed: {str(e)}"),
                actual=f"query error: {str(e)}",
                expected="successful query"
            )

        self._record_assertion(assertion_result)
        return assertion_result

class BillingAssertions(AssertionHelper):
    """Assertions specific to billing functionality"""

    def __init__(self, context: str = "Billing"):
        super().__init__(context)

    def assert_cost_calculation(self, requests: int, expected_cost_cents: int,
                              actual_cost_cents: int, message: str = None) -> AssertionResult:
        """Assert cost calculation is correct"""
        calculated_cost = requests * config.COST_PER_REQUEST_CENTS
        passed = actual_cost_cents == calculated_cost and calculated_cost == expected_cost_cents

        if not passed:
            details = {
                'requests': requests,
                'cost_per_request': config.COST_PER_REQUEST_CENTS,
                'calculated_cost': calculated_cost,
                'expected_cost': expected_cost_cents,
                'actual_cost': actual_cost_cents
            }
            msg = message or f"Cost calculation mismatch: {requests} × {config.COST_PER_REQUEST_CENTS} = {calculated_cost}, expected {expected_cost_cents}, got {actual_cost_cents}"
        else:
            details = {
                'requests': requests,
                'cost_per_request': config.COST_PER_REQUEST_CENTS,
                'total_cost': actual_cost_cents,
                'calculation': f"{requests} × {config.COST_PER_REQUEST_CENTS} = {actual_cost_cents}"
            }
            msg = message or f"Cost calculation correct: {requests} requests = {actual_cost_cents} cents"

        result = AssertionResult(
            passed=passed,
            message=self._format_message(msg),
            actual=actual_cost_cents,
            expected=calculated_cost,
            details=details
        )

        self._record_assertion(result)
        return result

    def assert_payment_status_transition(self, old_status: str, new_status: str,
                                      allowed_transitions: Dict[str, List[str]] = None,
                                      message: str = None) -> AssertionResult:
        """Assert payment status transition is valid"""
        if allowed_transitions is None:
            allowed_transitions = {
                'pending': ['paid', 'overdue', 'waived'],
                'paid': [],  # Paid is typically final
                'overdue': ['paid', 'waived'],
                'waived': []  # Waived is typically final
            }

        allowed_statuses = allowed_transitions.get(old_status, [])
        passed = new_status in allowed_statuses or old_status == new_status

        if old_status == new_status:
            msg = message or f"Payment status unchanged: {old_status}"
            details = {'old_status': old_status, 'new_status': new_status, 'transition_type': 'no_change'}
        elif passed:
            msg = message or f"Valid payment status transition: {old_status} → {new_status}"
            details = {'old_status': old_status, 'new_status': new_status, 'transition_type': 'valid'}
        else:
            msg = message or f"Invalid payment status transition: {old_status} → {new_status}"
            details = {
                'old_status': old_status,
                'new_status': new_status,
                'transition_type': 'invalid',
                'allowed_transitions': allowed_statuses
            }

        result = AssertionResult(
            passed=passed,
            message=self._format_message(msg),
            actual=f"{old_status} → {new_status}",
            expected=allowed_statuses if old_status != new_status else "no change",
            details=details
        )

        self._record_assertion(result)
        return result

    def assert_period_dates_valid(self, period_start: str, period_end: str,
                                message: str = None) -> AssertionResult:
        """Assert billing period dates are valid"""
        try:
            from datetime import datetime as dt
            start_date = dt.strptime(period_start, '%Y-%m-%d').date()
            end_date = dt.strptime(period_end, '%Y-%m-%d').date()
            passed = start_date <= end_date

            if passed:
                duration = (end_date - start_date).days + 1
                msg = message or f"Valid period dates: {period_start} to {period_end} ({duration} days)"
                details = {
                    'start_date': period_start,
                    'end_date': period_end,
                    'duration_days': duration,
                    'valid': True
                }
            else:
                msg = message or f"Invalid period dates: start {period_start} after end {period_end}"
                details = {
                    'start_date': period_start,
                    'end_date': period_end,
                    'valid': False
                }

            result = AssertionResult(
                passed=passed,
                message=self._format_message(msg),
                actual=f"{period_start} to {period_end}",
                expected="start_date <= end_date",
                details=details
            )

        except Exception as e:
            result = AssertionResult(
                passed=False,
                message=self._format_message(f"Invalid date format: {str(e)}"),
                actual=f"date error: {str(e)}",
                expected="valid YYYY-MM-DD format"
            )

        self._record_assertion(result)
        return result

    def assert_pagination_consistency(self, total_elements: int, page_size: int,
                                   current_page: int, actual_content_count: int,
                                   message: str = None) -> AssertionResult:
        """Assert pagination data is consistent"""
        expected_max_content = min(page_size, max(0, total_elements - current_page * page_size))
        passed = actual_content_count <= expected_max_content

        details = {
            'total_elements': total_elements,
            'page_size': page_size,
            'current_page': current_page,
            'actual_content': actual_content_count,
            'expected_max_content': expected_max_content
        }

        if passed:
            msg = message or f"Pagination consistent: {actual_content_count} items on page {current_page}"
        else:
            msg = message or f"Pagination inconsistent: expected max {expected_max_content} items, got {actual_content_count}"

        result = AssertionResult(
            passed=passed,
            message=self._format_message(msg),
            actual=actual_content_count,
            expected=f"≤ {expected_max_content}",
            details=details
        )

        self._record_assertion(result)
        return result

class UserAssertions(AssertionHelper):
    """Assertions for user-related functionality"""

    def __init__(self, context: str = "User"):
        super().__init__(context)

    def assert_user_email_format(self, email: str, message: str = None) -> AssertionResult:
        """Assert email format is valid"""
        passed = config.validate_email_format(email)
        msg = message or f"Email format {'valid' if passed else 'invalid'}: {email}"

        result = AssertionResult(
            passed=passed,
            message=self._format_message(msg),
            actual=email,
            expected="valid email format",
            details={'has_at': '@' in email, 'has_dot': '.' in email.split('@')[-1] if '@' in email else False}
        )

        self._record_assertion(result)
        return result

    def assert_user_fields_complete(self, user_data: Dict[str, Any],
                                  required_fields: List[str] = None,
                                  message: str = None) -> AssertionResult:
        """Assert user data contains all required fields"""
        if required_fields is None:
            required_fields = ['id', 'email', 'token']

        missing_fields = [field for field in required_fields if field not in user_data or not user_data[field]]
        passed = len(missing_fields) == 0

        msg = message or f"User data {'complete' if passed else 'incomplete'}: missing {missing_fields}"

        result = AssertionResult(
            passed=passed,
            message=self._format_message(msg),
            actual=list(user_data.keys()),
            expected=required_fields,
            details={'missing_fields': missing_fields, 'total_fields': len(user_data)}
        )

        self._record_assertion(result)
        return result

    def assert_token_valid(self, token: str, message: str = None) -> AssertionResult:
        """Assert JWT token appears valid (basic format check)"""
        # Basic JWT format check: three parts separated by dots
        parts = token.split('.') if token else []
        passed = len(parts) == 3 and all(len(part) > 0 for part in parts)

        msg = message or f"Token format {'valid' if passed else 'invalid'}"

        result = AssertionResult(
            passed=passed,
            message=self._format_message(msg),
            actual=f"{len(parts)} parts" if token else "0 parts",
            expected="3 parts",
            details={'has_header': len(parts) > 0, 'has_payload': len(parts) > 1, 'has_signature': len(parts) > 2}
        )

        self._record_assertion(result)
        return result

class StepAssertions:
    """Helper to integrate assertions into test steps"""

    @staticmethod
    def create_step_from_assertions(step_number: int, step_name: str,
                                  assertion_results: List[AssertionResult],
                                  success_message: str = None,
                                  failure_message: str = None) -> TestStep:
        """Create a TestStep from assertion results"""
        passed_count = sum(1 for result in assertion_results if result.passed)
        total_count = len(assertion_results)
        all_passed = passed_count == total_count

        if all_passed:
            status = "PASS"
            message = success_message or f"All {total_count} assertions passed"
            database_state = {'assertions_passed': passed_count, 'assertions_total': total_count}
        else:
            status = "FAIL"
            failed_assertions = [result for result in assertion_results if not result.passed]
            error_messages = [result.message for result in failed_assertions]
            message = failure_message or f"{passed_count}/{total_count} assertions passed: {'; '.join(error_messages[:2])}"
            database_state = {
                'assertions_passed': passed_count,
                'assertions_failed': total_count - passed_count,
                'failed_assertion_messages': error_messages
            }

        return TestStep(
            step_number=step_number,
            step_name=step_name,
            status=status,
            message=message,
            database_state=database_state
        )

class AssertionChain:
    """Chain multiple assertions together with early exit on failure"""

    def __init__(self, context: str = "Assertion Chain"):
        self.context = context
        self.assertions = []
        self.all_passed = True

    def add_assertion(self, assertion_result: AssertionResult) -> 'AssertionChain':
        """Add an assertion to the chain"""
        self.assertions.append(assertion_result)
        if not assertion_result.passed:
            self.all_passed = False
        return self

    def add_http_status_assertion(self, response, expected_status: int,
                                message: str = None) -> 'AssertionChain':
        """Add HTTP status assertion to chain"""
        http_assertions = HttpResponseAssertions(self.context)
        result = http_assertions.assert_status_code(response, expected_status, message)
        return self.add_assertion(result)

    def add_response_fields_assertion(self, response, required_fields: List[str],
                                    message: str = None) -> 'AssertionChain':
        """Add response fields assertion to chain"""
        http_assertions = HttpResponseAssertions(self.context)
        result = http_assertions.assert_response_contains_fields(response, required_fields, message)
        return self.add_assertion(result)

    def add_cost_calculation_assertion(self, requests: int, expected_cost: int,
                                     actual_cost: int, message: str = None) -> 'AssertionChain':
        """Add cost calculation assertion to chain"""
        billing_assertions = BillingAssertions(self.context)
        result = billing_assertions.assert_cost_calculation(requests, expected_cost, actual_cost, message)
        return self.add_assertion(result)

    def get_results(self) -> List[AssertionResult]:
        """Get all assertion results"""
        return self.assertions

    def is_successful(self) -> bool:
        """Check if all assertions in the chain passed"""
        return self.all_passed

    def get_failure_summary(self) -> str:
        """Get summary of failed assertions"""
        failed_assertions = [result for result in self.assertions if not result.passed]
        if not failed_assertions:
            return "All assertions passed"
        return "; ".join([result.message for result in failed_assertions])

# Predefined assertion chains for common scenarios
class CommonAssertionChains:
    """Predefined assertion chains for common test scenarios"""

    @staticmethod
    def successful_api_response(chain_context: str, response, expected_fields: List[str] = None) -> AssertionChain:
        """Chain for successful API response validation"""
        chain = AssertionChain(chain_context)

        chain.add_http_status_assertion(response, 200, "Successful API response")

        if expected_fields:
            chain.add_response_fields_assertion(response, expected_fields, "Required fields present")

        return chain

    @staticmethod
    def billing_period_validation(chain_context: str, period_data: Dict[str, Any],
                                 expected_requests: int, expected_cost: int) -> AssertionChain:
        """Chain for billing period validation"""
        chain = AssertionChain(chain_context)

        # Validate cost calculation
        actual_requests = period_data.get('totalRequests', 0)
        actual_cost = period_data.get('totalCostCents', 0)
        chain.add_cost_calculation_assertion(actual_requests, expected_cost, actual_cost)

        # Validate period dates
        if 'periodStart' in period_data and 'periodEnd' in period_data:
            billing_assertions = BillingAssertions(chain_context)
            result = billing_assertions.assert_period_dates_valid(
                period_data['periodStart'], period_data['periodEnd']
            )
            chain.add_assertion(result)

        return chain

    @staticmethod
    def user_creation_validation(chain_context: str, user_data: Dict[str, Any]) -> AssertionChain:
        """Chain for user creation validation"""
        chain = AssertionChain(chain_context)

        # Validate email format
        user_assertions = UserAssertions(chain_context)
        if 'email' in user_data:
            result = user_assertions.assert_user_email_format(user_data['email'])
            chain.add_assertion(result)

        # Validate required fields
        result = user_assertions.assert_user_fields_complete(user_data)
        chain.add_assertion(result)

        # Validate token format
        if 'token' in user_data:
            result = user_assertions.assert_token_valid(user_data['token'])
            chain.add_assertion(result)

        return chain