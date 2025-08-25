from django.contrib import admin

from .models import Settings


@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    list_display = ["cost_per_request_cents", "openai_model", "openai_timeout_s", "updated_at"]
    fields = ["cost_per_request_cents", "openai_model", "openai_timeout_s"]

    def has_add_permission(self, request):
        # Only allow adding if no Settings instance exists
        return not Settings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of the singleton
        return False
