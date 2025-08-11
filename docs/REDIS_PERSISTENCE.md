# Redis Session Persistence Architecture and Implementation

This document provides comprehensive documentation of the Redis session persistence architecture, which enables robust session storage with configurable TTL (Time To Live) support across distributed WebSocket service deployments.

## Architecture Overview

The Redis persistence system provides enterprise-grade session management capabilities:

- **Distributed Session Storage**: Centralized session data storage with Redis backend
- **Cross-Instance Persistence**: Session continuity across server restarts and multiple instances
- **Configurable TTL Management**: Automatic expiration with manual TTL extension capabilities
- **Graceful Degradation**: Fallback to in-memory storage when Redis is unavailable
- **High Availability**: Support for Redis clustering and failover scenarios

## Configuration Architecture

### Environment Configuration

```bash
# Redis connection configuration (default: redis://localhost:6379/0)
CHANNEL_REDIS_URL=redis://localhost:6379/0

# Session TTL configuration in seconds (default: 3600 = 1 hour)
REDIS_SESSION_TTL=3600
```

### Frontend Configuration Interface

Enable Redis persistence through the application interface:

1. **Access Configuration Panel**: Navigate to the WebSocket Chat application settings
2. **Enable Redis Persistence**: Toggle "Redis persistence" in the settings section
3. **Session Creation**: Create or reconnect to sessions with Redis persistence enabled
4. **Validation**: Verify Redis persistence is active through session indicators

## Core Features and Capabilities

### Session Persistence Architecture

When Redis persistence is enabled, the system implements the following storage architecture:

- **Key Format**: `session:{session_id}` for consistent Redis key management
- **Data Structure**: Comprehensive session metadata including:
  - Message count and sequence tracking
  - Last activity timestamp for session monitoring
  - Disconnection timestamp for session lifecycle management
  - TTL configuration and expiration tracking

### TTL Management System

The TTL management system provides flexible session lifecycle control:

- **Default TTL**: Configurable 1-hour default (adjustable via `REDIS_SESSION_TTL`)
- **Automatic Expiration**: Redis-managed session cleanup when TTL expires
- **Manual Extension**: API-driven TTL extension for session continuity
- **TTL Monitoring**: Real-time TTL status tracking and reporting

### API Integration Architecture

#### Redis Status Endpoint

```http
GET /api/redis/status/
```

**Response Architecture**:
```json
{
  "success": true,
  "redis_connected": true,
  "redis_url": "redis://localhost:6379/0",
  "default_ttl": 3600
}
```

#### Session Information Retrieval

```http
GET /api/sessions/{session_id}/
```

**Response Architecture**:
```json
{
  "success": true,
  "session_id": "test-session-123",
  "data": {
    "data": {
      "count": 5,
      "last_activity": 1640995200.0
    },
    "created_at": 1640991600.0,
    "ttl": 3600,
    "remaining_ttl": 1800
  }
}
```

#### Session TTL Extension

```http
POST /api/sessions/{session_id}/extend/
Content-Type: application/json

{
  "ttl": 7200
}
```

#### Session Deletion

```http
DELETE /api/sessions/{session_id}/delete/
```

### WebSocket Integration Architecture

Redis persistence integration with WebSocket connections:

```javascript
// Redis persistence enabled WebSocket connection
const ws = new WebSocket('/ws/chat/?session=my-session&redis_persistence=true');
```

## Implementation Examples

### Frontend Integration Architecture

```typescript
// Comprehensive WebSocket integration with Redis persistence
const { status, messages, count } = useWebSocket(
  '/ws/chat/',
  true,           // autoReconnect
  'my-session',   // sessionId
  true,           // persistMessages
  true            // redisPersistence
);
```

### Backend Session Management Implementation

```python
from chat.redis_session import get_redis_session_manager

# Initialize Redis session manager
redis_manager = get_redis_session_manager()

# Store session data with TTL configuration
await redis_manager.store_session(
    session_id="my-session",
    data={"count": 5, "last_activity": time.time()},
    ttl=3600  # 1 hour TTL
)

# Retrieve session data with error handling
session_data = await redis_manager.get_session("my-session")

# Extend session TTL for continuity
await redis_manager.extend_session("my-session", ttl=7200)

# Clean up session data
await redis_manager.delete_session("my-session")
```

## Testing and Validation

### Comprehensive Testing Protocol

Execute the Redis persistence validation suite:

```bash
python scripts/test_redis_persistence.py
```

