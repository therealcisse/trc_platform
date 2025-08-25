"""
Debug view to help diagnose authentication issues.
This should be removed in production.
"""

from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

User = get_user_model()


class DebugAuthView(APIView):
    """
    Debug view to show detailed authentication information.
    WARNING: This exposes sensitive information and should only be used for debugging.
    """

    permission_classes = [AllowAny]  # Allow any to see auth state

    def get(self, request: Request) -> Response:
        """Get detailed authentication state information."""

        debug_info = {
            "authentication": {
                "is_authenticated": (
                    request.user.is_authenticated if hasattr(request, "user") else False
                ),
                "user_id": (
                    str(request.user.id)
                    if hasattr(request, "user") and request.user.is_authenticated
                    else None
                ),
                "user_email": (
                    request.user.email
                    if hasattr(request, "user") and request.user.is_authenticated
                    else None
                ),
                "is_staff": (
                    request.user.is_staff
                    if hasattr(request, "user") and request.user.is_authenticated
                    else False
                ),
                "is_superuser": (
                    request.user.is_superuser
                    if hasattr(request, "user") and request.user.is_authenticated
                    else False
                ),
            },
            "session": {},
            "headers": {},
            "token": None,
            "request_meta": {},
        }

        # Session information
        if hasattr(request, "session"):
            debug_info["session"] = {
                "session_key": request.session.session_key if request.session else None,
                "has_session": bool(request.session),
                "_auth_user_id": request.session.get("_auth_user_id") if request.session else None,
                "_auth_user_backend": (
                    request.session.get("_auth_user_backend") if request.session else None
                ),
            }

            # Get actual user from session ID
            if request.session and "_auth_user_id" in request.session:
                try:
                    session_user = User.objects.get(pk=request.session["_auth_user_id"])
                    debug_info["session"]["session_user_email"] = session_user.email
                    debug_info["session"]["session_user_is_staff"] = session_user.is_staff
                except User.DoesNotExist:
                    debug_info["session"]["session_user_error"] = "User from session not found"

        # Headers
        debug_info["headers"] = {
            "Authorization": request.META.get("HTTP_AUTHORIZATION", "Not present"),
            "Cookie": "Present" if request.META.get("HTTP_COOKIE") else "Not present",
            "User-Agent": request.META.get("HTTP_USER_AGENT", "Not present"),
        }

        # Token information (if using token auth)
        if hasattr(request, "token") and request.token:
            debug_info["token"] = {
                "token_id": str(request.token.id),
                "token_name": request.token.name,
                "token_prefix": request.token.token_prefix,
                "token_user_email": request.token.user.email,
            }

        # Request META info
        debug_info["request_meta"] = {
            "REMOTE_ADDR": request.META.get("REMOTE_ADDR"),
            "REQUEST_METHOD": request.META.get("REQUEST_METHOD"),
            "PATH_INFO": request.META.get("PATH_INFO"),
        }

        # Authentication classes used
        if hasattr(request, "successful_authenticator"):
            debug_info["authenticator"] = str(request.successful_authenticator)

        return Response(debug_info)
