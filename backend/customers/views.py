from datetime import timedelta

from django.conf import settings
from django.contrib.auth import login, logout
from django.core.mail import send_mail
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.db.models import Count
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import DestroyAPIView, ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Settings
from core.permissions import IsEmailVerified
from usage.models import BillingPeriod, RequestLog
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


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Send verification email
        signer = TimestampSigner()
        token = signer.sign(user.email)
        verification_url = (
            f"{request.build_absolute_uri('/api/customers/verify-email')}?token={token}"
        )

        send_mail(
            subject="Verify your email address",
            message=(
                f"Please click the following link to verify your email address:\n\n"
                f"{verification_url}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
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

        return Response(
            {
                "id": str(user.id),
                "email": user.email,
            }
        )


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        user = request.user
        return Response(
            {
                "id": str(user.id),
                "email": user.email,
                "emailVerified": user.is_email_verified,
                "createdAt": user.date_joined.isoformat(),
            }
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


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


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

    def post(self, request: Request) -> Response:
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ApiTokenListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]
    serializer_class = ApiTokenListSerializer

    def get_queryset(self):
        return ApiToken.objects.filter(user=self.request.user)


class ApiTokenCreateView(APIView):
    permission_classes = [IsAuthenticated, IsEmailVerified]

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

        # Get settings for cost calculation
        settings = Settings.get_settings()
        cost_per_request = settings.cost_per_request_cents

        # Calculate periods
        periods = []

        # Today
        today_logs = RequestLog.objects.filter(user=request.user, request_ts__gte=today).aggregate(
            count=Count("id")
        )
        periods.append(
            {
                "title": "Today",
                "count": today_logs["count"] or 0,
                "cost_cents": (today_logs["count"] or 0) * cost_per_request,
            }
        )

        # Yesterday
        yesterday_logs = RequestLog.objects.filter(
            user=request.user, request_ts__gte=yesterday, request_ts__lt=today
        ).aggregate(count=Count("id"))
        periods.append(
            {
                "title": "Yesterday",
                "count": yesterday_logs["count"] or 0,
                "cost_cents": (yesterday_logs["count"] or 0) * cost_per_request,
            }
        )

        # Last 7 days
        week_logs = RequestLog.objects.filter(
            user=request.user, request_ts__gte=week_ago
        ).aggregate(count=Count("id"))
        periods.append(
            {
                "title": "Last 7 Days",
                "count": week_logs["count"] or 0,
                "cost_cents": (week_logs["count"] or 0) * cost_per_request,
            }
        )

        # This month
        month_logs = RequestLog.objects.filter(
            user=request.user, request_ts__gte=month_start
        ).aggregate(count=Count("id"))
        periods.append(
            {
                "title": "This Month",
                "count": month_logs["count"] or 0,
                "cost_cents": (month_logs["count"] or 0) * cost_per_request,
            }
        )

        # Total
        total_logs = RequestLog.objects.filter(user=request.user).aggregate(count=Count("id"))
        total_count = total_logs["count"] or 0
        total_cost = total_count * cost_per_request

        return Response(
            {
                "total_requests": total_count,
                "total_cost_cents": total_cost,
                "by_period": periods,
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
