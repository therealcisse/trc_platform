from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import QuerySet
from django.http import HttpRequest

from .models import ApiToken, InviteCode, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "is_active", "is_staff", "email_verified_at", "date_joined"]
    list_filter = ["is_active", "is_staff", "email_verified_at"]
    search_fields = ["email"]
    ordering = ["-date_joined"]
    actions = ["deactivate_users", "activate_users"]

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

    @admin.action(description="Deactivate selected users")
    def deactivate_users(self, request: HttpRequest, queryset: QuerySet[User]) -> None:
        """Deactivate selected users."""
        # Prevent deactivating superusers
        superusers = queryset.filter(is_superuser=True)
        if superusers.exists():
            self.message_user(
                request,
                f"Cannot deactivate {superusers.count()} superuser(s). Skipping them.",
                level=messages.WARNING,
            )
            queryset = queryset.exclude(is_superuser=True)

        # Prevent deactivating the current user
        if request.user in queryset:
            self.message_user(
                request, "You cannot deactivate your own account.", level=messages.ERROR
            )
            queryset = queryset.exclude(pk=request.user.pk)

        updated = queryset.update(is_active=False)
        if updated:
            self.message_user(
                request, f"Successfully deactivated {updated} user(s).", level=messages.SUCCESS
            )

    @admin.action(description="Activate selected users")
    def activate_users(self, request: HttpRequest, queryset: QuerySet[User]) -> None:
        """Activate selected users."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request, f"Successfully activated {updated} user(s).", level=messages.SUCCESS
        )


@admin.register(InviteCode)
class InviteCodeAdmin(admin.ModelAdmin):
    list_display = ["code", "is_active", "expires_at", "used_by", "used_at", "created_at"]
    list_filter = ["is_active", "expires_at", "created_at"]
    search_fields = ["code", "used_by__email"]
    readonly_fields = ["created_at", "used_at", "used_by"]
    ordering = ["-created_at"]


@admin.register(ApiToken)
class ApiTokenAdmin(admin.ModelAdmin):
    list_display = [
        "token_prefix",
        "user",
        "name",
        "is_active",
        "created_at",
        "revoked_at",
        "last_used_at",
    ]
    list_filter = ["created_at", "revoked_at", "last_used_at"]
    search_fields = ["token_prefix", "user__email", "name"]
    readonly_fields = ["id", "token_prefix", "token_hash", "created_at", "last_used_at"]
    ordering = ["-created_at"]
    actions = ["revoke_tokens"]

    def is_active(self, obj: ApiToken) -> bool:
        """Display whether the token is active (not revoked)."""
        return obj.revoked_at is None

    is_active.boolean = True  # This tells Django to use green checkmark/red X icons
    is_active.short_description = "Active"

    @admin.action(description="Revoke selected API tokens")
    def revoke_tokens(self, request: HttpRequest, queryset: QuerySet[ApiToken]) -> None:
        """Revoke selected API tokens."""
        # Filter out already revoked tokens
        already_revoked = queryset.filter(revoked_at__isnull=False)
        if already_revoked.exists():
            self.message_user(
                request,
                f"{already_revoked.count()} token(s) were already revoked. Skipping them.",
                level=messages.WARNING,
            )

        # Revoke only active tokens
        active_tokens = queryset.filter(revoked_at__isnull=True)
        revoked_count = 0
        for token in active_tokens:
            token.revoke()
            revoked_count += 1

        if revoked_count:
            self.message_user(
                request,
                f"Successfully revoked {revoked_count} API token(s).",
                level=messages.SUCCESS,
            )
