"""
Simple health check endpoint for shipping readiness.
"""
from django.http import JsonResponse


def health_view(request):
    """Return 200 OK with minimal JSON payload."""
    return JsonResponse({"status": "ok"})
