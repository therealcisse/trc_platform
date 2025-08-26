import base64
import json
import logging
import random
import time
from abc import ABC, abstractmethod
from typing import Any, Literal, overload

import requests
from django.conf import settings

from .exceptions import (
    APIError,
    AuthenticationError,
    InsufficientQuotaError,
    InvalidImageError,
    InvalidResponseError,
    ModelNotFoundError,
    NetworkError,
    RateLimitError,
    TimeoutError,
)
from .types import (
    ImageBytes,
    ImageValidationResult,
    ModelType,
    ResponseDict,
    SolveImageResult,
    TimeoutSeconds,
    UsageInfo,
)

logger = logging.getLogger(__name__)


# Math problem solving prompt
MATH_SOLVER_PROMPT = """You are a mathematical problem solver. Your task is to:
1. Identify the mathematical problem or expression in the image
2. Solve it step by step
3. Return ONLY the final numerical answer

Rules:
- If the image contains a math problem, return only the numerical answer
- For expressions like "2+2", return "4"
- For equations like "x=5+3", return "8"
- If there are multiple problems, solve all and return answers separated by commas
- If you cannot identify a math problem, return "ERROR: No math problem found"
- Do not include units, explanations, or any other text - just the number(s)

Examples:
- Image shows "3 + 5" → Return: "8"
- Image shows "12 × 4" → Return: "48"
- Image shows "100 ÷ 5" → Return: "20"
- Image shows "7 - 3" → Return: "4"
- Image shows "2³" → Return: "8"
- Image shows "√16" → Return: "4"
- Image shows "What is 15% of 200?" → Return: "30"
- Image shows multiple: "2+2" and "3×3" → Return: "4, 9"
"""


class BaseOpenAIClient(ABC):
    """Abstract base class for OpenAI client implementations."""

    def __init__(self) -> None:
        self.model: str = settings.OPENAI_MODEL
        self.timeout: int = settings.OPENAI_TIMEOUT_S
        self._validate_configuration()

    def _validate_configuration(self) -> None:
        """Validate client configuration."""
        if self.timeout <= 0:
            raise ValueError(f"Invalid timeout value: {self.timeout}")
        if not self.model:
            raise ValueError("Model name is required")

    @abstractmethod
    def solve_image(
        self,
        image_bytes: ImageBytes,
        model: str | None = None,
        timeout: TimeoutSeconds | None = None,
    ) -> SolveImageResult:
        """Process an image containing a math problem."""
        pass

    @abstractmethod
    def ping(self) -> bool:
        """Check if the service is available."""
        pass

    @staticmethod
    def validate_image(image_bytes: ImageBytes) -> ImageValidationResult:
        """
        Validate image input before processing.

        Args:
            image_bytes: Image data to validate

        Returns:
            ImageValidationResult with validation details
        """
        if not image_bytes:
            return ImageValidationResult(
                is_valid=False,
                error_message="Empty image data",
            )

        size_bytes = len(image_bytes)
        max_size = 20 * 1024 * 1024  # 20MB limit for OpenAI

        if size_bytes > max_size:
            return ImageValidationResult(
                is_valid=False,
                error_message=f"Image too large: {size_bytes} bytes (max {max_size} bytes)",
                image_size_bytes=size_bytes,
            )

        # Basic image format detection
        image_format = None
        if image_bytes.startswith(b"\xff\xd8\xff"):
            image_format = "jpeg"
        elif image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            image_format = "png"
        elif image_bytes.startswith(b"GIF87a") or image_bytes.startswith(b"GIF89a"):
            image_format = "gif"
        elif image_bytes.startswith(b"RIFF") and b"WEBP" in image_bytes[:12]:
            image_format = "webp"

        return ImageValidationResult(
            is_valid=True,
            image_format=image_format,
            image_size_bytes=size_bytes,
        )


