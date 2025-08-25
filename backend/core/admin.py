from typing import Any

from django.contrib import admin
from django.http import HttpRequest

from .models import Settings


@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ["cost_per_request_cents", "openai_model", "openai_timeout_s", "updated_at"]
    fields = ["cost_per_request_cents", "openai_model", "openai_timeout_s"]

    def has_add_permission(self, request: HttpRequest) -> bool:
        # Only allow adding if no Settings instance exists
        return not Settings.objects.exists()

    def has_delete_permission(self, request: HttpRequest, obj: Settings | None = None) -> bool:
        # Prevent deletion of the singleton
        return False
