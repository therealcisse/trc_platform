#!/usr/bin/env python3
"""
Shared Test Fixtures for Billing UAT Tests
Provides reusable test fixtures and helper methods to reduce code duplication
and improve maintainability across all billing tests.
"""

import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from uat_test_framework import (
    DatabaseHelper, HTTPClient, TokenManager, EmailVerificationHelper,
    print_success, print_error, print_info, print_warning
)
from uat_config import config
from billing_helpers import BillingDataManager

class UserFixture:
    """Fixture for creating and managing test users"""

    def __init__(self, db_helper: DatabaseHelper, http_client: HTTPClient,
                 token_manager: TokenManager, email_helper: EmailVerificationHelper):
        self.db_helper = db_helper
        self.http_client = http_client
        self.token_manager = token_manager
        self.email_helper = email_helper
        self.created_users = []

    def create_admin_user(self) -> Optional[Dict[str, Any]]:
        """Create admin user fixture"""
        return {
            'email': config.ADMIN_EMAIL,
            'password': config.ADMIN_PASSWORD,
            'id': config.ADMIN_USER_ID,
            'is_admin': True
        }

    def create_test_user(self, base_name: str, admin_token: str,
                        auto_verify: bool = True) -> Optional[Dict[str, Any]]:
        """
        Create a test user with invite code and authentication

        Args:
            base_name: Base name for email generation
            admin_token: Admin authentication token
            auto_verify: Whether to auto-verify email

        Returns:
            User dictionary with credentials and tokens, or None if failed
        """
        try:
            # Generate unique identifiers
            invite_code = config.generate_unique_invite_code(f"FIXTURE-{base_name.upper()}")
            user_email = config.generate_unique_email(f"fixture-{base_name}")
            user_password = "SecurePassword123!"

            # Create invite code
            response, _ = self.http_client.post(
                config.get_endpoint('admin_invites'),
                {"code": invite_code},
                auth_token=admin_token
            )
            if response.status_code != config.STATUS_CODES['success']:
                print_error(f"Failed to create invite code for {base_name}")
                return None

            # Register user
            registration_data = {
                "email": user_email,
                "password": user_password,
                "confirmPassword": user_password,
                "inviteCode": invite_code,
                "userAcceptedTerms": True,
                "userAcknowledgedDisclaimer": True
            }

            response, _ = self.http_client.post(
                config.get_endpoint('user_register'),
                registration_data
            )
            if response.status_code not in [config.STATUS_CODES['accepted'], config.STATUS_CODES['created']]:
                print_error(f"User registration failed for {user_email}")
                return None

            # Auto-verify email if requested
            if auto_verify:
                self.db_helper.execute_update(
                    "UPDATE users SET email_verified_at = NOW() WHERE email = %s",
                    (user_email,)
                )

            # Authenticate user
            response, _ = self.http_client.post(
                config.get_endpoint('login'),
                {"email": user_email, "password": user_password}
            )
            if response.status_code != config.STATUS_CODES['success']:
                print_error(f"User login failed for {user_email}")
                return None

            response_data = response.json()
            user_data = {
                'id': response_data['id'],
                'email': user_email,
                'password': user_password,
                'token': response_data['token'],
                'invite_code': invite_code,
                'base_name': base_name,
                'is_admin': False,
                'email_verified': auto_verify
            }

            # Store token for later use
            self.token_manager.store_token(f"user_{base_name}", response_data['token'])

            # Track created user
            self.created_users.append(user_data)

            print_success(f"Created test user: {user_email}")
            return user_data

        except Exception as e:
            print_error(f"Failed to create test user {base_name}: {e}")
            return None

    def create_multiple_users(self, scenarios: List[Dict[str, Any]],
                             admin_token: str) -> List[Dict[str, Any]]:
        """
        Create multiple test users with different scenarios

        Args:
            scenarios: List of user scenario dictionaries
            admin_token: Admin authentication token

        Returns:
            List of created user dictionaries
        """
        users = []
        for scenario in scenarios:
            user = self.create_test_user(scenario['name'], admin_token)
            if user:
                user['scenario'] = scenario
                users.append(user)
        return users

    def get_user_by_name(self, base_name: str) -> Optional[Dict[str, Any]]:
        """Get created user by base name"""
        for user in self.created_users:
            if user.get('base_name') == base_name:
                return user
        return None

    def cleanup_users(self):
        """Clean up all created users"""
        if self.created_users:
            print_info(f"Cleaning up {len(self.created_users)} test users...")
            # Note: Actual database cleanup should be handled by BillingDataManager
            self.created_users.clear()

