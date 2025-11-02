#!/usr/bin/env python3
"""
Centralized Authentication Utilities
Consolidates token validation, user creation, and authentication operations
to eliminate code duplication across the UAT framework.
"""

import jwt
import requests
import re
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

from uat_config import config
from uat_framework import (
    DatabaseHelper, HTTPClient,
    print_error, print_warning, print_success
)


class AuthenticationError(Exception):
    """Custom exception for authentication errors"""
    pass


class TokenValidationError(Exception):
    """Custom exception for token validation errors"""
    pass


class AuthenticationManager:
    """Centralized authentication management utility"""

    def __init__(self, db_helper: DatabaseHelper = None, http_client: HTTPClient = None):
        self.db_helper = db_helper
        self.http_client = http_client

    def extract_jwt_token(self, response: requests.Response) -> str:
        """Extract JWT token from response with improved error handling"""
        try:
            if not response.ok:
                raise AuthenticationError(f"Authentication failed with status {response.status_code}")

            data = response.json()
            token = data.get('token', '')

            if not token:
                raise AuthenticationError("No token found in response")

            return token

        except requests.JSONDecodeError:
            raise AuthenticationError("Invalid JSON response from authentication endpoint")
        except KeyError as e:
            raise AuthenticationError(f"Missing field in authentication response: {e}")

    def extract_json_field(self, response: requests.Response, field: str) -> Any:
        """Extract field from JSON response with error handling"""
        try:
            data = response.json()
            return data.get(field)
        except requests.JSONDecodeError:
            print_error(f"Failed to parse JSON response while extracting field '{field}'")
            return None

    def validate_api_token_format(self, token: str) -> bool:
        """Validate API token format"""
        if not token or not isinstance(token, str):
            return False

        # API token should start with prefix and have correct length
        return (token.startswith(config.api_token_prefix) and
                len(token) == config.api_token_length)

    def authenticate_user(self, email: str, password: str) -> str:
        """Authenticate user and return JWT token"""
        if not self.http_client:
            raise AuthenticationError("HTTP client not initialized")

        login_data = {
            'email': email,
            'password': password
        }

        try:
            response = self.http_client.post(
                config.get_endpoint('login', includeDomain=True),
                json=login_data
            )

            return self.extract_jwt_token(response)

        except requests.RequestException as e:
            raise AuthenticationError(f"Login request failed: {e}")

    def authenticate_admin(self) -> str:
        """Authenticate admin user and return JWT token"""
        if not config.admin_password:
            raise AuthenticationError("Admin password not configured")

        return self.authenticate_user(config.admin_email, config.admin_password)

    def create_user_with_invite(self, email: str, password: str, invite_code: str) -> Dict[str, Any]:
        """Create user with invite code and return registration response"""
        if not self.http_client:
            raise AuthenticationError("HTTP client not initialized")

        registration_data = {
            'email': email,
            'password': password,
            'inviteCode': invite_code
        }

        try:
            response = self.http_client.post(
                config.get_endpoint('user_register', includeDomain=True),
                json=registration_data
            )

            if response.ok:
                return {
                    'success': True,
                    'response': response,
                    'user_created': True
                }
            else:
                return {
                    'success': False,
                    'response': response,
                    'error': response.text
                }

        except requests.RequestException as e:
            raise AuthenticationError(f"User registration failed: {e}")

    def get_authenticated_headers(self, token: str) -> Dict[str, str]:
        """Get headers with JWT authentication"""
        return config.get_auth_headers(token)

    def get_api_token_headers(self, api_token: str) -> Dict[str, str]:
        """Get headers with API token authentication"""
        return config.get_api_token_headers(api_token)

    def verify_user_in_database(self, email: str) -> bool:
        """Check if user exists in database"""
        if not self.db_helper:
            raise AuthenticationError("Database helper not initialized")

        return self.db_helper.verify_user_exists(email)

    def verify_user_email_in_database(self, email: str) -> bool:
        """Directly verify user email in database for testing"""
        if not self.db_helper:
            raise AuthenticationError("Database helper not initialized")

        return self.db_helper.verify_user_email_directly(email)


class TokenManager:
    """Centralized token management utility"""

    def __init__(self, auth_manager: AuthenticationManager = None):
        self.auth_manager = auth_manager or AuthenticationManager()
        self._token_cache = {}

    def get_admin_token(self, refresh: bool = False) -> str:
        """Get admin JWT token with caching"""
        if refresh or 'admin' not in self._token_cache:
            token = self.auth_manager.authenticate_admin()
            self._token_cache['admin'] = token

        return self._token_cache['admin']

    def get_user_token(self, email: str, password: str, refresh: bool = False) -> str:
        """Get user JWT token with caching"""
        cache_key = f"user_{email}"

        if refresh or cache_key not in self._token_cache:
            token = self.auth_manager.authenticate_user(email, password)
            self._token_cache[cache_key] = token

        return self._token_cache[cache_key]

    def clear_token_cache(self, user_email: str = None):
        """Clear token cache for specific user or all users"""
        if user_email:
            cache_key = f"user_{user_email}"
            self._token_cache.pop(cache_key, None)
        else:
            self._token_cache.clear()

    def validate_token(self, token: str) -> bool:
        """Validate JWT token"""
        is_valid, _ = self.auth_manager.validate_jwt_token(token)
        return is_valid


# Create global instances for convenience
auth_manager = AuthenticationManager()
token_manager = TokenManager(auth_manager)


# Convenience functions for backward compatibility
def extract_jwt_token(response: requests.Response) -> str:
    """Extract JWT token from response (backward compatibility wrapper)"""
    return auth_manager.extract_jwt_token(response)


def extract_json_field(response: requests.Response, field: str) -> Any:
    """Extract field from JSON response (backward compatibility wrapper)"""
    return auth_manager.extract_json_field(response, field)


def get_admin_headers() -> Dict[str, str]:
    """Get admin headers with authentication"""
    token = token_manager.get_admin_token()
    return auth_manager.get_authenticated_headers(token)


def get_user_headers(email: str, password: str) -> Dict[str, str]:
    """Get user headers with authentication"""
    token = token_manager.get_user_token(email, password)
    return auth_manager.get_authenticated_headers(token)


def validate_email_format(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """Validate password strength according to system requirements"""
    from uat_config import auth_config

    errors = []

    if len(password) < auth_config.password_min_length:
        errors.append(f"Password must be at least {auth_config.password_min_length} characters")

    if auth_config.password_require_uppercase and not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter")

    if auth_config.password_require_lowercase and not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter")

    if auth_config.password_require_digit and not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit")

    if auth_config.password_require_special and not any(c in "!@#$%^&*" for c in password):
        errors.append("Password must contain at least one special character (!@#$%^&*)")

    return len(errors) == 0, " ".join(errors) if errors else ""
