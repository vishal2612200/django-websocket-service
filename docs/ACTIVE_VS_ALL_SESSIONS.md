# Active vs All Sessions - Broadcast Targeting Explained

## 🔍 **Understanding Session Types**

### **1. Active Sessions (Live WebSocket Connections)**
**Definition**: Sessions with currently open WebSocket connections to the server.

**Characteristics**:
- ✅ **Real-time communication**: Can receive instant WebSocket messages
- ✅ **Live connection**: WebSocket is open and connected
- ✅ **In-memory tracking**: Tracked in `_active_sessions` set in the consumer
- ✅ **Immediate delivery**: Broadcast messages delivered instantly via WebSocket

**How they're tracked**:
```python
# In app/chat/consumers.py
_active_sessions: set[str] = set()

def add_active_session(session_id: str) -> None:
    """Add a session to the active sessions list."""
    if session_id:
        _active_sessions.add(session_id)

def remove_active_session(session_id: str) -> None:
    """Remove a session from the active sessions list."""
    if session_id:
        _active_sessions.discard(session_id)

def get_active_sessions() -> set[str]:
    """Get the set of active sessions."""
    return _active_sessions.copy()
```

**When they're added/removed**:
- **Added**: When WebSocket connects (`connect()` method)
- **Removed**: When WebSocket disconnects (`disconnect()` method)

### **2. All Sessions (Redis Persistence)**
**Definition**: All sessions that exist in Redis, regardless of connection status.

**Characteristics**:
- 📦 **Data persistence**: Session data stored in Redis
- 📦 **Message history**: Messages stored for later retrieval
- 📦 **Session continuity**: Survives server restarts and reconnections
- 📦 **Delayed delivery**: Messages stored for when user reconnects

**Types of Redis sessions**:
```python
# Session data keys
session:abc123           # Session metadata (count, timestamps, etc.)

# Message list keys  
session:abc123:messages  # List of messages for this session
```

## 🎯 **Broadcast Targeting Strategy**

### **Current Implementation**
```python
# Get active sessions from WebSocket consumers (sessions with live connections)
from app.chat.consumers import get_active_sessions
active_session_ids = get_active_sessions()

# Also get sessions from Redis for persistence (fallback)
# ... Redis key discovery logic ...

# Prioritize active WebSocket sessions, but include all Redis sessions for persistence
target_sessions = active_session_ids.union(all_redis_sessions)
```

### **Why This Approach?**

#### **1. Immediate Delivery to Active Sessions**
- Active sessions receive broadcast instantly via WebSocket
- Real-time notification to connected users
- No delay or polling required

#### **2. Persistence for All Sessions**
- All sessions (active + inactive) get messages stored in Redis
- Inactive sessions can retrieve messages when they reconnect
- Ensures no messages are lost

#### **3. Hybrid Strategy Benefits**
- **Best of both worlds**: Immediate + persistent delivery
- **Graceful degradation**: Works even if WebSocket tracking fails
- **Future-proof**: Messages available for reconnecting users

## 📊 **Session Lifecycle and Broadcast Impact**

### **Session States**

```
1. Session Created (WebSocket connects)
   ├── Added to _active_sessions
   ├── Joins "broadcast" group
   └── Can receive real-time broadcasts

2. Session Active (User sending/receiving messages)
   ├── Remains in _active_sessions
   ├── Messages stored in Redis
   └── Receives all broadcasts immediately

3. Session Inactive (WebSocket disconnects)
   ├── Removed from _active_sessions
   ├── Leaves "broadcast" group
   ├── Session data remains in Redis
   └── Can still receive persistent broadcasts

4. Session Reconnected (WebSocket reconnects)
   ├── Re-added to _active_sessions
   ├── Re-joins "broadcast" group
   ├── Can retrieve missed messages from Redis
   └── Receives future broadcasts immediately
```

### **Broadcast Delivery Matrix**

