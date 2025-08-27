
from django.contrib import admin
from django.http import HttpRequest

from .models import Settings


@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ["cost_per_request_cents", "openai_model", "openai_timeout_s", "app_domain", "updated_at"]
    
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

    def has_add_permission(self, request: HttpRequest) -> bool:
        # Only allow adding if no Settings instance exists
        return not Settings.objects.exists()

    def has_delete_permission(self, request: HttpRequest, obj: Settings | None = None) -> bool:
        # Prevent deletion of the singleton
        return False
