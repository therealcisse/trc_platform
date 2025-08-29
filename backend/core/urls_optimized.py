"""
Optimized URL configuration for core app.
These URLs use the optimized views with caching and deferred operations.
"""

from django.urls import path

from .views_optimized import OptimizedSolveView, optimized_healthz

urlpatterns = [
    path("solve", OptimizedSolveView.as_view(), name="solve"),
    path("health", optimized_healthz, name="health"),
]
