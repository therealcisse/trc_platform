from typing import Any

from django.http import HttpRequest
from rest_framework.response import Response
from rest_framework.views import exception_handler


def problem_json_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """
    Custom exception handler that returns RFC7807 problem+json responses.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    if response is not None:
        # Get request for additional context
        request: HttpRequest = context.get("request")  # type: ignore

        # Build problem+json response
        problem_detail = {
            "type": "about:blank",
            "status": response.status_code,
            "title": _get_error_title(response.status_code),
            "detail": _get_error_detail(response.data),
        }

        # Add instance (request ID) if available
        if hasattr(request, "request_id"):
            problem_detail["instance"] = f"/requests/{request.request_id}"

        # Add error code if available
        if hasattr(exc, "default_code"):
            problem_detail["code"] = exc.default_code  # type: ignore
        elif isinstance(response.data, dict) and "code" in response.data:
            problem_detail["code"] = response.data["code"]

        # Add validation errors if present
        if response.status_code == 400 and isinstance(response.data, dict):
            errors = {}
            for field, value in response.data.items():
                if field not in ["detail", "code"]:
                    if isinstance(value, list):
                        errors[field] = value[0] if value else "Invalid value"
                    else:
                        errors[field] = str(value)
            if errors:
                problem_detail["errors"] = errors

        response.data = problem_detail
        response["Content-Type"] = "application/problem+json"

    return response


def _get_error_title(status_code: int) -> str:
    """Get a human-readable title for the status code."""
    titles = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        409: "Conflict",
        422: "Unprocessable Entity",
        429: "Too Many Requests",
        500: "Internal Server Error",
        502: "Bad Gateway",
        503: "Service Unavailable",
    }
    return titles.get(status_code, "Error")


def _get_error_detail(data: Any) -> str:
    """Extract error detail from response data."""
    if isinstance(data, dict):
        if "detail" in data:
            return str(data["detail"])
        elif "message" in data:
            return str(data["message"])
        elif "error" in data:
            return str(data["error"])
        else:
            # Try to get first error message
            for key, value in data.items():
                if key not in ["code", "status"]:
                    if isinstance(value, list) and value:
                        return str(value[0])
                    elif isinstance(value, str):
                        return value
    elif isinstance(data, list) and data:
        return str(data[0])
    elif isinstance(data, str):
        return data

    return "An error occurred"
