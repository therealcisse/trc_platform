from datetime import timedelta

from django.conf import settings
from django.contrib.auth import login, logout
from django.core.mail import send_mail
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.db.models import Count
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import DestroyAPIView
from rest_framework.permissions import AllowAny, BasePermission, IsAuthenticated
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
            f"{request.build_absolute_uri('/verify-email')}?token={token}"
        )

        # Send verification email with improved template
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    background-color: #ffffff;
                    border-radius: 8px;
                    padding: 30px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }}
                h1 {{
                    color: #2c3e50;
                    font-size: 24px;
                    margin-bottom: 20px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #3498db;
                    color: #ffffff;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: 600;
                    margin: 20px 0;
                }}
                .button:hover {{
                    background-color: #2980b9;
                }}
                .footer {{
                    margin-top: 30px;
                    font-size: 14px;
                    color: #7f8c8d;
                    border-top: 1px solid #ecf0f1;
                    padding-top: 20px;
                }}
                .link {{
                    color: #3498db;
                    word-break: break-all;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Welcome! Verify Your Email Address</h1>
                <p>Thank you for signing up! You're just one step away from completing your registration.</p>
                <p>Please confirm your email address by clicking the button below:</p>
                <a href="{verification_url}" class="button">Verify Email Address</a>
                <p>Or copy and paste this link in your browser:</p>
                <p><a href="{verification_url}" class="link">{verification_url}</a></p>
                <div class="footer">
                    <p>This verification link will expire in 24 hours.</p>
                    <p>If you didn't create an account, you can safely ignore this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        plain_message = (
            f"Welcome! Verify Your Email Address\n\n"
            f"Thank you for signing up! You're just one step away from completing your registration.\n\n"
            f"Please confirm your email address by clicking the following link:\n"
            f"{verification_url}\n\n"
            f"This verification link will expire in 24 hours.\n"
            f"If you didn't create an account, you can safely ignore this email."
        )

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
                "isEmailVerified": user.is_email_verified,
                "dateJoined": user.date_joined.isoformat(),
            }
        )


class LogoutView(APIView):
    permission_classes: list[type[BasePermission]] = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        logout(request)
        resp: Response = Response(status=status.HTTP_204_NO_CONTENT)
        resp.delete_cookie("sessionid")
        resp.delete_cookie("csrftoken")
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

        # Generate new verification token
        signer = TimestampSigner()
        token = signer.sign(user.email)
        verification_url = (
            f"{request.build_absolute_uri('/verify-email')}?token={token}"
        )

        # Send verification email with improved template
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    background-color: #ffffff;
                    border-radius: 8px;
                    padding: 30px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }}
                h1 {{
                    color: #2c3e50;
                    font-size: 24px;
                    margin-bottom: 20px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #3498db;
                    color: #ffffff;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: 600;
                    margin: 20px 0;
                }}
                .button:hover {{
                    background-color: #2980b9;
                }}
                .footer {{
                    margin-top: 30px;
                    font-size: 14px;
                    color: #7f8c8d;
                    border-top: 1px solid #ecf0f1;
                    padding-top: 20px;
                }}
                .link {{
                    color: #3498db;
                    word-break: break-all;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Verify Your Email Address</h1>
                <p>Thank you for signing up! Please verify your email address to complete your registration.</p>
                <p>Click the button below to verify your email:</p>
                <a href="{verification_url}" class="button">Verify Email</a>
                <p>Or copy and paste this link in your browser:</p>
                <p><a href="{verification_url}" class="link">{verification_url}</a></p>
                <div class="footer">
                    <p>This verification link will expire in 24 hours.</p>
                    <p>If you didn't create an account, you can safely ignore this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        plain_message = (
            f"Verify Your Email Address\n\n"
            f"Thank you for signing up! Please verify your email address to complete your registration.\n\n"
            f"Click the following link to verify your email:\n"
            f"{verification_url}\n\n"
            f"This verification link will expire in 24 hours.\n"
            f"If you didn't create an account, you can safely ignore this email."
        )

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
