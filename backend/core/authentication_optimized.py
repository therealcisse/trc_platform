"""
Optimized authentication class for Bearer token authentication with caching.
"""

import hashlib
import time
from collections import OrderedDict
from threading import Lock

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import authentication
from rest_framework.request import Request

from customers.models import ApiToken
from customers.models import User as UserModel

User = get_user_model()


class TokenCache:
    """Thread-safe LRU cache for token validation results."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300) -> None:
        self.cache: OrderedDict[str, tuple[UserModel | None, ApiToken | None, float]] = (
            OrderedDict()
        )
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.lock = Lock()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> tuple[UserModel | None, ApiToken | None, bool]:
        """Get cached token validation result."""
        with self.lock:
            if key in self.cache:
                user, token, timestamp = self.cache[key]
                if time.time() - timestamp < self.ttl_seconds:
                    # Move to end (most recently used)
                    self.cache.move_to_end(key)
                    self.hits += 1
                    return user, token, True
                else:
                    # Expired
                    del self.cache[key]
            self.misses += 1
            return None, None, False

    def set(self, key: str, user: UserModel | None, token: ApiToken | None) -> None:
        """Cache token validation result."""
        with self.lock:
            # Remove oldest if at capacity
            if len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)
            self.cache[key] = (user, token, time.time())


class OptimizedBearerTokenAuthentication(authentication.BaseAuthentication):
    """
    Optimized authentication class for Bearer tokens with caching.
    Does not enforce CSRF checks.
    """

    # Class-level cache shared across requests
    _token_cache = TokenCache(max_size=1000, ttl_seconds=300)

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

        # Check cache first
        cache_key = self._get_cache_key(token)
        user, api_token, found = self._token_cache.get(cache_key)
        if found:
            # Store token in request for later use
            request.token = api_token
            # Schedule async update of last_used
            if api_token:
                self._schedule_update_last_used(api_token)
            return (user, api_token) if user else None

        # Cache miss - validate token
        user, api_token = self._authenticate_token(token)

        # Cache the result (even if None for negative caching)
        self._token_cache.set(cache_key, user, api_token)

        if user and api_token:
            # Store token in request for later use
            request.token = api_token
            # Update last used timestamp
            self._schedule_update_last_used(api_token)
            return (user, api_token)

        return None

    def _get_cache_key(self, token: str) -> str:
        """Generate a cache key for the token."""
        # Use first 12 chars (prefix) + hash of full token for security
        token_hash = hashlib.sha256(token.encode()).hexdigest()[:16]
        return f"{token[:12]}:{token_hash}"

    def _authenticate_token(self, token: str) -> tuple[UserModel | None, ApiToken | None]:
        """Authenticate a token and return the associated user and token object."""
        token_prefix = token[:12]  # tok_ + 8 chars

        try:
            # Fetch token with user in single query, only necessary fields
            api_token = (
                ApiToken.objects.select_related("user")
                .only(
                    "id",
                    "token_hash",
                    "revoked_at",
                    "user__id",
                    "user__email",
                    "user__is_active",
                    "user__email_verified_at",
                )
                .get(token_prefix=token_prefix)
            )

            # Quick validation checks
            if (
                api_token.is_revoked
                or not api_token.user.is_active
                or not api_token.user.is_email_verified
            ):
                return None, None

            # Verify token hash
            ph = PasswordHasher()
            try:
                ph.verify(api_token.token_hash, token)
            except VerifyMismatchError:
                return None, None

            return api_token.user, api_token

        except ApiToken.DoesNotExist:
            return None, None

    def _schedule_update_last_used(self, api_token: ApiToken) -> None:
        """
        Schedule async update of last_used timestamp.
        Only update if more than 60 seconds since last update.
        """
        cache_key = f"token_last_updated:{api_token.id}"
        if not cache.get(cache_key):
            api_token.update_last_used()
            cache.set(cache_key, True, 60)  # Update at most once per minute

    def authenticate_header(self, request: Request) -> str:
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response.
        """
        return 'Bearer realm="api"'
