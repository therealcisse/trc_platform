from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import HttpResponse
from rest_framework.request import Request
from rest_framework.response import Response

from core.views import healthz

@ensure_csrf_cookie
def csrf_bootstrap(request: Request) -> Response:
    return HttpResponse(status=204)

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
    path("api/core/", include("core.urls")),
    path("api/usage/", include("usage.urls")),
    path("api/auth/csrf/", csrf_bootstrap),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
