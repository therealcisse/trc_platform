from datetime import timedelta

from django.db import models
from django.db.models import Avg, Count, Sum
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .models import RequestImage, RequestLog


@api_view(["GET"])
@permission_classes([IsAdminUser])
def image_performance_stats(request):
    """Get performance statistics for saved images."""

    # Get requests with saved images
    requests_with_images = RequestLog.objects.filter(saved_image__isnull=False).select_related(
        "saved_image"
    )

    # Overall statistics
    stats = requests_with_images.aggregate(
        total_requests=Count("id"),
        avg_duration_ms=Avg("duration_ms"),
        avg_image_size=Avg("saved_image__file_size"),
        total_storage_bytes=Sum("saved_image__file_size"),
        success_rate=(
            Avg(Count("id", filter=models.Q(status="success")) * 100.0 / Count("id"))
            if requests_with_images.exists()
            else 0
        ),
    )

    # Calculate success/error counts
    success_count = requests_with_images.filter(status="success").count()
    error_count = requests_with_images.filter(status="error").count()

    # Group by image dimensions (top 10 most common)
    dimension_stats = (
        requests_with_images.values("saved_image__width", "saved_image__height")
        .annotate(
            count=Count("id"),
            avg_duration=Avg("duration_ms"),
            avg_size=Avg("saved_image__file_size"),
            error_rate=Count("id", filter=models.Q(status="error")) * 100.0 / Count("id"),
        )
        .order_by("-count")[:10]
    )

    # Format dimension stats
    formatted_dimensions = []
    for dim in dimension_stats:
        width = dim["saved_image__width"]
        height = dim["saved_image__height"]
        formatted_dimensions.append(
            {
                "dimensions": f"{width}x{height}" if width and height else "Unknown",
                "count": dim["count"],
                "avg_duration_ms": round(dim["avg_duration"], 2) if dim["avg_duration"] else 0,
                "avg_size_kb": round(dim["avg_size"] / 1024, 2) if dim["avg_size"] else 0,
                "error_rate": round(dim["error_rate"], 2),
            }
        )

    # Group by MIME type
    mime_type_stats = (
        RequestImage.objects.values("mime_type")
        .annotate(count=Count("id"), total_size=Sum("file_size"), avg_size=Avg("file_size"))
        .order_by("-count")
    )

    # Recent performance trends (last 7 days)
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_stats = (
        requests_with_images.filter(request_ts__gte=seven_days_ago)
        .extra(select={"day": "date(request_ts)"})
        .values("day")
        .annotate(
            count=Count("id"),
            avg_duration=Avg("duration_ms"),
            error_count=Count("id", filter=models.Q(status="error")),
        )
        .order_by("day")
    )

    return Response(
        {
            "overall_stats": {
                "total_requests": stats["total_requests"] or 0,
                "success_count": success_count,
                "error_count": error_count,
                "avg_duration_ms": (
                    round(stats["avg_duration_ms"], 2) if stats["avg_duration_ms"] else 0
                ),
                "avg_image_size_kb": (
                    round(stats["avg_image_size"] / 1024, 2) if stats["avg_image_size"] else 0
                ),
                "total_storage_mb": round((stats["total_storage_bytes"] or 0) / (1024 * 1024), 2),
                "success_rate": round(
                    (
                        (success_count / (success_count + error_count) * 100)
                        if (success_count + error_count) > 0
                        else 0
                    ),
                    2,
                ),
            },
            "by_dimensions": formatted_dimensions,
            "by_mime_type": [
                {
                    "mime_type": m["mime_type"],
                    "count": m["count"],
                    "total_size_mb": round(m["total_size"] / (1024 * 1024), 2),
                    "avg_size_kb": round(m["avg_size"] / 1024, 2),
                }
                for m in mime_type_stats
            ],
            "recent_trends": list(recent_stats),
        }
    )
