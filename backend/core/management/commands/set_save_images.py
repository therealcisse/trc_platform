from typing import Any

from django.core.cache import cache
from django.core.management.base import BaseCommand, CommandError

from core.models import Settings


class Command(BaseCommand):
    help = "Enable, disable, or configure saving request images"

    def add_arguments(self, parser: Any) -> None:
        group = parser.add_mutually_exclusive_group(required=False)
        group.add_argument("--on", action="store_true", help="Enable saving request images")
        group.add_argument("--off", action="store_true", help="Disable saving request images")
        parser.add_argument("--max-size-mb", type=int, help="Set maximum saved image size in MB")
        parser.add_argument(
            "--retention-days", type=int, help="Set image retention period in days"
        )
        parser.add_argument(
            "--show",
            action="store_true",
            help="Show current values. If no other flags are supplied, show is implied.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        show: bool = bool(options.get("show"))
        turn_on: bool = bool(options.get("on"))
        turn_off: bool = bool(options.get("off"))
        max_size: int | None = options.get("max_size_mb")
        retention: int | None = options.get("retention_days")

        s = Settings.get_settings()

        # If no updates requested, show current values
        if show or not (turn_on or turn_off or max_size is not None or retention is not None):
            self.stdout.write(self._status(s))
            return

        if turn_on and turn_off:
            raise CommandError("Specify only one of --on or --off")

        updates: list[str] = []

        if turn_on:
            s.save_request_images = True
            updates.append("save_request_images")
        if turn_off:
            s.save_request_images = False
            updates.append("save_request_images")
        if max_size is not None:
            if max_size <= 0:
                raise CommandError("--max-size-mb must be positive")
            s.max_saved_image_size_mb = max_size
            updates.append("max_saved_image_size_mb")
        if retention is not None:
            if retention <= 0:
                raise CommandError("--retention-days must be positive")
            s.image_retention_days = retention
            updates.append("image_retention_days")

        # Always update timestamp
        updates.append("updated_at")
        s.save(update_fields=list(set(updates)))

        # Invalidate CachedSettings cache so API sees changes immediately
        cache.delete("app_settings")

        self.stdout.write(self._status(s))

    def _status(self, s: Settings) -> str:
        state = "ON" if s.save_request_images else "OFF"
        return (
            f"save_request_images: {state}\n"
            f"max_saved_image_size_mb: {s.max_saved_image_size_mb}\n"
            f"image_retention_days: {s.image_retention_days}"
        )
