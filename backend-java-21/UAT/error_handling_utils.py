#!/usr/bin/env python3
"""
Centralized Error Handling Utilities
Provides consistent error handling, logging, and recovery strategies
across the UAT framework to improve reliability and debugging.
"""

import sys
import traceback
import time
from typing import Any, Callable, Optional, Dict, List, Type, Union
from functools import wraps
from dataclasses import dataclass, field
from enum import Enum

from uat_framework import print_error, print_warning, print_info


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better organization"""
    AUTHENTICATION = "authentication"
    DATABASE = "database"
    NETWORK = "network"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    SYSTEM = "system"
    TEST = "test"


@dataclass
class ErrorContext:
    """Context information for errors"""
    operation: str
    component: str
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorInfo:
    """Structured error information"""
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    exception: Optional[Exception] = None
    context: Optional[ErrorContext] = None
    timestamp: float = field(default_factory=time.time)
    stack_trace: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


class UATError(Exception):
    """Base exception for UAT framework errors"""
    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.SYSTEM,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM, context: ErrorContext = None):
        super().__init__(message)
        self.category = category
        self.severity = severity
        self.context = context


class AuthenticationError(UATError):
    """Authentication related errors"""
    def __init__(self, message: str, context: ErrorContext = None):
        super().__init__(message, ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH, context)


class DatabaseError(UATError):
    """Database related errors"""
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.HIGH, context: ErrorContext = None):
        super().__init__(message, ErrorCategory.DATABASE, severity, context)


class NetworkError(UATError):
    """Network related errors"""
    def __init__(self, message: str, context: ErrorContext = None):
        super().__init__(message, ErrorCategory.NETWORK, ErrorSeverity.MEDIUM, context)


class ValidationError(UATError):
    """Input validation errors"""
    def __init__(self, message: str, context: ErrorContext = None):
        super().__init__(message, ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM, context)


class ConfigurationError(UATError):
    """Configuration related errors"""
    def __init__(self, message: str, context: ErrorContext = None):
        super().__init__(message, ErrorCategory.CONFIGURATION, ErrorSeverity.CRITICAL, context)


class TestError(UATError):
    """Test execution errors"""
    def __init__(self, message: str, context: ErrorContext = None):
        super().__init__(message, ErrorCategory.TEST, ErrorSeverity.LOW, context)


class ErrorHandler:
    """Centralized error handling utility"""

    def __init__(self):
        self.error_log: List[ErrorInfo] = []
        self.error_callbacks: Dict[ErrorCategory, List[Callable]] = {}
        self.max_log_size = 1000

    def handle_error(self, error: Union[Exception, str], category: ErrorCategory = ErrorCategory.SYSTEM,
                    severity: ErrorSeverity = ErrorSeverity.MEDIUM, context: ErrorContext = None,
                    should_raise: bool = False) -> ErrorInfo:
        """Handle error with consistent logging and optional re-raising"""
        error_id = self._generate_error_id()

        # Convert string errors to exceptions
        if isinstance(error, str):
            error = Exception(error)

        # Create error info
        error_info = ErrorInfo(
            error_id=error_id,
            category=category,
            severity=severity,
            message=str(error),
            exception=error,
            context=context,
            stack_trace=traceback.format_exc() if isinstance(error, Exception) else None
        )

        # Log error
        self._log_error(error_info)

        # Store in error log
        self._store_error(error_info)

        # Trigger error callbacks
        self._trigger_callbacks(error_info)

        # Re-raise if requested
        if should_raise:
            raise error

        return error_info

    def _generate_error_id(self) -> str:
        """Generate unique error ID"""
        import uuid
        return f"ERR_{uuid.uuid4().hex[:8].upper()}"

    def _log_error(self, error_info: ErrorInfo):
        """Log error with appropriate level based on severity"""
        prefix = f"[{error_info.error_id}] [{error_info.category.value.upper()}]"

        if error_info.context:
            prefix += f" [{error_info.context.component}:{error_info.context.operation}]"

        message = f"{prefix} {error_info.message}"

        if error_info.severity == ErrorSeverity.CRITICAL:
            print_error(f"🚨 CRITICAL: {message}")
            if error_info.stack_trace:
                print_error(f"Stack trace:\n{error_info.stack_trace}")
        elif error_info.severity == ErrorSeverity.HIGH:
            print_error(f"❌ HIGH: {message}")
        elif error_info.severity == ErrorSeverity.MEDIUM:
            print_warning(f"⚠️ MEDIUM: {message}")
        else:
            print_info(f"ℹ️ LOW: {message}")

    def _store_error(self, error_info: ErrorInfo):
        """Store error in log with size limit"""
        self.error_log.append(error_info)

        # Maintain maximum log size
        if len(self.error_log) > self.max_log_size:
            self.error_log = self.error_log[-self.max_log_size:]

    def _trigger_callbacks(self, error_info: ErrorInfo):
        """Trigger registered error callbacks"""
        callbacks = self.error_callbacks.get(error_info.category, [])
        for callback in callbacks:
            try:
                callback(error_info)
            except Exception as e:
                print_error(f"Error in error callback: {e}")

    def register_callback(self, category: ErrorCategory, callback: Callable[[ErrorInfo], None]):
        """Register callback for specific error category"""
        if category not in self.error_callbacks:
            self.error_callbacks[category] = []
        self.error_callbacks[category].append(callback)

    def get_errors_by_category(self, category: ErrorCategory) -> List[ErrorInfo]:
        """Get errors by category"""
        return [error for error in self.error_log if error.category == category]

    def get_errors_by_severity(self, severity: ErrorSeverity) -> List[ErrorInfo]:
        """Get errors by severity"""
        return [error for error in self.error_log if error.severity == severity]

    def clear_error_log(self):
        """Clear error log"""
        self.error_log.clear()

    def get_error_summary(self) -> Dict[str, int]:
        """Get summary of errors by category and severity"""
        summary = {
            'total_errors': len(self.error_log),
            'by_category': {},
            'by_severity': {}
        }

        for error in self.error_log:
            # Count by category
            category = error.category.value
            summary['by_category'][category] = summary['by_category'].get(category, 0) + 1

            # Count by severity
            severity = error.severity.value
            summary['by_severity'][severity] = summary['by_severity'].get(severity, 0) + 1

        return summary


# Global error handler instance
error_handler = ErrorHandler()


def safe_execute(operation: str, func: Callable, *args,
                category: ErrorCategory = ErrorCategory.SYSTEM,
                severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                context: ErrorContext = None,
                default_return: Any = None,
                re_raise: bool = False,
                **kwargs) -> Any:
    """Safely execute function with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_handler.handle_error(e, category, severity, context, should_raise=re_raise)
        return default_return


