import logging
import time
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import login, logout
from django.core.mail import send_mail
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.middleware.csrf import get_token
from django.db.models import Count
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import DestroyAPIView
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Settings
from core.permissions import IsEmailVerified
from core.services import openai_client
from core.services.exceptions import OpenAIError
from usage.models import BillingPeriod, RequestLog, RequestImage
from usage.serializers import CurrentBillingPeriodSerializer
from usage.utils import get_or_create_current_billing_period

from .models import ApiToken, User
from .serializers import (
    ApiTokenListSerializer,
    ApiTokenSerializer,
    ChangePasswordSerializer,
    LoginSerializer,
    RegisterSerializer,
)
from config import settings
from .utils import (
    build_verification_url,
    send_verification_email_html,
    send_verification_email_plain,
)

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Build verification URL using the utility function
        verification_url = build_verification_url(request, user.email)

        # Generate email content using utility functions
        html_message = send_verification_email_html(verification_url)
        plain_message = send_verification_email_plain(verification_url)

        send_mail(
            subject="Verify Your Email Address",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        return Response(status=status.HTTP_202_ACCEPTED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        login(request, user)
        
        # Get CSRF token for the session
        csrf_token = get_token(request)

        return Response(
            {
                "id": str(user.id),
                "email": user.email,
                "csrfToken": csrf_token,  # Include CSRF token in response
            }
        )


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        user = request.user
        
        # Get CSRF token for the session
        csrf_token = get_token(request)
        
        return Response(
            {
                "id": str(user.id),
                "email": user.email,
                "isEmailVerified": user.is_email_verified,
                "dateJoined": user.date_joined.isoformat(),
                "csrfToken": csrf_token,  # Include CSRF token in response
            }
        )


class LogoutView(APIView):
    permission_classes: list[type[BasePermission]] = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        logout(request)
        resp: Response = Response(status=status.HTTP_204_NO_CONTENT)

        resp.delete_cookie("sessionid")
        resp.delete_cookie("csrftoken")

        # Remove the cookie on the client. Attributes must match.
        resp.delete_cookie(
            key=settings.SESSION_COOKIE_NAME,                       # "sessionid" by default
            path=getattr(settings, "SESSION_COOKIE_PATH", "/"),
            domain=getattr(settings, "SESSION_COOKIE_DOMAIN", None),
            samesite=getattr(settings, "SESSION_COOKIE_SAMESITE", None),
        )

        return resp


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        token = request.query_params.get("token")
        if not token:
            return Response(
                {"detail": "Token is required", "code": "token_required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verify the token
        signer = TimestampSigner()
        try:
            email = signer.unsign(token, max_age=86400)  # 24 hours
        except SignatureExpired:
            return Response(
                {"detail": "Token has expired", "code": "token_expired"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except BadSignature:
            return Response(
                {"detail": "Invalid token", "code": "invalid_token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update user
        try:
            user = User.objects.get(email=email)
            if user.is_email_verified:
                return Response(
                    {"detail": "Email already verified", "code": "email_already_verified"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.email_verified_at = timezone.now()
            user.save(update_fields=["email_verified_at"])
            return Response(status=status.HTTP_204_NO_CONTENT)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found", "code": "user_not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class ResendVerificationEmailView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        user = request.user

        # Check if user is already verified
        if user.is_email_verified:
            return Response(
                {"detail": "Email already verified", "code": "email_already_verified"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Build verification URL using the utility function
        verification_url = build_verification_url(request, user.email)

        # Generate email content using utility functions
        html_message = send_verification_email_html(verification_url)
        plain_message = send_verification_email_plain(verification_url)

        try:
            send_mail(
                subject="Verify Your Email Address",
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )
            return Response(
                {"detail": "Verification email sent successfully"},
                status=status.HTTP_200_OK
            )
        except Exception:
            return Response(
                {"detail": "Failed to send verification email", "code": "email_send_failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def post(self, request: Request) -> Response:
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ApiTokenView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get(self, request: Request) -> Response:
        tokens = ApiToken.objects.filter(user=request.user)
        serializer = ApiTokenListSerializer(tokens, many=True)
        return Response(serializer.data)

    def post(self, request: Request) -> Response:
        serializer = ApiTokenSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ApiTokenRevokeView(DestroyAPIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get_queryset(self):
        return ApiToken.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        instance.revoke()


class UsageRequestsView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get(self, request: Request) -> Response:
        # Get query parameters
        from_date = request.query_params.get("from")
        to_date = request.query_params.get("to")
        page = int(request.query_params.get("page", 1))
        page_size = 25

        # Build query
        queryset = RequestLog.objects.filter(user=request.user)

        if from_date:
            queryset = queryset.filter(request_ts__gte=from_date)
        if to_date:
            queryset = queryset.filter(request_ts__lte=to_date)

        # Paginate
        total = queryset.count()
        offset = (page - 1) * page_size
        logs = queryset[offset : offset + page_size]

        # Serialize
        data = []
        for log in logs:
            data.append(
                {
                    "id": str(log.id),
                    "request_ts": log.request_ts.isoformat(),
                    "service": log.service,
                    "status": log.status,
                    "duration_ms": log.duration_ms,
                    "request_bytes": log.request_bytes,
                    "response_bytes": log.response_bytes,
                    "request_id": str(log.request_id),
                    "token_prefix": log.token.token_prefix if log.token else None,
                }
            )

        return Response(
            {
                "results": data,
                "count": total,
                "next": page + 1 if offset + page_size < total else None,
                "previous": page - 1 if page > 1 else None,
            }
        )


class UsageSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get(self, request: Request) -> Response:
        now = timezone.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        month_start = today.replace(day=1)

        # Today
        today_count = RequestLog.objects.filter(
            user=request.user, request_ts__gte=today
        ).count()

        # Yesterday
        yesterday_count = RequestLog.objects.filter(
            user=request.user, request_ts__gte=yesterday, request_ts__lt=today
        ).count()

        # Last 7 days
        last7_days_count = RequestLog.objects.filter(
            user=request.user, request_ts__gte=week_ago
        ).count()

        # This month
        this_month_count = RequestLog.objects.filter(
            user=request.user, request_ts__gte=month_start
        ).count()

        # Get last request
        last_request = RequestLog.objects.filter(user=request.user).order_by("-request_ts").first()
        last_request_at = last_request.request_ts.isoformat() if last_request else None

        return Response(
            {
                "today": today_count,
                "yesterday": yesterday_count,
                "last7Days": last7_days_count,
                "thisMonth": this_month_count,
                "lastRequestAt": last_request_at,
            }
        )


class BillingPeriodsListView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get(self, request: Request) -> Response:
        """List all billing periods for the user."""
        periods = BillingPeriod.objects.filter(user=request.user)

        # Optional filters
        status = request.query_params.get("status")
        if status:
            periods = periods.filter(payment_status=status)

        data = []
        for period in periods:
            data.append(
                {
                    "id": str(period.id),
                    "period_label": period.period_label,
                    "period_start": period.period_start.isoformat(),
                    "period_end": period.period_end.isoformat(),
                    "total_requests": period.total_requests,
                    "total_cost_cents": period.total_cost_cents,
                    "is_current": period.is_current,
                    "payment_status": period.payment_status,
                    "paid_at": period.paid_at.isoformat() if period.paid_at else None,
                    "paid_amount_cents": period.paid_amount_cents,
                    "payment_reference": period.payment_reference,
                }
            )

        return Response({"results": data})


class CurrentBillingPeriodView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get(self, request: Request) -> Response:
        """Get current billing period summary."""
        period = get_or_create_current_billing_period(request.user)

        # Use the serializer for automatic camelCase conversion
        serializer = CurrentBillingPeriodSerializer(period)
        return Response(serializer.data)


class BillingPeriodDetailView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def get(self, request: Request, period_id) -> Response:
        """Get detailed requests for a billing period."""
        try:
            period = BillingPeriod.objects.get(id=period_id, user=request.user)
        except BillingPeriod.DoesNotExist:
            return Response(
                {"detail": "Billing period not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Get paginated requests
        page = int(request.query_params.get("page", 1))
        page_size = 25

        requests_qs = RequestLog.objects.filter(billing_period=period)
        total = requests_qs.count()
        offset = (page - 1) * page_size
        requests = requests_qs[offset : offset + page_size]

        request_data = []
        for log in requests:
            request_data.append(
                {
                    "id": str(log.id),
                    "request_ts": log.request_ts.isoformat(),
                    "service": log.service,
                    "status": log.status,
                    "duration_ms": log.duration_ms,
                    "request_bytes": log.request_bytes,
                    "response_bytes": log.response_bytes,
                    "request_id": str(log.request_id),
                }
            )

        return Response(
            {
                "period": {
                    "id": str(period.id),
                    "period_label": period.period_label,
                    "period_start": period.period_start.isoformat(),
                    "period_end": period.period_end.isoformat(),
                    "total_requests": period.total_requests,
                    "total_cost_cents": period.total_cost_cents,
                    "payment_status": period.payment_status,
                    "paid_at": period.paid_at.isoformat() if period.paid_at else None,
                    "payment_reference": period.payment_reference,
                },
                "requests": {
                    "results": request_data,
                    "count": total,
                    "next": page + 1 if offset + page_size < total else None,
                    "previous": page - 1 if page > 1 else None,
                },
            }
        )


class TestSolveView(APIView):
    """Session-authenticated endpoint for testing the image solver without API tokens."""
    permission_classes = [IsAuthenticated, IsEmailVerified]
    parser_classes = [MultiPartParser, FileUploadParser]

    def post(self, request: Request) -> Response:
        """Process an image using session authentication for testing."""
        # Start timer
        start_time = time.time()

        # Get authenticated user from session
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
            return Response(
                {"detail": "No image provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate image size (max 10MB for test requests)
        max_size_bytes = 10 * 1024 * 1024  # 10MB
        if len(image_bytes) > max_size_bytes:
            return Response(
                {"detail": "Image size exceeds 10MB limit"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get settings
        app_settings = Settings.get_settings()

        # Process image
        try:
            # Use the same OpenAI client as the main solve endpoint
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

            # Log request with special service name to distinguish test requests
            request_log = RequestLog.objects.create(
                user=user,
                token=None,  # No token for test requests
                billing_period=billing_period,
                service="customers.test_solve",  # Different service name
                duration_ms=duration_ms,
                request_bytes=len(image_bytes),
                response_bytes=len(str(result["result"])),
                status="success",
                request_id=getattr(request, "request_id", None),
                result=str(result["result"]),  # Store the result
            )

            # Save image if feature is enabled
            if settings.SAVE_REQUEST_IMAGES:
                # Check size limit
                max_saved_size = settings.MAX_SAVED_IMAGE_SIZE_MB * 1024 * 1024
                if len(image_bytes) <= max_saved_size:
                    try:
                        # Detect MIME type from request
                        mime_type = "image/jpeg"  # Default
                        if "file" in request.FILES:
                            content_type = request.FILES["file"].content_type
                            if content_type:
                                mime_type = content_type

                        RequestImage.create_from_bytes(
                            request_log=request_log,
                            image_bytes=image_bytes,
                            mime_type=mime_type
                        )
                    except Exception as e:
                        # Log error but don't fail the request
                        logger.error(
                            f"Failed to save image for test request {getattr(request, 'request_id', 'unknown')}: {e}"
                        )

            # Update billing period totals (test requests are also billed)
            billing_period.total_requests += 1
            billing_period.total_cost_cents += app_settings.cost_per_request_cents
            billing_period.save(update_fields=["total_requests", "total_cost_cents", "updated_at"])

            # Return response
            return Response(
                {
                    "request_id": getattr(request, "request_id", None),
                    "result": result["result"],
                    "model": result["model"],
                    "duration_ms": duration_ms,
                    "is_test": True,  # Indicate this was a test request
                }
            )

        except OpenAIError as e:
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Get current billing period
            billing_period = get_or_create_current_billing_period(user)

            # Log error
            request_log = RequestLog.objects.create(
                user=user,
                token=None,
                billing_period=billing_period,
                service="customers.test_solve",
                duration_ms=duration_ms,
                request_bytes=len(image_bytes),
                response_bytes=0,
                status="error",
                error_code=e.error_code.value,
                request_id=getattr(request, "request_id", None),
                result=None,
            )

            # Save image even for errors if feature is enabled
            if settings.SAVE_REQUEST_IMAGES:
                max_saved_size = settings.MAX_SAVED_IMAGE_SIZE_MB * 1024 * 1024
                if len(image_bytes) <= max_saved_size:
                    try:
                        mime_type = "image/jpeg"  # Default
                        if "file" in request.FILES:
                            content_type = request.FILES["file"].content_type
                            if content_type:
                                mime_type = content_type

                        RequestImage.create_from_bytes(
                            request_log=request_log,
                            image_bytes=image_bytes,
                            mime_type=mime_type
                        )
                    except Exception as save_error:
                        logger.error(
                            f"Failed to save image for failed test request {getattr(request, 'request_id', 'unknown')}: {save_error}"
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
