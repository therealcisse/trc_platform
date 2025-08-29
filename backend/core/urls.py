"""
Core app URL configuration.
Using optimized views with caching and deferred operations.
"""

from django.urls import path

from .views import SolveView, healthz

urlpatterns = [
    path("solve", SolveView.as_view(), name="solve"),
    path("health", healthz, name="health"),
]
