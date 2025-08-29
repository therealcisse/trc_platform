from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.urls import include, path
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.request import Request

from core.views import healthz


@ensure_csrf_cookie
def csrf_bootstrap(request: Request) -> JsonResponse:
    """Return CSRF token in response body for cross-origin requests."""
    token = get_token(request)
    response = JsonResponse({"csrfToken": token})
    # Allow frontend to read the response
    response["Access-Control-Allow-Origin"] = (
        settings.CORS_ALLOWED_ORIGINS[0] if settings.CORS_ALLOWED_ORIGINS else "*"
    )
    response["Access-Control-Allow-Credentials"] = "true"
    return response


urlpatterns = [
    # Health check
    path("healthz", healthz, name="healthz"),
    # Admin
    path("admin/", admin.site.urls),
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # API endpoints
    path("api/customers/", include("customers.urls")),
    path("api/core/", include("core.urls")),  # Using optimized implementation
    path("api/usage/", include("usage.urls")),
    path("api/auth/csrf/", csrf_bootstrap),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
