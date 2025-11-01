#!/usr/bin/env python3
"""
Custom exceptions for billing UAT tests
Provides specific exception types for better error handling and debugging
"""

class BillingTestError(Exception):
    """Base exception for all billing test errors"""
    def __init__(self, message: str, test_id: str = None, step_name: str = None, context: dict = None):
        super().__init__(message)
        self.test_id = test_id
        self.step_name = step_name
        self.context = context or {}
        self.timestamp = __import__('datetime').datetime.now()

    def __str__(self):
        base_msg = super().__str__()
        if self.test_id and self.step_name:
            return f"[{self.test_id}:{self.step_name}] {base_msg}"
        elif self.test_id:
            return f"[{self.test_id}] {base_msg}"
        return base_msg


class DatabaseConnectionError(BillingTestError):
    """Raised when database connection fails"""
    pass


class DatabaseQueryError(BillingTestError):
    """Raised when database query execution fails"""
    def __init__(self, message: str, query: str = None, params: tuple = None, **kwargs):
        super().__init__(message, **kwargs)
        self.query = query
        self.params = params


class ApiConnectionError(BillingTestError):
    """Raised when API connection fails"""
    def __init__(self, message: str, endpoint: str = None, status_code: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.endpoint = endpoint
        self.status_code = status_code


class AuthenticationError(BillingTestError):
    """Raised when authentication fails"""
    def __init__(self, message: str, user_email: str = None, auth_type: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.user_email = user_email
        self.auth_type = auth_type


class DataValidationError(BillingTestError):
    """Raised when test data validation fails"""
    def __init__(self, message: str, field_name: str = None, expected_value=None, actual_value=None, **kwargs):
        super().__init__(message, **kwargs)
        self.field_name = field_name
        self.expected_value = expected_value
        self.actual_value = actual_value


class EmailVerificationError(BillingTestError):
    """Raised when email verification fails"""
    def __init__(self, message: str, recipient_email: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.recipient_email = recipient_email


class TestSetupError(BillingTestError):
    """Raised when test setup fails"""
    pass


class TestCleanupError(BillingTestError):
    """Raised when test cleanup fails"""
    def __init__(self, message: str, cleanup_stage: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.cleanup_stage = cleanup_stage


class ConfigurationError(BillingTestError):
    """Raised when configuration is invalid"""
    def __init__(self, message: str, config_key: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.config_key = config_key


class ServiceUnavailableError(BillingTestError):
    """Raised when required service is unavailable"""
    def __init__(self, message: str, service_name: str = None, service_url: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.service_name = service_name
        self.service_url = service_url


class BusinessLogicError(BillingTestError):
    """Raised when business logic validation fails"""
    def __init__(self, message: str, business_rule: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.business_rule = business_rule


class CostCalculationError(BusinessLogicError):
    """Raised when cost calculation is incorrect"""
    def __init__(self, message: str, expected_cost: int = None, actual_cost: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.expected_cost = expected_cost
        self.actual_cost = actual_cost


class PaymentStatusError(BusinessLogicError):
    """Raised when payment status validation fails"""
    def __init__(self, message: str, expected_status: str = None, actual_status: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.expected_status = expected_status
        self.actual_status = actual_status


class PeriodLifecycleError(BusinessLogicError):
    """Raised when billing period lifecycle validation fails"""
    def __init__(self, message: str, period_id: str = None, expected_state: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.period_id = period_id
        self.expected_state = expected_state