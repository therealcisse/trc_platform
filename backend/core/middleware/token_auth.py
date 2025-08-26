from collections.abc import Callable
from typing import TYPE_CHECKING

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest, HttpResponse

from customers.models import ApiToken

if TYPE_CHECKING:
    from customers.models import User
else:
    User = get_user_model()


class TokenAuthMiddleware:
    """Middleware to authenticate users via Bearer tokens."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        self.ph = PasswordHasher()

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Skip token auth if user is already authenticated via session
        if hasattr(request, "user") and request.user.is_authenticated:
            return self.get_response(request)

        # Try to authenticate via Bearer token
        token = self._extract_token(request)
        if token:
            user, api_token = self._authenticate_token(token)
            if user:
                request.user = user
                request.token = api_token  # type: ignore[attr-defined]
                # Update last used timestamp
                if api_token:
                    api_token.update_last_used()
            else:
                request.user = AnonymousUser()
                request.token = None  # type: ignore[attr-defined]

        return self.get_response(request)

    def _extract_token(self, request: HttpRequest) -> str | None:
        """Extract Bearer token from Authorization header."""
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
        return None

    def _authenticate_token(self, token: str) -> tuple[User | None, ApiToken | None]:
        """Authenticate a token and return the associated user and token object."""
        # Extract token prefix
        if not token.startswith("tok_"):
            return None, None

        token_prefix = token[:12]  # tok_ + 8 chars

        try:
            # Find token by prefix
            api_token = ApiToken.objects.select_related("user").get(token_prefix=token_prefix)

            # Check if token is revoked
            if api_token.is_revoked:
                return None, None

            # Check if user is active
            if not api_token.user.is_active:
                return None, None

            # Check if user's email is verified
            if not api_token.user.is_email_verified:
                return None, None

            # Verify token hash
            try:
                self.ph.verify(api_token.token_hash, token)
            except VerifyMismatchError:
                return None, None

            return api_token.user, api_token

        except ApiToken.DoesNotExist:
            return None, None
