#!/usr/bin/env python3
"""
Error handling utilities for billing UAT tests
Provides helper functions for consistent error handling and logging
"""

import traceback
from typing import Optional, Callable, Any, Dict
from functools import wraps

from uat_test_framework import Colors, print_error, print_warning
from billing_exceptions import (
    BillingTestError, DatabaseConnectionError, DatabaseQueryError,
    ApiConnectionError, AuthenticationError, DataValidationError,
    EmailVerificationError, TestSetupError, TestCleanupError,
    ConfigurationError, ServiceUnavailableError, BusinessLogicError
)


def handle_test_errors(test_id: str = None, step_name: str = None):
    """Decorator for consistent error handling in test methods"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except BillingTestError as e:
                # Add context if not already present
                if not e.test_id:
                    e.test_id = test_id
                if not e.step_name:
                    e.step_name = step_name
                raise e
            except Exception as e:
                # Wrap generic exceptions
                error_msg = f"Unexpected error in {func.__name__}: {str(e)}"
                raise BillingTestError(
                    message=error_msg,
                    test_id=test_id,
                    step_name=step_name,
                    context={'original_exception': str(e), 'traceback': traceback.format_exc()}
                )
        return wrapper
    return decorator


def safe_execute_database_query(
    db_helper,
    query_func: Callable,
    error_message: str = None,
    test_id: str = None,
    step_name: str = None,
    **kwargs
) -> Any:
    """Safely execute a database query with proper error handling"""
    try:
        return query_func(**kwargs)
    except Exception as e:
        if "connection" in str(e).lower():
            raise DatabaseConnectionError(
                message=error_message or f"Database connection failed: {str(e)}",
                test_id=test_id,
                step_name=step_name
            )
        else:
            raise DatabaseQueryError(
                message=error_message or f"Database query failed: {str(e)}",
                query=kwargs.get('query', 'Unknown'),
                params=kwargs.get('params', None),
                test_id=test_id,
                step_name=step_name
            )


def safe_execute_api_call(
    http_client,
    api_func: Callable,
    error_message: str = None,
    test_id: str = None,
    step_name: str = None,
    **kwargs
) -> Any:
    """Safely execute an API call with proper error handling"""
    try:
        response, response_time = api_func(**kwargs)

        if hasattr(response, 'status_code') and response.status_code >= 400:
            status_code = response.status_code
            endpoint = kwargs.get('endpoint', kwargs.get('url', 'Unknown'))

            if status_code == 401 or status_code == 403:
                raise AuthenticationError(
                    message=error_message or f"Authentication failed: {status_code}",
                    endpoint=endpoint,
                    status_code=status_code,
                    test_id=test_id,
                    step_name=step_name
                )
            else:
                raise ApiConnectionError(
                    message=error_message or f"API call failed: {status_code}",
                    endpoint=endpoint,
                    status_code=status_code,
                    test_id=test_id,
                    step_name=step_name
                )

        return response, response_time

    except ConnectionError as e:
        raise ApiConnectionError(
            message=error_message or f"API connection failed: {str(e)}",
            test_id=test_id,
            step_name=step_name
        )
    except (AuthenticationError, ApiConnectionError):
        raise
    except Exception as e:
        raise ApiConnectionError(
            message=error_message or f"Unexpected API error: {str(e)}",
            test_id=test_id,
            step_name=step_name
        )


def validate_test_data(
    data: Any,
    validator_func: Callable,
    error_message: str = None,
    field_name: str = None,
    test_id: str = None,
    step_name: str = None
) -> bool:
    """Validate test data with proper error handling"""
    try:
        result = validator_func(data)
        if not result:
            raise DataValidationError(
                message=error_message or f"Data validation failed for {field_name or 'unknown field'}",
                field_name=field_name,
                actual_value=data,
                test_id=test_id,
                step_name=step_name
            )
        return True
    except DataValidationError:
        raise
    except Exception as e:
        raise DataValidationError(
            message=error_message or f"Validation error: {str(e)}",
            field_name=field_name,
            actual_value=data,
            test_id=test_id,
            step_name=step_name
        )


def log_test_error(error: BillingTestError, context: Dict[str, Any] = None):
    """Log test errors with detailed context"""
    print_error(f"{Colors.RED}{'='*60}")
    print_error(f"TEST ERROR: {error}")
    print_error(f"{'='*60}")

    if error.test_id:
        print_error(f"Test ID: {error.test_id}")
    if error.step_name:
        print_error(f"Step: {error.step_name}")
    if error.timestamp:
        print_error(f"Time: {error.timestamp}")

    # Add type-specific context
    if isinstance(error, DatabaseQueryError) and error.query:
        print_error(f"Query: {error.query}")
        if error.params:
            print_error(f"Params: {error.params}")

    if isinstance(error, ApiConnectionError):
        if error.endpoint:
            print_error(f"Endpoint: {error.endpoint}")
        if error.status_code:
            print_error(f"Status Code: {error.status_code}")

    if isinstance(error, AuthenticationError):
        if error.user_email:
            print_error(f"User Email: {error.user_email}")
        if error.auth_type:
            print_error(f"Auth Type: {error.auth_type}")

    if isinstance(error, DataValidationError):
        if error.field_name:
            print_error(f"Field: {error.field_name}")
        if error.expected_value is not None:
            print_error(f"Expected: {error.expected_value}")
        if error.actual_value is not None:
            print_error(f"Actual: {error.actual_value}")

    # Add custom context
    if error.context:
        print_error("Context:")
        for key, value in error.context.items():
            print_error(f"  {key}: {value}")

    if context:
        print_error("Additional Context:")
        for key, value in context.items():
            print_error(f"  {key}: {value}")

    print_error(f"{Colors.RED}{'='*60}")


def create_error_context(**kwargs) -> Dict[str, Any]:
    """Create error context dictionary"""
    return {
        'timestamp': __import__('datetime').datetime.now().isoformat(),
        **kwargs
    }


class ErrorCollector:
    """Collect and manage multiple errors during test execution"""

    def __init__(self):
        self.errors = []
        self.warnings = []

    def add_error(self, error: BillingTestError, context: Dict[str, Any] = None):
        """Add an error to the collection"""
        self.errors.append((error, context))

    def add_warning(self, message: str, context: Dict[str, Any] = None):
        """Add a warning to the collection"""
        self.warnings.append((message, context))

    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Check if there are any warnings"""
        return len(self.warnings) > 0

    def get_error_summary(self) -> str:
        """Get a summary of all errors"""
        if not self.has_errors():
            return "No errors"

        summary = f"{len(self.errors)} error(s):\n"
        for i, (error, context) in enumerate(self.errors, 1):
            summary += f"  {i}. {error}\n"
        return summary

    def log_all_errors(self):
        """Log all collected errors"""
        for error, context in self.errors:
            log_test_error(error, context)

        for warning, context in self.warnings:
            print_warning(f"WARNING: {warning}")
            if context:
                for key, value in context.items():
                    print_warning(f"  {key}: {value}")

    def clear(self):
        """Clear all errors and warnings"""
        self.errors.clear()
        self.warnings.clear()