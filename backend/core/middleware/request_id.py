import uuid
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse


class RequestIDMiddleware:
    """Middleware to generate and attach a unique request ID to each request."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Generate a unique request ID
        request.request_id = str(uuid.uuid4())  # type: ignore

        # Process the request
        response = self.get_response(request)

        # Add request ID to response headers
        response["X-Request-ID"] = request.request_id  # type: ignore

        return response