class MockOpenAIClient(BaseOpenAIClient):
    """Mock implementation for testing without OpenAI API."""

    def __init__(self) -> None:
        super().__init__()
        # Sample math problems and answers for mock responses
        self.mock_problems: list[tuple[str, str]] = [
            ("2 + 2", "4"),
            ("10 - 3", "7"),
            ("5 × 6", "30"),
            ("100 ÷ 4", "25"),
            ("3² + 4²", "25"),
            ("√144", "12"),
            ("15% of 200", "30"),
            ("7 × 8", "56"),
            ("123 + 456", "579"),
            ("1000 - 337", "663"),
        ]
        self.call_count: int = 0
        self.last_request_time: float | None = None

    def solve_image(
        self,
        image_bytes: ImageBytes,
        model: str | None = None,
        timeout: TimeoutSeconds | None = None,
    ) -> SolveImageResult:
        """Return a mock math solution response."""
        self.call_count += 1
        self.last_request_time = time.time()

        # Validate image
        validation = self.validate_image(image_bytes)
        if not validation.is_valid:
            raise InvalidImageError(
                validation.error_message or "Invalid image",
                image_size=validation.image_size_bytes,
                image_format=validation.image_format,
            )

        # Simulate processing delay
        time.sleep(random.uniform(0.1, 0.3))

        # Randomly select a mock problem for demonstration
        problem, answer = random.choice(self.mock_problems)

        # Simulate some variation based on image size
        image_size = len(image_bytes)
        if image_size < 1000:
            # Small image - might be invalid
            usage = UsageInfo(
                prompt_tokens=50,
                completion_tokens=10,
                total_tokens=60,
            )
            return SolveImageResult(
                result="ERROR: No math problem found",
                model=model or self.model,
                usage=usage,
                request_id=f"mock-{self.call_count}",
                processing_time_ms=int(random.uniform(100, 500)),
            )

        # Calculate realistic token usage
        prompt_tokens = 100 + (image_size // 1000)
        completion_tokens = 5
        usage = UsageInfo(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )

        return SolveImageResult(
            result=answer,
            model=model or self.model,
            usage=usage,
            request_id=f"mock-{self.call_count}",
            processing_time_ms=int(random.uniform(200, 800)),
        )

    def ping(self) -> bool:
        """Mock service is always available."""
        return True


class ProductionOpenAIClient(BaseOpenAIClient):
    """Production implementation using actual OpenAI API."""

    def __init__(self) -> None:
        super().__init__()
        self.api_key: str = settings.OPENAI_API_KEY
        self.base_url: str = "https://api.openai.com/v1"
        self.max_retries: int = getattr(settings, "OPENAI_MAX_RETRIES", 3)
        self.retry_delay: float = getattr(settings, "OPENAI_RETRY_DELAY", 1.0)

        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY is required for production mode. "
                "Set USE_MOCK_OPENAI=true to use mock mode instead."
            )

    def solve_image(
        self,
        image_bytes: ImageBytes,
        model: str | None = None,
        timeout: TimeoutSeconds | None = None,
    ) -> SolveImageResult:
        """
        Process an image containing a math problem using OpenAI Vision API.

        Args:
            image_bytes: The image data as bytes
            model: Optional model override (defaults to gpt-4-vision-preview)
            timeout: Optional timeout override

        Returns:
            SolveImageResult containing the numerical answer and metadata

        Raises:
            InvalidImageError: If the image is invalid
            TimeoutError: If the request times out
            NetworkError: If a network error occurs
            APIError: If the API returns an error
            AuthenticationError: If authentication fails
            RateLimitError: If rate limits are exceeded
            InvalidResponseError: If the response is malformed
        """
        start_time = time.time()
        model = model or ModelType.GPT4_VISION.value
        timeout = timeout or self.timeout

        # Validate image before processing
        validation = self.validate_image(image_bytes)
        if not validation.is_valid:
            raise InvalidImageError(
                validation.error_message or "Invalid image",
                image_size=validation.image_size_bytes,
                image_format=validation.image_format,
            )

        # Retry logic with exponential backoff
        last_exception: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                return self._make_api_call(
                    image_bytes=image_bytes,
                    model=model,
                    timeout=timeout,
                    start_time=start_time,
                )
            except (RateLimitError, APIError) as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    retry_delay = self.retry_delay * (2**attempt)
                    if isinstance(e, RateLimitError) and e.retry_after:
                        retry_delay = e.retry_after
                    logger.warning(
                        f"Retrying after {retry_delay}s due to {e.__class__.__name__}: {e}"
                    )
                    time.sleep(retry_delay)
                else:
                    raise
            except (TimeoutError, NetworkError, InvalidResponseError):
                # Don't retry these errors
                raise

        # This should not be reached, but handle it just in case
        if last_exception:
            raise last_exception
        raise RuntimeError("Unexpected error in retry logic")

    def _make_api_call(
        self,
        image_bytes: ImageBytes,
        model: str,
        timeout: TimeoutSeconds,
        start_time: float,
    ) -> SolveImageResult:
        """Make the actual API call to OpenAI."""
        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_bytes).decode("utf-8")

            # Prepare the request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": MATH_SOLVER_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Solve the math problem in this image and "
                                    "return only the numerical answer."
                                ),
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}",
                                    "detail": "high",  # Use high detail for better OCR
                                },
                            },
                        ],
                    },
                ],
                # "max_tokens": 100,  # Math answers are typically short
                # "temperature": 0,  # Use deterministic output for math
                "temperature": 1,  # Use deterministic output for math
            }

            # Make the API call
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=timeout,
            )

            # Handle different status codes
            self._handle_response_status(response)

            # Parse the response
            result = response.json()
            return self._parse_api_response(result, model, start_time)

        except requests.Timeout as e:
            raise TimeoutError(
                f"OpenAI API timeout after {timeout} seconds",
                timeout_seconds=timeout,
            ) from e
        except requests.RequestException as e:
            raise NetworkError(
                f"Network error calling OpenAI API: {str(e)}",
                original_exception=e,
            ) from e

    def _handle_response_status(self, response: requests.Response) -> None:
        """Handle different HTTP status codes from the API."""
        if response.status_code == 200:
            return

        # Try to extract error details from response
        error_data: dict[str, Any] = {}
        try:
            error_data = response.json() if response.content else {}
        except json.JSONDecodeError:
            pass

        error_message = error_data.get("error", {}).get("message", "Unknown error")
        error_type = error_data.get("error", {}).get("type", "")

        if response.status_code == 401:
            raise AuthenticationError(f"Authentication failed: {error_message}")
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            retry_after_int = int(retry_after) if retry_after else None
            raise RateLimitError(
                f"Rate limit exceeded: {error_message}",
                retry_after=retry_after_int,
                limit_type=error_type,
            )
        elif response.status_code == 404:
            if "model" in error_message.lower():
                raise ModelNotFoundError(
                    model_name=error_data.get("error", {}).get("param", "unknown"),
                )
            raise APIError(
                f"Resource not found: {error_message}",
                status_code=response.status_code,
                response_body=response.text,
            )
        elif response.status_code == 402:
            raise InsufficientQuotaError(f"Insufficient quota: {error_message}")
        elif response.status_code >= 500:
            raise APIError(
                f"OpenAI server error: {error_message}",
                status_code=response.status_code,
                response_body=response.text,
            )
        else:
            raise APIError(
                f"OpenAI API error: {error_message}",
                status_code=response.status_code,
                response_body=response.text,
            )

    def _parse_api_response(
        self,
        response_data: dict[str, Any],
        model: str,
        start_time: float,
    ) -> SolveImageResult:
        """Parse the API response into a SolveImageResult."""
        try:
            # Extract the answer
            choices = response_data.get("choices", [])
            if not choices:
                raise InvalidResponseError(
                    "No choices in API response",
                    response_data=response_data,
                )

            answer = choices[0].get("message", {}).get("content", "").strip()
            if not answer:
                raise InvalidResponseError(
                    "Empty answer in API response",
                    response_data=response_data,
                )

            # Extract usage information
            usage_data = response_data.get("usage", {})
            usage = UsageInfo(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
            )

            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)

            return SolveImageResult(
                result=answer,
                model=model,
                usage=usage,
                request_id=response_data.get("id"),
                processing_time_ms=processing_time_ms,
            )

        except (KeyError, TypeError, ValueError) as e:
            raise InvalidResponseError(
                f"Failed to parse API response: {str(e)}",
                response_data=response_data,
            ) from e

    def ping(self) -> bool:
        """
        Check if the OpenAI API is reachable.

        Returns:
            True if the API is reachable, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=5,
            )
            return response.status_code == 200
        except Exception:
            return False


class OpenAIClient:
    """Facade class that delegates to mock or production implementation."""

    def __init__(self) -> None:
        # Choose implementation based on settings
        if settings.USE_MOCK_OPENAI:
            self._impl: BaseOpenAIClient = MockOpenAIClient()
        else:
            self._impl = ProductionOpenAIClient()

    @overload
    def solve_image(
        self,
        image_bytes: ImageBytes,
        model: str | None = None,
        timeout: TimeoutSeconds | None = None,
        *,
        return_dict: Literal[True],
    ) -> ResponseDict: ...

    @overload
    def solve_image(
        self,
        image_bytes: ImageBytes,
        model: str | None = None,
        timeout: TimeoutSeconds | None = None,
        *,
        return_dict: Literal[False] = False,
    ) -> SolveImageResult: ...

    def solve_image(
        self,
        image_bytes: ImageBytes,
        model: str | None = None,
        timeout: TimeoutSeconds | None = None,
        return_dict: bool = False,
    ) -> SolveImageResult | ResponseDict:
        """
        Solve a math problem from an image.

        Args:
            image_bytes: The image data as bytes
            model: Optional model override
            timeout: Optional timeout override
            return_dict: If True, return a dict for backwards compatibility

        Returns:
            SolveImageResult or dict depending on return_dict parameter
        """
        result = self._impl.solve_image(image_bytes, model, timeout)
        if return_dict:
            return result.to_dict()
        return result

    def ping(self) -> bool:
        """Delegate to the appropriate implementation."""
        return self._impl.ping()


# Singleton instance
openai_client = OpenAIClient()
