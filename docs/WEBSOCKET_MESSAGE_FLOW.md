# WebSocket Message Flow: Complete Architecture Guide

## 📋 Overview

This document provides a comprehensive explanation of how messages flow between the user interface and server through WebSocket connections in the Django WebSocket application. It covers the complete lifecycle from user input to server response and back.

## 🎯 Message Flow Architecture

```
User Types Message → UI Component → WebSocket Hook → WebSocket Connection → Django Consumer → Response Back
```

## 🔄 Complete Message Flow Example

### Scenario: User sends "Hello World" message

---

## 1. 🖥️ User Interface (UI Layer)

### A. User Types Message

```typescript
// In SessionCard.tsx - User types in TextField
<TextField 
  value={text} 
  onChange={(e) => setText(e.target.value)}  // text = "Hello World"
  placeholder="Type your message…" 
/>
```

### B. User Clicks Send Button

```typescript
// In SessionCard.tsx - Send button click handler
<Button 
  onClick={() => { 
    if (text.trim()) { 
      send(text);  // Calls send("Hello World")
      setText('')  // Clears input field
    } 
  }}
>
  Send
</Button>
```

---

## 2. 🔌 WebSocket Hook (useWebSocket.ts)

### A. Send Function Executes

```typescript
// In useWebSocket.ts
function send(text: string) {
  if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
    // 1. Send message through WebSocket
    wsRef.current.send(text)  // Sends "Hello World" to server
    
    // 2. Update UI immediately (optimistic update)
    const now = Date.now()
    const messageId = `${now}-${text.slice(0, 10)}`
    
    setMessages((m: DisplayMessage[]) => {
      const sentMessage: DisplayMessage = { 
        content: text,           // "Hello World"
        isSent: true,           // User sent this
        timestamp: now,         // 1703123456789
        id: messageId           // "1703123456789-Hello Worl"
      }
      return [...m, sentMessage].slice(-100)
    })
    
    // 3. Persist message locally
    persistMessage(text, true)
  }
}
```

### B. WebSocket Connection State

```typescript
// WebSocket connection details
const url = "ws://localhost:8000/ws/chat/?session=abc123&redis_persistence=true"
const ws = new WebSocket(url)  // Connection established
```

---

## 3. 🌐 Network Layer (WebSocket Protocol)

### A. WebSocket Frame Sent

```
WebSocket Frame:
├── Opcode: 1 (text frame)
├── Payload: "Hello World"
├── Length: 11 bytes
└── Destination: ws://localhost:8000/ws/chat/
```

### B. HTTP Upgrade (Initial Connection)

```http
GET /ws/chat/?session=abc123&redis_persistence=true HTTP/1.1
Host: localhost:8000
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13
```

---

## 4. 🐍 Django Server (Backend Layer)

### A. WebSocket Connection Established

```python
# In consumers.py - Connection handler
async def connect(self) -> None:
    # Parse session ID from URL
    query = parse_qs(self.scope.get("query_string", b"").decode())
    self.session_id = query.get("session", [None])[0]  # "abc123"
    
    # Load existing session data
    if self.session_id:
        redis_data = await redis_manager.get_session(self.session_id)
        if redis_data:
            self.count = redis_data["count"]  # Resume from 5
    
    # Accept WebSocket connection
    await self.accept()
    
    # Join broadcast group
    await self.channel_layer.group_add("broadcast", self.channel_name)
    
    # Update metrics
    ACTIVE_CONNECTIONS.inc()  # Active connections: 1
```

### B. Message Received by Consumer

```python
# In consumers.py - Message handler
async def receive(self, text_data: str | bytes | None = None) -> None:
    # 1. Increment message counter
    self.count += 1  # count: 5 → 6
    
    # 2. Update metrics
    MESSAGES_TOTAL.inc()  # Total messages: 100 → 101
    
    # 3. Parse message content
    echo = text_data  # "Hello World"
    
    # 4. Prepare response
    payload = {
        "count": self.count,  # 6
        "echo": echo         # "Hello World"
    }
    
    # 5. Send response back to client
    await self.send(text_data=json.dumps(payload))
    MESSAGES_SENT.inc()  # Messages sent: 100 → 101
    
    # 6. Store message in Redis (if persistence enabled)
    if self.session_id and self.use_redis_persistence:
        message_data = {
            "content": echo,                    # "Hello World"
            "timestamp": int(time.time() * 1000), # 1703123456789
            "isSent": True,                     # User sent this
            "sessionId": self.session_id        # "abc123"
        }
        await redis_manager.store_message(self.session_id, message_data)
    
    # 7. Update session state
    session_data = {
        "count": self.count,      # 6
        "last_activity": time.time()  # 1703123456.789
    }
    await redis_manager.update_session(self.session_id, session_data)
```

