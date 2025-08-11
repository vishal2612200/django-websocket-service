from __future__ import annotations

import asyncio
import json
import time
import logging
from typing import Any, ClassVar, Dict, Optional

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from urllib.parse import parse_qs
from asgiref.sync import sync_to_async

from app.metrics import (
    MESSAGES_TOTAL,
    MESSAGES_SENT,
    ACTIVE_CONNECTIONS,
    ERRORS_TOTAL,
    CONNECTIONS_OPENED_TOTAL,
    CONNECTIONS_CLOSED_TOTAL,
    SESSIONS_TRACKED,
    CONNECTION_MESSAGES,
)
from .redis_session import get_redis_session_manager
# Track active sessions for individual heartbeats
_active_sessions: set[str] = set()

def add_active_session(session_id: str) -> None:
    """Add a session to the active sessions list."""
    if session_id:
        _active_sessions.add(session_id)
        # Update sessions tracked metric
        try:
            SESSIONS_TRACKED.set(len(_active_sessions))
        except Exception:
            pass

def remove_active_session(session_id: str) -> None:
    """Remove a session from the active sessions list."""
    if session_id:
        _active_sessions.discard(session_id)
        # Update sessions tracked metric
        try:
            SESSIONS_TRACKED.set(len(_active_sessions))
        except Exception:
            pass

def get_active_sessions() -> set[str]:
    """Get the set of active sessions."""
    return _active_sessions.copy()


logger = logging.getLogger(__name__)

# Simple in-memory session cache with TTL (per-process)
SESSION_TTL_SECONDS = 300
_session_cache: Dict[str, tuple[int, float]] = {}


def _session_get(session_id: str) -> Optional[int]:
    now = time.time()
    entry = _session_cache.get(session_id)
    if not entry:
        return None
    count, ts = entry
    if now - ts > SESSION_TTL_SECONDS:
        _session_cache.pop(session_id, None)
        return None
    return count


def _session_put(session_id: str, count: int) -> None:
    _session_cache[session_id] = (count, time.time())


def simulate_blocking_io(duration_ms: int) -> Dict[str, int]:
    """Simulate a short blocking I/O call.

    This function blocks the calling thread using time.sleep. In async
    contexts, it must be offloaded to the thread pool using sync_to_async
    to avoid blocking the event loop.
    """
    time.sleep(max(0, duration_ms) / 1000.0)
    return {"blocked_ms": max(0, duration_ms)}


