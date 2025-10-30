#!/usr/bin/env python3
"""
UAT Configuration Management
Centralized configuration for all TRC Platform UAT tests
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional

class UATConfig:
    """Centralized configuration for UAT tests"""

    # Environment Configuration
    APP_URL = os.getenv('UAT_APP_URL', 'http://localhost:8080')
    DATABASE_URL = os.getenv('UAT_DATABASE_URL', 'postgresql://trc_user:trc_password@localhost:5432/trc_platform')
    MAILCATCHER_URL = os.getenv('UAT_MAILCATCHER_URL', 'http://localhost:1080')

    # Bootstrap Admin User (from test plans)
    ADMIN_EMAIL = 'admin@trc-platform.local'
    ADMIN_PASSWORD = 'password'
    ADMIN_USER_ID = '550e8400-e29b-41d4-a716-446655440000'

    # Pre-loaded Invite Codes (from test plans)
    PRELOADED_INVITE_CODES = [
        'TESTCODE123',
        'DEVINVITE456',
        'WELCOMETEST'
    ]

    # Test Data
    TEST_INVITE_CODES = {
        'UAT-TEST-01': {'expires': None, 'description': 'No expiration'},
        'UAT-TEST-02': {'expires': '2025-11-30T23:59:59', 'description': 'With expiration'},
        'INTEGRATION-TEST-01': {'expires': '2025-12-31T23:59:59', 'description': 'Integration test'}
    }

    TEST_USERS = {
        'registration': {
            'email': 'uat-test@example.com',
            'password': 'SecurePassword123!',
            'description': 'User registration test'
        },
        'integration': {
            'email': 'integration-test@example.com',
            'password': 'IntegrationTest123!',
            'description': 'Integration test user'
        },
        'password_change': {
            'email': 'password-change@example.com',
            'password': 'CurrentPassword123!',
            'new_password': 'NewSecurePassword456!',
            'description': 'Password change test'
        },
        'error_scenarios': {
            'weak_password': {
                'email': 'weak@example.com',
                'password': 'weak',
                'description': 'Weak password test'
            },
            'duplicate_email': {
                'email': 'uat-test@example.com',  # Same as registration user
                'password': 'DifferentPassword123!',
                'description': 'Duplicate email test'
            },
            'terms_rejected': {
                'email': 'terms@example.com',
                'password': 'SecurePassword123!',
                'description': 'Terms rejection test'
            }
        }
    }

    # HTTP Configuration
    DEFAULT_TIMEOUT = 30  # seconds
    EMAIL_TIMEOUT = 60    # seconds for email delivery
    POLL_INTERVAL = 1     # seconds for polling operations

    # API Endpoints
    ENDPOINTS = {
        'health': '/api/core/health',
        'admin_login': '/api/customers/login',
        'admin_invites': '/api/v1/admin/invites',
        'user_register': '/api/customers/register',
        'email_verify': '/api/auth/verify-email',
        'email_resend': '/api/auth/resend-verification',
        'password_change': '/api/auth/password/change',
        'accept_terms': '/api/auth/accept-terms',
        'accept_disclaimer': '/api/auth/accept-disclaimer',
        'user_me': '/api/customers/me'
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
        'check_admin_user': "SELECT id, email, is_staff, email_verified_at FROM users WHERE email = %s",
        'check_user_exists': "SELECT id FROM users WHERE email = %s",
        'check_invite_code': "SELECT id FROM invite_codes WHERE code = %s AND is_active = true",
        'check_invite_code_usage': """
            SELECT ic.code, ic.is_active, ic.used_at, ic.used_by_user_id,
                   u.email as used_by_email
            FROM invite_codes ic
            LEFT JOIN users u ON ic.used_by_user_id = u.id
            WHERE ic.code = %s
        """,
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
        'verify_invite_creator': """
            SELECT ic.code, u.email as creator_email, ic.created_at
            FROM invite_codes ic
            JOIN users u ON ic.created_by_user_id = u.id
            WHERE ic.code = %s
        """
    }

    # JWT Configuration
    JWT_TOKEN_PREFIX = 'Bearer '
    JWT_ALGORITHM = 'HS256'

    # Email Configuration
    EMAIL_FROM = 'test@trc-platform.local'
    EMAIL_SUBJECT = 'Verify your TRC Platform account'
    EMAIL_VERIFICATION_LINK_PATTERN = '/verify-email?token='

    # Test Data Storage
    TOKEN_STORAGE_DIR = '/tmp/uat-test-data'
    TOKEN_FILES = {
        'admin_token': 'admin_token.txt',
        'user_token': 'user_token.txt',
        'invite_codes': 'invite_codes.txt',
        'verification_token': 'verification_token.txt'
    }

    # Response Validation
    REQUIRED_RESPONSE_FIELDS = {
        'login': ['id', 'email', 'token'],
        'invite_create': ['id', 'code', 'active', 'createdAt', 'createdByUserId', 'createdByUserEmail'],
        'user_profile': ['id', 'email', 'isEmailVerified', 'dateJoined'],
        'invite_list': ['content', 'pageable']
    }

    # Password Requirements
    PASSWORD_REQUIREMENTS = {
        'min_length': 8,
        'require_uppercase': True,
        'require_lowercase': True,
        'require_digits': True,
        'require_special': True
    }

    # Logging Configuration
    LOG_LEVEL = os.getenv('UAT_LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    @classmethod
    def get_endpoint(cls, endpoint_name: str) -> str:
        """Get full endpoint URL"""
        if endpoint_name not in cls.ENDPOINTS:
            raise ValueError(f"Unknown endpoint: {endpoint_name}")
        return f"{cls.APP_URL}{cls.ENDPOINTS[endpoint_name]}"

    @classmethod
    def get_test_user(cls, user_type: str, **kwargs) -> Dict[str, Any]:
        """Get test user configuration"""
        if user_type not in cls.TEST_USERS:
            raise ValueError(f"Unknown test user type: {user_type}")

        user_config = cls.TEST_USERS[user_type].copy()
        user_config.update(kwargs)
        return user_config

    @classmethod
    def get_token_path(cls, token_type: str) -> str:
        """Get full path for token storage file"""
        if token_type not in cls.TOKEN_FILES:
            raise ValueError(f"Unknown token type: {token_type}")

        os.makedirs(cls.TOKEN_STORAGE_DIR, exist_ok=True)
        return os.path.join(cls.TOKEN_STORAGE_DIR, cls.TOKEN_FILES[token_type])

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
        # Parse DATABASE_URL if it's a full connection string
        if cls.DATABASE_URL.startswith('postgresql://'):
            # Extract connection details from URL
            import re
            match = re.match(r'postgresql://([^@]+)@([^:]+):(\d+)/(.+)', cls.DATABASE_URL)
            if match:
                return {
                    'host': match.group(2),
                    'port': int(match.group(3)),
                    'database': match.group(4),
                    'user': match.group(1),
                    'password': ''  # Would need to be provided separately
                }

        # Default connection parameters
        return {
            'host': 'localhost',
            'port': 5432,
            'database': 'trc_platform',
            'user': 'trc_user',
            'password': ''
        }

    @classmethod
    def print_config_summary(cls):
        """Print current configuration summary"""
        print("🔧 UAT Configuration Summary:")
        print(f"  App URL: {cls.APP_URL}")
        print(f"  Database: {cls.DATABASE_URL}")
        print(f"  Mailcatcher: {cls.MAILCATCHER_URL}")
        print(f"  Admin Email: {cls.ADMIN_EMAIL}")
        print(f"  Token Storage: {cls.TOKEN_STORAGE_DIR}")
        print(f"  Log Level: {cls.LOG_LEVEL}")
        print("=" * 50)

# Global configuration instance
config = UATConfig()

if __name__ == "__main__":
    # Print configuration summary when run directly
    config.print_config_summary()