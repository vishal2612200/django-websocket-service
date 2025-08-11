# Worker Configuration Guide

## Overview

This Django WebSocket service uses a multi-worker ASGI configuration optimized for I/O-bound operations typical of real-time messaging applications.

## Current Configuration

### ASGI Workers
- **Count**: 2 workers per container (`UVICORN_WORKERS=2`)
- **Type**: Process-based workers (separate Python processes)
- **Purpose**: Handle concurrent WebSocket connections

### Thread Pool Workers
- **Source**: `uvicorn[standard]` package
- **Size**: `min(32, cpu_count + 4)` per worker
- **Typical**: 6-8 threads per worker on 2-4 core containers
- **Total**: 12-16 concurrent threads across all workers
- **Purpose**: Handle blocking operations (I/O, database, external APIs)

## Why This Configuration?

### 1. I/O-Bound vs CPU-Bound Operations

**I/O-Bound Operations (Primary Workload):**
- WebSocket connections (async)
- Redis operations via channels-redis (async)
- Network communication
- File I/O for static files

**CPU-Bound Operations (Minimal):**
- JSON serialization/deserialization
- Basic message processing
- Health check calculations

### 2. Benefits of 2 ASGI Workers

1. **Fault Tolerance**: If one worker crashes, the other continues serving
2. **Load Distribution**: Connections distributed across processes
3. **Memory Efficiency**: ~50-100MB per worker, reasonable total usage
4. **Concurrency**: Handle multiple WebSocket connections simultaneously
5. **Resource Utilization**: Better use of available CPU cores

### 3. Thread Pool Benefits

1. **Blocking Operation Handling**: Database queries, external API calls
2. **Health Checks**: Synchronous operations for readiness/liveness probes
3. **Metrics Collection**: Prometheus metrics gathering
4. **File Operations**: Static file serving, logging

## Performance Characteristics

### Concurrency Model
```
Container
├── ASGI Worker 1 (Process)
│   ├── Thread 1 (async event loop)
│   ├── Thread 2 (thread pool)
│   ├── Thread 3 (thread pool)
│   └── ... (6-8 total threads)
└── ASGI Worker 2 (Process)
    ├── Thread 1 (async event loop)
    ├── Thread 2 (thread pool)
    ├── Thread 3 (thread pool)
    └── ... (6-8 total threads)
```

### Resource Usage (Typical)
- **Memory**: 150-300MB per container
- **CPU**: 0.5-2 cores recommended
- **Connections**: 1000+ concurrent WebSocket connections
- **Messages**: 10,000+ messages/second

## Scaling Guidelines

### Vertical Scaling (Increase Resources)
```yaml
# For higher load
environment:
  - UVICORN_WORKERS=3  # or 4 for high-end containers

# Container resources
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 1G
    reservations:
      cpus: '1.0'
      memory: 512M
```

### Horizontal Scaling (More Containers)
```yaml
# Scale to multiple containers
deploy:
  replicas: 3  # 3 containers × 2 workers = 6 total workers
```

### When to Scale

**Increase Workers (3-4):**
- High WebSocket connection count (>500 per container)
- CPU utilization >70%
- Memory usage <80%

**Add More Containers:**
- Total connections >1000
- Geographic distribution needed
- Fault tolerance requirements

**Increase Thread Pool:**
- Many blocking operations
- External API calls
- Database queries

## Monitoring

### Key Metrics
- `app_active_connections`: Current WebSocket connections
- `app_messages_total`: Total messages processed
- `app_errors_total`: Error count
- Container CPU/memory usage

### Health Checks
- `/readyz`: Application readiness
- `/healthz`: Basic health status
- `/metrics`: Prometheus metrics

## Troubleshooting

### Common Issues

**High Memory Usage:**
- Reduce `UVICORN_WORKERS`
- Check for memory leaks in WebSocket handlers
- Monitor connection count

**High CPU Usage:**
- Check for CPU-intensive operations in message handlers
- Consider increasing CPU allocation
- Profile application code

**Connection Drops:**
- Check Redis connectivity
- Monitor network stability
- Verify health check configuration

### Performance Tuning

**For High Message Volume:**
```yaml
environment:
  - UVICORN_WORKERS=3
  - CHANNEL_LAYER_CAPACITY=1000  # Redis channel capacity
```

**For High Connection Count:**
```yaml
environment:
  - UVICORN_WORKERS=2  # Keep moderate, scale horizontally
  - CHANNEL_LAYER_GROUP_EXPIRY=86400  # Longer group expiry
```

## Best Practices

1. **Start with 2 workers**: Good balance of performance and resource usage
2. **Monitor metrics**: Use Prometheus metrics for scaling decisions
3. **Test under load**: Use load testing tools to validate configuration
4. **Gradual scaling**: Increase workers/containers incrementally
5. **Resource limits**: Set appropriate CPU/memory limits
6. **Health checks**: Ensure proper readiness/liveness probes

## References

- [Uvicorn Documentation](https://www.uvicorn.org/)
- [Django Channels Documentation](https://channels.readthedocs.io/)
- [ASGI Specification](https://asgi.readthedocs.io/)
- [Redis Channel Layers](https://channels.readthedocs.io/en/stable/topics/channel_layers.html)
