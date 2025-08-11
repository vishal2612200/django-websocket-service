# Individual Session Persistence Architecture and Configuration

## Executive Summary

The WebSocket Chat service implements a sophisticated individual session persistence architecture that enables granular control over data storage preferences at the session level. This design provides enhanced flexibility, data integrity, and user experience by allowing each session to maintain its own immutable persistence configuration throughout its lifecycle.

## Architecture Overview

### Core Design Principles

The individual session persistence system is built upon three fundamental principles:

1. **Session-Level Granularity**: Each WebSocket session maintains independent persistence preferences
2. **Immutability After Creation**: Persistence type is locked at session creation to ensure data consistency
3. **Global Default Configuration**: System-wide defaults guide new session creation while preserving individual control

### Key Architectural Features

#### Individual Session Control
- **Independent Configuration**: Each session operates with its own persistence strategy
- **Mixed Deployment Support**: Concurrent sessions can utilize different storage backends
- **Consistent Behavior**: Predictable session lifecycle with immutable persistence settings
- **No Global Interference**: Individual sessions remain unaffected by system-wide changes

#### Immutable Persistence Design
- **Creation-Time Lock**: Persistence type is determined and locked during session initialization
- **Data Integrity Protection**: Prevents data corruption from mid-session storage migrations
- **Predictable Lifecycle**: Consistent behavior throughout session duration
- **Simplified State Management**: Eliminates complex storage switching logic

#### Session-Level Configuration Management
- **Storage Type Selection**: Configurable persistence strategy per session
- **Default Inheritance**: New sessions inherit global default settings
- **Immutable Preferences**: Session settings cannot be modified post-creation
- **Persistent Configuration**: Session preferences are maintained across browser sessions

## Implementation Architecture

### Global Default Configuration

The system maintains a global default persistence setting that serves as the foundation for new session creation:

```typescript
// Global default configuration
interface GlobalPersistenceConfig {
  defaultType: 'localStorage' | 'redis' | 'none';
  description: string;
  affectsNewSessionsOnly: boolean;
}
```

### Individual Session Preferences

Each session maintains its own immutable persistence configuration:

```typescript
// Individual session persistence configuration
interface SessionPersistenceConfig {
  sessionId: string;
  persistenceType: 'localStorage' | 'redis' | 'none';
  createdAt: number;
  immutable: boolean;
}
```

### Session Creation Workflow

1. **Default Inheritance**: New sessions inherit the global default persistence type
2. **Configuration Lock**: Persistence type is locked immediately upon session creation
3. **Storage Initialization**: Appropriate storage backend is initialized based on configuration
4. **Lifecycle Management**: Session maintains immutable configuration throughout its lifecycle

## Storage Backend Architecture

### localStorage Implementation

**Characteristics**:
- **Scope**: Browser-specific storage with cross-tab persistence
- **Performance**: High-speed local storage with minimal latency
- **Durability**: Survives browser restarts and tab closures
- **Limitations**: Device-specific, no cross-device synchronization

**Use Cases**:
- Temporary sessions requiring fast access
- Device-specific data that doesn't require cross-device availability
- Development and testing scenarios

### Redis Implementation

**Characteristics**:
- **Scope**: Server-wide storage with cross-device accessibility
- **Performance**: Network-based storage with configurable TTL
- **Durability**: Persistent across device changes and browser sessions
- **Scalability**: Supports high-volume concurrent sessions

**Use Cases**:
- Production sessions requiring cross-device access
- High-availability scenarios with multiple server instances
- Sessions requiring data persistence beyond browser lifecycle

### None Implementation

**Characteristics**:
- **Scope**: Session-only storage with no persistence
- **Performance**: Maximum performance with no storage overhead
- **Durability**: Data lost upon connection termination
- **Use Cases**: Testing, temporary sessions, performance-critical scenarios

## User Interface Architecture

### Global Settings Interface

The global settings provide system-wide configuration management:

```
┌─────────────────────────────────────┐
│ Default Persistence Configuration   │
│ ─────────────────────────────────── │
│ Type: [Redis ▼]                     │
│ Description: New sessions use Redis │
│ Scope: Affects new sessions only    │
└─────────────────────────────────────┘
```

### Individual Session Interface

Each session displays its immutable persistence configuration:

```
┌─────────────────────────────────────┐
│ WebSocket Session Configuration     │
│ ─────────────────────────────────── │
│ Persistence: [🟡 Redis] (Immutable) │
│ Controls: [🔄] [❌]                 │
│                                     │
│ ┌─ Message History ─┐ ┌─ Heartbeat ─┐│
│ │                   │ │             ││
│ └───────────────────┘ └─────────────┘│
└─────────────────────────────────────┘
```

## Data Architecture

### Session Preferences Storage

Session preferences are maintained in browser localStorage with the following structure:

```typescript
// localStorage key: 'ui:sessionPreferences'
interface SessionPreferencesStorage {
  [sessionId: string]: {
    persistenceType: 'localStorage' | 'redis' | 'none';
    createdAt: number;
    lastAccessed: number;
  };
}
```

### Session Creation Implementation

```typescript
// Session creation with persistence configuration
function createSession(id?: string): SessionConfig {
  const sessionId = (id && id.trim()) || generateUUID();
  const persistenceType = getGlobalDefaultPersistenceType();
  
  // Create session with immutable persistence configuration
  const sessionConfig: SessionConfig = {
    id: sessionId,
    persistenceType,
    createdAt: Date.now(),
    immutable: true
  };
  
  // Store session preferences
  setSessionPersistenceType(sessionId, persistenceType);
  
  return sessionConfig;
}
```

## Design Rationale: Immutable Persistence Architecture

### Immutability Justification

The immutable persistence design addresses several critical architectural concerns:

#### Data Consistency Protection
- **Prevents Data Loss**: Eliminates risk of partial data migration between storage backends
- **Maintains Integrity**: Ensures complete data availability throughout session lifecycle
- **Simplifies Recovery**: Clear data location eliminates recovery complexity

#### Predictable System Behavior
- **Deterministic Lifecycle**: Session behavior is predictable from creation to termination
- **Reduced Complexity**: Eliminates complex state management for storage switching
- **Clear Decision Points**: Forces architectural decisions at appropriate lifecycle stages

#### Performance Optimization
- **Eliminates Migration Overhead**: No runtime storage switching reduces performance impact
- **Simplified Caching**: Storage-specific caching strategies can be optimized
- **Reduced Network Overhead**: Eliminates unnecessary data transfer between storage backends

### Architectural Benefits

#### User Experience Enhancement
- **Clear Expectations**: Users understand session behavior from creation
- **No Confusion**: Eliminates unexpected behavior changes during session lifecycle
- **Intuitive Management**: Simple, predictable session management interface

#### System Reliability
- **Reduced Failure Points**: Eliminates complex storage migration logic
- **Simplified Testing**: Clear, testable session configurations
- **Easier Debugging**: Predictable data flow simplifies troubleshooting

## Migration Architecture

### Pre-Migration State (Global Configuration)

The previous architecture utilized global persistence settings:

```typescript
// Legacy global configuration
interface LegacyGlobalConfig {
  globalPersistenceType: 'localStorage' | 'redis' | 'none';
  affectsAllSessions: boolean;
  noIndividualControl: boolean;
}
```

### Post-Migration State (Individual Preferences)

The current architecture provides session-level granularity:

```typescript
// Current individual configuration
interface CurrentSessionConfig {
  sessionId: string;
  individualPersistenceType: 'localStorage' | 'redis' | 'none';
  immutableAfterCreation: boolean;
  globalDefaultInheritance: boolean;
}
```

## API Integration Architecture

### WebSocket Connection Configuration

Each session establishes connections with its specific persistence configuration:

```javascript
// Session-specific WebSocket connection
const wsUrl = `ws://localhost/ws/chat/?session=${sessionId}&redis_persistence=${sessionPersistenceType === 'redis'}`;
```

### Message Storage Integration

#### Redis Session Storage
- **Backend**: Redis with configurable TTL
- **API Endpoint**: `/chat/api/sessions/{session_id}/messages/`
- **Scope**: Server-wide with cross-device accessibility

#### localStorage Session Storage
- **Backend**: Browser localStorage
- **API Endpoint**: N/A (client-side storage)
- **Scope**: Browser-specific with cross-tab persistence

#### None Session Storage
- **Backend**: No persistence
- **API Endpoint**: N/A
- **Scope**: Session-only with no data retention

## Configuration Management

### Environment Configuration

```bash
# Redis backend configuration
CHANNEL_REDIS_URL=redis://redis_green:6379/0
REDIS_SESSION_TTL=300

# localStorage configuration (browser-managed)
# No additional environment configuration required
```

### Frontend Configuration

```typescript
// Global default configuration
interface GlobalConfig {
  sessionPersistenceType: 'localStorage' | 'redis' | 'none';
  description: string;
  affectsNewSessionsOnly: boolean;
}

// Individual session configuration
interface SessionConfig {
  sessionPreferences: Record<string, 'localStorage' | 'redis' | 'none'>;
  globalDefault: 'localStorage' | 'redis' | 'none';
}
```

## Operational Best Practices

### Session Planning Strategy

#### Redis Session Deployment
- **Use Case**: Production sessions requiring cross-device access
- **Considerations**: Network latency, server availability, data durability
- **Configuration**: Appropriate TTL settings, connection pooling

#### localStorage Session Deployment
- **Use Case**: Temporary sessions, device-specific data
- **Considerations**: Browser storage limits, device-specific scope
- **Configuration**: Storage quota management, cleanup policies

#### None Session Deployment
- **Use Case**: Testing, performance-critical scenarios
- **Considerations**: No data persistence, session-only scope
- **Configuration**: Minimal overhead, maximum performance

### User Experience Guidelines

#### Clear Communication
- **Storage Type Indicators**: Visual indicators for each persistence type
- **User Education**: Clear explanation of storage type implications
- **Decision Support**: Guidance for appropriate storage type selection

#### Performance Optimization
- **Redis Sessions**: Network overhead considerations
- **localStorage Sessions**: Browser storage limitations
- **None Sessions**: Maximum performance with no persistence

## Troubleshooting and Resolution

### Session Configuration Issues

#### Unexpected Storage Behavior
1. **Verify Session Configuration**: Check individual session persistence setting
2. **Validate Global Defaults**: Confirm global default configuration
3. **Session Creation Timing**: Ensure session was created after configuration changes
4. **Configuration Immutability**: Remember that persistence type cannot be changed post-creation

#### Data Persistence Issues

##### Redis Session Problems
1. **Connection Validation**: Verify Redis connectivity and configuration
2. **TTL Configuration**: Check session TTL settings
3. **API Endpoint Validation**: Confirm `/chat/api/sessions/{session_id}/messages/` functionality

##### localStorage Session Problems
1. **Browser Storage**: Verify localStorage availability and quota
2. **Cross-Tab Persistence**: Confirm data sharing across browser tabs
3. **Storage Limits**: Check browser storage quota limitations

#### Inconsistent Behavior Resolution
1. **Individual Session Settings**: Each session maintains independent configuration
2. **Global Default Scope**: Global settings affect only new sessions
3. **Configuration Immutability**: Persistence type cannot be modified after creation
4. **Session Recreation**: Create new sessions with correct configuration if needed
