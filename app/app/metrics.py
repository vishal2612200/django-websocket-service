from __future__ import annotations

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from django.http import HttpResponse

# Message metrics
MESSAGES_TOTAL = Counter("app_messages_total", "Total messages received from clients over websockets")
MESSAGES_SENT = Counter("app_messages_sent", "Total messages sent by server to clients over websockets")

# Connection metrics
ACTIVE_CONNECTIONS = Gauge("app_active_connections", "Number of active websocket connections")

# Error metrics
ERRORS_TOTAL = Counter("app_errors_total", "Total application errors")

# Performance metrics
SHUTDOWN_HISTOGRAM = Histogram(
    "app_shutdown_duration_seconds", "Duration of graceful shutdown in seconds"
)

# Product-oriented connection/session analytics
CONNECTIONS_OPENED_TOTAL = Counter(
    "app_connections_opened_total", "Total websocket connections opened"
)
CONNECTIONS_CLOSED_TOTAL = Counter(
    "app_connections_closed_total", "Total websocket connections closed"
)
SESSIONS_TRACKED = Gauge(
    "app_sessions_tracked", "Number of sessions tracked in server memory (TTL-bound)"
)
CONNECTION_MESSAGES = Histogram(
    "app_connection_messages", "Messages handled per connection"
)


def metrics_view(_request):
    data = generate_latest()
    return HttpResponse(data, content_type=CONTENT_TYPE_LATEST)
