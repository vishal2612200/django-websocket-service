# Reconnect Button Functionality

## Overview

The Django WebSocket Chat UI includes a comprehensive reconnect button system that allows users to manually reconnect WebSocket sessions and provides automatic reconnection with exponential backoff. This ensures reliable real-time communication even when network issues occur.

## Reconnect Button Location

### UI Component: SessionCard
The reconnect button is located in each individual session card:

```
┌─────────────────────────────────────┐
│ WebSocket Session        [🔄] [❌] │  ← Reconnect button (RefreshIcon)
│ Real-time messaging connection       │
│                                     │
│ [session-id] ● open                 │
│                                     │
│ Send Message                         │
│ [Input field] [Send] [Clear]        │
│                                     │
│ Message History                      │
│ [Message list]                       │
└─────────────────────────────────────┘
```

## Reconnect Button Features

### 1. Manual Reconnect Button
- **Icon**: RefreshIcon (🔄)
- **Tooltip**: "Reconnect"
- **Action**: Immediately closes current connection and triggers reconnection
- **Styling**: Hover effects with color changes

### 2. Auto-Reconnect Toggle
- **Location**: Main UI settings panel
- **Default**: Enabled (true)
- **Behavior**: Automatically reconnects on connection loss
- **Storage**: Persisted in localStorage

### 3. Visual Status Indicators
- **Connection Status**: Color-coded indicators (green=open, yellow=connecting, red=closed)
- **Pulse Animation**: Heartbeat indicators
- **Retry Timer**: Shows next retry attempt time

## How the Reconnect Button Works

### 1. User Interaction Flow
```
User clicks reconnect button (RefreshIcon)
    ↓
useWebSocket hook calls reconnect() function
    ↓
reconnect() closes current WebSocket connection
    ↓
useEffect detects connection close
    ↓
If autoReconnect=true, automatically reconnects
    ↓
New WebSocket connection established
    ↓
Session resumption if session ID provided
    ↓
UI updates with new connection status
```

### 2. Implementation Details

**UI Component (SessionCard.tsx):**
```tsx
<Tooltip title="Reconnect">
  <IconButton 
    size="small" 
    onClick={() => reconnect()}
    sx={{
      borderRadius: 2,
      width: 32,
      height: 32,
      color: 'text.secondary',
      '&:hover': {
        bgcolor: 'action.hover',
        color: 'primary.main',
      }
    }}
  >
    <RefreshIcon fontSize="small" />
  </IconButton>
</Tooltip>
```

**Hook Implementation (useWebSocket.ts):**
```tsx
function reconnect() {
  try { 
    wsRef.current?.close() 
  } catch {}
}

// Auto-reconnect logic
ws.onclose = () => {
  setStatus('closed')
  if (!cancelled && autoReconnect) {
    const wait = Math.min(backoffRef.current, 10000)
    setTimeout(connect, wait)
    backoffRef.current = Math.min(wait * 2, 10000)
    setNextRetryMs(wait)
  }
}
```

## Reconnection Strategies

### 1. Manual Reconnect
- **Trigger**: User clicks reconnect button
- **Behavior**: Immediate reconnection attempt
- **Use Case**: When user wants to force reconnection

### 2. Automatic Reconnect
- **Trigger**: Connection loss detection
- **Behavior**: Exponential backoff retry
- **Backoff**: 500ms → 1s → 2s → 4s → 8s → 10s (max)
- **Use Case**: Network interruptions, server restarts

### 3. Session Resumption
- **Trigger**: Reconnection with session ID
- **Behavior**: Counter continues from previous value
- **TTL**: 5 minutes session persistence
- **Use Case**: Maintaining conversation state

## Connection Status Tracking

### Status Types
```tsx
export type ConnectionStatus = 'connecting' | 'open' | 'closed'
```

### Visual Indicators
- **🟢 Open**: Connection active, messages flowing
- **🟡 Connecting**: Attempting to establish connection
- **🔴 Closed**: Connection lost, retrying (if auto-reconnect enabled)

### Status Updates
```tsx
ws.onopen = () => {
  setStatus('open')
  backoffRef.current = 500  // Reset backoff
  setNextRetryMs(null)
}

ws.onclose = () => {
  setStatus('closed')
  // Auto-reconnect logic...
}
```

## Exponential Backoff Algorithm

### Backoff Progression
```
Initial: 500ms
1st retry: 1s
2nd retry: 2s
3rd retry: 4s
4th retry: 8s
5th retry: 10s (maximum)
6th+ retry: 10s (capped)
```