class BillingPeriodFixture:
    """Fixture for creating and managing billing periods"""

    def __init__(self, db_helper: DatabaseHelper):
        self.db_helper = db_helper
        self.created_periods = []

    def create_billing_period(self, user_id: str, period_start: datetime,
                             total_requests: int, payment_status: str = 'pending',
                             paid_amount: int = 0, payment_reference: str = None,
                             notes: str = None) -> Optional[str]:
        """
        Create a billing period in the database

        Args:
            user_id: User ID for the period
            period_start: Start date of the period
            total_requests: Number of requests in the period
            payment_status: Payment status
            paid_amount: Amount paid in cents
            payment_reference: Payment reference
            notes: Period notes

        Returns:
            Period ID if successful, None otherwise
        """
        try:
            period_id = str(uuid.uuid4())
            period_end = period_start.replace(month=period_start.month + 1, day=1) - timedelta(days=1)

            paid_at = None
            if payment_status == 'paid' and paid_amount > 0:
                paid_at = period_end.date() + timedelta(days=5)

            # Determine if this should be the current period (most recent)
            is_current = (datetime.now().date() >= period_start.date() and
                         datetime.now().date() <= period_end.date())

            query = """
                INSERT INTO billing_periods
                (id, user_id, period_start, period_end, total_requests, total_cost_cents,
                 is_current, payment_status, paid_at, paid_amount_cents, payment_reference, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            self.db_helper.execute_update(
                query,
                (
                    period_id, user_id, period_start.date(), period_end.date(),
                    total_requests, total_requests * config.COST_PER_REQUEST_CENTS,
                    is_current, payment_status, paid_at, paid_amount, payment_reference, notes
                )
            )

            self.created_periods.append({
                'id': period_id,
                'user_id': user_id,
                'period_start': period_start.date(),
                'total_requests': total_requests,
                'payment_status': payment_status
            })

            return period_id

        except Exception as e:
            print_error(f"Failed to create billing period: {e}")
            return None

    def create_multiple_periods_for_user(self, user_id: str, scenarios: List[Dict[str, Any]]) -> List[str]:
        """
        Create multiple billing periods for a user

        Args:
            user_id: User ID
            scenarios: List of period scenarios

        Returns:
            List of created period IDs
        """
        period_ids = []
        base_date = datetime.now() - timedelta(days=90)

        for i, scenario in enumerate(scenarios):
            # Use custom period_start if provided, otherwise calculate default
            if 'period_start' in scenario:
                period_start = scenario['period_start']
            else:
                period_start = base_date + timedelta(days=i*30)
                period_start = period_start.replace(day=1)

            period_id = self.create_billing_period(
                user_id=user_id,
                period_start=period_start,
                total_requests=scenario.get('requests', 0),
                payment_status=scenario.get('status', 'pending'),
                paid_amount=scenario.get('paid_amount', 0),
                payment_reference=scenario.get('payment_reference'),
                notes=scenario.get('notes')
            )

            if period_id:
                period_ids.append(period_id)

        return period_ids

    def create_request_logs(self, period_id: str, count: int,
                           base_timestamp: datetime = None) -> bool:
        """
        Create request logs for a billing period

        Args:
            period_id: Billing period ID
            count: Number of request logs to create
            base_timestamp: Base timestamp for requests

        Returns:
            True if successful, False otherwise
        """
        try:
            if base_timestamp is None:
                base_timestamp = datetime.now() - timedelta(days=1)

            for i in range(count):
                request_ts = base_timestamp + timedelta(minutes=i)

                query = """
                    INSERT INTO request_logs
                    (id, user_id, billing_period_id, service, request_ts, duration_ms,
                     request_bytes, response_bytes, status, request_id, flow_id, result)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """

                self.db_helper.execute_update(
                    query,
                    (
                        str(uuid.uuid4()),
                        self.get_user_id_for_period(period_id),
                        period_id, 'test-service', request_ts,
                        100 + i * 10, 1000 + i * 50, 2000 + i * 75,
                        'SUCCESS', str(uuid.uuid4()), str(uuid.uuid4())[:8],
                        f"Test result {i+1}"
                    )
                )

            return True

        except Exception as e:
            print_error(f"Failed to create request logs: {e}")
            return False

    def get_user_id_for_period(self, period_id: str) -> Optional[str]:
        """Get user ID for a billing period"""
        try:
            result = self.db_helper.execute_query(
                "SELECT user_id FROM billing_periods WHERE id = %s",
                (period_id,)
            )
            return result[0]['user_id'] if result else None
        except Exception:
            return None

    def cleanup_periods(self):
        """Clean up all created periods"""
        if self.created_periods:
            print_info(f"Cleaning up {len(self.created_periods)} billing periods...")
            self.created_periods.clear()

class AuthenticationFixture:
    """Fixture for authentication operations"""

    def __init__(self, http_client: HTTPClient, token_manager: TokenManager):
        self.http_client = http_client
        self.token_manager = token_manager

    def authenticate_admin(self) -> Optional[str]:
        """Authenticate admin and return token"""
        try:
            login_data = {
                "email": config.ADMIN_EMAIL,
                "password": config.ADMIN_PASSWORD
            }

            response, _ = self.http_client.post(config.get_endpoint('login'), login_data)

            if response.status_code != config.STATUS_CODES['success']:
                print_error(f"Admin login failed: {response.status_code}")
                return None

            token = response.json()['token']
            self.token_manager.store_token('admin', token)
            print_success("Admin authentication successful")
            return token

        except Exception as e:
            print_error(f"Admin authentication failed: {e}")
            return None

    def authenticate_user(self, user_data: Dict[str, Any]) -> Optional[str]:
        """Authenticate user and return token"""
        try:
            login_data = {
                "email": user_data['email'],
                "password": user_data['password']
            }

            response, _ = self.http_client.post(config.get_endpoint('login'), login_data)

            if response.status_code != config.STATUS_CODES['success']:
                print_error(f"User login failed for {user_data['email']}: {response.status_code}")
                return None

            token = response.json()['token']
            user_data['token'] = token

            # Store token with user's base name if available
            token_key = f"user_{user_data.get('base_name', 'default')}"
            self.token_manager.store_token(token_key, token)

            return token

        except Exception as e:
            print_error(f"User authentication failed: {e}")
            return None

class TestEnvironmentFixture:
    """Main fixture that orchestrates all other fixtures"""

    def __init__(self):
        self.db_helper = DatabaseHelper(config.DATABASE_URL)
        self.http_client = HTTPClient(config.APP_URL)
        self.token_manager = TokenManager()
        self.email_helper = EmailVerificationHelper(config.MAILCATCHER_URL)
        self.data_manager = BillingDataManager(db_helper=self.db_helper)

        # Sub-fixtures
        self.users = UserFixture(self.db_helper, self.http_client,
                                self.token_manager, self.email_helper)
        self.periods = BillingPeriodFixture(self.db_helper)
        self.auth = AuthenticationFixture(self.http_client, self.token_manager)

        self.setup_complete = False

    def setup(self) -> bool:
        """Setup test environment"""
        if self.setup_complete:
            return True

        print_info("Setting up test environment fixtures...")

        if not self.db_helper.connect():
            print_error("Failed to connect to database")
            return False

        if not self.email_helper.connect_mailcatcher():
            print_error("Failed to connect to Mailcatcher")
            return False

        self.email_helper.clear_all_emails()
        self.setup_complete = True
        print_success("Test environment setup completed")
        return True

    def create_standard_test_scenario(self) -> Dict[str, Any]:
        """
        Create a standard test scenario with admin, user, and billing periods

        Returns:
            Dictionary containing admin user, test user, and created periods
        """
        if not self.setup_complete:
            raise RuntimeError("Environment not setup. Call setup() first.")

        # Authenticate admin
        admin_token = self.auth.authenticate_admin()
        if not admin_token:
            raise RuntimeError("Failed to authenticate admin")

        admin_user = self.users.create_admin_user()
        admin_user['token'] = admin_token

        # Create test user
        test_user = self.users.create_test_user('standard', admin_token)
        if not test_user:
            raise RuntimeError("Failed to create test user")

        # Create billing periods for test user (ensure current month is included)
        current_month_start = datetime.now().replace(day=1)
        period_scenarios = [
            {
                'requests': 15, 'status': 'pending',
                'period_start': current_month_start  # This will be marked as current
            },
            {'requests': 10, 'status': 'paid', 'paid_amount': 500, 'payment_reference': 'STD-001'},
            {'requests': 5, 'status': 'waived', 'notes': 'Standard test waiver'}
        ]

        period_ids = self.periods.create_multiple_periods_for_user(
            test_user['id'], period_scenarios
        )

        # Create request logs for each period
        for period_id in period_ids:
            requests_count = next(s['requests'] for s in period_scenarios if
                                any(pid == period_id for pid in
                                    [pid for pid in period_ids]))
            self.periods.create_request_logs(period_id, requests_count)

        return {
            'admin_user': admin_user,
            'test_user': test_user,
            'period_ids': period_ids,
            'period_scenarios': period_scenarios
        }

    def create_multi_user_scenario(self, user_scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a multi-user test scenario

        Args:
            user_scenarios: List of user scenario dictionaries

        Returns:
            Dictionary containing admin user, test users, and created periods
        """
        if not self.setup_complete:
            raise RuntimeError("Environment not setup. Call setup() first.")

        # Authenticate admin
        admin_token = self.auth.authenticate_admin()
        if not admin_token:
            raise RuntimeError("Failed to authenticate admin")

        admin_user = self.users.create_admin_user()
        admin_user['token'] = admin_token

        # Create multiple test users
        test_users = self.users.create_multiple_users(user_scenarios, admin_token)

        # Create billing periods for each user
        all_period_ids = []
        for user in test_users:
            period_scenarios = user['scenario']['periods']
            period_ids = self.periods.create_multiple_periods_for_user(
                user['id'], period_scenarios
            )

            # Create request logs
            for period_id in period_ids:
                requests_count = next(s['requests'] for s in period_scenarios)
                self.periods.create_request_logs(period_id, requests_count)

            user['period_ids'] = period_ids
            all_period_ids.extend(period_ids)

        return {
            'admin_user': admin_user,
            'test_users': test_users,
            'all_period_ids': all_period_ids
        }

    def cleanup(self):
        """Clean up all test fixtures"""
        try:
            print_info("Cleaning up test environment fixtures...")

            # Clean up sub-fixtures
            self.users.cleanup_users()
            self.periods.cleanup_periods()

            # Clean up test data
            if self.data_manager.cleanup_test_data():
                print_info("Test data cleanup successful")
            else:
                print_warning("Test data cleanup had issues")

            # Disconnect from database
            self.db_helper.disconnect()
            print_info("Fixture cleanup completed")

        except Exception as e:
            print_warning(f"Fixture cleanup warning: {e}")
        finally:
            self.setup_complete = False

