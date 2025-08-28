from typing import Any
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models


class FlexibleURLValidator(URLValidator):
    """URLValidator that allows underscores in domain names for Cloudflare Workers."""

    def __call__(self, value: str) -> None:
        """Validate URL, allowing underscores for Cloudflare Workers domains.

        Args:
            value: The URL string to validate

        Raises:
            ValidationError: If the URL is invalid
        """
        # Temporarily replace underscores with hyphens for validation
        # This allows Cloudflare Workers domains like xxx_xxx.workers.dev
        if "_" in value:
            # Extract the domain part and check if it's a workers.dev domain
            parsed = urlparse(value)
            if parsed.hostname and ".workers.dev" in parsed.hostname:
                # Replace underscores with hyphens just for validation
                temp_value = value.replace("_", "-")
                super().__call__(temp_value)
                return
        super().__call__(value)


class Settings(models.Model):
    """Singleton settings model for the application."""

    cost_per_request_cents = models.IntegerField(default=100)
    openai_model = models.CharField(max_length=100, default="gpt-vision")
    openai_timeout_s = models.IntegerField(default=30)
    app_domain = models.URLField(
        max_length=255,
        blank=True,
        help_text="Frontend application domain for email verification links (e.g., https://app.example.com). If empty, uses the backend domain.",
        verbose_name="Application Domain",
        validators=[FlexibleURLValidator()],
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "settings"
        verbose_name = "Settings"
        verbose_name_plural = "Settings"

    def __str__(self) -> str:
        return "Application Settings"

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Ensure only one Settings instance exists."""
        if not self.pk and Settings.objects.exists():
            # If a new instance is being created and one already exists
            raise ValidationError("Only one Settings instance is allowed.")
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls) -> "Settings":
        """Get or create the singleton settings instance."""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings
