from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import ApiToken, InviteCode, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "is_active", "is_staff", "email_verified_at", "date_joined"]
    list_filter = ["is_active", "is_staff", "email_verified_at"]
    search_fields = ["email"]
    ordering = ["-date_joined"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Important dates", {"fields": ("email_verified_at", "date_joined", "last_login")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_staff", "is_active"),
            },
        ),
    )

    readonly_fields = ["date_joined", "last_login"]


@admin.register(InviteCode)
class InviteCodeAdmin(admin.ModelAdmin):
    list_display = ["code", "is_active", "expires_at", "used_by", "used_at", "created_at"]
    list_filter = ["is_active", "expires_at", "created_at"]
    search_fields = ["code", "used_by__email"]
    readonly_fields = ["created_at", "used_at", "used_by"]
    ordering = ["-created_at"]


@admin.register(ApiToken)
class ApiTokenAdmin(admin.ModelAdmin):
    list_display = ["token_prefix", "user", "name", "created_at", "revoked_at", "last_used_at"]
    list_filter = ["created_at", "revoked_at", "last_used_at"]
    search_fields = ["token_prefix", "user__email", "name"]
    readonly_fields = ["id", "token_prefix", "token_hash", "created_at", "last_used_at"]
    ordering = ["-created_at"]