| Session State | WebSocket Broadcast | Redis Storage | User Experience |
|---------------|-------------------|---------------|-----------------|
| **Active** | ✅ Immediate | ✅ Persistent | Instant notification |
| **Inactive** | ❌ No connection | ✅ Persistent | Message on reconnect |
| **Reconnecting** | ✅ Immediate | ✅ Historical | Instant + missed messages |

## 🔧 **Implementation Details**

### **WebSocket Broadcast (Real-time)**
```python
# In ChatConsumer.server_broadcast()
async def server_broadcast(self, event: Dict[str, Any]) -> None:
    """Handle broadcast messages from server."""
    try:
        # Send broadcast message to client
        await self.send(text_data=json.dumps({
            "type": "broadcast",
            "message": event["message"],
            "timestamp": event.get("timestamp", int(time.time() * 1000)),
            "level": event.get("level", "info"),
            "title": event.get("title", "System Message")
        }))
        MESSAGES_SENT.inc()
    except Exception as e:
        logger.error(f"Failed to send broadcast message: {e}")
```

### **Redis Storage (Persistent)**
```python
# In broadcast API/command
for session_id in target_sessions:
    messages_key = f"session:{session_id}:messages"
    
    # Store broadcast message for this session in shared Redis
    await message_client.rpush(messages_key, json.dumps(message_data))
    
    # Set TTL on the messages list
    await message_client.expire(messages_key, default_ttl)
```

## 🧪 **Testing and Verification**

### **Debug Script**
Use `scripts/debug_broadcast_sessions.py` to understand session coverage:

```bash
python scripts/debug_broadcast_sessions.py
```

**Expected Output**:
```
🔍 Debugging Broadcast Session Coverage
==================================================

📊 Active WebSocket Connections:
   Active connections: 3

📊 Redis Session Counts:
   Total session data keys: 5
   Total message list keys: 4
   Unique session IDs (data): 5
   Unique session IDs (messages): 4
   Combined unique sessions: 5

📡 Broadcast Coverage Test:
   Broadcast successful: 5 sessions updated

📊 Coverage Analysis:
   Active WebSocket connections: 3
   Sessions targeted by broadcast: 5
   ⚠️  Broadcast targeted 5 sessions but only 3 are actively connected
   💡 This means some sessions exist in Redis but have no live WebSocket connection
```

### **Manual Testing**

#### **1. Test Active Sessions**
```bash
# Open multiple browser tabs with WebSocket connections
# Send broadcast
curl -X POST http://localhost:8000/chat/api/broadcast/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Test active sessions", "title": "Test", "level": "info"}'
```

#### **2. Test Inactive Sessions**
```bash
# Close browser tabs (sessions become inactive)
# Send broadcast
python app/manage.py broadcast_message "Test inactive sessions" --title "Test" --level warning
# Reopen browser tabs - should see stored messages
```

## 🎯 **Key Takeaways**

### **Active Sessions**
- **Definition**: Live WebSocket connections
- **Tracking**: In-memory `_active_sessions` set
- **Broadcast**: Immediate WebSocket delivery
- **Count**: Available via `app_active_connections` metric

### **All Sessions**
- **Definition**: All sessions in Redis (active + inactive)
- **Tracking**: Redis keys (`session:*` and `session:*:messages`)
- **Broadcast**: Persistent storage for later retrieval
- **Count**: Available via Redis key counting

### **Broadcast Strategy**
- **Primary**: Target active sessions for immediate delivery
- **Secondary**: Include all Redis sessions for persistence
- **Result**: Complete coverage with both immediate and persistent delivery

### **Why Single Session Issue Occurred**
The original issue where broadcast only reached one session was likely due to:
1. **Limited active connections**: Only one WebSocket connection was open
2. **Redis-only targeting**: Only targeting sessions with existing message lists
3. **Missing session discovery**: Not finding all active sessions properly

The fix ensures comprehensive coverage by:
1. **Using active session tracking**: Prioritizing live WebSocket connections
2. **Including all Redis sessions**: Ensuring persistence for all sessions
3. **Better session discovery**: Finding both active and stored sessions

This approach guarantees that broadcasts reach all intended recipients, whether they're currently connected or will reconnect later.
