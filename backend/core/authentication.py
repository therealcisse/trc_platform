"""
Custom authentication class for Bearer token authentication in DRF.
"""


from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from django.contrib.auth import get_user_model
from rest_framework import authentication
from rest_framework.request import Request

from customers.models import ApiToken
from customers.models import User as UserModel

User = get_user_model()


class BearerTokenAuthentication(authentication.BaseAuthentication):
    """
    Custom authentication class for Bearer tokens.
    Does not enforce CSRF checks like SessionAuthentication.
    """

    def authenticate(self, request: Request) -> tuple[UserModel, ApiToken] | None:
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
        # Extract token from Authorization header
        auth_header = authentication.get_authorization_header(request).decode("utf-8")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header[7:]  # Remove 'Bearer ' prefix

        # Validate token format
        if not token.startswith("tok_"):
            return None

        token_prefix = token[:12]  # tok_ + 8 chars

        try:
            # Find token by prefix
            api_token = ApiToken.objects.select_related("user").get(token_prefix=token_prefix)

            # Check if token is revoked
            if api_token.is_revoked:
                return None

            # Check if user is active
            if not api_token.user.is_active:
                return None

            # Check if user's email is verified
            if not api_token.user.is_email_verified:
                return None

            # Verify token hash
            ph = PasswordHasher()
            try:
                ph.verify(api_token.token_hash, token)
            except VerifyMismatchError:
                return None

            # Update last used timestamp
            api_token.update_last_used()

            # Store token in request for later use
            request.token = api_token

            return (api_token.user, api_token)

        except ApiToken.DoesNotExist:
            return None

    def authenticate_header(self, request: Request) -> str:
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response.
        """
        return 'Bearer realm="api"'