class ChatConsumer(AsyncWebsocketConsumer):
    group_name: ClassVar[str] = "broadcast"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.count: int = 0
        self.session_id: Optional[str] = None
        self.use_redis_persistence: bool = False

    async def connect(self) -> None:
        try:
            query = parse_qs(self.scope.get("query_string", b"").decode())
            self.session_id = (query.get("session", [None]) or [None])[0]
            self.use_redis_persistence = query.get("redis_persistence", ["false"])[0].lower() == "true"
            
            if self.session_id:
                if self.use_redis_persistence:
                    # Try to load from Redis first
                    redis_manager = get_redis_session_manager()
                    redis_data = await redis_manager.get_session(self.session_id)
                    if redis_data and "count" in redis_data:
                        self.count = redis_data["count"]
                        logger.info(f"Session loaded from Redis: {self.session_id}, count: {self.count}")
                    else:
                        # Fallback to in-memory cache
                        prior = _session_get(self.session_id)
                        if prior is not None:
                            self.count = prior
                else:
                    # Use in-memory cache only
                    prior = _session_get(self.session_id)
                    if prior is not None:
                        self.count = prior
            await self.accept()
            
            # Join broadcast group for general messages
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            
            # Join individual heartbeat group for this session
            if self.session_id:
                heartbeat_group = f"heartbeat_{self.session_id}"
                await self.channel_layer.group_add(heartbeat_group, self.channel_name)
                # Add to active sessions for heartbeat tracking
                add_active_session(self.session_id)
            
            ACTIVE_CONNECTIONS.inc()
            CONNECTIONS_OPENED_TOTAL.inc()
            # Update sessions tracked based on active sessions
            try:
                SESSIONS_TRACKED.set(len(_active_sessions))
            except Exception:
                pass
            logger.info("ws_connect", extra={"event": "ws_connect", "session_id": self.session_id})
        except Exception:
            ERRORS_TOTAL.inc()
            raise

    async def receive(self, text_data: str | bytes | None = None, bytes_data: bytes | None = None) -> None:
        try:
            self.count += 1
            MESSAGES_TOTAL.inc()
            echo: Optional[str] = None
            io_result: Optional[Dict[str, int]] = None
            if isinstance(text_data, str):
                echo = text_data
            elif isinstance(text_data, (bytes, bytearray)):
                try:
                    echo = text_data.decode("utf-8", errors="ignore")
                except Exception:
                    echo = None
            elif isinstance(bytes_data, (bytes, bytearray)):
                try:
                    echo = bytes_data.decode("utf-8", errors="ignore")
                except Exception:
                    echo = None
            # Demonstrate offloading of blocking work to the thread pool.
            # If the client sends a message like "block:150", we will simulate
            # a 150ms blocking I/O operation using sync_to_async to avoid
            # blocking the event loop.
            if isinstance(echo, str) and echo.startswith("block:"):
                try:
                    _, raw_ms = echo.split(":", 1)
                    duration_ms = int(raw_ms)
                except Exception:
                    duration_ms = 100
                io_result = await sync_to_async(
                    simulate_blocking_io,
                    thread_sensitive=False,
                )(duration_ms)

            # Send response with count and echo
            payload: Dict[str, Any] = {"count": self.count}
            if echo:
                payload["echo"] = echo
            await self.send(text_data=json.dumps(payload))
            MESSAGES_SENT.inc()
            
            # Store message in Redis if persistence is enabled
            if self.session_id and self.use_redis_persistence and echo:
                try:
                    redis_manager = get_redis_session_manager()
                    
                    # Store only the user message (not the server response)
                    message_data = {
                        "content": echo,
                        "timestamp": int(time.time() * 1000),  # milliseconds
                        "isSent": True,  # This was sent by the user
                        "sessionId": self.session_id
                    }
                    
                    await redis_manager.store_message(self.session_id, message_data)
                    
                    logger.info(f"User message stored in shared Redis for session {self.session_id}: {echo}")
                except Exception as e:
                    logger.error(f"Failed to store message in shared Redis for session {self.session_id}: {e}")
            
            if self.session_id:
                if self.use_redis_persistence:
                    # Store in Redis with TTL
                    redis_manager = get_redis_session_manager()
                    session_data = {
                        "count": self.count,
                        "last_activity": time.time()
                    }
                    await redis_manager.update_session(self.session_id, session_data)
                else:
                    # Use in-memory cache
                    _session_put(self.session_id, self.count)
            logger.info(
                "ws_receive",
                extra={"event": "ws_receive", "session_id": self.session_id, "count": self.count},
            )
        except Exception:
            ERRORS_TOTAL.inc()
            raise

    async def disconnect(self, close_code: int) -> None:
        try:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            
            # Leave individual heartbeat group
            if self.session_id:
                heartbeat_group = f"heartbeat_{self.session_id}"
                await self.channel_layer.group_discard(heartbeat_group, self.channel_name)
                # Remove from active sessions
                remove_active_session(self.session_id)
            
            ACTIVE_CONNECTIONS.dec()
            CONNECTIONS_CLOSED_TOTAL.inc()
            # Best-effort notify (cannot send after close if client initiated)
            try:
                await self.send(text_data=json.dumps({"bye": True, "total": self.count}))
                MESSAGES_SENT.inc()
            except Exception:
                pass
            logger.info(
                "ws_disconnect",
                extra={"event": "ws_disconnect", "session_id": self.session_id, "total": self.count},
            )
        finally:
            if self.session_id:
                if self.use_redis_persistence:
                    # Store final state in Redis
                    redis_manager = get_redis_session_manager()
                    session_data = {
                        "count": self.count,
                        "last_activity": time.time(),
                        "disconnected_at": time.time()
                    }
                    await redis_manager.update_session(self.session_id, session_data)
                else:
                    # Use in-memory cache
                    _session_put(self.session_id, self.count)
            # Observe per-connection message volume
            try:
                CONNECTION_MESSAGES.observe(self.count)
            except Exception:
                pass
            # Update sessions tracked based on active sessions
            try:
                SESSIONS_TRACKED.set(len(_active_sessions))
            except Exception:
                pass

    # Server-driven events
    async def server_heartbeat(self, event: Dict[str, Any]) -> None:
        try:
            await self.send(text_data=json.dumps(event["payload"]))
            MESSAGES_SENT.inc()
        except Exception:
            ERRORS_TOTAL.inc()

    async def server_broadcast(self, event: Dict[str, Any]) -> None:
        """Handle broadcast messages from server (e.g., deployment notifications)."""
        try:
            # Send broadcast message to client
            await self.send(text_data=json.dumps({
                "type": "broadcast",
                "message": event["message"],
                "timestamp": event.get("timestamp", int(time.time() * 1000)),
                "level": event.get("level", "info"),  # info, warning, error, success
                "title": event.get("title", "System Message")
            }))
            MESSAGES_SENT.inc()
            
            # Send notification to client that new messages are available in Redis
            await self.send(text_data=json.dumps({
                "type": "new_messages_available",
                "sessionId": self.session_id,
                "timestamp": int(time.time() * 1000),
                "source": "broadcast"
            }))
            
            # Note: Broadcast messages are stored in Redis by the API endpoint
            # to avoid duplication, we don't store them here in the WebSocket consumer
        except Exception as e:
            logger.error(f"Failed to send broadcast message: {e}")
            ERRORS_TOTAL.inc()

    async def server_shutdown(self, _event: Dict[str, Any]) -> None:
        """Handle graceful shutdown - finish in-flight messages and close with code 1001."""
        logger.info("ws_shutdown_started", extra={
            "event": "ws_shutdown_started", 
            "session_id": self.session_id,
            "count": self.count
        })
        
        # Step 1: Send goodbye message to client
        try:
            await self.send(text_data=json.dumps({
                "bye": True, 
                "total": self.count,
                "message": "Server is shutting down gracefully"
            }))
            MESSAGES_SENT.inc()
            logger.info("ws_shutdown_bye_sent", extra={
                "event": "ws_shutdown_bye_sent", 
                "session_id": self.session_id
            })
        except Exception as e:
            logger.warning("ws_shutdown_bye_failed", extra={
                "event": "ws_shutdown_bye_failed", 
                "session_id": self.session_id,
                "error": str(e)
            })
        
        # Step 2: Ensure any pending messages are processed
        # This gives time for any in-flight messages to be sent
        await asyncio.sleep(0.1)  # 100ms to process any pending messages
        
        # Step 3: Save final session state
        if self.session_id:
            try:
                if self.use_redis_persistence:
                    # Store final state in Redis
                    redis_manager = get_redis_session_manager()
                    session_data = {
                        "count": self.count,
                        "last_activity": time.time(),
                        "disconnected_at": time.time(),
                        "shutdown_reason": "graceful_shutdown"
                    }
                    await redis_manager.update_session(self.session_id, session_data)
                else:
                    # Use in-memory cache
                    _session_put(self.session_id, self.count)
                
                logger.info("ws_shutdown_session_saved", extra={
                    "event": "ws_shutdown_session_saved", 
                    "session_id": self.session_id
                })
            except Exception as e:
                logger.error("ws_shutdown_session_save_failed", extra={
                    "event": "ws_shutdown_session_save_failed", 
                    "session_id": self.session_id,
                    "error": str(e)
                })
        
        # Step 4: Close connection with code 1001 (going away)
        try:
            await self.close(code=1001)
            logger.info("ws_shutdown_completed", extra={
                "event": "ws_shutdown_completed", 
                "session_id": self.session_id
            })
        except Exception as e:
            logger.error("ws_shutdown_close_failed", extra={
                "event": "ws_shutdown_close_failed", 
                "session_id": self.session_id,
                "error": str(e)
            })

    async def server_new_messages_available(self, event: Dict[str, Any]) -> None:
        """Notify client that new messages are available in Redis."""
        try:
            await self.send(text_data=json.dumps({
                "type": "new_messages_available",
                "sessionId": self.session_id,
                "timestamp": event.get("timestamp", int(time.time() * 1000)),
                "source": event.get("source", "server")
            }))
            MESSAGES_SENT.inc()
        except Exception as e:
            logger.error(f"Failed to send new messages notification: {e}")
            ERRORS_TOTAL.inc()
