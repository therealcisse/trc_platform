#!/usr/bin/env python3
"""
UAT Configuration Management for API Token Testing
Centralized configuration for all TRC Platform API Token UAT tests
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class UATConfig:
    """Centralized configuration for API Token UAT tests"""

    # Environment Configuration
    APP_URL = os.getenv('UAT_APP_URL', 'http://localhost:8080')
    DATABASE_URL = os.getenv('UAT_DATABASE_URL', 'postgresql://trc_user:trc_password@localhost:5432/trc_platform')
    MAILCATCHER_URL = os.getenv('UAT_MAILCATCHER_URL', 'http://localhost:1080')

    # Bootstrap Admin User (from auth tests)
    ADMIN_EMAIL = 'admin@trc-platform.local'
    ADMIN_PASSWORD = 'password'
    ADMIN_USER_ID = '550e8400-e29b-41d4-a716-446655440000'

    # Pre-loaded Invite Codes (from auth tests)
    PRELOADED_INVITE_CODES = [
        'TESTCODE123',
        'DEVINVITE456',
        'WELCOMETEST'
    ]

    # API Token Test Data
    TEST_API_TOKENS = {
        'basic_token': {
            'name': 'Basic API Token',
            'description': 'Basic token for testing'
        },
        'expired_token': {
            'name': 'Expired API Token',
            'description': 'Token that will expire for testing expiration handling'
        },
        'revoked_token': {
            'name': 'Revoked API Token',
            'description': 'Token that will be revoked for testing revocation'
        },
        'performance_token': {
            'name': 'Performance Test Token',
            'description': 'Token for performance testing'
        }
    }

    # Test Users
    TEST_USERS = {
        'token_registration': {
            'email': 'api-token-test@example.com',
            'password': 'SecureTokenPassword123!',
            'description': 'User for API token registration tests'
        },
        'token_authentication': {
            'email': 'api-auth-test@example.com',
            'password': 'SecureAuthPassword123!',
            'description': 'User for API token authentication tests'
        },
        'token_listing': {
            'email': 'api-list-test@example.com',
            'password': 'SecureListPassword123!',
            'description': 'User for API token listing tests'
        },
        'token_revocation': {
            'email': 'api-revoke-test@example.com',
            'password': 'SecureRevokePassword123!',
            'description': 'User for API token revocation tests'
        },
        'token_security': {
            'email': 'api-security-test@example.com',
            'password': 'SecureSecurityPassword123!',
            'description': 'User for API token security tests'
        },
        'token_expiration': {
            'email': 'api-expire-test@example.com',
            'password': 'SecureExpirePassword123!',
            'description': 'User for API token expiration tests'
        }
    }

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
        'email_resend': '/api/auth/resend-verification',
        'password_change': '/api/auth/password/change',
        'accept_terms': '/api/auth/accept-terms',
        'accept_disclaimer': '/api/auth/accept-disclaimer',
        'user_me': '/api/customers/me',
        # API Token Endpoints (expected contract)
        'api_tokens': '/api/customers/tokens',
        'api_token_create': '/api/customers/tokens',
        'api_token_get': '/api/customers/tokens/{id}',
        'api_token_delete': '/api/customers/tokens/{id}',
        # Test endpoints for API token validation
        'core_solve': '/api/core/solve',
        'usage_current': '/api/usage/current'
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
        # API Token specific queries
        'get_user_tokens': """
            SELECT id, name, token_prefix, created_at, last_used_at, expires_at, revoked_at
            FROM api_tokens
            WHERE user_id = %s
            ORDER BY created_at DESC
        """,
        'get_token_by_id': """
            SELECT id, user_id, name, token_prefix, token_hash, created_at,
                   last_used_at, expires_at, revoked_at
            FROM api_tokens
            WHERE id = %s
        """,
        'get_token_by_prefix': """
            SELECT id, user_id, name, token_prefix, created_at,
                   last_used_at, expires_at, revoked_at
            FROM api_tokens
            WHERE token_prefix = %s
        """,
        'check_token_exists': """
            SELECT id FROM api_tokens
            WHERE user_id = %s AND name = %s AND revoked_at IS NULL
        """,
        'verify_token_revoked': """
            SELECT revoked_at FROM api_tokens
            WHERE id = %s AND revoked_at IS NOT NULL
        """,
        'get_token_usage_count': """
            SELECT COUNT(*) as usage_count
            FROM request_logs
            WHERE token_id = %s
        """,
        'check_token_usage_update': """
            SELECT last_used_at FROM api_tokens
            WHERE id = %s AND last_used_at IS NOT NULL
        """,
        'verify_token_hash': """
            SELECT token_hash FROM api_tokens
            WHERE id = %s
        """
    }

    # JWT Configuration
    JWT_TOKEN_PREFIX = 'Bearer '
    JWT_ALGORITHM = 'HS256'

    # API Token Configuration
    API_TOKEN_PREFIX = 'tok_'
    API_TOKEN_LENGTH = 32  # bytes (not including prefix)
    API_TOKEN_PREFIX_LENGTH = 12  # characters shown in UI
    API_TOKEN_DEFAULT_EXPIRY_HOURS = 24
    TOKEN_DEFAULT_EXPIRY = timedelta(hours=API_TOKEN_DEFAULT_EXPIRY_HOURS)

    # API Token Validation
    API_TOKEN_PATTERNS = {
        'valid_pattern': r'^tok_[A-Za-z0-9_-]{43}$',  # tok_ + base64url encoding of 32 bytes
        'prefix_pattern': r'^tok_[A-Za-z0-9_-]{11}$'  # First 12 characters including tok_
    }

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
        'verification_token': 'verification_token.txt',
        'api_tokens': 'api_tokens.txt',
        'user_credentials': 'user_credentials.txt'
    }

    # Response Validation
    REQUIRED_RESPONSE_FIELDS = {
        'login': ['id', 'email', 'token'],
        'invite_create': ['id', 'code', 'active', 'createdAt', 'createdByUserId', 'createdByUserEmail'],
        'user_profile': ['id', 'email', 'isEmailVerified', 'dateJoined'],
        'invite_list': ['content', 'pageable'],
        # API Token response fields
        'token_create': ['id', 'token', 'name', 'createdAt', 'expiresAt'],
        'token_list': ['content', 'pageable'],
        'token_item': ['id', 'name', 'createdAt', 'lastUsedAt', 'expiresAt', 'revokedAt'],
        'token_info': ['id', 'name', 'tokenPrefix', 'createdAt', 'lastUsedAt', 'expiresAt', 'revokedAt']
    }

    # Password Requirements
    PASSWORD_REQUIREMENTS = {
        'min_length': 8,
        'require_uppercase': True,
        'require_lowercase': True,
        'require_digits': True,
        'require_special': True
    }

    # API Token Requirements
    API_TOKEN_REQUIREMENTS = {
        'name_min_length': 1,
        'name_max_length': 255,
        'max_tokens_per_user': 10,  # Assumed limit
        'default_expiration_days': 365,
        'token_format': 'base64url'
    }

    # Test Scenarios Configuration
    TEST_SCENARIOS = {
        'valid_tokens': [
            {'name': 'Valid Token No Expiry', 'expires_at': None},
            {'name': 'Valid Token With Expiry', 'expires_at': (datetime.now() + timedelta(days=30)).isoformat()},
            {'name': 'Valid Token Short Name', 'expires_at': None}
        ],
        'invalid_tokens': [
            'invalid_format_token',
            'tok_too_short',
            'tok_no_base64_chars_$%^&*',
            '',
            None
        ],
        'expired_scenarios': [
            {'name': 'Already Expired', 'expires_at': (datetime.now() - timedelta(days=1)).isoformat()},
            {'name': 'Expires Soon', 'expires_at': (datetime.now() + timedelta(minutes=5)).isoformat()}
        ]
    }

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
            # Simple template substitution for path parameters
            for key, value in kwargs.items():
                endpoint = endpoint.replace(f'{{{key}}}', str(value))

        return f"{cls.APP_URL}{endpoint}"

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
    def validate_api_token_format(cls, token: str) -> bool:
        """Validate API token format"""
        if not token or not isinstance(token, str):
            return False

        import re
        return bool(re.match(cls.API_TOKEN_PATTERNS['valid_pattern'], token))

    @classmethod
    def validate_api_token_name(cls, name: str) -> bool:
        """Validate API token name"""
        if not name or not isinstance(name, str):
            return False

        length = len(name)
        min_len = cls.API_TOKEN_REQUIREMENTS['name_min_length']
        max_len = cls.API_TOKEN_REQUIREMENTS['name_max_length']

        return min_len <= length <= max_len

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
    def generate_unique_token_name(cls, base_name: str) -> str:
        """Generate unique token name with timestamp"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"{base_name} - {timestamp}"

    @classmethod
    def print_config_summary(cls):
        """Print current configuration summary"""
        print("🔧 API Token UAT Configuration Summary:")
        print(f"  App URL: {cls.APP_URL}")
        print(f"  Database: {cls.DATABASE_URL}")
        print(f"  Admin Email: {cls.ADMIN_EMAIL}")
        print(f"  Token Storage: {cls.TOKEN_STORAGE_DIR}")
        print(f"  Log Level: {cls.LOG_LEVEL}")
        print(f"  API Token Prefix: {cls.API_TOKEN_PREFIX}")
        print(f"  API Token Length: {cls.API_TOKEN_LENGTH} bytes")
        print("=" * 50)

# Global configuration instance
config = UATConfig()

if __name__ == "__main__":
    # Print configuration summary when run directly
    config.print_config_summary()
