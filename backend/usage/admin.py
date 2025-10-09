import base64
from typing import Any
from io import StringIO

from django.contrib import admin
from django.contrib import messages
from django.core.management import call_command
from django.http import HttpRequest
from django.utils.html import format_html
from django.utils.timezone import localtime
from django.utils import dateformat

from .models import BillingPeriod, RequestImage, RequestLog


@admin.register(RequestLog)
class RequestLogAdmin(admin.ModelAdmin):
    list_display = [
        "request_id",
        "user",
        "service",
        "status",
        "request_ts_display",
        "duration_ms",
        "result",  # Display result in list view
        "flow_id",  # Display flow id after result
    ]
    list_filter = ["status", "service", "request_ts"]
    search_fields = ["request_id", "user__email", "error_code", "result"]
    readonly_fields = [
        "id",
        "user",
        "token",
        "service",
        "request_ts",
        "duration_ms",
        "request_bytes",
        "response_bytes",
        "status",
        "error_code",
        "request_id",
        "result",  # Make result read-only in detail view
        "billing_period",
    ]
    ordering = ["-request_ts"]

    def request_ts_display(self, obj: RequestLog) -> str:
        dt = localtime(obj.request_ts)
        # Format example: "Oct. 9, 2025, 2:58:00 p.m."
        return dateformat.format(dt, "M j, Y, g:i:s a")

    request_ts_display.short_description = "REQUEST TS"  # type: ignore[attr-defined]
    request_ts_display.admin_order_field = "request_ts"

    def has_add_permission(self, request: HttpRequest) -> bool:
        # Make RequestLog read-only in admin
        return False

    def has_delete_permission(self, request: HttpRequest, obj: RequestLog | None = None) -> bool:
        # Prevent deletion of logs
        return False


@admin.register(BillingPeriod)
class BillingPeriodAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "period_label",
        "total_requests",
        "total_cost_cents_display",
        "payment_status_badge",
        "paid_at",
        "payment_reference",
        "is_current",
    ]
    list_filter = ["payment_status", "is_current", "period_start"]
    search_fields = ["user__email", "payment_reference"]
    readonly_fields = ["created_at", "updated_at"]

    actions = ["mark_as_paid", "mark_as_overdue", "mark_as_waived"]

    fieldsets = (
        ("Period Information", {"fields": ("user", "period_start", "period_end", "is_current")}),
        ("Usage & Cost", {"fields": ("total_requests", "total_cost_cents")}),
        (
            "Payment Information",
            {
                "fields": (
                    "payment_status",
                    "paid_at",
                    "paid_amount_cents",
                    "payment_reference",
                    "payment_notes",
                )
            },
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    def total_cost_cents_display(self, obj: BillingPeriod) -> str:
        return f"${obj.total_cost_cents / 100:.2f}"

    total_cost_cents_display.short_description = "Total Cost"  # type: ignore[attr-defined]

    def payment_status_badge(self, obj: BillingPeriod) -> str:
        colors = {
            "pending": "orange",
            "paid": "green",
            "overdue": "red",
            "waived": "gray",
        }
        color = colors.get(obj.payment_status, "black")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_payment_status_display(),
        )

    payment_status_badge.short_description = "Payment Status"  # type: ignore[attr-defined]

    def mark_as_paid(self, request: HttpRequest, queryset: Any) -> None:
        count = 0
        for period in queryset:
            if period.can_be_marked_paid:
                period.mark_as_paid()
                count += 1
        self.message_user(request, f"{count} billing periods marked as paid.")

    mark_as_paid.short_description = "Mark selected periods as paid"  # type: ignore[attr-defined]

    def mark_as_overdue(self, request: HttpRequest, queryset: Any) -> None:
        count = 0
        for period in queryset:
            if not period.is_current and period.payment_status != "paid":
                period.mark_as_overdue()
                count += 1
        self.message_user(request, f"{count} billing periods marked as overdue.")

    mark_as_overdue.short_description = "Mark selected periods as overdue"  # type: ignore[attr-defined]

    def mark_as_waived(self, request: HttpRequest, queryset: Any) -> None:
        count = 0
        for period in queryset:
            if not period.is_current and period.payment_status not in ["paid", "waived"]:
                period.mark_as_waived()
                count += 1
        self.message_user(request, f"{count} billing periods marked as waived.")

    mark_as_waived.short_description = "Mark selected periods as waived"  # type: ignore[attr-defined]


@admin.register(RequestImage)
class RequestImageAdmin(admin.ModelAdmin):
    list_display = [
        "request_log_id",
        "file_size_display",
        "dimensions",
        "mime_type",
        "created_at_display",
    ]
    list_filter = ["mime_type", "created_at"]
    search_fields = ["request_log__request_id", "image_hash"]
    readonly_fields = [
        "id",
        "request_log",
        "image_preview",
        "image_hash",
        "file_size",
        "width",
        "height",
        "mime_type",
        "created_at",
    ]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]

    def created_at_display(self, obj: RequestImage) -> str:
        dt = localtime(obj.created_at)
        # Example: "Oct. 9, 2025, 2:58:00 p.m."
        return dateformat.format(dt, "M j, Y, g:i:s a")

    created_at_display.short_description = "Created at"  # type: ignore[attr-defined]
    created_at_display.admin_order_field = "created_at"

    actions = ["run_cleanup_old_images"]

    def run_cleanup_old_images(self, request: HttpRequest, queryset: Any) -> None:
        buf = StringIO()
        try:
            call_command("cleanup_old_images", stdout=buf)
            output = buf.getvalue().strip() or "Cleanup completed."
            self.message_user(request, output, level=messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f"Cleanup failed: {e}", level=messages.ERROR)

    run_cleanup_old_images.short_description = "Clean up old images using defaults"  # type: ignore[attr-defined]

    def has_add_permission(self, request: HttpRequest) -> bool:
        # Make RequestImage read-only in admin
        return False

    def request_log_id(self, obj: RequestImage) -> str:
        return obj.request_log.request_id

    request_log_id.short_description = "Request ID"  # type: ignore[attr-defined]

    def file_size_display(self, obj: RequestImage) -> str:
        # Convert bytes to human-readable format
        size = obj.file_size
        for unit in ["B", "KB", "MB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} GB"

    file_size_display.short_description = "Size"  # type: ignore[attr-defined]

    def dimensions(self, obj: RequestImage) -> str:
        if obj.width and obj.height:
            return f"{obj.width}x{obj.height}"
        return "Unknown"

    dimensions.short_description = "Dimensions"  # type: ignore[attr-defined]

    def image_preview(self, obj: RequestImage) -> str:
        # Show preview in admin
        if obj.image_data:
            b64_image = base64.b64encode(obj.image_data).decode("utf-8")
            return format_html(
                '<img src="data:{};base64,{}" style="max-width: 400px; max-height: 400px; border: 1px solid #ddd; padding: 5px;" />',
                obj.mime_type,
                b64_image,
            )
        return "No image"

    image_preview.short_description = "Preview"  # type: ignore[attr-defined]
