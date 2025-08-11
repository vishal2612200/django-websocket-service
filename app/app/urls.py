from __future__ import annotations

from django.urls import include, path
from django.views.static import serve as static_serve
from django.conf import settings
from pathlib import Path
from app.chat import views as chat_views
from .metrics import metrics_view
from .health import healthz_view, readyz_view

urlpatterns = [
    path("", chat_views.index_view, name="index"),
    path("metrics", metrics_view, name="metrics"),
    path("healthz", healthz_view, name="healthz"),
    path("readyz", readyz_view, name="readyz"),
    path("chat/", include("app.chat.urls")),
    path("static/<path:path>", static_serve, {"document_root": settings.STATIC_ROOT}),
    path(
        "assets/<path:path>",
        static_serve,
        {"document_root": Path(settings.STATIC_ROOT) / "assets"},
    ),
    path(
        "favicon.svg",
        static_serve,
        {"document_root": settings.STATIC_ROOT, "path": "favicon.svg"},
    ),
]
