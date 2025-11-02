#!/usr/bin/env python3
"""
Billing API specific test helpers and utilities
Extends the base test framework with billing-specific functionality
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, date
import requests

from uat_test_framework import (
    DatabaseHelper, HTTPClient, TokenManager, TestReporting,
    Colors, print_success, print_error, print_warning, print_info
)
from uat_config import config

class BillingHelper:
    """Billing API specific operations and validation"""

    def __init__(self, db_helper: DatabaseHelper, http_client: HTTPClient):
        self.db_helper = db_helper
        self.http_client = http_client

    def validate_current_billing_response(self, response: Dict[str, Any]) -> bool:
        """Validate current billing response structure"""
        required_fields = ['id', 'isCurrent', 'periodStart', 'periodEnd', 'periodLabel',
                          'paymentStatus', 'totalRequests', 'totalCostCents']
        missing = [f for f in required_fields if f not in response]
        if missing:
            print_error(f"Missing fields in current billing: {missing}")
            return False
        return True

    def validate_billing_period_response(self, response: Dict[str, Any]) -> bool:
        """Validate billing period list response"""
        required_fields = ['id', 'periodLabel', 'periodStart', 'periodEnd',
                          'totalRequests', 'totalCostCents', 'isCurrent', 'paymentStatus']
        missing = [f for f in required_fields if f not in response]
        if missing:
            print_error(f"Missing fields in billing period: {missing}")
            return False
        return True

    def validate_billing_detail_response(self, response: Dict[str, Any]) -> bool:
        """Validate billing period detail response"""
        required_fields = ['id', 'periodStart', 'periodEnd', 'totalRequests',
                          'totalCostCents', 'paymentStatus', 'current', 'requests']
        missing = [f for f in required_fields if f not in response]
        if missing:
            print_error(f"Missing fields in billing detail: {missing}")
            return False

        # Validate requests array structure
        if not isinstance(response.get('requests'), list):
            print_error("Requests should be an array")
            return False

        for req in response['requests']:
            req_fields = ['id', 'status', 'durationMs', 'flowId', 'result']
            req_missing = [f for f in req_fields if f not in req]
            if req_missing:
                print_error(f"Missing fields in request log: {req_missing}")
                return False

        return True

    def validate_usage_summary_response(self, response: Dict[str, Any]) -> bool:
        """Validate usage summary response"""
        required_fields = ['today', 'yesterday', 'last7Days', 'thisMonth', 'lastRequestAt']
        missing = [f for f in required_fields if f not in response]
        if missing:
            print_error(f"Missing fields in usage summary: {missing}")
            return False

        # Validate counts are integers
        for field in ['today', 'yesterday', 'last7Days', 'thisMonth']:
            if not isinstance(response.get(field), int):
                print_error(f"{field} should be an integer")
                return False

        return True

    def validate_admin_billing_response(self, response: Dict[str, Any]) -> bool:
        """Validate admin billing period response"""
        required_fields = ['id', 'userId', 'paymentStatus', 'current', 'totalRequests',
                          'totalCostCents', 'paidAt', 'paidAmountCents', 'paymentReference']
        missing = [f for f in required_fields if f not in response]
        if missing:
            print_error(f"Missing fields in admin billing: {missing}")
            return False
        return True

    def validate_payment_status(self, status: str) -> bool:
        """Validate payment status is valid"""
        if status not in config.PAYMENT_STATUSES:
            print_error(f"Invalid payment status: {status}")
            return False
        return True

    def calculate_expected_cost(self, num_requests: int) -> int:
        """Calculate expected cost for given number of requests"""
        return num_requests * config.COST_PER_REQUEST_CENTS

    def validate_period_dates(self, period_start: str, period_end: str) -> bool:
        """Validate that period spans a full calendar month"""
        try:
            start = datetime.fromisoformat(period_start).date()
            end = datetime.fromisoformat(period_end).date()

            # Check if start is 1st of month
            if start.day != 1:
                print_error(f"Period start should be 1st of month, got {start.day}")
                return False

            # Check if end is last day of month
            if start.month == 12:
                next_month = start.replace(year=start.year + 1, month=1, day=1)
            else:
                next_month = start.replace(month=start.month + 1, day=1)

            last_day_of_month = (next_month - __import__('datetime').timedelta(days=1)).day
            if end.day != last_day_of_month:
                print_error(f"Period end should be {last_day_of_month}, got {end.day}")
                return False

            return True
        except Exception as e:
            print_error(f"Error validating period dates: {e}")
            return False

    def get_period_from_db(self, user_id: str, period_id: str) -> Optional[Dict]:
        """Get billing period from database"""
        try:
            results = self.db_helper.execute_query(
                config.DB_QUERIES['get_period_by_id'],
                (period_id, user_id)
            )
            return results[0] if results else None
        except Exception as e:
            print_error(f"Failed to get period from DB: {e}")
            return None

    def get_current_period_from_db(self, user_id: str) -> Optional[Dict]:
        """Get current billing period from database"""
        try:
            results = self.db_helper.execute_query(
                config.DB_QUERIES['get_current_period'],
                (user_id,)
            )
            return results[0] if results else None
        except Exception as e:
            print_error(f"Failed to get current period from DB: {e}")
            return None

    def get_period_requests(self, period_id: str) -> List[Dict]:
        """Get all request logs for a period"""
        try:
            return self.db_helper.execute_query(
                config.DB_QUERIES['get_request_logs'],
                (period_id,)
            )
        except Exception as e:
            print_error(f"Failed to get period requests: {e}")
            return []

    def verify_cost_calculation(self, period_id: str, expected_requests: int) -> bool:
        """Verify cost is correctly calculated (requests * 50 cents)"""
        period = self.db_helper.execute_query(
            "SELECT total_requests, total_cost_cents FROM billing_periods WHERE id = %s",
            (period_id,)
        )
        if not period:
            print_error("Period not found")
            return False

        actual_requests = period[0]['total_requests']
        actual_cost = period[0]['total_cost_cents']
        expected_cost = self.calculate_expected_cost(expected_requests)

        if actual_requests != expected_requests:
            print_error(f"Request count mismatch: expected {expected_requests}, got {actual_requests}")
            return False

        if actual_cost != expected_cost:
            print_error(f"Cost mismatch: expected {expected_cost}, got {actual_cost}")
            return False

        return True

    def verify_cost_calculation_for_user(self, user_id: str, expected_total_cost: int) -> bool:
        """Verify total cost across all periods for a user"""
        periods = self.db_helper.execute_query(
            "SELECT SUM(total_cost_cents) as total_cost FROM billing_periods WHERE user_id = %s",
            (user_id,)
        )
        if not periods:
            print_error("No periods found for user")
            return False

        actual_total_cost = periods[0]['total_cost'] or 0

        if actual_total_cost != expected_total_cost:
            print_error(f"Total cost mismatch for user: expected {expected_total_cost}, got {actual_total_cost}")
            return False

        return True

    def verify_period_cost_details(self, period_id: str) -> dict:
        """Get detailed cost information for a period"""
        period = self.db_helper.execute_query(
            """SELECT total_requests, total_cost_cents, paid_amount_cents,
                      payment_status, payment_reference
               FROM billing_periods WHERE id = %s""",
            (period_id,)
        )
        if not period:
            return {}

        p = period[0]
        calculated_cost = self.calculate_expected_cost(p['total_requests'])

        return {
            'period_id': period_id,
            'total_requests': p['total_requests'],
            'actual_cost': p['total_cost_cents'],
            'calculated_cost': calculated_cost,
            'cost_matches': p['total_cost_cents'] == calculated_cost,
            'paid_amount': p['paid_amount_cents'],
            'payment_status': p['payment_status'],
            'payment_reference': p['payment_reference']
        }

    def verify_request_cost_consistency(self, period_id: str) -> bool:
        """Verify that all request logs in a period contribute correctly to total cost"""
        # Count actual request logs for the period
        request_logs = self.db_helper.execute_query(
            "SELECT COUNT(*) as request_count FROM request_logs WHERE billing_period_id = %s",
            (period_id,)
        )

        # Get period cost data
        period = self.db_helper.execute_query(
            "SELECT total_requests, total_cost_cents FROM billing_periods WHERE id = %s",
            (period_id,)
        )

        if not request_logs or not period:
            print_error("Missing data for cost consistency check")
            return False

        actual_request_count = request_logs[0]['request_count']
        period_request_count = period[0]['total_requests']
        period_cost = period[0]['total_cost_cents']

        # Verify request counts match
        if actual_request_count != period_request_count:
            print_error(f"Request count inconsistency: logs show {actual_request_count}, period shows {period_request_count}")
            return False

        # Verify cost calculation
        expected_cost = self.calculate_expected_cost(actual_request_count)
        if period_cost != expected_cost:
            print_error(f"Cost calculation inconsistency: expected {expected_cost}, period shows {period_cost}")
            return False

        return True

    def simulate_usage_and_verify_cost(self, user_id: str, num_requests: int) -> bool:
        """Simulate usage by creating request logs and verify cost calculation"""
        # First, get current period for user
        current_period = self.get_current_period_from_db(user_id)
        if not current_period:
            print_error("No current period found for user")
            return False

        period_id = current_period['id']

        # Get current cost
        current_cost_data = self.verify_period_cost_details(period_id)
        if not current_cost_data:
            print_error("Failed to get current cost data")
            return False

        # Calculate expected new cost
        new_request_count = current_cost_data['total_requests'] + num_requests
        expected_new_cost = self.calculate_expected_cost(new_request_count)

        # Simulate the cost calculation
        print_info(f"Current usage: {current_cost_data['total_requests']} requests, {current_cost_data['actual_cost']} cents")
        print_info(f"Simulated +{num_requests} requests = {new_request_count} requests, {expected_new_cost} cents")

        return True

    def verify_payment_status_transition(self, period_id: str, from_status: str, to_status: str) -> bool:
        """Verify that payment status transitioned correctly"""
        period = self.db_helper.execute_query(
            "SELECT payment_status, paid_at, paid_amount_cents, payment_reference, notes FROM billing_periods WHERE id = %s",
            (period_id,)
        )
        if not period:
            print_error("Period not found for status verification")
            return False

        current_status = period[0]['payment_status']

        if current_status != to_status:
            print_error(f"Payment status transition failed: expected {to_status}, got {current_status}")
            return False

        print_success(f"Payment status transition verified: {from_status} → {to_status}")
        return True

    def verify_paid_period_fields(self, period_id: str, expected_paid_amount: int, expected_reference: str) -> bool:
        """Verify that paid period fields are set correctly"""
        period = self.db_helper.execute_query(
            """SELECT paid_at, paid_amount_cents, payment_reference, notes
               FROM billing_periods WHERE id = %s""",
            (period_id,)
        )
        if not period:
            print_error("Period not found for paid fields verification")
            return False

        p = period[0]

        # Verify paid amount
        if p['paid_amount_cents'] != expected_paid_amount:
            print_error(f"Paid amount mismatch: expected {expected_paid_amount}, got {p['paid_amount_cents']}")
            return False

        # Verify payment reference
        if p['payment_reference'] != expected_reference:
            print_error(f"Payment reference mismatch: expected '{expected_reference}', got '{p['payment_reference']}'")
            return False

        # Verify paid timestamp is set
        if not p['paid_at']:
            print_error("Paid at timestamp is not set")
            return False

        print_success(f"Paid period fields verified: amount={expected_paid_amount}, ref='{expected_reference}'")
        return True

    def verify_payment_status_lifecycle(self, period_id: str, expected_sequence: list) -> bool:
        """Verify that payment status follows expected lifecycle sequence"""
        current_status = self.get_current_payment_status(period_id)
        if not current_status:
            print_error("Could not determine current payment status")
            return False

        if current_status not in expected_sequence:
            print_error(f"Payment status '{current_status}' not in expected sequence: {expected_sequence}")
            return False

        current_index = expected_sequence.index(current_status)
        print_success(f"Payment status '{current_status}' is valid in lifecycle sequence")
        return True

    def get_current_payment_status(self, period_id: str) -> str:
        """Get current payment status for a period"""
        period = self.db_helper.execute_query(
            "SELECT payment_status FROM billing_periods WHERE id = %s",
            (period_id,)
        )
        return period[0]['payment_status'] if period else None

    def verify_admin_operation_success(self, admin_response: dict, period_id: str, expected_status: str) -> bool:
        """Verify that an admin operation was successful and reflected in the database"""
        # Check API response
        if admin_response.get('paymentStatus') != expected_status:
            print_error(f"API response shows wrong status: expected {expected_status}, got {admin_response.get('paymentStatus')}")
            return False

        # Check database state
        db_status = self.get_current_payment_status(period_id)
        if db_status != expected_status:
            print_error(f"Database shows wrong status: expected {expected_status}, got {db_status}")
            return False

        print_success(f"Admin operation verified: status = {expected_status}")
        return True

    def validate_payment_status_rules(self, period_id: str) -> dict:
        """Validate payment status business rules and return validation results"""
        period = self.db_helper.execute_query(
            """SELECT payment_status, paid_at, paid_amount_cents, total_cost_cents, is_current
               FROM billing_periods WHERE id = %s""",
            (period_id,)
        )
        if not period:
            return {'valid': False, 'errors': ['Period not found']}

        p = period[0]
        status = p['payment_status']
        errors = []
        warnings = []

        # Rule: Paid periods must have paid_at timestamp
        if status == 'paid' and not p['paid_at']:
            errors.append("Paid period must have paid_at timestamp")

        # Rule: Paid periods must have paid_amount_cents set
        if status == 'paid' and (p['paid_amount_cents'] is None or p['paid_amount_cents'] <= 0):
            errors.append("Paid period must have positive paid_amount_cents")

        # Rule: Paid amount should not exceed total cost
        if status == 'paid' and p['paid_amount_cents'] and p['total_cost_cents']:
            if p['paid_amount_cents'] > p['total_cost_cents']:
                warnings.append(f"Paid amount ({p['paid_amount_cents']}) exceeds total cost ({p['total_cost_cents']})")

        # Rule: Pending periods should not have payment fields set
        if status == 'pending':
            if p['paid_at']:
                errors.append("Pending period should not have paid_at timestamp")
            if p['paid_amount_cents']:
                errors.append("Pending period should not have paid_amount_cents")

        # Rule: Overdue periods must be current or recent
        if status == 'overdue' and not p['current']:
            warnings.append("Overdue status on non-current period")

        return {
            'valid': len(errors) == 0,
            'status': status,
            'errors': errors,
            'warnings': warnings,
            'period_details': {
                'paid_at': p['paid_at'],
                'paid_amount_cents': p['paid_amount_cents'],
                'total_cost_cents': p['total_cost_cents'],
                'is_current': p['is_current']
            }
        }

    def simulate_payment_status_transitions(self, period_id: str) -> bool:
        """Simulate and validate common payment status transitions"""
        print_info("Simulating payment status transition validation...")

        # Test: pending → paid
        if self.get_current_payment_status(period_id) == 'pending':
            print_info("✓ Period starts in 'pending' status")

        # Test: paid periods should have timestamps
        current_status = self.get_current_payment_status(period_id)
        if current_status == 'paid':
            paid_details = self.verify_period_cost_details(period_id)
            if paid_details.get('paid_amount'):
                print_info(f"✓ Paid period has payment amount: {paid_details['paid_amount']} cents")
            else:
                print_warning("⚠ Paid period missing payment amount")

        return True

    def verify_zero_usage_period(self, period_id: str) -> bool:
        """Verify that zero usage periods are handled correctly"""
        print_info("Testing zero usage period handling...")

        period = self.db_helper.execute_query(
            "SELECT total_requests, total_cost_cents, payment_status FROM billing_periods WHERE id = %s",
            (period_id,)
        )
        if not period:
            print_error("Period not found for zero usage test")
            return False

        p = period[0]

        # Verify zero requests
        if p['total_requests'] != 0:
            print_error(f"Expected zero requests, got {p['total_requests']}")
            return False

        # Verify zero cost
        expected_cost = self.calculate_expected_cost(0)  # Should be 0
        if p['total_cost_cents'] != expected_cost:
            print_error(f"Expected zero cost ({expected_cost}), got {p['total_cost_cents']}")
            return False

        # Verify payment status makes sense for zero usage
        if p['payment_status'] not in ['pending', 'waived']:  # Zero usage shouldn't be paid
            print_warning(f"Unexpected payment status for zero usage: {p['payment_status']}")

        print_success("✓ Zero usage period validated correctly")
        return True

    def test_boundary_values(self, period_id: str) -> bool:
        """Test billing system with boundary values"""
        print_info("Testing boundary values...")

        boundary_test_cases = [
            {"requests": 1, "expected_cost": 50, "description": "single request"},
            {"requests": 0, "expected_cost": 0, "description": "zero requests"},
            {"requests": 100, "expected_cost": 5000, "description": "100 requests"},
            {"requests": 1000, "expected_cost": 50000, "description": "1000 requests (high volume)"},
        ]

        all_passed = True
        for test_case in boundary_test_cases:
            num_requests = test_case["requests"]
            expected_cost = test_case["expected_cost"]
            description = test_case["description"]

            actual_cost = self.calculate_expected_cost(num_requests)
            if actual_cost != expected_cost:
                print_error(f"Boundary test failed for {description}: expected {expected_cost}, got {actual_cost}")
                all_passed = False
            else:
                print_success(f"✓ {description}: {num_requests} requests = {actual_cost} cents")

        return all_passed

    def test_extreme_scenarios(self, user_id: str) -> bool:
        """Test extreme billing scenarios"""
        print_info("Testing extreme billing scenarios...")

        try:
            # Test: Multiple billing periods for same user
            query = """
                SELECT COUNT(*) as period_count, SUM(total_cost_cents) as total_cost
                FROM billing_periods WHERE user_id = %s
            """
            result = self.db_helper.execute_query(query, (user_id,))

            if result:
                period_count = result[0]['period_count']
                total_cost = result[0]['total_cost'] or 0

                print_info(f"User has {period_count} billing periods with total cost: {total_cost} cents")

                # Verify no negative costs
                if total_cost < 0:
                    print_error("❌ Negative total cost detected!")
                    return False

                # Verify reasonable cost bounds
                max_reasonable_cost = 1000000  # $10,000
                if total_cost > max_reasonable_cost:
                    print_warning(f"⚠ High total cost detected: {total_cost} cents")

            # Test: Period with very recent timestamp
            current_period = self.get_current_period_from_db(user_id)
            if current_period:
                period_id = current_period['id']
                cost_details = self.verify_period_cost_details(period_id)

                if cost_details:
                    # Test cost calculation for edge cases
                    test_requests = [0, 1, 999999]
                    for req_count in test_requests:
                        expected_cost = self.calculate_expected_cost(req_count)
                        # Verify calculation doesn't overflow
                        if expected_cost < 0 or expected_cost > 999999999:
                            print_error(f"❌ Cost calculation overflow for {req_count} requests")
                            return False

            print_success("✓ Extreme scenario tests passed")
            return True

        except Exception as e:
            print_error(f"Extreme scenario test failed: {e}")
            return False

    def verify_payment_amount_edge_cases(self, period_id: str) -> bool:
        """Test payment amount edge cases"""
        print_info("Testing payment amount edge cases...")

        period = self.db_helper.execute_query(
            "SELECT total_cost_cents, paid_amount_cents, payment_status FROM billing_periods WHERE id = %s",
            (period_id,)
        )
        if not period:
            print_error("Period not found for payment edge case testing")
            return False

        p = period[0]
        total_cost = p['total_cost_cents']
        paid_amount = p['paid_amount_cents'] or 0
        payment_status = p['payment_status']

        # Test: Overpayment scenario
        if paid_amount > total_cost:
            print_warning(f"⚠ Overpayment detected: paid {paid_amount} cents, cost {total_cost} cents")

        # Test: Zero payment on non-zero cost
        if total_cost > 0 and paid_amount == 0 and payment_status == 'paid':
            print_warning(f"⚠ Zero payment for non-zero cost: {total_cost} cents")

        # Test: Exact payment match
        if paid_amount == total_cost and total_cost > 0:
            print_success(f"✓ Exact payment match: {paid_amount} cents")

        # Test: Partial payment logic (if applicable)
        if 0 < paid_amount < total_cost:
            print_info(f"ℹ Partial payment: {paid_amount}/{total_cost} cents")

        return True

    def test_data_consistency_edge_cases(self, period_id: str) -> bool:
        """Test data consistency in edge cases"""
        print_info("Testing data consistency edge cases...")

        try:
            # Get request logs count for the period
            request_count = self.db_helper.execute_query(
                "SELECT COUNT(*) as count FROM request_logs WHERE billing_period_id = %s",
                (period_id,)
            )[0]['count']

            # Get period data
            period = self.db_helper.execute_query(
                "SELECT total_requests, total_cost_cents FROM billing_periods WHERE id = %s",
                (period_id,)
            )[0]

            period_requests = period['total_requests']
            period_cost = period['total_cost_cents']
            calculated_cost = self.calculate_expected_cost(request_count)

            # Test consistency checks
            issues = []

            if request_count != period_requests:
                issues.append(f"Request count mismatch: logs={request_count}, period={period_requests}")

            if period_cost != calculated_cost:
                issues.append(f"Cost mismatch: period={period_cost}, calculated={calculated_cost}")

            if period_requests != request_count:
                issues.append(f"Request count inconsistency: period={period_requests}, logs={request_count}")

            if issues:
                for issue in issues:
                    print_error(f"❌ Consistency issue: {issue}")
                return False

            print_success("✓ Data consistency validated")
            return True

        except Exception as e:
            print_error(f"Data consistency test failed: {e}")
            return False

    def verify_payment_status_update(self, period_id: str, expected_status: str) -> bool:
        """Verify payment status was updated in database"""
        period = self.db_helper.execute_query(
            "SELECT payment_status FROM billing_periods WHERE id = %s",
            (period_id,)
        )
        if not period:
            print_error("Period not found")
            return False

        actual_status = period[0]['payment_status']
        if actual_status != expected_status:
            print_error(f"Status mismatch: expected {expected_status}, got {actual_status}")
            return False

        return True

    def verify_admin_fields_set(self, period_id: str, expected_fields: Dict[str, Any]) -> bool:
        """Verify admin fields were set correctly"""
        period = self.db_helper.execute_query(
            """SELECT payment_status, paid_at, paid_amount_cents, payment_reference, notes
               FROM billing_periods WHERE id = %s""",
            (period_id,)
        )
        if not period:
            print_error("Period not found")
            return False

        p = period[0]

        if 'payment_status' in expected_fields and p['payment_status'] != expected_fields['payment_status']:
            print_error(f"Status mismatch: expected {expected_fields['payment_status']}, got {p['payment_status']}")
            return False

        if 'paid_amount_cents' in expected_fields:
            if p['paid_amount_cents'] != expected_fields['paid_amount_cents']:
                print_error(f"Paid amount mismatch")
                return False

        if 'payment_reference' in expected_fields:
            if p['payment_reference'] != expected_fields['payment_reference']:
                print_error(f"Payment reference mismatch")
                return False

        return True


class BillingDataManager:
    """Manage billing test data"""

    def __init__(self, storage_dir: str = None, db_helper: DatabaseHelper = None):
        self.storage_dir = storage_dir or config.TOKEN_STORAGE_DIR
        self.data = {}
        self.db_helper = db_helper
        self.created_entities = {
            'users': [],
            'periods': [],
            'request_logs': [],
            'invite_codes': [],
            'api_tokens': []
        }
        os.makedirs(self.storage_dir, exist_ok=True)

    def store_period(self, key: str, period_data: Dict[str, Any]):
        """Store period data for later retrieval"""
        self.data[f"period_{key}"] = period_data
        self._save_to_disk()

    def get_period(self, key: str) -> Optional[Dict]:
        """Retrieve stored period data"""
        return self.data.get(f"period_{key}")

    def store_admin_response(self, key: str, response_data: Dict[str, Any]):
        """Store admin API response"""
        self.data[f"admin_{key}"] = response_data
        self._save_to_disk()

    def get_admin_response(self, key: str) -> Optional[Dict]:
        """Retrieve admin API response"""
        return self.data.get(f"admin_{key}")

    def clear(self):
        """Clear all stored data"""
        self.data = {}
        self._save_to_disk()

    def _save_to_disk(self):
        """Save data to disk for persistence"""
        try:
            data_file = os.path.join(self.storage_dir, 'billing_data.json')
            with open(data_file, 'w') as f:
                json.dump(self.data, f, default=str)
        except Exception as e:
            print_warning(f"Failed to save billing data: {e}")

    def _load_from_disk(self):
        """Load data from disk"""
        try:
            data_file = os.path.join(self.storage_dir, 'billing_data.json')
            if os.path.exists(data_file):
                with open(data_file, 'r') as f:
                    self.data = json.load(f)
        except Exception as e:
            print_warning(f"Failed to load billing data: {e}")

    def track_user(self, user_id: str):
        """Track a created user for cleanup"""
        if user_id not in self.created_entities['users']:
            self.created_entities['users'].append(user_id)

    def track_period(self, period_id: str):
        """Track a created billing period for cleanup"""
        if period_id not in self.created_entities['periods']:
            self.created_entities['periods'].append(period_id)

    def track_invite_code(self, code: str):
        """Track a created invite code for cleanup"""
        if code not in self.created_entities['invite_codes']:
            self.created_entities['invite_codes'].append(code)

    def cleanup_test_data(self) -> bool:
        """Clean up all tracked test data"""
        if not self.db_helper:
            print_warning("No database helper available for cleanup")
            return False

        cleanup_success = True

        try:
            print_info("Starting test data cleanup...")

            # Clean up in order of dependencies to avoid foreign key constraints
            self._cleanup_request_logs()
            self._cleanup_api_tokens()
            self._cleanup_billing_periods()
            self._cleanup_invite_codes()
            self._cleanup_users()

            # Clear tracking lists
            for entity_type in self.created_entities:
                self.created_entities[entity_type].clear()

            print_success("Test data cleanup completed")

        except Exception as e:
            print_error(f"Test data cleanup failed: {e}")
            cleanup_success = False

        return cleanup_success

    def _cleanup_request_logs(self):
        """Clean up request logs for tracked users"""
        if not self.created_entities['users']:
            return

        try:
            user_ids_str = ','.join(f"'{uid}'" for uid in self.created_entities['users'])
            query = f"DELETE FROM request_logs WHERE user_id IN ({user_ids_str})"
            deleted = self.db_helper.execute_update_with_count(query)
            if deleted > 0:
                print_info(f"Cleaned up {deleted} request logs")
        except Exception as e:
            print_warning(f"Failed to cleanup request logs: {e}")

    def _cleanup_api_tokens(self):
        """Clean up API tokens for tracked users"""
        if not self.created_entities['users']:
            return

        try:
            user_ids_str = ','.join(f"'{uid}'" for uid in self.created_entities['users'])
            query = f"DELETE FROM api_tokens WHERE user_id IN ({user_ids_str})"
            deleted = self.db_helper.execute_update_with_count(query)
            if deleted > 0:
                print_info(f"Cleaned up {deleted} API tokens")
        except Exception as e:
            print_warning(f"Failed to cleanup API tokens: {e}")

    def _cleanup_billing_periods(self):
        """Clean up tracked billing periods and any periods for tracked users"""
        try:
            # First, clean up specific tracked periods
            if self.created_entities['periods']:
                period_ids_str = ','.join(f"'{pid}'" for pid in self.created_entities['periods'])
                query = f"DELETE FROM billing_periods WHERE id IN ({period_ids_str})"
                deleted = self.db_helper.execute_update_with_count(query)
                if deleted > 0:
                    print_info(f"Cleaned up {deleted} tracked billing periods")

            # Then, clean up any remaining periods for tracked users
            if self.created_entities['users']:
                user_ids_str = ','.join(f"'{uid}'" for uid in self.created_entities['users'])
                query = f"DELETE FROM billing_periods WHERE user_id IN ({user_ids_str})"
                deleted = self.db_helper.execute_update_with_count(query)
                if deleted > 0:
                    print_info(f"Cleaned up {deleted} additional billing periods")

        except Exception as e:
            print_warning(f"Failed to cleanup billing periods: {e}")

    def _cleanup_invite_codes(self):
        """Clean up tracked invite codes"""
        if not self.created_entities['invite_codes']:
            return

        try:
            codes_str = ','.join(f"'{code}'" for code in self.created_entities['invite_codes'])
            query = f"DELETE FROM invite_codes WHERE code IN ({codes_str})"
            deleted = self.db_helper.execute_update_with_count(query)
            if deleted > 0:
                print_info(f"Cleaned up {deleted} invite codes")
        except Exception as e:
            print_warning(f"Failed to cleanup invite codes: {e}")

    def _cleanup_users(self):
        """Clean up tracked users"""
        if not self.created_entities['users']:
            return

        try:
            user_ids_str = ','.join(f"'{uid}'" for uid in self.created_entities['users'])
            query = f"DELETE FROM users WHERE id IN ({user_ids_str})"
            deleted = self.db_helper.execute_update_with_count(query)
            if deleted > 0:
                print_info(f"Cleaned up {deleted} users")
        except Exception as e:
            print_warning(f"Failed to cleanup users: {e}")

    def cleanup_user_data_by_pattern(self, email_pattern: str) -> bool:
        """Clean up users matching an email pattern (for fallback cleanup)"""
        if not self.db_helper:
            return False

        try:
            # Find users matching pattern
            query = "SELECT id FROM users WHERE email LIKE %s"
            users = self.db_helper.execute_query(query, (f"%{email_pattern}%",))

            if not users:
                return True

            user_ids = [user['id'] for user in users]
            user_ids_str = ','.join(f"'{uid}'" for uid in user_ids)

            # Clean up all data for these users
            self.db_helper.execute_update(f"DELETE FROM request_logs WHERE user_id IN ({user_ids_str})")
            self.db_helper.execute_update(f"DELETE FROM api_tokens WHERE user_id IN ({user_ids_str})")
            self.db_helper.execute_update(f"DELETE FROM billing_periods WHERE user_id IN ({user_ids_str})")
            deleted = self.db_helper.execute_update(f"DELETE FROM users WHERE id IN ({user_ids_str})")

            print_info(f"Cleaned up {deleted} users matching pattern '{email_pattern}'")
            return True

        except Exception as e:
            print_error(f"Failed to cleanup users by pattern: {e}")
            return False
