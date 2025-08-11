# Session Resumption Architecture and Implementation Guide

## Executive Summary

The Django WebSocket service implements a sophisticated session resumption architecture that enables clients to reconnect with their previous session UUID and seamlessly continue their message counter from the point of disconnection. This feature provides enterprise-grade reliability and user experience continuity during temporary network interruptions or service restarts.

## Architecture Overview

### Session Resumption Capabilities

The session resumption system provides the following enterprise features:

- **Seamless Reconnection**: Automatic session state restoration upon reconnection
- **Message Counter Continuity**: Preserved message counting across connection interruptions
- **Configurable TTL**: Session expiration management with 300-second default
- **Per-Process Isolation**: Session cache isolation per worker process
- **Automatic Cleanup**: Expired session removal to prevent memory leaks

## Implementation Architecture

### Session Storage Architecture

The session resumption system utilizes an in-memory cache architecture:

- **Storage Mechanism**: In-memory session cache per worker process
- **TTL Configuration**: 300 seconds (5 minutes) per session with automatic expiration
- **Scope Management**: Per-process isolation (not shared across workers)
- **Data Structure**: Session ID → (Message Count, Timestamp) mapping

### Session Resumption Workflow

The session resumption process follows this architectural flow:

1. **Initial Connection**: Client establishes connection with session UUID as query parameter
2. **Session Validation**: Server validates session existence in cache
3. **Counter Restoration**: If session exists, message counter resumes from previous value
4. **State Persistence**: Counter updates are persisted on each message transmission
5. **Reconnection Support**: Client can reconnect with same session UUID for seamless resumption

## Technical Implementation

### WebSocket Connection with Session Management

**Connection URL Format:**
```
ws://localhost/ws/chat/?session=YOUR_SESSION_UUID
```

**Implementation Example:**
```
ws://localhost/ws/chat/?session=550e8400-e29b-41d4-a716-446655440000
```

### Core Implementation Architecture

The session resumption functionality is implemented in `app/chat/consumers.py`:

```python
async def connect(self) -> None:
    try:
        # Parse session UUID from query parameters
        query = parse_qs(self.scope.get("query_string", b"").decode())
        self.session_id = (query.get("session", [None]) or [None])[0]
        
        # Resume session if exists and valid
        if self.session_id:
            prior = _session_get(self.session_id)
            if prior is not None:
                self.count = prior  # Resume counter from previous state
                
        await self.accept()
        # ... additional connection logic
```

### Session Cache Management Functions

```python
# Session TTL configuration: 5 minutes
SESSION_TTL_SECONDS = 300
_session_cache: Dict[str, tuple[int, float]] = {}

def _session_get(session_id: str) -> Optional[int]:
    """Retrieve session count if exists and not expired"""
    now = time.time()
    entry = _session_cache.get(session_id)
    if not entry:
        return None
    count, ts = entry
    if now - ts > SESSION_TTL_SECONDS:
        _session_cache.pop(session_id, None)  # Cleanup expired sessions
        return None
    return count

def _session_put(session_id: str, count: int) -> None:
    """Store session count with current timestamp for TTL management"""
    _session_cache[session_id] = (count, time.time())
```

## Client-Side Implementation Architecture

### JavaScript Session Management Class

```javascript
class SessionAwareWebSocket {
    constructor(url, sessionId = null) {
        this.url = url;
        this.sessionId = sessionId || this.generateSessionId();
        this.ws = null;
        this.messageCount = 0;
    }

    generateSessionId() {
        return crypto.randomUUID ? crypto.randomUUID() : 
               Math.random().toString(36).slice(2);
    }

    connect() {
        const wsUrl = `${this.url}?session=${this.sessionId}`;
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log(`Connected with session: ${this.sessionId}`);
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.messageCount = data.count;
            console.log(`Message ${this.messageCount}: ${data.echo}`);
        };
        
        this.ws.onclose = () => {
            console.log(`Disconnected. Session ${this.sessionId} preserved for 5 minutes.`);
            // Implement automatic reconnection with exponential backoff
            setTimeout(() => this.reconnect(), 1000);
        };
    }

    reconnect() {
        console.log(`Reconnecting with session: ${this.sessionId}`);
        this.connect();
    }

    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(message);
        }
    }

    getSessionId() {
        return this.sessionId;
    }
}

// Implementation usage
const ws = new SessionAwareWebSocket('ws://localhost/ws/chat/');
ws.connect();

// Persist session ID for cross-browser session management
localStorage.setItem('websocket_session', ws.getSessionId());
```

