from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from usage.models import RequestImage


class Command(BaseCommand):
    help = "Clean up old saved images based on retention policy"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=settings.IMAGE_RETENTION_DAYS,
            help="Number of days to retain images (default: from settings)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )

    def handle(self, *args, **options):
        days = options["days"]
        dry_run = options["dry_run"]

        cutoff_date = timezone.now() - timedelta(days=days)
        old_images = RequestImage.objects.filter(created_at__lt=cutoff_date)
        count = old_images.count()

        if count == 0:
            self.stdout.write(
                self.style.SUCCESS(f"No images older than {days} days found. Nothing to delete.")
            )
            return

        # Calculate total size of images to be deleted
        total_size = sum(img.file_size for img in old_images)
        size_mb = total_size / (1024 * 1024)

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"DRY RUN: Would delete {count} images older than {days} days "
                    f"(total size: {size_mb:.2f} MB)"
                )
            )
            # Show sample of images that would be deleted
            sample_images = old_images[:5]
            if sample_images:
                self.stdout.write("\nSample of images to be deleted:")
                for img in sample_images:
                    self.stdout.write(
                        f"  - Request {img.request_log.request_id} "
                        f"from {img.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                if count > 5:
                    self.stdout.write(f"  ... and {count - 5} more")
        else:
            old_images.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully deleted {count} old images "
                    f"(freed {size_mb:.2f} MB of storage)"
                )
            )
