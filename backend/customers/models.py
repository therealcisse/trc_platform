import secrets
import string
import uuid
from datetime import UTC, datetime

from argon2 import PasswordHasher
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email: str, password: str | None = None, **extra_fields) -> "User":
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields) -> "User":
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("email_verified_at", datetime.now(UTC))

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        return self.email

    @property
    def is_email_verified(self) -> bool:
        return self.email_verified_at is not None


class InviteCode(models.Model):
    """One-time use invite code tied to a user."""

    code = models.CharField(max_length=32, unique=True, db_index=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    used_by = models.OneToOneField(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="invite_code_used"
    )

    class Meta:
        db_table = "invite_codes"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.code

    @classmethod
    def generate_code(cls) -> str:
        """Generate a random invite code."""
        alphabet = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(8))

    def mark_as_used(self, user: User) -> None:
        """Mark invite code as used by a specific user."""
        self.used_by = user
        self.used_at = datetime.now(UTC)
        self.is_active = False
        self.save(update_fields=["used_by", "used_at", "is_active"])

    @property
    def is_expired(self) -> bool:
        """Check if the invite code has expired."""
        if not self.expires_at:
            return False
        return datetime.now(UTC) > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if the invite code is valid for use."""
        return self.is_active and not self.is_expired and self.used_by is None


class ApiToken(models.Model):
    """API token for programmatic access."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="api_tokens")
    name = models.CharField(max_length=100)
    token_prefix = models.CharField(max_length=8, db_index=True)
    token_hash = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "api_tokens"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["token_prefix"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.name}"

    @classmethod
    def generate_token(cls) -> tuple[str, str, str]:
        """Generate a new API token.

        Returns:
            tuple: (full_token, token_prefix, token_hash)
        """
        # Generate 32 random bytes
        secrets.token_bytes(32)
        # Convert to base64url string
        full_token = secrets.token_urlsafe(32)
        # Get prefix (first 8 chars including 'tok_' prefix)
        token_with_prefix = f"tok_{full_token}"
        token_prefix = token_with_prefix[:12]  # tok_ + 8 chars

        # Hash the full token
        ph = PasswordHasher()
        token_hash = ph.hash(token_with_prefix)

        return token_with_prefix, token_prefix, token_hash

    @property
    def is_revoked(self) -> bool:
        """Check if the token has been revoked."""
        return self.revoked_at is not None

    def revoke(self) -> None:
        """Revoke the token."""
        self.revoked_at = datetime.now(UTC)
        self.save(update_fields=["revoked_at"])

    def update_last_used(self) -> None:
        """Update the last used timestamp."""
        self.last_used_at = datetime.now(UTC)
        self.save(update_fields=["last_used_at"])
