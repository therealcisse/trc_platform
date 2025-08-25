from typing import Any

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView

from .types import get_authenticated_user


class IsTokenAuthenticated(permissions.BasePermission):
    """
    Custom permission to only allow access to users authenticated via API token.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        # Check if user is authenticated
        user = get_authenticated_user(request)
        if user is None:
            return False

        # Check if authentication was via token (not session)
        return hasattr(request, "token") and getattr(request, "token", None) is not None


class IsEmailVerified(permissions.BasePermission):
    """
    Custom permission to only allow access to users with verified email.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = get_authenticated_user(request)
        if user is None:
            return False

        return user.is_email_verified
