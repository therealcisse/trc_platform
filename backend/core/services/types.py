"""
Type definitions for the OpenAI client module.

This module provides comprehensive type definitions to ensure type safety
and improve maintainability of the OpenAI client implementation.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Literal


class ErrorCode(str, Enum):
    """Enumeration of possible error codes for OpenAI operations."""

    API_ERROR = "openai_api_error"
    TIMEOUT = "openai_timeout"
    NETWORK_ERROR = "openai_network_error"
    INVALID_RESPONSE = "openai_invalid_response"
    INVALID_IMAGE = "invalid_image"
    RATE_LIMIT = "openai_rate_limit"
    AUTHENTICATION = "openai_authentication"
    INSUFFICIENT_QUOTA = "openai_insufficient_quota"
    MODEL_NOT_FOUND = "openai_model_not_found"
    UNKNOWN = "openai_unknown_error"


class ModelType(str, Enum):
    """Supported OpenAI model types."""

    GPT4_VISION = "gpt-4-vision-preview"
    GPT4_TURBO = "gpt-4-turbo"
    GPT4 = "gpt-4"
    GPT35_TURBO = "gpt-3.5-turbo"


@dataclass(frozen=True)
class UsageInfo:
    """Token usage information for an API call."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    def __post_init__(self) -> None:
        """Validate usage data."""
        if self.prompt_tokens < 0:
            raise ValueError("prompt_tokens must be non-negative")
        if self.completion_tokens < 0:
            raise ValueError("completion_tokens must be non-negative")
        if self.total_tokens != self.prompt_tokens + self.completion_tokens:
            raise ValueError("total_tokens must equal prompt_tokens + completion_tokens")


@dataclass(frozen=True)
class SolveImageResult:
    """
    Result from the solve_image operation.

    This class encapsulates the response from the OpenAI API when processing
    a math problem image, providing type-safe access to all response fields.
    """

    result: str
    model: str
    usage: UsageInfo
    request_id: str | None = None
    processing_time_ms: int | None = None

    def is_error_response(self) -> bool:
        """Check if the result indicates an error in processing."""
        return self.result.startswith("ERROR:")

    def get_numeric_result(self) -> float | list[float] | None:
        """
        Attempt to parse the result as a numeric value or list of values.

        Returns:
            A float, list of floats, or None if parsing fails.
        """
        if self.is_error_response():
            return None

        try:
            # Try to parse as a single number
            return float(self.result.replace(",", "").strip())
        except ValueError:
            # Try to parse as comma-separated numbers
            try:
                parts = self.result.split(",")
                return [float(part.strip()) for part in parts]
            except ValueError:
                return None

    def to_dict(self) -> dict[str, str | dict[str, int] | int | None]:
        """
        Convert the result to a dictionary for backwards compatibility.

        Returns:
            Dictionary representation of the result.
        """
        base_dict: dict[str, str | dict[str, int] | int | None] = {
            "result": self.result,
            "model": self.model,
            "usage": {
                "prompt_tokens": self.usage.prompt_tokens,
                "completion_tokens": self.usage.completion_tokens,
                "total_tokens": self.usage.total_tokens,
            },
        }

        if self.request_id:
            base_dict["request_id"] = self.request_id

        if self.processing_time_ms is not None:
            base_dict["processing_time_ms"] = self.processing_time_ms

        return base_dict


@dataclass
class OpenAIConfig:
    """Configuration for OpenAI client."""

    api_key: str
    model: str = ModelType.GPT4_VISION.value
    timeout_s: int = 30
    base_url: str = "https://api.openai.com/v1"
    max_retries: int = 3
    retry_delay_s: float = 1.0
    temperature: float = 0.0  # Deterministic for math problems
    max_tokens: int = 100  # Math answers are typically short
    image_detail: Literal["low", "high", "auto"] = "high"  # High detail for better OCR

    def __post_init__(self) -> None:
        """Validate configuration."""
        if not self.api_key:
            raise ValueError("API key is required")
        if self.timeout_s <= 0:
            raise ValueError("Timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("Max retries must be non-negative")
        if not (0.0 <= self.temperature <= 2.0):
            raise ValueError("Temperature must be between 0.0 and 2.0")
        if self.max_tokens <= 0:
            raise ValueError("Max tokens must be positive")


@dataclass
class ImageValidationResult:
    """Result of image validation."""

    is_valid: bool
    error_message: str | None = None
    image_format: str | None = None
    image_size_bytes: int | None = None
    dimensions: tuple[int, int] | None = None  # (width, height)


# Type aliases for clarity and consistency
ImageBytes = bytes
TimeoutSeconds = int
ResponseDict = dict[str, str | dict[str, int] | int | None]
