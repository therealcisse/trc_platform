from django.db import transaction
from django.contrib.auth import get_user_model
from usage.models import RequestLog
from usage.utils import get_or_create_current_billing_period
from django.db.models import F
import time
import logging

User = get_user_model()

logger = logging.getLogger(__name__)


def log_request(p) -> None:
    with transaction.atomic():
        # app_settings = Settings.get_settings()
        start_db = time.time()
        user = User.objects.get(id=p["user_id"])
        bp = get_or_create_current_billing_period(user)
        RequestLog.objects.create(
            user=user,
            token_id=p["token_id"],
            billing_period=bp,
            flow_id=p["flow_id"],
            service="core.image_solve",
            duration_ms=p["duration_ms"],
            request_bytes=p["request_len"],
            response_bytes=p["response_len"],
            status=p["status"],
            error_code=p["error_code"],
            request_id=p["request_id"],
            result=None,  # see note below
        )
        bp.total_requests = F("total_requests") + 1
        bp.total_cost_cents = F("total_cost_cents") + p["cost_cents"]
        bp.save(update_fields=["total_requests", "total_cost_cents"])

        # Skip image saving in critical path
        # This can be done asynchronously or conditionally
        # if app_settings.save_request_images and self._should_save_image(
        #         image_bytes, app_settings
        #         ):
        #     self._schedule_image_save(request_log.id, image_bytes)

        db_ms = int((time.time() - start_db) * 1000)
        logger.debug(f"DB transaction ms for {p['request_id']}: {db_ms}")
