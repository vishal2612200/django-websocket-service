# Redis Message Persistence and API Integration Guide

## Problem Statement

The Redis Messages API (`/chat/api/sessions/{session_id}/messages/`) may return empty message arrays due to configuration or connectivity issues. This guide provides comprehensive troubleshooting and resolution strategies for Redis message persistence integration.

## Common Issues and Root Causes

### Primary Issue: Redis Persistence Not Enabled

The WebSocket service defaults to `localStorage` persistence rather than Redis. Messages are only stored in Redis when Redis persistence is explicitly configured and enabled.

### Secondary Issue: No Messages with Redis Persistence

Even with Redis persistence enabled, messages are only stored in Redis when:
- WebSocket connections are established with `redis_persistence=true` parameter
- Messages are transmitted through Redis-enabled connections
- Redis connectivity and configuration are properly established

## Redis Persistence Configuration

### Step 1: Session Persistence Configuration

1. **Access Application Settings**:
   - Navigate to the WebSocket Chat application interface
   - Locate the **Settings** section
   - Find the **"Session Persistence"** configuration option

2. **Configure Persistence Type**:
   - Change the persistence dropdown from `localStorage` to `Redis`
   - Verify the UI displays: "Sessions stored in Redis with TTL"
   - Confirm the configuration change is applied

### Step 2: Session Creation with Redis Persistence

1. **Create New Session**:
   - Enter a session identifier (or allow auto-generation)
   - Click **"Add Session"** to create the session
   - Verify the session card displays a **"Redis"** indicator

2. **Validate Session Configuration**:
   - Confirm the session shows Redis persistence chip
   - Verify the refresh button is available for manual message fetching

### Step 3: Message Transmission and Storage

1. **Establish WebSocket Connection**:
   - Connect to the Redis-enabled session
   - Verify WebSocket connection establishes automatically

2. **Send Test Messages**:
   - Transmit messages through the chat interface
   - Confirm messages are stored in Redis with appropriate TTL

### Step 4: Redis Storage Validation

1. **Manual Message Fetching**:
   - Use the refresh button (🔄) adjacent to the Redis chip
   - Manually fetch messages from Redis storage

2. **API Validation**:
   - Call the API directly: `GET /chat/api/sessions/{session_id}/messages/`
   - Verify message retrieval and storage integrity

## API Response Architecture

### Successful Redis Persistence Response

When Redis persistence is functioning correctly, the API returns:

```json
{
  "success": true,
  "session_id": "your-session-id",
  "messages": [
    {
      "content": "Hello Redis!",
      "timestamp": 1703123456789,
      "isSent": true,
      "sessionId": "your-session-id"
    },
    {
      "content": "Message #1: Hello Redis!",
      "timestamp": 1703123456790,
      "isSent": false,
      "sessionId": "your-session-id"
    }
  ],
  "count": 2
}
```

### Empty Messages Response

```json
{
  "success": true,
  "session_id": "test-session",
  "messages": [],
  "count": 0
}
```

**Potential Causes**:
- Session persistence configured for `localStorage` or `none`
- No messages transmitted with Redis persistence enabled
- Redis connectivity or configuration issues
- Session TTL expiration

## Troubleshooting and Resolution

### Redis Connectivity Validation

Validate Redis service status:

```bash
curl http://localhost/chat/api/redis/status/
```

**Expected Response**:
```json
{
  "success": true,
  "redis_connected": true,
  "redis_url": "redis://redis_green:6379/0",
  "default_ttl": 300
}
```

### Configuration Validation

1. **Verify Session Persistence Setting**:
   - Confirm session persistence is set to `Redis`
   - Validate session was created after configuration change

2. **Check Redis Service Status**:
   - Ensure Redis service is running and accessible
   - Verify network connectivity to Redis instance

3. **Validate Message Transmission**:
   - Confirm messages were sent through Redis-enabled connections
   - Check for any transmission errors or failures

## Testing and Validation Procedures

### Manual Testing Protocol

1. **Configuration Setup**:
   - Set session persistence to `Redis`
   - Create session with identifier: `test-redis-123`

2. **Message Transmission**:
   - Send test message: "Hello Redis test!"
   - Verify message transmission success

3. **Storage Validation**:
   - Call API: `GET /chat/api/sessions/test-redis-123/messages/`
   - Confirm message storage in Redis

### Programmatic Testing

```bash
# Step 1: Validate Redis service status
curl http://localhost/chat/api/redis/status/

# Step 2: Check message storage for session
curl http://localhost/chat/api/sessions/test-session-123/messages/

# Step 3: Verify message persistence after Redis configuration
curl http://localhost/chat/api/sessions/your-session-id/messages/
```

## Critical Configuration Points

### Default Behavior
- **Redis persistence is disabled by default**
- **Messages are only stored in Redis when explicitly enabled**
- **Each WebSocket connection requires `redis_persistence=true` parameter**
- **Messages have configurable TTL and will expire automatically**
- **Manual refresh functionality is available for message fetching**

### Persistence Configuration

#### Environment Variables
```bash
# Redis connection configuration
CHANNEL_REDIS_URL=redis://redis_green:6379/0

# Session TTL configuration (seconds)
REDIS_SESSION_TTL=300
```

#### Frontend Configuration
```typescript
// Session persistence type configuration
sessionPersistenceType: 'localStorage' | 'redis' | 'none' = 'localStorage'
```

## Advanced Troubleshooting

### Redis Service Issues

1. **Service Status Check**:
   ```bash
   docker compose -f docker/compose.yml ps redis_green
   ```

2. **Redis Connection Test**:
   ```bash
   docker compose -f docker/compose.yml exec redis_green redis-cli ping
   ```

3. **Redis Logs Analysis**:
   ```bash
   docker compose -f docker/compose.yml logs redis_green
   ```

### Network Connectivity Issues

1. **Port Validation**:
   ```bash
   netstat -an | grep 6379
   ```

2. **Connection Testing**:
   ```bash
   telnet localhost 6379
   ```

### Configuration Validation

1. **Environment Variable Verification**:
   ```bash
   docker compose -f docker/compose.yml exec app_green env | grep REDIS
   ```

2. **Application Configuration Check**:
   ```bash
   curl http://localhost/chat/api/redis/status/
   ```

## Performance Considerations

### Redis Performance Optimization

1. **Connection Pooling**: Configure appropriate connection pool sizes
2. **TTL Management**: Set appropriate TTL values for message retention
3. **Memory Management**: Monitor Redis memory usage and configuration
4. **Network Latency**: Consider Redis deployment proximity to application

### Monitoring and Alerting

1. **Redis Metrics**: Monitor Redis performance metrics
2. **Connection Health**: Track Redis connection status
3. **Message Storage**: Monitor message storage and retrieval performance
4. **Error Rates**: Track Redis-related error rates and failures

## Best Practices

### Configuration Management

1. **Environment-Specific Settings**: Use appropriate Redis configurations for different environments
2. **Security Configuration**: Implement proper Redis security settings
3. **Backup Strategies**: Establish Redis data backup and recovery procedures
4. **Monitoring Setup**: Configure comprehensive Redis monitoring and alerting

### Development Workflow

1. **Local Development**: Use local Redis instances for development
2. **Testing Procedures**: Implement comprehensive Redis testing protocols
3. **Documentation**: Maintain current Redis configuration documentation
4. **Version Control**: Track Redis configuration changes in version control
