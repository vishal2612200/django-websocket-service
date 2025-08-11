# Heartbeat Functionality

## Overview

The Django WebSocket service implements a robust heartbeat mechanism that broadcasts a heartbeat message every 30 seconds to all active WebSocket connections. This ensures connection health monitoring, enables automatic reconnection, and provides real-time visibility into system connectivity. The heartbeat system is designed to detect connection failures quickly while minimizing false positives.

## Implementation Details

### Server-Side Heartbeat

**Location**: `app/asgi.py`

The heartbeat is implemented at the ASGI level using Django Channels to ensure reliable delivery to all active connections:

```python
async def publish_heartbeat_forever() -> None:
    channel_layer = get_channel_layer()
    while not shutdown_event.is_set():
        try:
            ts = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            await channel_layer.group_send(
                "broadcast",
                {"type": "server.heartbeat", "payload": {"ts": ts}},
            )
        except Exception:
            pass
        await asyncio.sleep(30)  # 30-second interval
```

**Key Features**:
- **30-second interval** - exactly as specified for optimal balance between responsiveness and overhead
- **ISO timestamp format** - `{"ts": "2024-01-15T10:30:00+00:00"}` for precise timing
- **Broadcast to all active sockets** - uses Django Channels group messaging for efficient delivery
- **Graceful shutdown handling** - stops heartbeat during shutdown to prevent resource leaks
- **Error handling** - continues heartbeat even if individual sends fail to maintain system stability

### Consumer Handling

**Location**: `app/chat/consumers.py`

Each WebSocket consumer handles heartbeat messages with proper error handling and metrics collection:

```python
async def server_heartbeat(self, event: Dict[str, Any]) -> None:
    try:
        await self.send(text_data=json.dumps(event["payload"]))
    except Exception:
        ERRORS_TOTAL.inc()
```

## UI Enhancements

### HeartbeatMonitor Component

**Location**: `ui/src/components/HeartbeatMonitor.tsx`

A dedicated component that provides comprehensive heartbeat visualization and monitoring capabilities:

#### Features:
- **Real-time heartbeat tracking** with latency calculations for performance monitoring
- **Health status indicators** (Healthy/Warning/Error) with clear visual feedback
- **Progress bar** showing time until next expected heartbeat for user awareness
- **Statistics dashboard** with average latency and total heartbeats for trend analysis
- **Timeline view** of recent heartbeats with age indicators for historical analysis
- **Connection status** with last heartbeat timestamp for immediate status assessment

#### Usage:
```tsx
<HeartbeatMonitor
  heartbeats={heartbeats}
  lastHeartbeatAt={lastHeartbeatAt}
  status={status}
  onRefresh={reconnect}
/>
```

### Enhanced SessionCard

**Location**: `ui/src/components/SessionCard.tsx`

The SessionCard now includes tabbed interface with dedicated heartbeat monitoring for comprehensive session management:

#### Features:
- **Tab navigation** between Chat and Heartbeat views for organized interface
- **Integrated heartbeat monitor** in dedicated tab for focused monitoring
- **Visual pulse animation** when heartbeats are received for immediate feedback
- **Real-time status indicators** with color coding for quick status assessment

### GlobalHeartbeatDashboard Component

**Location**: `ui/src/components/GlobalHeartbeatDashboard.tsx`

System-wide heartbeat monitoring across all sessions for comprehensive system health assessment:

#### Features:
- **Aggregate statistics** across all active sessions for system-wide insights
- **Global health status** with overall system health assessment
- **Session health overview** with individual session status for detailed monitoring
- **Missed heartbeat tracking** across all connections for failure detection
- **Real-time progress indicators** for next expected heartbeats for proactive monitoring

## Technical Architecture

### Heartbeat Message Format

The heartbeat message follows a standardized format to ensure consistency and enable proper parsing:

```json
{
  "ts": "2024-01-15T10:30:00+00:00"
}
```

**Message Properties**:
- `ts`: ISO 8601 timestamp in UTC with timezone offset
- Format: `YYYY-MM-DDTHH:MM:SS±HH:MM`
- Example: `2024-01-15T10:30:00+00:00`

### Client-Side Processing

**Location**: `ui/src/hooks/useWebSocket.ts`

The WebSocket hook processes heartbeat messages and maintains connection state:

```typescript
const handleMessage = useCallback((event: MessageEvent) => {
  try {
    const data = JSON.parse(event.data);
    
    if (data.ts) {
      // Heartbeat message received
      const heartbeatTime = new Date(data.ts);
      const latency = Date.now() - heartbeatTime.getTime();
      
      setHeartbeats(prev => [...prev.slice(-9), { timestamp: heartbeatTime, latency }]);
      setLastHeartbeatAt(heartbeatTime);
      setStatus('connected');
    } else {
      // Regular message processing
      setMessages(prev => [...prev, data]);
    }
  } catch (error) {
    console.error('Error processing message:', error);
  }
}, []);
```

### Health Status Calculation

The system calculates health status based on heartbeat timing and latency:

