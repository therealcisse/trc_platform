"""
Optimized token authentication middleware with in-memory caching.
This reduces Argon2 verification overhead significantly.
"""

import hashlib
import time
from collections import OrderedDict
from collections.abc import Callable
from threading import Lock
from typing import TYPE_CHECKING, Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse

from customers.models import ApiToken

if TYPE_CHECKING:
    from customers.models import User
else:
    User = get_user_model()


class TokenCache:
    """Thread-safe LRU cache for token validation results."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300) -> None:
        self.cache: OrderedDict[str, tuple[User | None, ApiToken | None, float]] = (
            OrderedDict()
        )
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.lock = Lock()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> tuple[User | None, ApiToken | None, bool]:
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

    def set(self, key: str, user: User | None, token: ApiToken | None) -> None:
        """Cache token validation result."""
        with self.lock:
            # Remove oldest if at capacity
            if len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)
            self.cache[key] = (user, token, time.time())

    def invalidate(self, key: str) -> None:
        """Remove a token from cache."""
        with self.lock:
            self.cache.pop(key, None)

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total = self.hits + self.misses
            hit_rate = self.hits / total if total > 0 else 0
            return {
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "size": len(self.cache),
            }


class OptimizedTokenAuthMiddleware:
    """
    Optimized middleware for Bearer token authentication with caching.

    Key optimizations:
    1. In-memory LRU cache for validated tokens
    2. Fast token fingerprinting for cache keys
    3. Batch prefetching of related data
    4. Minimal database queries
    """

    # Class-level cache shared across requests
    _token_cache = TokenCache(max_size=1000, ttl_seconds=300)

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response
        self.ph = PasswordHasher()

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Skip if already authenticated via session
        if hasattr(request, "user") and request.user.is_authenticated:
            return self.get_response(request)

        # Extract and validate token
        token = self._extract_token(request)
        if token:
            user, api_token = self._authenticate_token_cached(token)
            if user:
                request.user = user
                request.token = api_token  # type: ignore[attr-defined]
                # Update last used timestamp asynchronously
                if api_token:
                    self._schedule_update_last_used(api_token)
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

    def _get_cache_key(self, token: str) -> str:
        """Generate a cache key for the token."""
        # Use first 12 chars (prefix) + hash of full token for security
        token_hash = hashlib.sha256(token.encode()).hexdigest()[:16]
        return f"{token[:12]}:{token_hash}"

    def _authenticate_token_cached(self, token: str) -> tuple[User | None, ApiToken | None]:
        """Authenticate token with caching."""
        # Check cache first
        cache_key = self._get_cache_key(token)
        user, api_token, found = self._token_cache.get(cache_key)
        if found:
            return user, api_token

        # Cache miss - validate token
        user, api_token = self._authenticate_token(token)

        # Cache the result (even if None for negative caching)
        self._token_cache.set(cache_key, user, api_token)

        return user, api_token

    def _authenticate_token(self, token: str) -> tuple[User | None, ApiToken | None]:
        """Authenticate a token and return the associated user and token object."""
        # Validate token format
        if not token.startswith("tok_"):
            return None, None

        token_prefix = token[:12]  # tok_ + 8 chars

        try:
            # Fetch token with user in single query
            api_token = (
                ApiToken.objects.select_related("user")
                .only(
                    "id",
                    "token_hash",
                    "revoked_at",
                    "user__id",
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
            try:
                self.ph.verify(api_token.token_hash, token)
            except VerifyMismatchError:
                return None, None

            return api_token.user, api_token

        except ApiToken.DoesNotExist:
            return None, None

    def _schedule_update_last_used(self, api_token: ApiToken) -> None:
        """
        Schedule async update of last_used timestamp.
        In production, this would use a task queue.
        For now, we'll do a lightweight update.
        """
        # Only update if more than 60 seconds since last update
        cache_key = f"token_last_updated:{api_token.id}"
        if not cache.get(cache_key):
            api_token.update_last_used()
            cache.set(cache_key, True, 60)  # Update at most once per minute

    @classmethod
    def invalidate_token(cls, token_prefix: str) -> None:
        """Invalidate a token in the cache (useful when token is revoked)."""
        # We need to invalidate all possible cache entries for this prefix
        # In production, you might want to store the full cache key with the token
        pass  # For now, the cache will expire naturally

    @classmethod
    def get_cache_stats(cls) -> dict[str, Any]:
        """Get cache statistics for monitoring."""
        return cls._token_cache.get_stats()
