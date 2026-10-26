# ==============================================================================
# FILE: backend/core/exceptions.py
# PURPOSE: Global custom REST Framework exception handler and error response envelope.
# VIVA EXPLANATION: Normalizes all application errors into a predictable JSON schema ({ error: { code, message, details } }) and suppresses sensitive database stack traces in production.
# ==============================================================================

import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    NotFound,
    MethodNotAllowed,
    ValidationError,
)
from django.http import Http404
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied

logger = logging.getLogger(__name__)


# --- custom_exception_handler ---
# What it does: Catches all DRF and Django exceptions, mapping them to standard error codes and sanitized messages.
# Why it's structured this way: Enforces API consistency across all endpoints and prevents sensitive stack traces from leaking to clients.
# Parameters & Returns: Takes (exc, context); returns DRF Response object containing structured error JSON.
# ------------------------------------------------------------------------------
def custom_exception_handler(exc, context):
    """
    Standardized MediCare exception handler.
    Ensures all API errors follow the schema:
    {
        "error": {
            "code": "ERROR_CODE",
            "message": "Human-readable message",
            "details": {}
        }
    }
    Prevents leaking internal stack traces in production.
    """
    response = exception_handler(exc, context)

    # Determine error code and default message
    if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
        code = "AUTHENTICATION_FAILED"
        message = "Authentication credentials were not provided or are invalid."
    elif isinstance(exc, (PermissionDenied, DjangoPermissionDenied)):
        code = "PERMISSION_DENIED"
        message = "You do not have permission to perform this action or access this resource."
    elif isinstance(exc, (NotFound, Http404)):
        code = "NOT_FOUND"
        message = "The requested resource was not found."
    elif isinstance(exc, ValidationError):
        code = "VALIDATION_ERROR"
        message = "Invalid input data provided."
    elif isinstance(exc, MethodNotAllowed):
        code = "METHOD_NOT_ALLOWED"
        message = f"Method '{context['request'].method}' not allowed."
    elif isinstance(exc, APIException):
        code = getattr(exc, "default_code", "API_ERROR").upper()
        message = str(exc.detail) if hasattr(exc, "detail") else "An API error occurred."
    else:
        # Unhandled internal server error
        logger.exception("Unhandled exception in API request: %s", exc)
        return Response(
            {
                "error": {
                    "code": "SERVER_ERROR",
                    "message": "An unexpected server error occurred. Please try again later.",
                    "details": {},
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Structure the error details safely
    details = {}
    if response is not None and isinstance(response.data, dict):
        if "detail" in response.data:
            message = str(response.data["detail"])
            details = {k: v for k, v in response.data.items() if k != "detail"}
        else:
            details = response.data
    elif response is not None and isinstance(response.data, list):
        details = {"errors": response.data}
        if len(response.data) > 0:
            message = str(response.data[0])

    custom_data = {
        "error": {
            "code": code,
            "message": message,
            "details": details,
        }
    }

    if response is not None:
        response.data = custom_data
        return response

    return Response(custom_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
