#!/usr/bin/env python3
"""
UAT Configuration Management for Billing API Testing
Centralized configuration for all TRC Platform Billing UAT tests
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class UATBillingConfig:
    """Centralized configuration for Billing API UAT tests"""

    # Environment Configuration
    APP_URL = os.getenv('UAT_APP_URL', 'http://localhost:8080')
    DATABASE_URL = os.getenv('UAT_DATABASE_URL', 'postgresql://trc_user:trc_password@localhost:5432/trc_platform')
    MAILCATCHER_URL = os.getenv('UAT_MAILCATCHER_URL', 'http://localhost:1080')

    # Bootstrap Admin User
    ADMIN_EMAIL = 'admin@trc-platform.local'
    ADMIN_PASSWORD = 'password'
    ADMIN_USER_ID = '550e8400-e29b-41d4-a716-446655440000'

    # Pre-loaded Invite Codes
    PRELOADED_INVITE_CODES = [
        'TESTCODE123',
        'DEVINVITE456',
        'WELCOMETEST'
    ]

    # HTTP Configuration
    DEFAULT_TIMEOUT = 30  # seconds
    EMAIL_TIMEOUT = 60    # seconds for email delivery
    POLL_INTERVAL = 1     # seconds for polling operations

    # API Endpoints
    ENDPOINTS = {
        'health': '/api/core/health',
        'login': '/api/customers/login',
        'admin_invites': '/api/v1/admin/invites',
        'user_register': '/api/customers/register',
        'email_verify': '/api/auth/verify-email',
        'user_me': '/api/customers/me',
        # Billing Endpoints
        'billing_current': '/api/billing/current',
        'billing_periods': '/api/billing/periods',
        'billing_period_detail': '/api/billing/periods/{periodId}',
        'usage_summary': '/api/usage/summary',
        # Admin Billing Endpoints
        'admin_billing_list': '/api/v1/admin/billing/periods',
        'admin_billing_mark_paid': '/api/v1/admin/billing/periods/{periodId}/mark-paid',
        'admin_billing_mark_overdue': '/api/v1/admin/billing/periods/{periodId}/mark-overdue',
        'admin_billing_mark_waived': '/api/v1/admin/billing/periods/{periodId}/mark-waived',
    }

    # Expected HTTP Status Codes
    STATUS_CODES = {
        'success': 200,
        'created': 201,
        'accepted': 202,
        'no_content': 204,
        'bad_request': 400,
        'unauthorized': 401,
        'forbidden': 403,
        'not_found': 404,
        'conflict': 409,
        'server_error': 500
    }

    # Test Configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds

    # Database Configuration
    DB_QUERIES = {
        'get_user_id': "SELECT id FROM users WHERE email = %s",
        'verify_email_verified': """
            SELECT email_verified_at FROM users
            WHERE email = %s AND email_verified_at IS NOT NULL
        """,
        'check_complete_user': """
            SELECT id, email, is_staff, email_verified_at, date_joined,
                   user_accepted_terms, user_acknowledged_disclaimer, version
            FROM users
            WHERE email = %s
        """,
        'get_billing_periods': """
            SELECT id, user_id, period_start, period_end, total_requests,
                   total_cost_cents, is_current, payment_status, paid_at,
                   paid_amount_cents, payment_reference, notes
            FROM billing_periods
            WHERE user_id = %s
            ORDER BY period_start DESC
        """,
        'get_current_period': """
            SELECT id, user_id, period_start, period_end, total_requests,
                   total_cost_cents, is_current, payment_status, paid_at,
                   paid_amount_cents, payment_reference, notes
            FROM billing_periods
            WHERE user_id = %s AND is_current = true
        """,
        'get_period_by_id': """
            SELECT id, user_id, period_start, period_end, total_requests,
                   total_cost_cents, is_current, payment_status, paid_at,
                   paid_amount_cents, payment_reference, notes
            FROM billing_periods
            WHERE id = %s AND user_id = %s
        """,
        'get_request_logs': """
            SELECT id, user_id, billing_period_id, request_ts, status,
                   duration_ms, flow_id, result
            FROM request_logs
            WHERE billing_period_id = %s
            ORDER BY request_ts DESC
        """,
        'count_request_logs': """
            SELECT COUNT(*) as count
            FROM request_logs
            WHERE user_id = %s AND request_ts >= %s
        """,
    }

    # JWT Configuration
    JWT_TOKEN_PREFIX = 'Bearer '
    JWT_ALGORITHM = 'HS256'

    # Email Configuration
    EMAIL_FROM = 'test@trc-platform.local'
    EMAIL_SUBJECT = 'Verify your TRC Platform account'
    EMAIL_VERIFICATION_LINK_PATTERN = '/verify-email?token='

    # Test Data Storage
    TOKEN_STORAGE_DIR = '/tmp/uat-billing-test-data'
    TOKEN_FILES = {
        'admin_token': 'admin_token.txt',
        'user_token': 'user_token.txt',
        'invite_codes': 'invite_codes.txt',
        'verification_token': 'verification_token.txt',
        'user_credentials': 'user_credentials.txt',
        'billing_data': 'billing_data.json'
    }

    # Response Validation
    REQUIRED_RESPONSE_FIELDS = {
        'login': ['id', 'email', 'token'],
        'current_billing': ['id', 'isCurrent', 'periodStart', 'periodEnd', 'periodLabel', 
                           'paymentStatus', 'totalRequests', 'totalCostCents'],
        'billing_periods_list': ['content', 'totalElements', 'totalPages', 'size', 'number', 'first', 'last'],
        'billing_period_response': ['id', 'periodLabel', 'periodStart', 'periodEnd',
                                   'totalRequests', 'totalCostCents', 'isCurrent', 'paymentStatus'],
        'billing_period_detail': ['id', 'periodStart', 'periodEnd', 'totalRequests',
                                 'totalCostCents', 'paymentStatus', 'current', 'requests'],
        'usage_summary': ['today', 'yesterday', 'last7Days', 'thisMonth', 'lastRequestAt'],
        'billing_admin_response': ['id', 'userId', 'paymentStatus', 'current', 'totalRequests',
                                  'totalCostCents', 'paidAt', 'paidAmountCents', 'paymentReference'],
    }

    # Password Requirements
    PASSWORD_REQUIREMENTS = {
        'min_length': 8,
        'require_uppercase': True,
        'require_lowercase': True,
        'require_digits': True,
        'require_special': True
    }

    # Billing Constants
    COST_PER_REQUEST_CENTS = 50
    MAX_PERIODS_PER_REQUEST = 100

    # Payment Statuses
    PAYMENT_STATUSES = ['pending', 'paid', 'overdue', 'waived']

    # Logging Configuration
    LOG_LEVEL = os.getenv('UAT_LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    @classmethod
    def get_endpoint(cls, endpoint_name: str, **kwargs) -> str:
        """Get full endpoint URL with path parameters"""
        if endpoint_name not in cls.ENDPOINTS:
            raise ValueError(f"Unknown endpoint: {endpoint_name}")

        endpoint = cls.ENDPOINTS[endpoint_name]
        if kwargs:
            for key, value in kwargs.items():
                endpoint = endpoint.replace(f'{{{key}}}', str(value))

        return endpoint

    @classmethod
    def validate_email_format(cls, email: str) -> bool:
        """Basic email format validation"""
        return '@' in email and '.' in email.split('@')[-1]

    @classmethod
    def validate_password_strength(cls, password: str) -> bool:
        """Validate password meets requirements"""
        if len(password) < cls.PASSWORD_REQUIREMENTS['min_length']:
            return False

        if cls.PASSWORD_REQUIREMENTS['require_uppercase'] and not any(c.isupper() for c in password):
            return False

        if cls.PASSWORD_REQUIREMENTS['require_lowercase'] and not any(c.islower() for c in password):
            return False

        if cls.PASSWORD_REQUIREMENTS['require_digits'] and not any(c.isdigit() for c in password):
            return False

        if cls.PASSWORD_REQUIREMENTS['require_special'] and not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            return False

        return True

    @classmethod
    def get_database_connection_params(cls) -> Dict[str, Any]:
        """Get database connection parameters"""
        if cls.DATABASE_URL.startswith('postgresql://'):
            import re
            match = re.match(r'postgresql://([^@]+)@([^:]+):(\d+)/(.+)', cls.DATABASE_URL)
            if match:
                return {
                    'host': match.group(2),
                    'port': int(match.group(3)),
                    'database': match.group(4),
                    'user': match.group(1),
                    'password': ''
                }

        return {
            'host': 'localhost',
            'port': 5432,
            'database': 'trc_platform',
            'user': 'trc_user',
            'password': ''
        }

    @classmethod
    def generate_unique_email(cls, base_name: str) -> str:
        """Generate unique email with timestamp"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"{base_name}-{timestamp}@example.com"

    @classmethod
    def generate_unique_invite_code(cls, base_code: str) -> str:
        """Generate unique invite code with timestamp"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"{base_code}-{timestamp}"

    @classmethod
    def print_config_summary(cls):
        """Print current configuration summary"""
        print("🔧 Billing UAT Configuration Summary:")
        print(f"  App URL: {cls.APP_URL}")
        print(f"  Database: {cls.DATABASE_URL}")
        print(f"  Admin Email: {cls.ADMIN_EMAIL}")
        print(f"  Token Storage: {cls.TOKEN_STORAGE_DIR}")
        print(f"  Log Level: {cls.LOG_LEVEL}")
        print(f"  Cost Per Request: {cls.COST_PER_REQUEST_CENTS} cents")
        print(f"  Payment Statuses: {', '.join(cls.PAYMENT_STATUSES)}")
        print("=" * 50)

# Global configuration instance
config = UATBillingConfig()

if __name__ == "__main__":
    config.print_config_summary()
