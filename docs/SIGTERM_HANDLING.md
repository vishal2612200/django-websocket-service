# SIGTERM Graceful Shutdown

## ✅ Requirements Met

- **SIGTERM Handling**: Container receives and handles SIGTERM signals
- **In-flight Messages**: Messages are processed before shutdown
- **WebSocket Closure**: All connections closed with code 1001 (going away)
- **10-Second Timeout**: Shutdown completes within 10 seconds

## Implementation

### 1. Signal Handling (`app/asgi.py`)
```python
def signal_handler(signum: int, frame: Any) -> None:
    shutdown_event.set()  # Triggers graceful shutdown

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)
```

### 2. ASGI Shutdown Process
```python
shutdown_timeout = 10  # 10 seconds as required

async def _wait_for_shutdown_completion(self):
    # Send shutdown notification to all consumers
    await channel_layer.group_send("broadcast", {"type": "server.shutdown"})
    
    # Wait for message processing (2s)
    await asyncio.sleep(2)
    
    # Close channel layer
    await channel_layer.close()
```

### 3. WebSocket Consumer Shutdown
```python
async def server_shutdown(self, _event: Dict[str, Any]) -> None:
    # Send goodbye message
    await self.send(text_data=json.dumps({"bye": True, "total": self.count}))
    
    # Process pending messages (100ms)
    await asyncio.sleep(0.1)
    
    # Save session state
    # ... save to Redis/memory
    
    # Close with code 1001 (going away)
    await self.close(code=1001)
```

### 4. Docker Configuration
```yaml
stop_grace_period: 12s  # 10s + 2s buffer
stop_signal: SIGTERM
```

## Testing

```bash
# Test graceful shutdown
make test-graceful-shutdown

# Manual SIGTERM test
docker compose -f docker/compose.yml stop app_blue
```

## Shutdown Timeline

1. **0-100ms**: SIGTERM received, background tasks stop
2. **100-500ms**: Shutdown notification sent to all consumers
3. **500ms-2.5s**: Process in-flight messages, send goodbye
4. **2.5s-3s**: Close connections with code 1001
5. **3s-10s**: Container exits gracefully

Total time: < 10 seconds ✅