```typescript
const calculateStatus = (lastHeartbeat: Date | null): 'connected' | 'warning' | 'error' => {
  if (!lastHeartbeat) return 'error';
  
  const timeSinceLastHeartbeat = Date.now() - lastHeartbeat.getTime();
  const thirtySeconds = 30 * 1000;
  
  if (timeSinceLastHeartbeat > thirtySeconds * 2) {
    return 'error';
  } else if (timeSinceLastHeartbeat > thirtySeconds) {
    return 'warning';
  }
  
  return 'connected';
};
```

## Performance Considerations

### Latency Monitoring

The heartbeat system provides valuable latency metrics for performance monitoring:

```typescript
const calculateAverageLatency = (heartbeats: Heartbeat[]): number => {
  if (heartbeats.length === 0) return 0;
  
  const totalLatency = heartbeats.reduce((sum, hb) => sum + hb.latency, 0);
  return totalLatency / heartbeats.length;
};
```

### Connection Quality Assessment

Heartbeat data enables connection quality assessment and troubleshooting:

```typescript
const assessConnectionQuality = (heartbeats: Heartbeat[]): ConnectionQuality => {
  if (heartbeats.length < 3) return 'unknown';
  
  const recentHeartbeats = heartbeats.slice(-3);
  const avgLatency = calculateAverageLatency(recentHeartbeats);
  const latencyVariance = calculateLatencyVariance(recentHeartbeats);
  
  if (avgLatency < 50 && latencyVariance < 20) {
    return 'excellent';
  } else if (avgLatency < 100 && latencyVariance < 50) {
    return 'good';
  } else if (avgLatency < 200) {
    return 'fair';
  } else {
    return 'poor';
  }
};
```

## Monitoring and Alerting

### Heartbeat Metrics

The system collects comprehensive metrics for monitoring and alerting:

```python
# Heartbeat-specific metrics
HEARTBEATS_SENT = Counter('app_heartbeats_sent_total', 'Total heartbeats sent')
HEARTBEATS_RECEIVED = Counter('app_heartbeats_received_total', 'Total heartbeats received')
HEARTBEAT_LATENCY = Histogram('app_heartbeat_latency_seconds', 'Heartbeat latency')
MISSED_HEARTBEATS = Counter('app_missed_heartbeats_total', 'Total missed heartbeats')
```

### Alert Rules

Prometheus alert rules for heartbeat monitoring:

```yaml
- alert: HighHeartbeatLatency
  expr: histogram_quantile(0.95, rate(app_heartbeat_latency_seconds_bucket[5m])) > 0.5
  for: 2m
  labels:
    severity: warning
  annotations:
    summary: "High heartbeat latency detected"
    description: "95th percentile heartbeat latency is {{ $value }}s"

- alert: MissedHeartbeats
  expr: rate(app_missed_heartbeats_total[5m]) > 0
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Heartbeats are being missed"
    description: "{{ $value }} missed heartbeats per second"
```

## Troubleshooting

### Common Issues

1. **High Latency**: Network congestion or server overload
   - Monitor network metrics and server resources
   - Check for background processes consuming CPU
   - Verify Redis connection pool health

2. **Missed Heartbeats**: Connection instability or server issues
   - Check WebSocket connection status
   - Verify Redis channel layer connectivity
   - Monitor server error logs

3. **Inconsistent Timing**: Clock synchronization issues
   - Ensure all servers use NTP for time synchronization
   - Verify timezone configuration
   - Check for system clock drift

### Debugging Tools

**Heartbeat Logging**:
```python
import logging

logger = logging.getLogger('websocket.heartbeat')

async def publish_heartbeat_forever() -> None:
    channel_layer = get_channel_layer()
    while not shutdown_event.is_set():
        try:
            ts = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            logger.debug(f"Broadcasting heartbeat: {ts}")
            await channel_layer.group_send(
                "broadcast",
                {"type": "server.heartbeat", "payload": {"ts": ts}},
            )
        except Exception as e:
            logger.error(f"Heartbeat broadcast failed: {e}")
        await asyncio.sleep(30)
```

**Client-Side Debugging**:
```typescript
const debugHeartbeat = (heartbeat: Heartbeat) => {
  console.log('Heartbeat received:', {
    timestamp: heartbeat.timestamp,
    latency: heartbeat.latency,
    age: Date.now() - heartbeat.timestamp.getTime()
  });
};
```

## Future Enhancements

### Adaptive Heartbeat Intervals

Consider implementing adaptive heartbeat intervals based on connection quality:

```python
async def adaptive_heartbeat_interval() -> int:
    """Calculate adaptive heartbeat interval based on connection quality"""
    avg_latency = get_average_latency()
    error_rate = get_error_rate()
    
    if error_rate > 0.1 or avg_latency > 1000:
        return 15  # More frequent heartbeats for poor connections
    elif avg_latency > 500:
        return 20  # Moderate frequency for fair connections
    else:
        return 30  # Standard frequency for good connections
```

### Heartbeat Compression

For high-volume scenarios, consider implementing heartbeat compression:

```python
import gzip
import json

async def send_compressed_heartbeat():
    heartbeat_data = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    compressed = gzip.compress(json.dumps(heartbeat_data).encode())
    await channel_layer.group_send(
        "broadcast",
        {"type": "server.heartbeat.compressed", "payload": compressed}
    )
```

This heartbeat functionality provides a robust foundation for connection health monitoring, enabling proactive issue detection and ensuring reliable WebSocket communication across the application.
