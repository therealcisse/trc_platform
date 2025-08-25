import hashlib
import io
import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone as django_timezone

User = get_user_model()


class BillingPeriod(models.Model):
    """Represents a monthly billing period."""

    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("overdue", "Overdue"),
        ("waived", "Waived"),  # For free credits or special cases
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="billing_periods")
    period_start = models.DateField(db_index=True)
    period_end = models.DateField(db_index=True)
    total_requests = models.IntegerField(default=0)
    total_cost_cents = models.IntegerField(default=0)
    is_current = models.BooleanField(default=False)

    # Payment tracking fields
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default="pending", db_index=True
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    paid_amount_cents = models.IntegerField(null=True, blank=True)
    payment_reference = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="External invoice or payment reference number",
    )
    payment_notes = models.TextField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "billing_periods"
        unique_together = ["user", "period_start"]
        ordering = ["-period_start"]
        indexes = [
            models.Index(fields=["user", "is_current"]),
            models.Index(fields=["period_start", "period_end"]),
            models.Index(fields=["payment_status"]),
            models.Index(fields=["user", "payment_status"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.period_start.strftime('%Y-%m')} - {self.payment_status}"

    @property
    def period_label(self) -> str:
        """Returns a human-readable period label like 'January 2025'"""
        return self.period_start.strftime("%B %Y")

    @property
    def can_be_marked_paid(self) -> bool:
        """Check if this period can be marked as paid."""
        return not self.is_current and self.payment_status in ["pending", "overdue"]

    def mark_as_paid(self, amount_cents=None, reference=None, notes=None):
        """Mark billing period as paid."""
        if self.is_current:
            raise ValueError("Cannot mark current billing period as paid")

        if self.payment_status == "paid":
            raise ValueError("Billing period is already marked as paid")

        self.payment_status = "paid"
        self.paid_at = django_timezone.now()
        self.paid_amount_cents = amount_cents or self.total_cost_cents
        self.payment_reference = reference
        self.payment_notes = notes
        self.save(
            update_fields=[
                "payment_status",
                "paid_at",
                "paid_amount_cents",
                "payment_reference",
                "payment_notes",
                "updated_at",
            ]
        )

    def mark_as_overdue(self):
        """Mark billing period as overdue."""
        if self.is_current:
            raise ValueError("Cannot mark current billing period as overdue")

        if self.payment_status == "paid":
            raise ValueError("Cannot mark paid billing period as overdue")

        self.payment_status = "overdue"
        self.save(update_fields=["payment_status", "updated_at"])

    def mark_as_waived(self, notes=None):
        """Mark billing period as waived (no payment required)."""
        if self.is_current:
            raise ValueError("Cannot waive current billing period")

        self.payment_status = "waived"
        self.payment_notes = notes
        self.save(update_fields=["payment_status", "payment_notes", "updated_at"])


class RequestLog(models.Model):
    """Log of API requests for usage tracking."""

    STATUS_CHOICES = [
        ("success", "Success"),
        ("error", "Error"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="request_logs")
    token = models.ForeignKey(
        "customers.ApiToken",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="request_logs",
    )
    service = models.CharField(max_length=100, default="core.image_solve")
    request_ts = models.DateTimeField(auto_now_add=True, db_index=True)
    duration_ms = models.IntegerField()
    request_bytes = models.IntegerField()
    response_bytes = models.IntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    error_code = models.CharField(max_length=50, null=True, blank=True)
    request_id = models.UUIDField(db_index=True)
    billing_period = models.ForeignKey(
        "BillingPeriod", null=True, blank=True, on_delete=models.SET_NULL, related_name="requests"
    )
    # Store the actual result for successful requests (added for auditing/debugging)
    result = models.TextField(
        null=True,
        blank=True,
        help_text="The solver result/answer for successful requests",
    )

    class Meta:
        db_table = "request_logs"
        ordering = ["-request_ts"]
        indexes = [
            models.Index(fields=["user", "-request_ts"]),
            models.Index(fields=["request_ts"]),
            models.Index(fields=["request_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.service} - {self.request_ts}"


class RequestImage(models.Model):
    """Stores image data for requests when SAVE_REQUEST_IMAGES is enabled."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request_log = models.OneToOneField(
        "RequestLog", on_delete=models.CASCADE, related_name="saved_image"
    )
    image_data = models.BinaryField()  # Raw image bytes
    mime_type = models.CharField(max_length=50, default="image/jpeg")
    file_size = models.IntegerField()  # Size in bytes
    image_hash = models.CharField(max_length=64, db_index=True)  # SHA256 for deduplication
    width = models.IntegerField(null=True, blank=True)
    height = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "request_images"
        indexes = [
            models.Index(fields=["image_hash"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"Image for request {self.request_log.request_id}"

    @classmethod
    def create_from_bytes(
        cls, request_log: "RequestLog", image_bytes: bytes, mime_type: str = "image/jpeg"
    ) -> "RequestImage":
        """Create RequestImage from raw bytes with metadata extraction."""
        # Calculate hash for deduplication
        image_hash = hashlib.sha256(image_bytes).hexdigest()

        # Extract image dimensions if possible
        width, height = None, None
        try:
            from PIL import Image

            img = Image.open(io.BytesIO(image_bytes))
            width, height = img.size
        except Exception:
            pass  # If we can't read the image, just skip dimensions

        return cls.objects.create(
            request_log=request_log,
            image_data=image_bytes,
            mime_type=mime_type,
            file_size=len(image_bytes),
            image_hash=image_hash,
            width=width,
            height=height,
        )
