from __future__ import annotations

from django.urls import path
from .views import index_view, session_info, delete_session, extend_session, redis_status, get_session_messages, broadcast_message

urlpatterns = [
    path("", index_view, name="chat-index"),
    path("api/redis/status/", redis_status, name="redis-status"),
    path("api/sessions/<str:session_id>/", session_info, name="session-info"),
    path("api/sessions/<str:session_id>/delete/", delete_session, name="delete-session"),
    path("api/sessions/<str:session_id>/extend/", extend_session, name="extend-session"),
    path("api/sessions/<str:session_id>/messages/", get_session_messages, name="get-session-messages"),
    path("api/broadcast/", broadcast_message, name="broadcast-message"),
]
