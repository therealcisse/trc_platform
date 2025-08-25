
from rest_framework import serializers

from .models import BillingPeriod, RequestImage, RequestLog


class BillingPeriodSerializer(serializers.ModelSerializer):
    """Serializer for BillingPeriod model with automatic camelCase conversion."""

    period_label = serializers.ReadOnlyField()
    can_be_marked_paid = serializers.ReadOnlyField()

    class Meta:
        model = BillingPeriod
        fields = [
            "id",
            "user",
            "period_start",
            "period_end",
            "total_requests",
            "total_cost_cents",
            "is_current",
            "payment_status",
            "paid_at",
            "paid_amount_cents",
            "payment_reference",
            "payment_notes",
            "created_at",
            "updated_at",
            "period_label",
            "can_be_marked_paid",
        ]
        read_only_fields = [
            "id",
            "user",
            "created_at",
            "updated_at",
            "period_label",
            "can_be_marked_paid",
        ]


class CurrentBillingPeriodSerializer(serializers.ModelSerializer):
    """Simplified serializer for current billing period display."""

    period_label = serializers.ReadOnlyField()
    last_request_at = serializers.SerializerMethodField()

    class Meta:
        model = BillingPeriod
        fields = [
            "id",
            "is_current",
            "period_start",
            "period_end",
            "period_label",
            "total_requests",
            "total_cost_cents",
            "last_request_at",
        ]

    def get_last_request_at(self, obj: BillingPeriod) -> str | None:
        """Get the timestamp of the last request in this period."""
        last_request = obj.requests.order_by("-request_ts").first()
        return last_request.request_ts.isoformat() if last_request else None


class RequestLogSerializer(serializers.ModelSerializer):
    """Serializer for RequestLog model."""

    class Meta:
        model = RequestLog
        fields = [
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
            "billing_period",
            "result",
        ]
        read_only_fields = fields


class RequestImageSerializer(serializers.ModelSerializer):
    """Serializer for RequestImage model."""

    class Meta:
        model = RequestImage
        fields = [
            "id",
            "request_log",
            "mime_type",
            "file_size",
            "image_hash",
            "width",
            "height",
            "created_at",
        ]
        read_only_fields = fields
        # Exclude the actual image data from serialization for performance
        exclude = ["image_data"]


class UsageStatisticsSerializer(serializers.Serializer):
    """Serializer for usage statistics."""

    total_requests = serializers.IntegerField()
    total_cost_cents = serializers.IntegerField()
    average_request_duration_ms = serializers.FloatField()
    total_request_bytes = serializers.IntegerField()
    total_response_bytes = serializers.IntegerField()
    success_rate = serializers.FloatField()
    period_start = serializers.DateField()
    period_end = serializers.DateField()


class MarkBillingPeriodAsPaidSerializer(serializers.Serializer):
    """Serializer for marking a billing period as paid."""

    amount_cents = serializers.IntegerField(required=False, allow_null=True)
    reference = serializers.CharField(max_length=255, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate_amount_cents(self, value: int | None) -> int | None:
        """Validate that amount is positive if provided."""
        if value is not None and value < 0:
            raise serializers.ValidationError("Amount must be positive")
        return value