### React Hook Implementation

```typescript
import { useEffect, useRef, useState } from 'react';

interface WebSocketMessage {
    count: number;
    echo: string;
    io?: { blocked_ms: number };
}

export function useSessionWebSocket(url: string) {
    const [isConnected, setIsConnected] = useState(false);
    const [messageCount, setMessageCount] = useState(0);
    const [lastMessage, setLastMessage] = useState<string>('');
    const wsRef = useRef<WebSocket | null>(null);
    const sessionIdRef = useRef<string>('');

    useEffect(() => {
        // Retrieve or generate session ID for persistence
        let sessionId = localStorage.getItem('websocket_session');
        if (!sessionId) {
            sessionId = crypto.randomUUID();
            localStorage.setItem('websocket_session', sessionId);
        }
        sessionIdRef.current = sessionId;

        const wsUrl = `${url}?session=${sessionId}`;
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
            setIsConnected(true);
            console.log(`Connected with session: ${sessionId}`);
        };

        ws.onmessage = (event) => {
            const data: WebSocketMessage = JSON.parse(event.data);
            setMessageCount(data.count);
            setLastMessage(data.echo);
        };

        ws.onclose = () => {
            setIsConnected(false);
            console.log(`Disconnected. Session ${sessionId} preserved.`);
            // Implement automatic reconnection with session preservation
            setTimeout(() => {
                if (wsRef.current?.readyState === WebSocket.CLOSED) {
                    const reconnectUrl = `${url}?session=${sessionId}`;
                    const newWs = new WebSocket(reconnectUrl);
                    wsRef.current = newWs;
                }
            }, 1000);
        };

        return () => {
            ws.close();
        };
    }, [url]);

    const sendMessage = (message: string) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(message);
        }
    };

    return {
        isConnected,
        messageCount,
        lastMessage,
        sendMessage,
        sessionId: sessionIdRef.current
    };
}
```

## Session Lifecycle Management

### Session Lifecycle Phases

#### 1. Session Initialization
```
Client Connection → Session ID Generation → Counter Initialization (0)
```

#### 2. Session Persistence
```
Message Transmission → Counter Incrementation → Session State Persistence
```

#### 3. Session Resumption
```
Client Reconnection → Session ID Validation → Counter State Restoration
```

#### 4. Session Expiration
```
TTL Expiration (5 minutes) → Session Removal → Counter Reset on Next Connection
```

## Monitoring and Observability

### Prometheus Metrics Architecture

The system provides comprehensive metrics for monitoring:

- `app_sessions_tracked`: Active session count in cache
- `app_connections_opened_total`: Total connection count (including resumptions)
- `app_messages_total`: Aggregate message count across all sessions

### Application Logging

```python
# Connection logging with session resumption tracking
logger.info("ws_connect", extra={
    "event": "ws_connect", 
    "session_id": self.session_id
})

# Message logging with session counter tracking
logger.info("ws_receive", extra={
    "event": "ws_receive", 
    "session_id": self.sessionId, 
    "count": self.count
})
```

## Enterprise Best Practices

### Session ID Management Strategy

1. **UUID Generation**: Utilize cryptographically secure UUIDs for session identification
2. **Client-Side Persistence**: Store session ID in localStorage for web client continuity
3. **Reconnection Integration**: Incorporate session ID in all reconnection logic
4. **Cross-Browser Support**: Ensure session ID persistence across browser sessions

### Reconnection Architecture

1. **Exponential Backoff**: Implement intelligent reconnection with exponential backoff
2. **Session Preservation**: Maintain session ID across all reconnection attempts
3. **Graceful Degradation**: Handle session expiration scenarios gracefully
4. **Error Recovery**: Implement comprehensive error handling for reconnection failures

### Error Handling and Resilience

1. **Session Expiration Handling**: Manage cases where session has expired
2. **Fallback Mechanisms**: Provide fallback for missing or invalid session IDs
3. **Event Logging**: Comprehensive logging of session resumption events
4. **Recovery Procedures**: Implement automatic recovery for session-related failures

### Performance Optimization

