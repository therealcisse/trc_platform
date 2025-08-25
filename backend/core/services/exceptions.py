"""
Exception classes for the OpenAI client module.

This module provides a comprehensive hierarchy of exceptions for better
error handling and debugging capabilities.
"""

from typing import Any, Optional

from .types import ErrorCode


class OpenAIError(Exception):
    """
    Base exception for all OpenAI client errors.

    This is the base class for all exceptions raised by the OpenAI client,
    providing a consistent interface for error handling.
    """

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.UNKNOWN,
        details: Optional[dict[str, Any]] = None,
        retry_after: Optional[int] = None,
    ) -> None:
        """
        Initialize the OpenAI error.

        Args:
            message: Human-readable error message
            error_code: Specific error code from ErrorCode enum
            details: Additional error details for debugging
            retry_after: Seconds to wait before retrying (for rate limits)
        """
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}
        self.retry_after = retry_after

    def __str__(self) -> str:
        """String representation of the error."""
        base_msg = f"[{self.error_code.value}] {super().__str__()}"
        if self.retry_after:
            base_msg += f" (retry after {self.retry_after}s)"
        return base_msg

    def __repr__(self) -> str:
        """Developer-friendly representation of the error."""
        return (
            f"{self.__class__.__name__}("
            f"message={super().__str__()!r}, "
            f"error_code={self.error_code!r}, "
            f"details={self.details!r}, "
            f"retry_after={self.retry_after!r})"
        )


class APIError(OpenAIError):
    """
    Exception for API-level errors from OpenAI.

    This includes errors like invalid requests, server errors, etc.
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Initialize API error with HTTP details.

        Args:
            message: Error message
            status_code: HTTP status code
            response_body: Raw response body for debugging
            details: Additional error details
        """
        super().__init__(message, ErrorCode.API_ERROR, details)
        self.status_code = status_code
        self.response_body = response_body
        if self.details:
            self.details["status_code"] = status_code
            self.details["response_body"] = response_body


class TimeoutError(OpenAIError):
    """Exception for request timeout errors."""

    def __init__(self, message: str, timeout_seconds: int) -> None:
        """
        Initialize timeout error.

        Args:
            message: Error message
            timeout_seconds: The timeout value that was exceeded
        """
        super().__init__(
            message,
            ErrorCode.TIMEOUT,
            {"timeout_seconds": timeout_seconds},
        )
        self.timeout_seconds = timeout_seconds


class NetworkError(OpenAIError):
    """Exception for network-related errors."""

    def __init__(
        self,
        message: str,
        original_exception: Optional[Exception] = None,
    ) -> None:
        """
        Initialize network error.

        Args:
            message: Error message
            original_exception: The underlying network exception
        """
        details = {}
        if original_exception:
            details["original_error"] = str(original_exception)
            details["original_error_type"] = type(original_exception).__name__

        super().__init__(message, ErrorCode.NETWORK_ERROR, details)
        self.original_exception = original_exception


class InvalidResponseError(OpenAIError):
    """Exception for invalid or malformed API responses."""

    def __init__(
        self,
        message: str,
        response_data: Optional[Any] = None,
    ) -> None:
        """
        Initialize invalid response error.

        Args:
            message: Error message
            response_data: The invalid response data for debugging
        """
        super().__init__(
            message,
            ErrorCode.INVALID_RESPONSE,
            {"response_data": str(response_data) if response_data else None},
        )
        self.response_data = response_data


class InvalidImageError(OpenAIError):
    """Exception for invalid image input."""

    def __init__(
        self,
        message: str,
        image_size: Optional[int] = None,
        image_format: Optional[str] = None,
    ) -> None:
        """
        Initialize invalid image error.

        Args:
            message: Error message
            image_size: Size of the invalid image in bytes
            image_format: Detected format of the invalid image
        """
        details = {}
        if image_size is not None:
            details["image_size_bytes"] = image_size
        if image_format:
            details["image_format"] = image_format

        super().__init__(message, ErrorCode.INVALID_IMAGE, details)
        self.image_size = image_size
        self.image_format = image_format


class RateLimitError(OpenAIError):
    """Exception for rate limit errors."""

    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        limit_type: Optional[str] = None,
    ) -> None:
        """
        Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
            limit_type: Type of limit hit (requests, tokens, etc.)
        """
        details = {}
        if limit_type:
            details["limit_type"] = limit_type

        super().__init__(
            message,
            ErrorCode.RATE_LIMIT,
            details,
            retry_after,
        )
        self.limit_type = limit_type


class AuthenticationError(OpenAIError):
    """Exception for authentication failures."""

    def __init__(self, message: str = "Invalid API key or authentication failed") -> None:
        """Initialize authentication error."""
        super().__init__(message, ErrorCode.AUTHENTICATION)


class InsufficientQuotaError(OpenAIError):
    """Exception for insufficient quota or credits."""

    def __init__(
        self,
        message: str = "Insufficient quota or credits",
        remaining_quota: Optional[float] = None,
    ) -> None:
        """
        Initialize insufficient quota error.

        Args:
            message: Error message
            remaining_quota: Remaining quota if known
        """
        details = {}
        if remaining_quota is not None:
            details["remaining_quota"] = remaining_quota

        super().__init__(message, ErrorCode.INSUFFICIENT_QUOTA, details)
        self.remaining_quota = remaining_quota


class ModelNotFoundError(OpenAIError):
    """Exception for model not found errors."""

    def __init__(self, model_name: str, available_models: Optional[list[str]] = None) -> None:
        """
        Initialize model not found error.

        Args:
            model_name: The requested model that was not found
            available_models: List of available models if known
        """
        message = f"Model '{model_name}' not found"
        details = {"requested_model": model_name}
        if available_models:
            details["available_models"] = available_models
            message += f". Available models: {', '.join(available_models)}"

        super().__init__(message, ErrorCode.MODEL_NOT_FOUND, details)
        self.model_name = model_name
        self.available_models = available_models
