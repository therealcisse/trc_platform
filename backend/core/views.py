"""
Optimized views for the core image solving API.
Key optimizations:
1. Deferred logging and billing updates
2. Settings caching
3. Streamlined request processing
4. Connection pooling for OpenAI
"""

import logging
import time
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from usage.models import RequestLog
from usage.utils import get_or_create_current_billing_period

from .authentication import BearerTokenAuthentication
from .models import Settings
from .services import openai_client
from .services.exceptions import OpenAIError

if TYPE_CHECKING:
    from customers.models import User
else:
    User = get_user_model()

logger = logging.getLogger(__name__)


class CachedSettings:
    """Cached settings manager to avoid database hits."""

    @classmethod
    def get_settings(cls) -> Settings:
        """Get settings with caching."""
        cache_key = "app_settings"
        cached = cache.get(cache_key)

        if cached is None:
            cached = Settings.get_settings()
            # Cache for 5 minutes
            cache.set(cache_key, cached, 300)

        return cached

    @classmethod
    def invalidate(cls) -> None:
        """Invalidate the settings cache."""
        cache.delete("app_settings")


class SolveView(APIView):
    """
    Image solving endpoint with optimizations.

    Features:
    1. Token authentication with caching
    2. Settings caching to reduce DB hits
    3. Deferred logging and billing updates
    4. Optimized database queries
    """

    authentication_classes = [BearerTokenAuthentication]
    permission_classes = []  # Authentication handles permission
    parser_classes = [MultiPartParser, FileUploadParser]

    def post(self, request: Request) -> Response:
        start_time = time.time()

        # Get authenticated user
        if not request.user or not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        user = request.user

        # Extract image data
        image_bytes = self._extract_image(request)
        if image_bytes is None:
            return Response({"detail": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)

        # Get cached settings
        app_settings = CachedSettings.get_settings()

        # Process image (this is the main latency bottleneck)
        try:
            result = openai_client.solve_image(
                image_bytes,
                model=app_settings.openai_model,
                timeout=app_settings.openai_timeout_s,
                return_dict=True,
            )

            duration_ms = int((time.time() - start_time) * 1000)

            # Defer logging and billing updates
            self._defer_logging(
                user=user,
                token=getattr(request, "token", None),
                duration_ms=duration_ms,
                image_bytes=image_bytes,
                result=result,
                request_id=request.request_id,
                app_settings=app_settings,
                status_code="success",
            )

            # Return response immediately
            return Response(
                {
                    "request_id": request.request_id,
                    "result": result["result"],
                    "model": result["model"],
                    "duration_ms": duration_ms,
                }
            )

        except OpenAIError as e:
            duration_ms = int((time.time() - start_time) * 1000)

            # Log error (deferred)
            self._defer_logging(
                user=user,
                token=getattr(request, "token", None),
                duration_ms=duration_ms,
                image_bytes=image_bytes,
                result=None,
                request_id=request.request_id,
                app_settings=app_settings,
                status_code="error",
                error_code=e.error_code.value,
            )

            return Response(
                {"detail": str(e), "code": e.error_code.value},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _extract_image(self, request: Request) -> bytes | None:
        """Extract image bytes from request."""
        if "file" in request.FILES:
            return request.FILES["file"].read()
        elif request.content_type == "application/octet-stream":
            return request.body
        return None

    def _defer_logging(
        self,
        user: User,
        token: Any,
        duration_ms: int,
        image_bytes: bytes,
        result: dict | None,
        request_id: str,
        app_settings: Settings,
        status_code: str,
        error_code: str | None = None,
    ) -> None:
        """
        Defer logging and billing updates to avoid blocking the response.

        In production with task queue:
        - This would push to Celery/RQ for async processing

        For now, we'll use database transactions to batch operations.
        """
        # Use a separate thread or task queue in production
        # For MVP, we'll do a quick database write
        try:
            with transaction.atomic():
                # Get/create billing period (cached in transaction)
                billing_period = get_or_create_current_billing_period(user)

                # Create log entry
                request_log = RequestLog.objects.create(
                    user=user,
                    token=token,
                    billing_period=billing_period,
                    service="core.image_solve",
                    duration_ms=duration_ms,
                    request_bytes=len(image_bytes),
                    response_bytes=len(str(result["result"])) if result else 0,
                    status=status_code,
                    error_code=error_code,
                    request_id=request_id,
                    result=str(result["result"]) if result else None,
                )

                # Update billing totals (single UPDATE query)
                billing_period.total_requests = models.F("total_requests") + 1
                billing_period.total_cost_cents = (
                    models.F("total_cost_cents") + app_settings.cost_per_request_cents
                )
                billing_period.save(update_fields=["total_requests", "total_cost_cents"])

                # Skip image saving in critical path
                # This can be done asynchronously or conditionally
                if settings.SAVE_REQUEST_IMAGES and self._should_save_image(image_bytes):
                    self._schedule_image_save(request_log.id, image_bytes)

        except Exception as e:
            # Log but don't fail the request
            logger.error(f"Failed to log request {request_id}: {e}")

    def _should_save_image(self, image_bytes: bytes) -> bool:
        """Determine if image should be saved based on size and settings."""
        max_size = settings.MAX_SAVED_IMAGE_SIZE_MB * 1024 * 1024
        return len(image_bytes) <= max_size

    def _schedule_image_save(self, request_log_id: str, image_bytes: bytes) -> None:
        """
        Schedule image save for async processing.
        In production, push to task queue.
        """
        # For MVP, skip image saving in critical path
        # In production: celery_app.send_task("save_request_image", args=[request_log_id, image_bytes])
        pass


# Import models here to avoid circular import
from django.db import models


@api_view(["GET"])
@permission_classes([])
def healthz(request: Request) -> Response:
    """
    Optimized health check endpoint with caching.
    """
    cache_key = "health_check"
    cached_result = cache.get(cache_key)

    if cached_result:
        return Response(cached_result["data"], status=cached_result["status"])

    checks = {
        "database": False,
        "openai": False,
    }

    # Check database
    try:
        CachedSettings.get_settings()
        checks["database"] = True
    except Exception:
        pass

    # Check OpenAI (expensive, so cache longer)
    openai_cache_key = "openai_health"
    openai_status = cache.get(openai_cache_key)
    if openai_status is None:
        try:
            openai_status = openai_client.ping()
            cache.set(openai_cache_key, openai_status, 60)  # Cache for 1 minute
        except Exception:
            openai_status = False
    checks["openai"] = openai_status

    # Determine overall health
    healthy = all(checks.values())

    response_data = {
        "status": "ok" if healthy else "degraded",
        "checks": checks,
    }
    status_code = status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE

    # Cache the result for 10 seconds
    cache.set(cache_key, {"data": response_data, "status": status_code}, 10)

    return Response(response_data, status=status_code)