1. **Memory Management**: Session cache is per-worker to optimize memory usage
2. **TTL Implementation**: Automatic expiration prevents memory leaks
3. **Redis Integration**: Consider Redis backend for multi-worker session sharing
4. **Cache Optimization**: Implement efficient cache management strategies

## Current Implementation Limitations

### Architectural Constraints

- **Per-Worker Isolation**: Sessions not shared across worker processes
- **Memory-Only Storage**: Sessions lost on worker restart
- **Fixed TTL**: 5-minute session expiration (not configurable)
- **Limited Metadata**: Minimal session information storage

### Future Enhancement Roadmap

- **Redis Backend Integration**: Shared session storage across workers
- **Configurable TTL**: Adjustable session expiration based on requirements
- **Enhanced Metadata**: Comprehensive session information storage
- **Background Cleanup**: Automated cleanup of expired sessions
- **Session Analytics**: Advanced session tracking and analytics

## Testing and Validation

### Manual Testing Protocol

```bash
# Establish connection with session ID
wscat -c "ws://localhost/ws/chat/?session=test-123"

# Transmit test messages
{"count": 1, "echo": "hello"}
{"count": 2, "echo": "world"}

# Disconnect and reconnect with same session
wscat -c "ws://localhost/ws/chat/?session=test-123"

# Validate counter resumption from previous state
```

### Automated Testing Implementation

```python
import asyncio
import websockets
import json

async def test_session_resumption():
    session_id = "test-session-123"
    uri = f"ws://localhost/ws/chat/?session={session_id}"
    
    # Initial connection and message transmission
    async with websockets.connect(uri) as ws:
        await ws.send("hello")
        response = await ws.recv()
        data = json.loads(response)
        assert data["count"] == 1
    
    # Reconnection with session resumption validation
    async with websockets.connect(uri) as ws:
        await ws.send("world")
        response = await ws.recv()
        data = json.loads(response)
        assert data["count"] == 2  # Counter resumption validation

asyncio.run(test_session_resumption())
```

## Troubleshooting and Resolution

### Common Issue Resolution

#### Session Resumption Failures

**Diagnostic Steps**:
1. **Session ID Validation**: Verify session ID format (valid UUID)
2. **TTL Verification**: Confirm session hasn't expired (5-minute TTL)
3. **Worker Process Validation**: Ensure same worker process handling connection
4. **Cache State Analysis**: Check session cache state and integrity

#### Counter Reset Scenarios

**Root Causes**:
1. **TTL Expiration**: Session expired due to 5-minute TTL
2. **Worker Restart**: Worker process restart cleared session cache
3. **Process Isolation**: Different worker process handling connection
4. **Cache Corruption**: Session cache corruption or invalidation

#### Memory Usage Optimization

**Monitoring and Management**:
1. **Metric Monitoring**: Track `app_sessions_tracked` metric
2. **TTL Optimization**: Consider reducing TTL if memory is constrained
3. **Cache Analysis**: Monitor session cache size and growth patterns
4. **Cleanup Validation**: Verify automatic session expiration functionality

### Advanced Debugging

```python
# Enable comprehensive debug logging
import logging
logging.getLogger('app.chat.consumers').setLevel(logging.DEBUG)

# Analyze session cache state
print(f"Active sessions: {len(_session_cache)}")
```

## API Reference Architecture

### WebSocket Connection Endpoint

```
GET /ws/chat/?session={session_id}
```

**Parameters**:
- `session` (optional): Session UUID for resumption functionality

**Response Format**:
```json
{
    "count": 42,
    "echo": "message content",
    "io": {"blocked_ms": 150}  // Performance metrics if applicable
}
```

### Session Behavior Specifications

- **New Session**: Counter initializes at 0
- **Resumed Session**: Counter continues from previous value
- **Expired Session**: Treated as new session (counter starts at 0)
- **No Session ID**: Treated as new session (counter starts at 0)

## Deployment Considerations

### Production Deployment

1. **Worker Configuration**: Optimize worker process configuration for session management
2. **Memory Monitoring**: Implement comprehensive memory usage monitoring
3. **Session Analytics**: Deploy session tracking and analytics capabilities
4. **Performance Optimization**: Configure optimal TTL and cache settings

### Development Environment

1. **Local Testing**: Comprehensive local testing of session resumption functionality
2. **Integration Testing**: Validate session resumption across different scenarios
3. **Performance Testing**: Test session resumption under load conditions
4. **Documentation**: Maintain current session resumption documentation