def retry_operation(operation: str, func: Callable, *args,
                   max_retries: int = 3, retry_delay: float = 1.0,
                   backoff_factor: float = 2.0,
                   retry_on: tuple = (Exception,),
                   context: ErrorContext = None,
                   **kwargs) -> Any:
    """Execute operation with retry logic"""
    last_exception = None
    current_delay = retry_delay

    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                print_info(f"Retrying operation '{operation}' (attempt {attempt + 1}/{max_retries + 1})")
                time.sleep(current_delay)
                current_delay *= backoff_factor

            result = func(*args, **kwargs)
            if attempt > 0:
                print_success(f"Operation '{operation}' succeeded after {attempt + 1} attempts")
            return result

        except retry_on as e:
            last_exception = e
            if attempt < max_retries:
                print_warning(f"Operation '{operation}' failed (attempt {attempt + 1}): {e}")
            else:
                error_handler.handle_error(
                    e, ErrorCategory.NETWORK, ErrorSeverity.HIGH, context,
                    should_raise=False
                )

    raise last_exception


def handle_errors(category: ErrorCategory = ErrorCategory.SYSTEM,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 default_return: Any = None,
                 re_raise: bool = False):
    """Decorator for automatic error handling"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            operation = f"{func.__module__}.{func.__name__}"
            context = ErrorContext(
                operation=operation,
                component=func.__module__.split('.')[-1] if '.' in func.__module__ else func.__module__
            )

            return safe_execute(
                operation, func, *args,
                category=category, severity=severity,
                context=context, default_return=default_return,
                re_raise=re_raise, **kwargs
            )
        return wrapper
    return decorator


def retry_on_failure(max_retries: int = 3, retry_delay: float = 1.0,
                    backoff_factor: float = 2.0,
                    retry_on: tuple = (Exception,)):
    """Decorator for automatic retry on failure"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            operation = f"{func.__module__}.{func.__name__}"
            context = ErrorContext(
                operation=operation,
                component=func.__module__.split('.')[-1] if '.' in func.__module__ else func.__module__
            )

            return retry_operation(
                operation, func, *args,
                max_retries=max_retries, retry_delay=retry_delay,
                backoff_factor=backoff_factor, retry_on=retry_on,
                context=context, **kwargs
            )
        return wrapper
    return decorator


# Convenience functions for common error scenarios
def handle_database_error(error: Exception, operation: str, context: ErrorContext = None) -> ErrorInfo:
    """Handle database-related errors"""
    return error_handler.handle_error(
        error, ErrorCategory.DATABASE, ErrorSeverity.HIGH, context
    )


def handle_network_error(error: Exception, operation: str, context: ErrorContext = None) -> ErrorInfo:
    """Handle network-related errors"""
    return error_handler.handle_error(
        error, ErrorCategory.NETWORK, ErrorSeverity.MEDIUM, context
    )


def handle_validation_error(error: Exception, operation: str, context: ErrorContext = None) -> ErrorInfo:
    """Handle validation errors"""
    return error_handler.handle_error(
        error, ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM, context
    )


def handle_authentication_error(error: Exception, operation: str, context: ErrorContext = None) -> ErrorInfo:
    """Handle authentication errors"""
    return error_handler.handle_error(
        error, ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH, context
    )


def create_error_context(operation: str, component: str, **kwargs) -> ErrorContext:
    """Create error context with additional data"""
    return ErrorContext(
        operation=operation,
        component=component,
        additional_data=kwargs
    )


# Import print_success for use in retry operation
from uat_framework import print_success