---

## 5. 🔄 Response Back to Client

### A. Server Sends Response

```python
# Server sends JSON response
await self.send(text_data=json.dumps({
    "count": 6,
    "echo": "Hello World"
}))
```

### B. WebSocket Frame Received

```
WebSocket Frame:
├── Opcode: 1 (text frame)
├── Payload: '{"count": 6, "echo": "Hello World"}'
├── Length: 35 bytes
└── Source: ws://localhost:8000/ws/chat/
```

---

## 6. 🖥️ Client Receives Response

### A. WebSocket Message Handler

```typescript
// In useWebSocket.ts - Message received
ws.onmessage = (ev) => {
  const data = JSON.parse(ev.data)
  
  if (typeof data.count === 'number') {
    // Extract message content
    const messageContent = data.echo || `Server Message #${data.count}`
    const now = Date.now()
    const messageId = `${now}-${messageContent.slice(0, 10)}`
    
    // Add server response to messages
    setMessages((m: DisplayMessage[]) => {
      const receivedMessage: DisplayMessage = { 
        content: messageContent,  // "Hello World"
        isSent: false,           // Server sent this
        timestamp: now,          // 1703123456789
        id: messageId            // "1703123456789-Hello Worl"
      }
      return [...m, receivedMessage].slice(-100)
    })
    
    // Update message count
    setCount(data.count)  // 6
    
    // Persist message
    persistMessage(messageContent, false)
  }
}
```

---

## 7. 📊 Final State

### A. UI Display

```typescript
// Messages array now contains:
[
  {
    content: "Hello World",
    isSent: true,      // User sent
    timestamp: 1703123456789,
    id: "1703123456789-Hello Worl"
  },
  {
    content: "Hello World", 
    isSent: false,     // Server echoed back
    timestamp: 1703123456790,
    id: "1703123456790-Hello Worl"
  }
]
```

### B. Server State

```python
# Session data in Redis:
{
  "session_id": "abc123",
  "count": 6,
  "last_activity": 1703123456.789,
  "messages": [
    {
      "content": "Hello World",
      "timestamp": 1703123456789,
      "isSent": True,
      "sessionId": "abc123"
    }
  ]
}
```

### C. Metrics Updated

```python
# Prometheus metrics:
app_active_connections: 1
app_messages_total: 101      # Messages received from clients
app_messages_sent: 101       # Messages sent to clients
app_connections_opened_total: 10
```

---

## 🔄 Connection Lifecycle

### Connection Establishment

```typescript
// 1. Client creates WebSocket
const ws = new WebSocket("ws://localhost:8000/ws/chat/?session=abc123")

// 2. Connection opens
ws.onopen = () => {
  setStatus('open')  // UI shows "Connected"
}

// 3. Server accepts connection
await self.accept()  # Django accepts WebSocket
```

### Message Exchange

```typescript
// 4. Client sends message
ws.send("Hello World")

// 5. Server processes and responds
await self.send(json.dumps({"count": 6, "echo": "Hello World"}))

// 6. Client receives response
ws.onmessage = (ev) => {
  const data = JSON.parse(ev.data)
  // Update UI with response
}
```

### Connection Closure

```typescript
// 7. Client closes connection
ws.close()

// 8. Server handles disconnect
async def disconnect(self, close_code: int):
    ACTIVE_CONNECTIONS.dec()  # Decrease active count
    # Store final session state
    await redis_manager.update_session(self.session_id, session_data)
```

---

## 🎯 Key Interconnections

### 1. Session ID Links Everything

- **URL**: `ws://localhost:8000/ws/chat/?session=abc123`
- **Server**: `self.session_id = "abc123"`
- **Redis**: `session:abc123` key stores all data
- **UI**: Session card displays messages for this session

### 2. WebSocket Connection State

- **Connection**: One WebSocket per session
- **Messages**: All messages flow through this connection
- **Persistence**: Session survives connection drops
- **Reconnection**: Same session ID = same data

### 3. Message Flow

- **User Input** → **WebSocket Send** → **Server Process** → **WebSocket Response** → **UI Update**

### 4. Data Persistence

- **Redis**: Stores messages and session state
- **localStorage**: Fallback for client-side persistence
- **Session Continuity**: Data survives reconnections

---

## 🏗️ Component Architecture

### Frontend Components

#### SessionCard.tsx
- **Purpose**: Main UI component for each WebSocket session
- **Features**: Message input, display, connection status
- **Props**: Session ID, persistence settings, auto-reconnect

