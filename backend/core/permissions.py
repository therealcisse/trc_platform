from django.http import HttpRequest
from rest_framework import permissions


class IsTokenAuthenticated(permissions.BasePermission):
    """
    Custom permission to only allow access to users authenticated via API token.
    """

    def has_permission(self, request: HttpRequest, view) -> bool:
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:  # type: ignore
            return False

        # Check if authentication was via token (not session)
        return hasattr(request, "token") and request.token is not None  # type: ignore


class IsEmailVerified(permissions.BasePermission):
    """
    Custom permission to only allow access to users with verified email.
    """

    def has_permission(self, request: HttpRequest, view) -> bool:
        if not request.user or not request.user.is_authenticated:  # type: ignore
            return False

        return request.user.is_email_verified  # type: ignore
