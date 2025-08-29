import logging
import time
from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from usage.models import RequestImage, RequestLog
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


class SolveView(APIView):
    authentication_classes = [BearerTokenAuthentication]
    permission_classes = []  # Authentication handles permission
    parser_classes = [MultiPartParser, FileUploadParser]

    def post(self, request: Request) -> Response:
        # Start timer
        start_time = time.time()

        # Get authenticated user
        if not request.user or not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication credentials were not provided."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        user = request.user

        # Get image from request
        if "file" in request.FILES:
            # multipart/form-data
            image_file = request.FILES["file"]
            image_bytes = image_file.read()
        elif request.content_type == "application/octet-stream":
            # Raw binary upload
            image_bytes = request.body
        else:
            return Response({"detail": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)

        # Get settings
        app_settings = Settings.get_settings()

        # Process image
        try:
            # Use return_dict=True for backwards compatibility
            result = openai_client.solve_image(
                image_bytes,
                model=app_settings.openai_model,
                timeout=app_settings.openai_timeout_s,
                return_dict=True,
            )

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Get current billing period
            billing_period = get_or_create_current_billing_period(user)

            # Log request with billing period and store the result
            request_log = RequestLog.objects.create(
                user=user,
                token=getattr(request, "token", None),
                billing_period=billing_period,
                service="core.image_solve",
                duration_ms=duration_ms,
                request_bytes=len(image_bytes),
                response_bytes=len(str(result["result"])),
                status="success",
                request_id=request.request_id,
                result=str(result["result"]),  # Store the actual result as string
            )

            # Save image if feature is enabled
            if settings.SAVE_REQUEST_IMAGES:
                # Check size limit
                max_size_bytes = settings.MAX_SAVED_IMAGE_SIZE_MB * 1024 * 1024
                if len(image_bytes) <= max_size_bytes:
                    try:
                        # Detect MIME type from request
                        mime_type = "image/jpeg"  # Default
                        if "file" in request.FILES:
                            content_type = request.FILES["file"].content_type
                            if content_type:
                                mime_type = content_type

                        RequestImage.create_from_bytes(
                            request_log=request_log, image_bytes=image_bytes, mime_type=mime_type
                        )
                    except Exception as e:
                        # Log error but don't fail the request
                        logger.error(f"Failed to save image for request {request.request_id}: {e}")

            # Update billing period totals
            billing_period.total_requests += 1
            billing_period.total_cost_cents += app_settings.cost_per_request_cents
            billing_period.save(update_fields=["total_requests", "total_cost_cents", "updated_at"])

            # Return response
            return Response(
                {
                    "request_id": request.request_id,
                    "result": result["result"],
                    "model": result["model"],
                    "duration_ms": duration_ms,
                }
            )

        except OpenAIError as e:
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Get current billing period (even for errors to track all requests)
            billing_period = get_or_create_current_billing_period(user)

            # Log error with billing period (no result stored for errors)
            request_log = RequestLog.objects.create(
                user=user,
                token=getattr(request, "token", None),
                billing_period=billing_period,
                service="core.image_solve",
                duration_ms=duration_ms,
                request_bytes=len(image_bytes),
                response_bytes=0,
                status="error",
                error_code=e.error_code.value,
                request_id=request.request_id,
                result=None,  # No result for errors
            )

            # Save image even for errors if feature is enabled (for debugging)
            if settings.SAVE_REQUEST_IMAGES:
                max_size_bytes = settings.MAX_SAVED_IMAGE_SIZE_MB * 1024 * 1024
                if len(image_bytes) <= max_size_bytes:
                    try:
                        mime_type = "image/jpeg"  # Default
                        if "file" in request.FILES:
                            content_type = request.FILES["file"].content_type
                            if content_type:
                                mime_type = content_type

                        RequestImage.create_from_bytes(
                            request_log=request_log, image_bytes=image_bytes, mime_type=mime_type
                        )
                    except Exception as save_error:
                        logger.error(
                            f"Failed to save image for failed request {request.request_id}: {save_error}"
                        )

            # Update billing period totals (charge even for errors)
            billing_period.total_requests += 1
            billing_period.total_cost_cents += app_settings.cost_per_request_cents
            billing_period.save(update_fields=["total_requests", "total_cost_cents", "updated_at"])

            # Return error
            return Response(
                {"detail": str(e), "code": e.error_code.value},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@api_view(["GET"])
@permission_classes([])
def healthz(request: Request) -> Response:
    """Health check endpoint."""
    checks = {
        "database": False,
        "openai": False,
    }

    # Check database
    try:
        Settings.get_settings()
        checks["database"] = True
    except Exception:
        pass

    # Check OpenAI
    try:
        checks["openai"] = openai_client.ping()
    except Exception:
        pass

    # Determine overall health
    healthy = all(checks.values())

    return Response(
        {"status": "ok" if healthy else "degraded", "checks": checks},
        status=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
    )