#### useWebSocket.ts
- **Purpose**: Custom React hook for WebSocket management
- **Features**: Connection handling, message sending/receiving, persistence
- **State**: Connection status, messages, heartbeats

### Backend Components

#### ChatConsumer (consumers.py)
- **Purpose**: Django Channels WebSocket consumer
- **Features**: Message processing, session management, metrics tracking
- **Methods**: `connect()`, `receive()`, `disconnect()`

#### RedisSessionManager (redis_session.py)
- **Purpose**: Session and message persistence
- **Features**: Redis storage, TTL management, cross-instance sharing
- **Methods**: `store_message()`, `get_session()`, `update_session()`

---

## 📡 Message Types

### 1. User Messages
```typescript
// Sent by user
{
  content: "Hello World",
  isSent: true,
  timestamp: 1703123456789
}
```

### 2. Server Responses
```json
// Sent by server
{
  "count": 6,
  "echo": "Hello World"
}
```

### 3. Heartbeat Messages
```json
// Server heartbeat
{
  "ts": "1703123456789"
}
```

### 4. Broadcast Messages
```json
// Server broadcast
{
  "type": "broadcast",
  "message": "System maintenance in 5 minutes",
  "title": "System Alert",
  "level": "warning",
  "timestamp": 1703123456789
}
```

### 5. Shutdown Messages
```json
// Server shutdown
{
  "bye": true,
  "total": 6,
  "message": "Server is shutting down gracefully"
}
```

---

## 🔧 Configuration

### WebSocket URL Format
```
ws://localhost:8000/ws/chat/?session={session_id}&redis_persistence={true|false}
```

### Environment Variables
```bash
# Redis configuration
CHANNEL_REDIS_URL=redis://localhost:6379/0
MESSAGE_REDIS_URL=redis://localhost:6379/1
REDIS_SESSION_TTL=3600

# Metrics polling
METRICS_POLLING_INTERVAL=30000
```

### Session Persistence Types
1. **localStorage**: Client-side persistence only
2. **redis**: Server-side persistence with Redis
3. **none**: No persistence

---

## 🚀 Performance Considerations

### Message Optimization
- **Duplicate Detection**: Prevents duplicate messages in UI
- **Message Limits**: Keeps last 100 messages in memory
- **Optimistic Updates**: UI updates immediately, then syncs with server

### Connection Management
- **Auto-reconnect**: Automatic reconnection with exponential backoff
- **Connection Pooling**: Efficient WebSocket connection reuse
- **Graceful Shutdown**: Proper cleanup on connection close

### Data Persistence
- **TTL Management**: Automatic cleanup of old session data
- **Cross-Instance Sharing**: Redis enables multi-instance deployments
- **Fallback Mechanisms**: Graceful degradation when Redis unavailable

---

## 🐛 Troubleshooting

### Common Issues

#### Connection Problems
```typescript
// Check WebSocket state
if (wsRef.current?.readyState === WebSocket.OPEN) {
  // Connection is open
} else {
  // Connection is closed or connecting
}
```

#### Message Not Received
```python
# Check server logs
logger.info("ws_receive", extra={
    "event": "ws_receive", 
    "session_id": self.session_id, 
    "count": self.count
})
```

#### Session Data Missing
```python
# Verify Redis connection
redis_data = await redis_manager.get_session(session_id)
if redis_data is None:
    logger.warning(f"Session {session_id} not found in Redis")
```

### Debug Mode
```typescript
// Enable debug logging
localStorage.setItem('debug', 'websocket:*')
console.log('WebSocket URL:', url)
console.log('Connection status:', status)
```

---

## 📚 Related Documentation

- [API Documentation](./API.md) - Complete API reference
- [Session Resumption](./SESSION_RESUMPTION.md) - Session management details
- [Redis Persistence](./REDIS_PERSISTENCE.md) - Data persistence architecture
- [Metrics Dashboard](./METRICS_DASHBOARD.md) - Monitoring and observability
- [Deployment Guide](./DEPLOYMENT.md) - Production deployment instructions

---

## 🎯 Summary

This WebSocket message flow architecture provides:

✅ **Real-time Communication**: Instant message delivery between client and server  
✅ **Session Persistence**: Data survives connection drops and server restarts  
✅ **Scalable Design**: Supports multiple instances and high concurrency  
✅ **Reliable Delivery**: Proper error handling and reconnection logic  
✅ **Observability**: Comprehensive metrics and monitoring  
✅ **User Experience**: Seamless messaging with optimistic updates  

The architecture ensures that every message flows seamlessly from the UI through the WebSocket connection to the server and back, with proper session management and data persistence throughout the entire lifecycle.
