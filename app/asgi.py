from __future__ import annotations

import asyncio
import os
import signal
import time
from typing import Any, Awaitable, Callable, Dict

from channels.layers import get_channel_layer
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from app.health import readiness
from app.metrics import SHUTDOWN_HISTOGRAM
from app.chat.routing import websocket_urlpatterns

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

# Defer Django ASGI app creation for faster startup
django_asgi_app = None

heartbeat_task: asyncio.Task | None = None
shutdown_event = asyncio.Event()
shutdown_timeout = 4  # 4 seconds timeout for aggressive shutdown

# Defer import for faster startup
def get_django_asgi_app():
    global django_asgi_app
    if django_asgi_app is None:
        django_asgi_app = get_asgi_application()
    return django_asgi_app

from app.chat.consumers import get_active_sessions


async def publish_heartbeat_forever() -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    while not shutdown_event.is_set():
        try:
            ts = str(int(time.time() * 1000))  # Current time in milliseconds
            
            # Send individual heartbeats to each active session
            active_sessions = get_active_sessions()
            for session_id in list(active_sessions):
                try:
                    heartbeat_group = f"heartbeat_{session_id}"
                    await channel_layer.group_send(
                        heartbeat_group,
                        {"type": "server.heartbeat", "payload": {"ts": ts}},
                    )
                except Exception:
                    # Session will be removed on next disconnect
                    pass
                    
        except Exception:
            # Let logging in consumer increment error counter if needed.
            pass
        try:
            await asyncio.sleep(30)  # Wait for 30 seconds
        except Exception:
            # If sleep is interrupted, continue the loop
            continue


def signal_handler(signum: int, frame: Any) -> None:
    """Handle SIGTERM signal to initiate graceful shutdown."""
    print(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_event.set()


class LifespanApp:
    def __init__(
        self, app: Callable[[Dict[str, Any], Callable, Callable], Awaitable[Any]]
    ):
        self.app = app
        # Register signal handlers
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    async def __call__(self, scope: Dict[str, Any], receive: Callable, send: Callable) -> Any:
        global heartbeat_task
        if scope["type"] == "lifespan":
            while True:
                message = await receive()
                if message["type"] == "lifespan.startup":
                    readiness.set_ready(False)
                    # Set ready immediately for faster health check response
                    readiness.set_ready(True)
                    await send({"type": "lifespan.startup.complete"})
                    # Start heartbeat in background after startup complete (non-blocking)
                    if heartbeat_task is None or heartbeat_task.done():
                        heartbeat_task = asyncio.create_task(publish_heartbeat_forever())
                elif message["type"] == "lifespan.shutdown":
                    readiness.set_ready(False)
                    start = time.perf_counter()
                    
                    # Set shutdown event to stop heartbeat
                    shutdown_event.set()
                    
                    # Ask all consumers to shutdown gracefully
                    channel_layer = get_channel_layer()
                    if channel_layer is not None:
                        await channel_layer.group_send(
                            "broadcast", {"type": "server.shutdown"}
                        )
                    
                    # Wait for graceful shutdown with timeout
                    try:
                        await asyncio.wait_for(
                            self._wait_for_shutdown_completion(),
                            timeout=shutdown_timeout
                        )
                    except asyncio.TimeoutError:
                        print(f"Shutdown timeout ({shutdown_timeout}s) reached, forcing exit")
                    
                    # Cancel heartbeat task immediately
                    if heartbeat_task is not None:
                        heartbeat_task.cancel()
                        try:
                            await asyncio.wait_for(heartbeat_task, timeout=1.0)
                        except asyncio.TimeoutError:
                            pass
                    
                    duration = time.perf_counter() - start
                    SHUTDOWN_HISTOGRAM.observe(duration)
                    await send({"type": "lifespan.shutdown.complete"})
                    return
        else:
            return await self.app(scope, receive, send)
    
    async def _wait_for_shutdown_completion(self) -> None:
        """Wait for all WebSocket connections to close gracefully."""
        print("Starting graceful shutdown process...")
        
        # Step 1: Send shutdown notification to all consumers
        channel_layer = get_channel_layer()
        if channel_layer is not None:
            try:
                await channel_layer.group_send(
                    "broadcast", {"type": "server.shutdown"}
                )
                print("Shutdown notification sent to all consumers")
            except Exception as e:
                print(f"Error sending shutdown notification: {e}")
        
        # Step 2: Wait for consumers to process shutdown and close connections
        # This gives time for in-flight messages to be processed
        await asyncio.sleep(2)  # Allow 2 seconds for message processing
        
        # Step 3: Close channel layer
        if channel_layer is not None:
            try:
                await channel_layer.close()
                print("Channel layer closed")
            except Exception as e:
                print(f"Error closing channel layer: {e}")
        
        # Step 4: Final cleanup
        await asyncio.sleep(0.5)  # Small delay for final cleanup
        print("Graceful shutdown process completed")


# Create a wrapper for the Django ASGI app to handle deferred initialization
class DjangoASGIWrapper:
    def __init__(self):
        self._app = None
    
    async def __call__(self, scope, receive, send):
        if self._app is None:
            self._app = get_django_asgi_app()
        return await self._app(scope, receive, send)


# Optimized application creation with deferred Django initialization
def create_application():
    return LifespanApp(
        ProtocolTypeRouter(
            {
                "http": DjangoASGIWrapper(),
                "websocket": URLRouter(websocket_urlpatterns),
            }
        )
    )

application = create_application()