### Implementation
```tsx
const backoffRef = useRef(500)

ws.onclose = () => {
  if (!cancelled && autoReconnect) {
    const wait = Math.min(backoffRef.current, 10000)
    setTimeout(connect, wait)
    backoffRef.current = Math.min(wait * 2, 10000)
    setNextRetryMs(wait)
  }
}
```

## Session Persistence

### Session Resumption
When reconnecting with a session ID, the message counter resumes:

```
First connection:  /ws/chat/?session=abc123
Messages sent: 3
Connection lost

Second connection: /ws/chat/?session=abc123
Counter resumes: 4 (not 1)
```

### Session Storage
- **Server-side**: In-memory cache with 5-minute TTL
- **Client-side**: Session ID in URL query parameter
- **Persistence**: Survives page refreshes (if enabled)

## Error Handling

### Connection Errors
```tsx
ws.onerror = () => {
  setStatus('closed')
  ws.close()  // Trigger onclose handler
}
```

### Message Parsing Errors
```tsx
ws.onmessage = (ev) => {
  try {
    const data = JSON.parse(ev.data)
    // Process message...
  } catch {
    // Handle non-JSON messages
    setMessages((m: string[]) => [ev.data, ...m].slice(0, 100))
  }
}
```

## Testing Reconnect Functionality

### Manual Testing
1. **Open UI**: Navigate to `http://localhost`
2. **Create Session**: Add a new WebSocket session
3. **Send Messages**: Send a few test messages
4. **Click Reconnect**: Click the refresh button (🔄)
5. **Verify**: Connection re-establishes, counter continues

### Automated Testing
```bash
# Test reconnect functionality
make test-reconnect

# Test message format
make test-message-format

# Test session resumption
make test-session-resumption
```

### Test Scenarios
1. **Basic Reconnect**: Manual reconnection without session
2. **Session Reconnect**: Reconnection with session persistence
3. **Auto-Reconnect**: Automatic reconnection on connection loss
4. **Backoff Testing**: Multiple rapid disconnections
5. **Error Recovery**: Recovery from various error conditions

## Configuration Options

### Auto-Reconnect Toggle
```tsx
const [autoReconnect, setAutoReconnect] = useLocalStorage<boolean>('ui:autoReconnect', true)
```

### Session Persistence
```tsx
const [persistSession, setPersistSession] = useLocalStorage<boolean>('ui:persistSession', true)
```

### Backoff Configuration
```tsx
const backoffRef = useRef(500)  // Initial backoff: 500ms
const maxBackoff = 10000        // Maximum backoff: 10s
```

## Best Practices

### 1. User Experience
- **Visual Feedback**: Clear status indicators
- **Immediate Response**: Reconnect button responds instantly
- **Progressive Disclosure**: Show retry timers for advanced users

### 2. Reliability
- **Exponential Backoff**: Prevents server overload
- **Session Resumption**: Maintains conversation state
- **Error Recovery**: Graceful handling of various error types

### 3. Performance
- **Connection Pooling**: Efficient WebSocket management
- **Memory Management**: Cleanup on component unmount
- **State Synchronization**: Consistent UI state

## Troubleshooting

### Common Issues

**Reconnect Button Not Working:**
- Check WebSocket server status
- Verify network connectivity
- Check browser console for errors

**Auto-Reconnect Not Triggering:**
- Verify auto-reconnect toggle is enabled
- Check localStorage for settings
- Monitor connection status indicators

**Session Not Resuming:**
- Verify session ID is in URL
- Check server-side session storage
- Ensure session hasn't expired (5-minute TTL)

### Debugging
```javascript
// Enable debug logging
localStorage.setItem('debug', 'websocket')

// Check connection status
console.log('WebSocket status:', status)
console.log('Auto-reconnect:', autoReconnect)
console.log('Session ID:', sessionId)
```

## Performance Characteristics

### Reconnection Timing
- **Manual Reconnect**: Immediate (user-triggered)
- **Auto-Reconnect**: 500ms to 10s (exponential backoff)
- **Session Resumption**: ~100ms (server lookup)

### Resource Usage
- **Memory**: Minimal (connection state only)
- **CPU**: Low (event-driven reconnection)
- **Network**: Efficient (single WebSocket connection)

## Future Enhancements

### Potential Improvements
1. **Connection Quality Metrics**: Signal strength indicators
2. **Smart Reconnection**: Adaptive backoff based on network conditions
3. **Offline Support**: Message queuing during disconnection
4. **Multi-Server Support**: Automatic failover between servers
5. **Connection Diagnostics**: Detailed connection health information

## References

- [WebSocket API](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)
- [React Hooks](https://react.dev/reference/react/hooks)
- [Material-UI Icons](https://mui.com/material-ui/material-icons/)
- [Exponential Backoff](https://en.wikipedia.org/wiki/Exponential_backoff)