**Testing Coverage**:
1. **Redis Connectivity Validation**: Verify Redis connection and configuration
2. **WebSocket Integration Testing**: Test WebSocket connections with Redis persistence
3. **Message Storage Validation**: Verify message persistence and retrieval
4. **Session Management Testing**: Test session creation, retrieval, and TTL extension
5. **Reconnection Validation**: Verify session persistence across connection interruptions
6. **Cleanup Procedures**: Validate session deletion and cleanup processes

## Monitoring and Observability

### Redis Key Management

Monitor Redis keys with comprehensive pattern matching:

```bash
# Enumerate all session keys
redis-cli keys "session:*"

# Retrieve specific session data
redis-cli get "session:my-session-id"

# Monitor TTL status
redis-cli ttl "session:my-session-id"
```

### Application Logging

The application provides comprehensive Redis operation logging:

```
INFO: Session stored in Redis: my-session, TTL: 3600s
INFO: Session loaded from Redis: my-session, count: 5
INFO: Session TTL extended in Redis: my-session, new TTL: 7200s
INFO: Session deleted from Redis: my-session
```

## Error Handling and Resilience

### Redis Connection Failure Management

When Redis becomes unavailable, the system implements graceful degradation:

1. **Automatic Fallback**: Seamless transition to in-memory session storage
2. **Service Continuity**: WebSocket connections maintain normal operation
3. **Error Logging**: Comprehensive error logging for debugging and monitoring
4. **Recovery Procedures**: Automatic recovery when Redis connectivity is restored

### Session Data Integrity Protection

Robust handling of session data corruption scenarios:

1. **Corruption Detection**: Automatic detection of corrupted session data
2. **Graceful Recovery**: Session reset to initial state (count starts from 0)
3. **Error Reporting**: Detailed error logging for investigation
4. **Service Continuity**: Application continues normal operation

## Performance Optimization

### Memory Management

- **Session Data Size**: Each session consumes approximately 200-500 bytes in Redis
- **Automatic Cleanup**: TTL ensures automatic removal of expired sessions
- **Memory Monitoring**: Comprehensive Redis memory usage monitoring for large deployments

### Network Performance

- **Minimal Latency**: Redis operations add minimal latency to WebSocket connections
- **Asynchronous Operations**: Non-blocking async operations prevent event loop blocking
- **High Availability**: Redis clustering support for enterprise deployments

## Security Architecture

### Data Protection

- **Storage Security**: Session data stored in Redis without encryption (configurable)
- **Encryption Options**: Redis encryption support for sensitive deployment scenarios
- **Access Controls**: Comprehensive Redis access control implementation

### Access Management

- **API Security**: API endpoints require appropriate authentication/authorization
- **Redis ACLs**: Redis Access Control Lists for instance-level security
- **Network Security**: Secure Redis network configuration and access controls

## Troubleshooting and Resolution

### Common Issue Resolution

#### Redis Connection Failures

**Diagnostic Steps**:
1. **Service Validation**: Verify Redis service status with `redis-cli ping`
2. **Configuration Verification**: Validate `CHANNEL_REDIS_URL` environment variable
3. **Network Connectivity**: Ensure network connectivity to Redis instance

#### Session Persistence Issues

**Diagnostic Steps**:
1. **UI Configuration**: Verify Redis persistence is enabled in application interface
2. **Redis Logs**: Review Redis logs for error conditions
3. **TTL Configuration**: Validate TTL settings and expiration behavior

#### Memory Usage Optimization

**Diagnostic Steps**:
1. **Memory Monitoring**: Execute `redis-cli info memory` for memory analysis
2. **Expired Session Cleanup**: Verify expired sessions are properly removed
3. **TTL Adjustment**: Optimize TTL settings based on usage patterns

### Advanced Debugging Commands

```bash
# Redis service status validation
curl http://localhost:8000/api/redis/status/

# Session information retrieval
curl http://localhost:8000/api/sessions/my-session/

# Redis operation monitoring
redis-cli monitor

# Memory usage analysis
redis-cli info memory
```

## Deployment Considerations

### Production Deployment

1. **Redis Clustering**: Implement Redis clustering for high availability
2. **Monitoring Setup**: Configure comprehensive Redis monitoring and alerting
3. **Backup Procedures**: Establish Redis data backup and recovery procedures
4. **Security Configuration**: Implement appropriate Redis security measures

### Development Environment

1. **Local Redis**: Use local Redis instances for development and testing
2. **Configuration Management**: Maintain environment-specific Redis configurations
3. **Testing Procedures**: Implement comprehensive Redis testing protocols
4. **Documentation**: Maintain current Redis configuration documentation
