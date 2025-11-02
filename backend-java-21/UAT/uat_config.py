"""
Consolidated UAT Configuration
Shared configuration for all TRC Platform UAT tests across all domains.
"""

import os
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class UATConfig:
    """Consolidated UAT configuration for all domains"""

    # Environment configuration
    app_url: str = "http://localhost:8080"
    database_url: str = "postgresql://trc_user:trc_password@localhost:5432/trc_platform"
    mailcatcher_url: str = "http://localhost:1080"

    # Timing and timeouts
    http_timeout: int = 60
    email_timeout: int = 30
    database_timeout: int = 10

    # Admin configuration - loaded from environment variables for security
    admin_email: str = None  # Load from UAT_ADMIN_EMAIL
    admin_password: str = None  # Load from UAT_ADMIN_PASSWORD

    # Test user configuration - more secure defaults
    test_email_domain: str = "uat-test.trc-platform.local"
    test_password_base: str = None  # Load from UAT_TEST_PASSWORD or generate securely

    # JWT configuration
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "trc-platform"

    # API Token configuration
    api_token_prefix: str = "tok_"
    api_token_length: int = 47  # tok_ + 43 chars
    token_expiration_days: int = 30

    # Billing configuration
    billing_cost_per_request: int = 50  # cents
    billing_timezone: str = "Europe/Berlin"

    # Usage configuration
    usage_default_page_size: int = 25
    usage_max_page_size: int = 100
    usage_request_log_retention_days: int = 90

    # API Endpoints
    ENDPOINTS = {
        'login': '/api/customers/login',
        'user_register': '/api/customers/register',
        'admin_invites': '/api/v1/admin/invites',
        'api_tokens': '/api/customers/tokens',
        'core_solve': '/api/core/solve',
        'core_test_solve': '/api/core/test-solve',
        'billing_current': '/api/customers/billing/current',
        'billing_periods': '/api/customers/billing/periods',
        'billing_period_detail': '/api/customers/billing/periods/{periodId}',
        'billing_history': '/api/customers/billing/history',
        'usage_summary': '/api/customers/usage/summary',
        'usage_requests': '/api/customers/usage/requests',
        'admin_billing_list': '/api/v1/admin/billing',
        'admin_billing_mark_paid': '/api/v1/admin/billing/{periodId}/mark-paid',
        'admin_billing_mark_overdue': '/api/v1/admin/billing/{periodId}/mark-overdue',
        'admin_billing_waive': '/api/v1/admin/billing/{periodId}/waive',
        'email_verify': '/api/customers/verify-email',
        'email_resend': '/api/customers/resend-verification',
        'password_change': '/api/customers/password-change',
        'users_me': '/api/customers/me',
        'health': '/api/monitoring/health'
    }

    # Status codes
    STATUS_CODES = {
        'success': 200,
        'created': 201,
        'accepted': 202,
        'no_content': 204,
        'bad_request': 400,
        'unauthorized': 401,
        'forbidden': 403,
        'not_found': 404,
        'method_not_allowed': 405,
        'conflict': 409,
        'unprocessable_entity': 422,
        'internal_server_error': 500,
        'service_unavailable': 503
    }

    def get_endpoint(self, endpoint_name: str, includeDomain: bool = False, **kwargs) -> str:
        """Get endpoint URL by name with optional parameter substitution"""
        endpoint = self.ENDPOINTS.get(endpoint_name)
        if not endpoint:
            raise ValueError(f"Unknown endpoint: {endpoint_name}")

        if kwargs:
            try:
                endpoint = endpoint.format(**kwargs)
            except KeyError as e:
                raise ValueError(f"Missing parameter for endpoint {endpoint_name}: {e}")

        return f"{self.app_url}{endpoint}" if includeDomain else endpoint

    # Admin configuration aliases for backward compatibility
    @property
    def ADMIN_EMAIL(self):
        return self.admin_email

    @property
    def ADMIN_PASSWORD(self):
        return self.admin_password

    # Utility methods
    def generate_unique_email(self, prefix: str) -> str:
        """Generate unique email for testing"""
        import uuid
        timestamp = int(time.time())
        unique_id = str(uuid.uuid4())[:8]
        return f"{prefix}-{timestamp}-{unique_id}@{self.test_email_domain}"

    def generate_unique_invite_code(self, prefix: str) -> str:
        """Generate unique invite code for testing (6-32 characters)"""
        import uuid
        unique_id = str(uuid.uuid4())[:8].upper()
        # Create code that fits within 6-32 characters
        if len(prefix) <= 10:
            return f"{prefix[:10]}-{unique_id}"  # Max ~21 chars
        else:
            # If prefix is long, use shorter version
            short_prefix = prefix[:8]
            return f"{short_prefix}-{unique_id}"  # Max ~19 chars
    usage_supported_services: list = None
    usage_default_sort: str = "requestTs"
    usage_default_sort_direction: str = "desc"

    # Logging
    log_level: str = "INFO"

    # Test execution
    max_retry_attempts: int = 3
    retry_delay: float = 1.0

    def __post_init__(self):
        """Initialize configuration from environment variables"""
        import secrets
        import string

        # Override with environment variables if present
        self.app_url = os.getenv('UAT_APP_URL', self.app_url)
        self.database_url = os.getenv('UAT_DATABASE_URL', self.database_url)
        self.mailcatcher_url = os.getenv('UAT_MAILCATCHER_URL', self.mailcatcher_url)
        self.log_level = os.getenv('UAT_LOG_LEVEL', self.log_level)

        # Load sensitive configuration from environment variables
        self.admin_email = os.getenv('UAT_ADMIN_EMAIL', 'admin@trc-platform.local')
        self.admin_password = os.getenv('UAT_ADMIN_PASSWORD')

        # Generate secure test password if not provided
        self.test_password_base = os.getenv('UAT_TEST_PASSWORD')
        if not self.test_password_base:
            # Generate a secure random password for testing
            self.test_password_base = self._generate_secure_password()

        # Validate that required sensitive config is available
        self._validate_sensitive_config()

    def _generate_secure_password(self) -> str:
        """Generate a secure random password for testing"""
        import secrets
        import string

        # Generate 16-character password with all required character types
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        while True:
            password = ''.join(secrets.choice(alphabet) for _ in range(16))
            # Ensure it meets password requirements
            if (len(password) >= 8 and
                any(c.isupper() for c in password) and
                any(c.islower() for c in password) and
                any(c.isdigit() for c in password) and
                any(c in "!@#$%^&*" for c in password)):
                return password

    def _validate_sensitive_config(self):
        """Validate that sensitive configuration is available"""
        if not self.admin_password:
            raise ValueError(
                "UAT_ADMIN_PASSWORD environment variable is required. "
                "This is a security measure to prevent hardcoded credentials."
            )

        # Initialize default values for list fields
        if self.usage_supported_services is None:
            self.usage_supported_services = [
                "core.image_solve",
                "core.text_solve",
                "core.analysis",
                "core.processing"
            ]

    @property
    def http_headers(self) -> Dict[str, str]:
        """Default HTTP headers for requests"""
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'TRC-Platform-UAT/1.0.0'
        }

    def generate_test_email(self, test_name: str, timestamp: str = None) -> str:
        """Generate unique test email address"""
        import time
        if timestamp is None:
            timestamp = str(int(time.time()))

        return f"{test_name.lower().replace(' ', '-')}--{timestamp}@{self.test_email_domain}"

    def generate_test_password(self, suffix: str = "") -> str:
        """Generate test password"""
        if suffix:
            return f"{self.test_password_base}{suffix}"
        return self.test_password_base

    def get_auth_headers(self, token: str) -> Dict[str, str]:
        """Get headers with JWT authentication"""
        headers = self.http_headers.copy()
        headers['Authorization'] = f"Bearer {token}"
        return headers

    def get_api_token_headers(self, api_token: str) -> Dict[str, str]:
        """Get headers with API token authentication"""
        headers = self.http_headers.copy()
        headers['X-API-Key'] = api_token
        return headers

    def validate_environment(self) -> Dict[str, bool]:
        """Validate that required environment components are available"""
        results = {
            'app_available': False,
            'database_available': False,
            'mailcatcher_available': False
        }

        try:
            import requests
            # Test app availability
            response = requests.get(f"{self.app_url}/api/monitoring/health", timeout=5)
            results['app_available'] = response.status_code == 200
        except:
            pass

        try:
            import psycopg2
            # Test database availability
            conn = psycopg2.connect(self.database_url, connect_timeout=5)
            conn.close()
            results['database_available'] = True
        except:
            pass

        try:
            import requests
            # Test mailcatcher availability
            response = requests.get(f"{self.mailcatcher_url}/messages", timeout=5)
            results['mailcatcher_available'] = response.status_code == 200
        except:
            pass

        return results

    def print_environment_status(self) -> bool:
        """Print environment validation status"""
        from uat_framework import print_success, print_error, print_warning, print_info

        print_info("Validating UAT Environment...")

        validation = self.validate_environment()
        all_good = True

        if validation['app_available']:
            print_success(f"✓ Application available at {self.app_url}")
        else:
            print_error(f"❌ Application not available at {self.app_url}")
            all_good = False

        if validation['database_available']:
            print_success("✓ Database connection successful")
        else:
            print_error(f"❌ Database connection failed: {self.database_url}")
            all_good = False

        if validation['mailcatcher_available']:
            print_success(f"✓ Mailcatcher available at {self.mailcatcher_url}")
        else:
            print_error(f"❌ Mailcatcher not available at {self.mailcatcher_url}")
            all_good = False

        return all_good

    # Add missing method for backward compatibility
    def print_config_summary(self):
        """Print configuration summary (method version for backward compatibility)"""
        from uat_framework import print_info, print_success

        print_info("UAT Configuration Summary:")
        print_info(f"  Application URL: {self.app_url}")
        print_info(f"  Database: {self.database_url}")
        print_info(f"  Mailcatcher: {self.mailcatcher_url}")
        print_info(f"  Log Level: {self.log_level}")

        print_success("Configuration loaded successfully")

    # Centralized database queries for all test domains
    DB_QUERIES = {
        # User and authentication queries
        'check_admin_user': 'SELECT id, email, is_staff, email_verified_at FROM users WHERE email = %s',
        'check_complete_user': 'SELECT id, email, email_verified_at FROM users WHERE email = %s',
        'get_user_by_email': 'SELECT id, email, is_staff, email_verified_at, created_at FROM users WHERE email = %s',
        'get_user_id': 'SELECT id FROM users WHERE email = %s',
        'verify_email_exists': 'SELECT id FROM users WHERE email = %s AND email_verified_at IS NOT NULL',

        # Invite code queries
        'check_invite_code': 'SELECT id, code, is_active, expires_at FROM invite_codes WHERE code = %s',
        'check_active_invite_code': 'SELECT id, code, is_active, expires_at FROM invite_codes WHERE code = %s AND is_active = true',
        'create_invite_code': 'INSERT INTO invite_codes (code, is_active, created_by, expires_at) VALUES (%s, %s, %s, %s) RETURNING id',

        # API token queries
        'get_user_tokens': 'SELECT id, name, token_prefix, created_at, last_used_at, expires_at, revoked_at FROM api_tokens WHERE user_id = %s ORDER BY created_at DESC',
        'get_token_by_id': 'SELECT id, user_id, name, token_prefix, created_at, expires_at, revoked_at FROM api_tokens WHERE id = %s',
        'revoke_token': 'UPDATE api_tokens SET revoked_at = NOW() WHERE id = %s',

        # Billing queries
        'get_current_billing_period': 'SELECT id, start_date, end_date, total_requests, total_cost_cents, status FROM billing_periods WHERE user_id = %s AND status = \'ACTIVE\' ORDER BY start_date DESC LIMIT 1',
        'get_billing_periods': 'SELECT id, start_date, end_date, total_requests, total_cost_cents, status FROM billing_periods WHERE user_id = %s ORDER BY start_date DESC',
        'get_billing_period_by_id': 'SELECT * FROM billing_periods WHERE id = %s',
        'update_billing_period': 'UPDATE billing_periods SET status = %s, updated_at = NOW() WHERE id = %s',

        # Usage queries
        'get_usage_requests': 'SELECT id, request_type, processing_time_ms, cost_cents, created_at FROM usage_requests WHERE user_id = %s ORDER BY created_at DESC',
        'get_usage_summary': 'SELECT COUNT(*) as total_requests, SUM(cost_cents) as total_cost FROM usage_requests WHERE user_id = %s AND created_at >= %s',

        # Email verification queries
        'get_email_verification': 'SELECT id, token, expires_at FROM email_verifications WHERE email = %s ORDER BY created_at DESC LIMIT 1',
        'verify_user_email': 'UPDATE users SET email_verified_at = NOW() WHERE email = %s RETURNING id',
    }

    # Centralized response field validation for all test domains
    REQUIRED_RESPONSE_FIELDS = {
        # Authentication endpoints
        'login': ['id', 'email', 'token'],
        'user_registration': ['id', 'email'],
        'admin_login': ['id', 'email', 'token'],

        # Email verification endpoints
        'email_verification': ['message'],
        'resend_verification': ['message'],

        # API token endpoints
        'token_creation': ['id', 'name', 'token', 'expires_at'],
        'token_listing': ['id', 'name', 'token_prefix', 'created_at', 'expires_at'],
        'token_details': ['id', 'name', 'token_prefix', 'created_at', 'expires_at', 'last_used_at'],

        # Billing endpoints
        'billing_current': ['id', 'start_date', 'end_date', 'total_requests', 'total_cost_cents', 'status'],
        'billing_periods': ['id', 'start_date', 'end_date', 'total_requests', 'total_cost_cents', 'status'],
        'billing_period_detail': ['id', 'start_date', 'end_date', 'total_requests', 'total_cost_cents', 'status'],
        'billing_history': ['id', 'start_date', 'end_date', 'total_requests', 'total_cost_cents', 'status'],
        'usage_summary': ['total_requests', 'total_cost_cents', 'period_start', 'period_end'],

        # Admin endpoints
        'invite_creation': ['id', 'code', 'is_active'],
        'invite_list': ['id', 'code', 'is_active', 'created_at', 'expires_at'],
        'admin_billing_list': ['id', 'user_email', 'start_date', 'end_date', 'total_requests', 'total_cost_cents', 'status'],

        # Usage endpoints
        'usage_requests': ['id', 'request_type', 'processing_time_ms', 'cost_cents', 'created_at'],

        # Core endpoints
        'core_solve': ['id', 'solution', 'processing_time_ms', 'cost_cents'],
        'core_test_solve': ['id', 'solution', 'processing_time_ms', 'cost_cents'],
    }

    # Property aliases for backward compatibility
    @property
    def APP_URL(self):
        """Backward compatibility property"""
        return self.app_url

    @property
    def DATABASE_URL(self):
        """Backward compatibility property"""
        return self.database_url

    @property
    def MAILCATCHER_URL(self):
        """Backward compatibility property"""
        return self.mailcatcher_url

