from django.urls import path

from .views import image_performance_stats

urlpatterns = [
    path("image-performance-stats", image_performance_stats, name="image_performance_stats"),
]
