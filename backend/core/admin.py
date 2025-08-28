from typing import Any

from django.contrib import admin
from django.http import HttpRequest, HttpResponseRedirect
from django.utils.html import format_html

from .models import Settings


@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = [
        "display_title",
        "cost_per_request_cents",
        "openai_model",
        "openai_timeout_s",
        "app_domain",
        "updated_at",
    ]
    list_display_links = ["display_title"]  # Make the title clickable

    fieldsets = [
        (
            "API Settings",
            {
                "fields": ["openai_model", "openai_timeout_s"],
                "description": "Configuration for OpenAI API integration",
            },
        ),
        (
            "Billing Settings",
            {
                "fields": ["cost_per_request_cents"],
                "description": "Cost configuration for usage tracking",
            },
        ),
        (
            "Application Settings",
            {
                "fields": ["app_domain"],
                "description": "Frontend application configuration. Set the app_domain to your frontend URL (e.g., https://trc_platform.cisse-amadou-9.workers.dev)",
            },
        ),
    ]

    def display_title(self, obj: Settings) -> str:
        """Display a clickable title for the settings."""
        return format_html("<strong>Click here to edit settings</strong>")

    display_title.short_description = "Settings"

    def changelist_view(
        self, request: HttpRequest, extra_context: dict[str, Any] | None = None
    ) -> Any:
        """Redirect directly to the edit page if a Settings instance exists."""
        if Settings.objects.exists():
            settings = Settings.objects.first()
            if settings:
                return HttpResponseRedirect(f"/admin/core/settings/{settings.pk}/change/")
        return super().changelist_view(request, extra_context)

    def has_add_permission(self, request: HttpRequest) -> bool:
        # Only allow adding if no Settings instance exists
        return not Settings.objects.exists()

    def has_delete_permission(self, request: HttpRequest, obj: Settings | None = None) -> bool:
        # Prevent deletion of the singleton
        return False
