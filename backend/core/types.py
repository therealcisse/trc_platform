"""Type utilities for handling Django authentication types."""
from typing import TypeGuard, Union, cast

from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest


from customers.models import User


# Type alias for the union of User and AnonymousUser
AuthUserType = Union[User, AnonymousUser]


class AuthenticatedRequest(HttpRequest):
    """Request type with authenticated user."""

    user: User


def is_authenticated_user(user: AuthUserType) -> TypeGuard[User]:
    """Type guard to check if a user is authenticated.

    This helps mypy understand that after this check, the user is a real User,
    not an AnonymousUser.

    Args:
        user: The user object from request.user

    Returns:
        True if the user is authenticated (not AnonymousUser)
    """
    return user.is_authenticated


def get_authenticated_user(request: HttpRequest) -> User | None:
    """Get an authenticated user from a request, or None.

    This helper function properly handles the type checking for request.user,
    returning None for AnonymousUser instead of the AnonymousUser object itself.

    Args:
        request: The HTTP request

    Returns:
        The authenticated User object, or None if not authenticated
    """
    if hasattr(request, "user") and is_authenticated_user(request.user):
        return request.user
    return None


def require_authenticated_user(request: HttpRequest) -> User:
    """Get an authenticated user from a request, raising an error if not authenticated.

    This should only be used in views that are protected by IsAuthenticated permission.

    Args:
        request: The HTTP request

    Returns:
        The authenticated User object

    Raises:
        ValueError: If the user is not authenticated
    """
    user = get_authenticated_user(request)
    if user is None:
        raise ValueError("User is not authenticated. This function should only be used in protected views.")
    return user