# Domain-specific configurations
class AuthConfig:
    """Authentication domain specific configuration"""

    # Password requirements
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_digit: bool = True
    password_require_special: bool = True

    # Email verification
    email_verification_token_timeout: int = 300  # 5 minutes
    email_resend_timeout: int = 60  # 1 minute

    # Session management
    session_timeout_minutes: int = 60
    refresh_token_days: int = 30


class ApiTokenConfig:
    """API Token domain specific configuration"""

    # Token creation
    max_tokens_per_user: int = 10
    default_token_expiration_days: int = 30
    max_token_expiration_days: int = 365

    # Token security
    token_revocation_grace_seconds: int = 300
    token_usage_logging: bool = True

    # Rate limiting
    token_request_rate_limit: int = 100  # requests per hour


class BillingConfig:
    """Billing domain specific configuration"""

    # Billing periods
    billing_period_start_day: int = 1
    billing_period_timezone: str = "Europe/Berlin"

    # Cost calculation
    cost_per_request_cents: int = 50
    minimum_billable_requests: int = 0

    # Payment processing
    payment_grace_period_days: int = 30
    auto_overdue_days: int = 45

    # Usage tracking
    request_log_retention_days: int = 400
    billing_history_retention_months: int = 24


# Create global configuration instance
config = UATConfig()
auth_config = AuthConfig()
api_token_config = ApiTokenConfig()
billing_config = BillingConfig()


def get_domain_config(domain: str):
    """Get configuration for specific domain"""
    if domain == 'auth':
        return auth_config
    elif domain == 'api_token':
        return api_token_config
    elif domain == 'billing':
        return billing_config
    else:
        raise ValueError(f"Unknown domain: {domain}")


def print_config_summary():
    """Print configuration summary"""
    from uat_framework import print_info, print_success

    print_info("UAT Configuration Summary:")
    print_info(f"  Application URL: {config.app_url}")
    print_info(f"  Database: {config.database_url}")
    print_info(f"  Mailcatcher: {config.mailcatcher_url}")
    print_info(f"  Log Level: {config.log_level}")

    print_success("Configuration loaded successfully")