# Predefined test scenarios
STANDARD_USER_SCENARIOS = [
    {
        'name': 'light-user',
        'periods': [
            {'requests': 5, 'status': 'paid', 'paid_amount': 250},
            {'requests': 3, 'status': 'pending'}
        ]
    },
    {
        'name': 'heavy-user',
        'periods': [
            {'requests': 50, 'status': 'paid', 'paid_amount': 2500},
            {'requests': 75, 'status': 'paid', 'paid_amount': 3750},
            {'requests': 60, 'status': 'overdue'}
        ]
    },
    {
        'name': 'medium-user',
        'periods': [
            {'requests': 20, 'status': 'waived', 'notes': 'Service credit'},
            {'requests': 15, 'status': 'paid', 'paid_amount': 750},
            {'requests': 25, 'status': 'pending'}
        ]
    }
]

ADMIN_REPORTING_SCENARIOS = [
    {
        'name': 'light-user',
        'periods': [
            {'requests': 5, 'status': 'paid', 'paid_amount': 250, 'payment_reference': 'LIGHT-001'},
            {'requests': 8, 'status': 'pending'},
            {'requests': 3, 'status': 'paid', 'paid_amount': 150, 'payment_reference': 'LIGHT-002'}
        ]
    },
    {
        'name': 'heavy-user',
        'periods': [
            {'requests': 50, 'status': 'paid', 'paid_amount': 2500, 'payment_reference': 'HEAVY-001'},
            {'requests': 75, 'status': 'paid', 'paid_amount': 3750, 'payment_reference': 'HEAVY-002'},
            {'requests': 60, 'status': 'overdue'}
        ]
    },
    {
        'name': 'medium-user',
        'periods': [
            {'requests': 20, 'status': 'waived', 'notes': 'Medium user waiver'},
            {'requests': 15, 'status': 'paid', 'paid_amount': 750, 'payment_reference': 'MEDIUM-001'},
            {'requests': 25, 'status': 'pending'}
        ]
    }
]

EDGE_CASE_SCENARIOS = [
    {
        'name': 'zero-usage',
        'periods': [
            {'requests': 0, 'status': 'pending'},
            {'requests': 0, 'status': 'waived', 'notes': 'No usage waiver'}
        ]
    },
    {
        'name': 'single-request',
        'periods': [
            {'requests': 1, 'status': 'paid', 'paid_amount': 50, 'payment_reference': 'SINGLE-001'}
        ]
    },
    {
        'name': 'high-volume',
        'periods': [
            {'requests': 1000, 'status': 'paid', 'paid_amount': 50000, 'payment_reference': 'HIGH-VOL-001'}
        ]
    }
]