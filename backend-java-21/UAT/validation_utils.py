#!/usr/bin/env python3
"""
Centralized Input Validation Utilities
Provides comprehensive input validation and sanitization functions
to prevent injection attacks and ensure data integrity.
"""

import re
import html
import uuid
from typing import Any, Optional, List, Dict, Union
from datetime import datetime, date
from dataclasses import dataclass

from uat_framework import print_error, print_warning


@dataclass
class ValidationResult:
    """Result of input validation"""
    is_valid: bool
    error_message: str = ""
    sanitized_value: Any = None


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class InputValidator:
    """Centralized input validation utility"""

    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(--|#|\/\*|\*\/)",
        r"(\b(MASTER|DBO|SYSADMIN)\b)",
        r"(\b(SLEEP|BENCHMARK|WAITFOR)\b)",
        r"(\b(XP_|SP_)\w+)",
    ]

    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        r"<link[^>]*>",
        r"<meta[^>]*>",
    ]

    @classmethod
    def validate_email(cls, email: str) -> ValidationResult:
        """Validate email format and check for injection attempts"""
        if not email or not isinstance(email, str):
            return ValidationResult(False, "Email is required and must be a string")

        # Check for SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, email, re.IGNORECASE):
                return ValidationResult(False, "Email contains potentially dangerous content")

        # Check for XSS patterns
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, email, re.IGNORECASE):
                return ValidationResult(False, "Email contains potentially dangerous content")

        # Validate email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email.strip()):
            return ValidationResult(False, "Invalid email format")

        # Sanitize and return
        return ValidationResult(True, "", email.strip().lower())

    @classmethod
    def validate_password(cls, password: str, field_name: str = "Password") -> ValidationResult:
        """Validate password strength"""
        if not password or not isinstance(password, str):
            return ValidationResult(False, f"{field_name} is required and must be a string")

        if len(password) < 8:
            return ValidationResult(False, f"{field_name} must be at least 8 characters long")

        if len(password) > 128:
            return ValidationResult(False, f"{field_name} must be less than 128 characters")

        # Check for basic password requirements
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)

        if not (has_upper and has_lower and has_digit and has_special):
            return ValidationResult(
                False,
                f"{field_name} must contain at least one uppercase letter, one lowercase letter, "
                f"one digit, and one special character"
            )

        return ValidationResult(True, "", password)

    @classmethod
    def validate_invite_code(cls, code: str) -> ValidationResult:
        """Validate invite code format"""
        if not code or not isinstance(code, str):
            return ValidationResult(False, "Invite code is required and must be a string")

        code = code.strip()

        if len(code) < 6 or len(code) > 32:
            return ValidationResult(False, "Invite code must be between 6 and 32 characters")

        # Check for SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                return ValidationResult(False, "Invite code contains potentially dangerous content")

        # Validate invite code format (alphanumeric with optional hyphens)
        if not re.match(r'^[a-zA-Z0-9-]+$', code):
            return ValidationResult(False, "Invite code can only contain letters, numbers, and hyphens")

        return ValidationResult(True, "", code.upper())

    @classmethod
    def validate_uuid(cls, uuid_str: str, field_name: str = "UUID") -> ValidationResult:
        """Validate UUID format"""
        if not uuid_str or not isinstance(uuid_str, str):
            return ValidationResult(False, f"{field_name} is required and must be a string")

        try:
            uuid.UUID(uuid_str.strip())
            return ValidationResult(True, "", uuid_str.strip())
        except ValueError:
            return ValidationResult(False, f"Invalid {field_name} format")

    @classmethod
    def validate_token(cls, token: str, token_type: str = "JWT") -> ValidationResult:
        """Validate token format"""
        if not token or not isinstance(token, str):
            return ValidationResult(False, f"{token_type} token is required and must be a string")

        token = token.strip()

        # Check for SQL injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, token, re.IGNORECASE):
                return ValidationResult(False, f"{token_type} token contains potentially dangerous content")

        if token_type == "JWT":
            # JWT should have 3 parts separated by dots
            parts = token.split('.')
            if len(parts) != 3 or not all(part.strip() for part in parts):
                return ValidationResult(False, "Invalid JWT token format")

        elif token_type == "API":
            # API token validation (customize based on your format)
            if not token.startswith('tok_'):
                return ValidationResult(False, "Invalid API token format - must start with 'tok_'")

            if len(token) != 47:  # tok_ + 43 chars
                return ValidationResult(False, "Invalid API token length")

        return ValidationResult(True, "", token)

    @classmethod
    def validate_string_field(cls, value: Any, field_name: str, min_length: int = 1,
                            max_length: int = 255, allow_empty: bool = False) -> ValidationResult:
        """Validate string field with length constraints"""
        if value is None:
            return ValidationResult(allow_empty, "" if allow_empty else f"{field_name} is required")

        if not isinstance(value, str):
            return ValidationResult(False, f"{field_name} must be a string")

        value = value.strip()

        if not value and not allow_empty:
            return ValidationResult(False, f"{field_name} cannot be empty")

        if not allow_empty and (len(value) < min_length or len(value) > max_length):
            return ValidationResult(
                False,
                f"{field_name} must be between {min_length} and {max_length} characters"
            )

        # Check for injection patterns
        for pattern in cls.SQL_INJECTION_PATTERNS + cls.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return ValidationResult(False, f"{field_name} contains potentially dangerous content")

        # Sanitize HTML entities
        sanitized_value = html.escape(value)

        return ValidationResult(True, "", sanitized_value)

    @classmethod
    def validate_date(cls, date_value: Union[str, date, datetime], field_name: str = "Date") -> ValidationResult:
        """Validate date input"""
        if date_value is None:
            return ValidationResult(False, f"{field_name} is required")

        if isinstance(date_value, str):
            try:
                # Try parsing common date formats
                for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ']:
                    try:
                        parsed_date = datetime.strptime(date_value.strip(), fmt)
                        return ValidationResult(True, "", parsed_date)
                    except ValueError:
                        continue

                return ValidationResult(False, f"Invalid {field_name} format")
            except Exception:
                return ValidationResult(False, f"Invalid {field_name} format")

        elif isinstance(date_value, (date, datetime)):
            return ValidationResult(True, "", date_value)

        else:
            return ValidationResult(False, f"{field_name} must be a date or datetime")

    @classmethod
    def validate_positive_integer(cls, value: Any, field_name: str, min_value: int = 1,
                                max_value: int = None) -> ValidationResult:
        """Validate positive integer input"""
        if value is None:
            return ValidationResult(False, f"{field_name} is required")

        try:
            int_value = int(value)
            if int_value < min_value:
                return ValidationResult(False, f"{field_name} must be at least {min_value}")

            if max_value is not None and int_value > max_value:
                return ValidationResult(False, f"{field_name} must be at most {max_value}")

            return ValidationResult(True, "", int_value)

        except (ValueError, TypeError):
            return ValidationResult(False, f"{field_name} must be a valid integer")

    @classmethod
    def validate_table_name(cls, table_name: str) -> ValidationResult:
        """Validate table name against whitelist"""
        if not table_name or not isinstance(table_name, str):
            return ValidationResult(False, "Table name is required")

        # Whitelist of allowed table names
        allowed_tables = {
            'users', 'invite_codes', 'api_tokens', 'billing_periods', 'usage_requests',
            'email_verifications', 'request_logs', 'billing_adjustments',
            'payment_statuses', 'usage_statistics'
        }

        table_name = table_name.strip().lower()

        if table_name not in allowed_tables:
            return ValidationResult(False, f"Table '{table_name}' is not in the allowed list")

        return ValidationResult(True, "", table_name)

    @classmethod
    def sanitize_sql_identifier(cls, identifier: str) -> str:
        """Sanitize SQL identifier (table/column names)"""
        if not identifier or not isinstance(identifier, str):
            raise ValidationError("SQL identifier must be a non-empty string")

        # Only allow alphanumeric characters and underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '', identifier)

        if not sanitized:
            raise ValidationError("Invalid SQL identifier after sanitization")

        return sanitized

    @classmethod
    def validate_page_size(cls, page_size: Any, default_size: int = 25, max_size: int = 100) -> int:
        """Validate and normalize page size for pagination"""
        try:
            size = int(page_size)
            if size < 1:
                return default_size
            if size > max_size:
                return max_size
            return size
        except (ValueError, TypeError):
            return default_size

    @classmethod
    def validate_sort_field(cls, sort_field: str, allowed_fields: List[str], default_field: str = "id") -> str:
        """Validate sort field against allowed list"""
        if not sort_field or sort_field not in allowed_fields:
            return default_field
        return sort_field

    @classmethod
    def validate_sort_direction(cls, direction: str, default_direction: str = "asc") -> str:
        """Validate sort direction"""
        if direction and direction.lower() in ['asc', 'desc']:
            return direction.lower()
        return default_direction


