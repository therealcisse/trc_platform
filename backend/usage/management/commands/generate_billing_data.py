import calendar
import io
import random
import uuid
from datetime import date, datetime, timedelta
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont

from customers.models import ApiToken, User
from usage.models import BillingPeriod, RequestImage, RequestLog


class Command(BaseCommand):
    help = "Generate sample RequestLog and RequestImage data for any month (current or past)"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--month",
            type=int,
            required=True,
            choices=range(1, 13),
            help="Month number (1-12)",
        )
        parser.add_argument(
            "--year",
            type=int,
            required=True,
            help="Year (e.g., 2025)",
        )
        parser.add_argument(
            "--user-email",
            type=str,
            default="test@example.com",
            help="Email of the user to generate data for",
        )
        parser.add_argument(
            "--min-requests-per-day",
            type=int,
            default=10,
            help="Minimum number of requests to generate per day",
        )
        parser.add_argument(
            "--max-requests-per-day",
            type=int,
            default=30,
            help="Maximum number of requests to generate per day",
        )
        parser.add_argument(
            "--payment-status",
            type=str,
            choices=["paid", "pending", "overdue", "waived"],
            help="Payment status for the period (auto-determined if not specified)",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        month = options["month"]
        year = options["year"]
        user_email = options["user_email"]
        min_requests = options["min_requests_per_day"]
        max_requests = options["max_requests_per_day"]
        payment_status = options.get("payment_status")

        # Validate that we're not generating future data
        current_date = timezone.now().date()
        period_start = date(year, month, 1)

        if period_start > current_date:
            raise CommandError(
                f"Cannot generate data for future months. {calendar.month_name[month]} {year} is in the future."
            )

        # Get month name for token
        month_name = calendar.month_name[month].upper()

        # Determine if this is the current billing period
        is_current = year == current_date.year and month == current_date.month

        # Auto-determine payment status if not specified
        if payment_status is None:
            if is_current:
                payment_status = "pending"
            else:
                # For past months, randomly choose between paid and overdue
                payment_status = "overdue" if month % 2 == 0 else "paid"

        # Validate payment status for current period
        if is_current and payment_status not in ["pending"]:
            self.stdout.write(
                self.style.WARNING(
                    "Current billing period must be 'pending'. Setting to 'pending'."
                )
            )
            payment_status = "pending"

        period_label = f"{calendar.month_name[month]} {year}"
        self.stdout.write(f"Starting data generation for {period_label}...")

        if is_current:
            self.stdout.write(self.style.SUCCESS("This is the CURRENT billing period"))
        else:
            self.stdout.write(f"This is a CLOSED billing period (status: {payment_status})")

        with transaction.atomic():
            # Get or create user
            user, user_created = User.objects.get_or_create(
                email=user_email,
                defaults={
                    "is_active": True,
                    "email_verified_at": timezone.now(),
                },
            )
            if user_created:
                self.stdout.write(self.style.SUCCESS(f"Created new user: {user_email}"))
            else:
                self.stdout.write(f"Using existing user: {user_email}")

            # Create or get the API token for this month
            api_token = self._create_or_get_api_token(user, month_name, year, month)

            # Create or get billing period
            billing_period = self._create_or_get_billing_period(
                user, year, month, is_current, payment_status
            )

            # Generate data for the entire month
            last_day = calendar.monthrange(year, month)[1]
            start_date = date(year, month, 1)

            # For current month, only generate up to today
            if is_current:
                end_date = min(date(year, month, last_day), current_date)
            else:
                end_date = date(year, month, last_day)

            total_requests_generated = 0
            current_gen_date = start_date

            while current_gen_date <= end_date:
                # Generate random number of requests for this day
                num_requests = random.randint(min_requests, max_requests)

                for _ in range(num_requests):
                    request_log = self._generate_request_log(
                        user, api_token, billing_period, current_gen_date, is_current
                    )

                    # Generate RequestImage for successful requests
                    # Higher chance for current month, lower for older months
                    image_chance = (
                        0.8 if is_current else max(0.6, 0.8 - (current_date.month - month) * 0.05)
                    )
                    if request_log.status == "success" and random.random() < image_chance:
                        self._generate_request_image(request_log, month_name)

                    total_requests_generated += 1

                self.stdout.write(
                    f"Generated {num_requests} requests for {current_gen_date.strftime('%Y-%m-%d')}"
                )
                current_gen_date += timedelta(days=1)

            # Update billing period totals and close it if not current
            self._update_billing_period(billing_period, is_current, payment_status, year, month)

            self.stdout.write(
                self.style.SUCCESS(
                    f"\nSuccessfully generated {total_requests_generated} requests for {period_label}!"
                )
            )
            self.stdout.write(
                f"Billing period total: {billing_period.total_requests} requests, "
                f"${billing_period.total_cost_cents / 100:.2f}"
            )

            if is_current:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Period status: CURRENT - Payment status: {billing_period.payment_status.upper()}"
                    )
                )
            else:
                self.stdout.write(
                    f"Period status: CLOSED - Payment status: {billing_period.payment_status.upper()}"
                )
                if payment_status == "overdue":
                    self.stdout.write(
                        self.style.WARNING("This period is OVERDUE and requires payment!")
                    )

    def _create_or_get_api_token(
        self, user: User, month_name: str, year: int, month: int
    ) -> ApiToken:
        """Create or retrieve the API token for the specified month."""
        # Check if token already exists
        try:
            token = ApiToken.objects.get(user=user, name=month_name, revoked_at__isnull=True)
            self.stdout.write(f"Using existing API token: {month_name}")
            return token
        except ApiToken.DoesNotExist:
            # Generate new token
            full_token, token_prefix, token_hash = ApiToken.generate_token()
            token = ApiToken.objects.create(
                user=user,
                name=month_name,
                token_prefix=token_prefix,
                token_hash=token_hash,
            )

            # Set last used date to end of the month for past months
            current_date = timezone.now().date()
            if date(year, month, 1) < date(current_date.year, current_date.month, 1):
                last_day = calendar.monthrange(year, month)[1]
                token.last_used_at = datetime(
                    year, month, last_day, 23, 59, 59, tzinfo=timezone.get_current_timezone()
                )
                token.save(update_fields=["last_used_at"])

            self.stdout.write(
                self.style.SUCCESS(
                    f"Created new API token '{month_name}' with prefix: {token_prefix}"
                )
            )
            self.stdout.write(self.style.WARNING(f"Full token (save this): {full_token}"))
            return token

    def _create_or_get_billing_period(
        self, user: User, year: int, month: int, is_current: bool, payment_status: str
    ) -> BillingPeriod:
        """Create or retrieve billing period for the specified month."""
        period_start = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        period_end = date(year, month, last_day)

        billing_period, created = BillingPeriod.objects.get_or_create(
            user=user,
            period_start=period_start,
            defaults={
                "period_end": period_end,
                "is_current": is_current,
                "payment_status": "pending",  # Will be updated later
            },
        )

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created billing period for {calendar.month_name[month]} {year}"
                )
            )
        else:
            self.stdout.write(
                f"Using existing billing period for {calendar.month_name[month]} {year}"
            )
            # Update is_current flag in case it changed
            if billing_period.is_current != is_current:
                billing_period.is_current = is_current
                billing_period.save(update_fields=["is_current"])

        return billing_period

    def _generate_request_log(
        self,
        user: User,
        api_token: ApiToken,
        billing_period: BillingPeriod,
        request_date: date,
        is_current: bool,
    ) -> RequestLog:
        """Generate a random RequestLog entry."""
        # Random time within the day
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)

        request_time = datetime.combine(
            request_date,
            datetime.min.time().replace(hour=hour, minute=minute, second=second),
            tzinfo=timezone.get_current_timezone(),
        )

        # Success rate varies: 90% for current, 85-88% for past
        success_rate = 0.9 if is_current else random.uniform(0.85, 0.88)
        status = "success" if random.random() < success_rate else "error"

        # Generate random metrics
        duration_ms = random.randint(40, 2500)
        request_bytes = random.randint(500, 60000)
        response_bytes = (
            random.randint(100, 15000) if status == "success" else random.randint(40, 800)
        )

        # Random error codes for failed requests
        error_codes = [
            "INVALID_IMAGE",
            "TIMEOUT",
            "RATE_LIMIT",
            "SERVER_ERROR",
            "BAD_REQUEST",
            "UNSUPPORTED_FORMAT",
            "AUTH_FAILED",
            "QUOTA_EXCEEDED",
        ]
        error_code = random.choice(error_codes) if status == "error" else None

        # Generate random result for successful requests
        result = None
        if status == "success":
            result_types = [
                f"Solution: {random.randint(1, 100)}",
                f"Text: {self._generate_random_text()}",
                f"Captcha: {''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))}",
                f"Math: {random.randint(1, 999)} + {random.randint(1, 999)} = {random.randint(2, 1998)}",
                f"Verification: {'PASSED' if random.random() > 0.2 else 'FAILED'}",
                f"OCR: {self._generate_random_ocr_text()}",
                f"Pattern: {self._generate_pattern_result()}",
            ]
            result = random.choice(result_types)

        request_log = RequestLog(
            user=user,
            token=api_token,
            service="core.image_solve",
            duration_ms=duration_ms,
            request_bytes=request_bytes,
            response_bytes=response_bytes,
            status=status,
            error_code=error_code,
            request_id=uuid.uuid4(),
            billing_period=billing_period,
            result=result,
        )
        request_log.save()
        # Manually update the timestamp after creation
        RequestLog.objects.filter(id=request_log.id).update(request_ts=request_time)

        return request_log

    def _generate_request_image(self, request_log: RequestLog, month_name: str) -> RequestImage:
        """Generate a random image for the request."""
        width = random.choice([180, 200, 250, 300, 350, 400, 450, 500])
        height = random.choice([80, 100, 120, 150, 180, 200, 250, 300])

        # Create image with random background color
        bg_color = (
            random.randint(180, 255),
            random.randint(180, 255),
            random.randint(180, 255),
        )
        image = Image.new("RGB", (width, height), bg_color)
        draw = ImageDraw.Draw(image)

        # Add random shapes
        for _ in range(random.randint(2, 12)):
            shape_type = random.choice(["rectangle", "ellipse", "line", "polygon", "arc"])
            color = (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255),
            )

            if shape_type == "rectangle":
                coords = [
                    random.randint(0, width // 2),
                    random.randint(0, height // 2),
                    random.randint(width // 2, width),
                    random.randint(height // 2, height),
                ]
                draw.rectangle(coords, outline=color, width=2)
            elif shape_type == "ellipse":
                coords = [
                    random.randint(0, width // 2),
                    random.randint(0, height // 2),
                    random.randint(width // 2, width),
                    random.randint(height // 2, height),
                ]
                draw.ellipse(coords, outline=color, width=2)
            elif shape_type == "arc":
                coords = [
                    random.randint(0, width // 2),
                    random.randint(0, height // 2),
                    random.randint(width // 2, width),
                    random.randint(height // 2, height),
                ]
                draw.arc(
                    coords,
                    start=random.randint(0, 180),
                    end=random.randint(180, 360),
                    fill=color,
                    width=2,
                )
            elif shape_type == "polygon":
                points = []
                for _ in range(random.randint(3, 7)):
                    points.append((random.randint(0, width), random.randint(0, height)))
                if len(points) > 2:
                    draw.polygon(points, outline=color, width=2)
            else:  # line
                coords = [
                    random.randint(0, width),
                    random.randint(0, height),
                    random.randint(0, width),
                    random.randint(0, height),
                ]
                draw.line(coords, fill=color, width=random.randint(1, 5))

        # Add text with month reference
        text_options = [
            f"{month_name}-{random.randint(1, 31):02d}",
            f"ID: {request_log.request_id.hex[:10]}",
            f"Code: {month_name[:3]}{random.randint(10000, 99999)}",
            f"Batch: {random.randint(100, 999)}",
            f"{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=8))}",
            f"{random.randint(100, 999)} / {random.randint(10, 99)}",
        ]
        text = random.choice(text_options)

        try:
            font = ImageFont.load_default()
        except:
            font = None

        text_color = (
            random.randint(0, 120),
            random.randint(0, 120),
            random.randint(0, 120),
        )
        draw.text((10, 10), text, fill=text_color, font=font)

        # Convert to bytes
        img_byte_arr = io.BytesIO()
        quality = 85 if month_name in ["AUGUST", "JULY"] else 75  # Lower quality for older data
        image.save(img_byte_arr, format="JPEG", quality=quality)
        image_bytes = img_byte_arr.getvalue()

        return RequestImage.create_from_bytes(
            request_log=request_log,
            image_bytes=image_bytes,
            mime_type="image/jpeg",
        )

    def _generate_random_text(self) -> str:
        """Generate random text for results."""
        words = [
            "verified",
            "authenticated",
            "solved",
            "completed",
            "processed",
            "alpha",
            "beta",
            "gamma",
            "delta",
            "epsilon",
            "zeta",
            "eta",
            "theta",
            "success",
            "valid",
            "accepted",
            "confirmed",
            "approved",
            "passed",
            "analyzed",
            "detected",
            "recognized",
            "identified",
            "matched",
        ]
        return " ".join(random.sample(words, k=random.randint(2, 4)))

    def _generate_random_ocr_text(self) -> str:
        """Generate random OCR-like text."""
        templates = [
            f"Invoice #{random.randint(100000, 999999)}",
            f"Order ID: {uuid.uuid4().hex[:12].upper()}",
            f"Reference: {''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=10))}",
            f"Account: {random.randint(1000000, 9999999)}",
            f"Serial: {random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
            f"Document: DOC-{random.randint(100000, 999999)}",
            f"Receipt: RCP{random.randint(100000000, 999999999)}",
        ]
        return random.choice(templates)

    def _generate_pattern_result(self) -> str:
        """Generate pattern-based results."""
        patterns = [
            f"Grid: {random.randint(3, 9)}x{random.randint(3, 9)}",
            f"Sequence: {', '.join([str(random.randint(1, 99)) for _ in range(5)])}",
            f"Pattern: {''.join(random.choices('ABXY', k=8))}",
            f"Matrix: [{random.randint(0, 1)} {random.randint(0, 1)} {random.randint(0, 1)}]",
            f"Shape: {random.choice(['Triangle', 'Square', 'Circle', 'Pentagon', 'Hexagon'])}",
        ]
        return random.choice(patterns)

    def _update_billing_period(
        self,
        billing_period: BillingPeriod,
        is_current: bool,
        payment_status: str,
        year: int,
        month: int,
    ) -> None:
        """Update billing period with calculated totals and status."""
        # Count total requests
        total_requests = RequestLog.objects.filter(billing_period=billing_period).count()

        # Calculate cost (assuming $0.01 per request)
        total_cost_cents = total_requests * 1  # 1 cent per request

        billing_period.total_requests = total_requests
        billing_period.total_cost_cents = total_cost_cents
        billing_period.is_current = is_current

        # Set payment status
        if is_current:
            billing_period.payment_status = "pending"
        else:
            billing_period.payment_status = payment_status

            if payment_status == "paid":
                # Set a random payment date in the following month
                if month == 12:
                    payment_month = 1
                    payment_year = year + 1
                else:
                    payment_month = month + 1
                    payment_year = year

                payment_day = random.randint(1, 15)
                billing_period.paid_at = datetime(
                    payment_year,
                    payment_month,
                    payment_day,
                    random.randint(9, 17),
                    random.randint(0, 59),
                    0,
                    tzinfo=timezone.get_current_timezone(),
                )
                billing_period.paid_amount_cents = total_cost_cents
                billing_period.payment_reference = (
                    f"INV-{year}-{month:02d}-{random.randint(1000, 9999)}"
                )
                billing_period.payment_notes = random.choice(
                    [
                        "Payment received via bank transfer",
                        "Payment received via credit card",
                        "Payment received via wire transfer",
                    ]
                )
            elif payment_status == "overdue":
                days_overdue = (
                    timezone.now().date() - date(year, month + 1 if month < 12 else 1, 1)
                ).days
                billing_period.payment_notes = f"Payment due since {calendar.month_name[month + 1 if month < 12 else 1]} 1, {year}. Overdue by {days_overdue} days"
            elif payment_status == "waived":
                billing_period.payment_notes = random.choice(
                    [
                        "Promotional period - charges waived",
                        "Beta testing period - charges waived",
                        "Special credit applied - charges waived",
                    ]
                )

        billing_period.save()
