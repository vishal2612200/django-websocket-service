from __future__ import annotations

from dataclasses import dataclass
from django.http import HttpResponse, JsonResponse

# Pre-computed responses for faster health checks
HEALTH_RESPONSE = JsonResponse({"ok": True})
READY_RESPONSE = JsonResponse({"ready": True})
NOT_READY_RESPONSE = JsonResponse({"ready": False}, status=503)


@dataclass
class Readiness:
    ready: bool = False

    def set_ready(self, value: bool) -> None:
        self.ready = value


readiness = Readiness()


def healthz_view(_request):
    """Optimized health check - always returns cached response"""
    return HEALTH_RESPONSE


def readyz_view(_request):
    """Optimized readiness check - returns cached response based on state"""
    return READY_RESPONSE if readiness.ready else NOT_READY_RESPONSE