# Convenience functions for common validations
def validate_registration_data(email: str, password: str, invite_code: str) -> List[ValidationResult]:
    """Validate complete user registration data"""
    validator = InputValidator()
    results = [
        validator.validate_email(email),
        validator.validate_password(password, "Password"),
        validator.validate_invite_code(invite_code)
    ]
    return results


def validate_login_data(email: str, password: str) -> List[ValidationResult]:
    """Validate login credentials"""
    validator = InputValidator()
    results = [
        validator.validate_email(email),
        validator.validate_password(password, "Password")
    ]
    return results


def validate_token_input(token: str, token_type: str = "JWT") -> ValidationResult:
    """Validate token input"""
    return InputValidator.validate_token(token, token_type)


def sanitize_user_input(value: str) -> str:
    """Quick sanitization for user input"""
    result = InputValidator.validate_string_field(value, "input", allow_empty=True)
    return result.sanitized_value if result.is_valid else ""


def is_safe_input(value: str) -> bool:
    """Quick check if input is safe (no injection patterns)"""
    if not value or not isinstance(value, str):
        return False

    # Check for SQL injection patterns
    for pattern in InputValidator.SQL_INJECTION_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            return False

    # Check for XSS patterns
    for pattern in InputValidator.XSS_PATTERNS:
        if re.search(pattern, value, re.IGNORECASE):
            return False

    return True