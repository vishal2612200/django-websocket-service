# Scaling to 10,000 Concurrent Connections

## 🎯 Overview

This guide provides step-by-step instructions to scale the Django WebSocket service from the current 5,000 connection capacity to 10,000 concurrent connections.

## 📊 Current vs Target Configuration

| Metric | Current (5K) | Target (10K) | Change |
|--------|-------------|-------------|---------|
| **UVICORN_WORKERS** | 6 | 10 | +67% |
| **Total Threads** | 36-48 | 60-80 | +67% |
| **Memory per Container** | 1-2GB | 2-4GB | +100% |
| **CPU Cores** | 2-4 | 4-8 | +100% |
| **File Descriptors** | Default | 65536 | +1000% |

## 🔧 Configuration Changes Required

### **1. Docker Compose Configuration**

**File**: `docker/compose.yml`

```yaml
# Current configuration
- UVICORN_WORKERS=6

# Updated configuration for 10K connections
- UVICORN_WORKERS=10
```

**Full Update**:
```yaml
app_blue:
  build:
    context: ..
    dockerfile: docker/Dockerfile
  environment:
    - COLOR=blue
    - CHANNEL_REDIS_URL=redis://redis_blue:6379/0
    - MESSAGE_REDIS_URL=redis://redis_shared:6379/1
    - DJANGO_SETTINGS_MODULE=app.settings
    # ASGI Workers: 10 workers for 10K+ concurrent connections
    # Each worker has ~6-8 thread pool workers for blocking operations
    - UVICORN_WORKERS=10
  # Add resource limits for 10K connections
  deploy:
    resources:
      limits:
        memory: 4G
        cpus: '4.0'
      reservations:
        memory: 2G
        cpus: '2.0'
  # Increase ulimit for file descriptors
  ulimits:
    nofile:
      soft: 65536
      hard: 65536
```

### **2. Dockerfile Updates**

**File**: `docker/Dockerfile`

```dockerfile
# Add system-level optimizations for high concurrency
RUN echo "* soft nofile 65536" >> /etc/security/limits.conf && \
    echo "* hard nofile 65536" >> /etc/security/limits.conf && \
    echo "session required pam_limits.so" >> /etc/pam.d/common-session

# Optimize Python for high concurrency
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONOPTIMIZE=2

# Increase default thread pool size
ENV UVICORN_THREAD_POOL_SIZE=8
```

### **3. Redis Configuration**

**File**: `docker/compose.yml` (Redis services)

```yaml
redis_blue:
  image: redis:7-alpine
  command: redis-server --appendonly yes --save 60 1000 --maxclients 20000 --tcp-keepalive 300
  # Add resource limits
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: '2.0'
  # Increase ulimit
  ulimits:
    nofile:
      soft: 65536
      hard: 65536

redis_green:
  image: redis:7-alpine
  command: redis-server --appendonly yes --save 60 1000 --maxclients 20000 --tcp-keepalive 300
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: '2.0'
  ulimits:
    nofile:
      soft: 65536
      hard: 65536

redis_shared:
  image: redis:7-alpine
  command: redis-server --appendonly yes --save 60 1000 --maxclients 20000 --tcp-keepalive 300
  volumes:
    - redis_shared_data:/data
  deploy:
    resources:
      limits:
        memory: 4G
        cpus: '2.0'
  ulimits:
    nofile:
      soft: 65536
      hard: 65536
```

### **4. Traefik Configuration**

**File**: `docker/traefik/traefik.yml`

```yaml
# Add high concurrency settings
api:
  dashboard: true
  insecure: true

entryPoints:
  web:
    address: ":80"
    # Increase connection limits
    http:
      middlewares:
        - headers
      tls: {}

# Add middleware for connection limits
http:
  middlewares:
    headers:
      headers:
        # Increase connection limits
        customRequestHeaders:
          X-Forwarded-Proto: "http"
        # Add keep-alive settings
        customResponseHeaders:
          Connection: "keep-alive"
          Keep-Alive: "timeout=300"

# Increase provider limits
providers:
  file:
    directory: "/etc/traefik/dynamic"
    watch: true
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false
    # Increase connection limits
    network: "web"
```

### **5. System-Level Optimizations**

**File**: `docker/sysctl.conf` (create new file)

```bash
# Network optimizations for high concurrency
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_keepalive_probes = 3
net.ipv4.tcp_keepalive_intvl = 15
net.ipv4.tcp_tw_reuse = 1
net.ipv4.ip_local_port_range = 1024 65535

# File descriptor limits
fs.file-max = 2097152
fs.nr_open = 2097152
```

### **6. Load Testing Configuration**

**File**: `scripts/load_test.py`

```python
# Update default concurrency for 10K testing
parser.add_argument("--concurrency", type=int, default=int(os.environ.get("N", "10000")),
                   help="Number of concurrent connections (default: 10000)")
```

## 🚀 Deployment Steps

### **1. Update Configuration Files**

```bash
# Update Docker Compose
sed -i 's/UVICORN_WORKERS=6/UVICORN_WORKERS=10/g' docker/compose.yml

# Update load test default
sed -i 's/default=int(os.environ.get("N", "1000")/default=int(os.environ.get("N", "10000")/g' scripts/load_test.py
```

### **2. Rebuild and Deploy**

```bash
# Stop current deployment
make dev-down

# Rebuild with new configuration
docker compose -f docker/compose.yml build

# Start with new configuration
make dev-up

# Verify deployment
make logs
```

### **3. Test Scaling**

```bash
# Test with 10K connections
N=10000 make load-test

# Run performance test
make test-performance

# Monitor metrics
curl http://localhost/metrics | grep active_connections
```

## 📊 Performance Monitoring

### **Key Metrics to Watch**

1. **Active Connections**: Should reach 10,000
2. **Connection Rate**: Should handle 100+ connections/second
3. **Memory Usage**: Should stay under 4GB per container
4. **CPU Usage**: Should stay under 80% per container
5. **Redis Connections**: Should handle 20,000+ clients

### **Monitoring Commands**

```bash
# Check active connections
curl -s http://localhost/metrics | grep app_active_connections

# Monitor container resources
docker stats

# Check Redis connections
docker compose -f docker/compose.yml exec redis_blue redis-cli info clients

# Monitor system resources
htop
```

## ⚠️ Important Considerations

### **1. Hardware Requirements**

**Minimum Requirements for 10K Connections**:
- **CPU**: 8 cores (4 per container)
- **Memory**: 8GB RAM (4GB per container)
- **Network**: 1Gbps bandwidth
- **Storage**: SSD with 100GB+ free space

**Recommended Requirements**:
- **CPU**: 16 cores (8 per container)
- **Memory**: 16GB RAM (8GB per container)
- **Network**: 10Gbps bandwidth
- **Storage**: NVMe SSD with 200GB+ free space

### **2. Network Configuration**

```bash
# Increase system file descriptor limits
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Apply network optimizations
sudo sysctl -w net.core.somaxconn=65535
sudo sysctl -w net.core.netdev_max_backlog=5000
```

### **3. Horizontal Scaling**

For even higher concurrency (20K+ connections), consider horizontal scaling:

```yaml
# Add multiple app instances
app_blue_1:
  # ... configuration
app_blue_2:
  # ... configuration
app_blue_3:
  # ... configuration
```

## 🧪 Testing Strategy

### **1. Gradual Scaling Test**

```bash
# Test with increasing concurrency
for n in 1000 2000 5000 7500 10000; do
  echo "Testing with $n connections..."
  N=$n make load-test
  sleep 30
done
```

### **2. Stress Test**

```bash
# Run extended stress test
N=10000 timeout 300 make load-test

# Monitor for memory leaks
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

### **3. Failover Test**

```bash
# Test blue/green deployment with 10K connections
N=10000 make load-test &
LOAD_PID=$!

# Perform deployment
make promote

# Verify no connection loss
wait $LOAD_PID
```

## 🔍 Troubleshooting

### **Common Issues**

1. **"Too many open files"**
   - Solution: Increase ulimit to 65536

2. **"Connection refused"**
   - Solution: Check Redis maxclients setting

3. **"Out of memory"**
   - Solution: Increase container memory limits

4. **"High CPU usage"**
   - Solution: Add more CPU cores or reduce UVICORN_WORKERS

### **Debug Commands**

```bash
# Check file descriptors
docker compose -f docker/compose.yml exec app_blue cat /proc/sys/fs/file-nr

# Check Redis memory
docker compose -f docker/compose.yml exec redis_blue redis-cli info memory

# Check network connections
docker compose -f docker/compose.yml exec app_blue netstat -an | wc -l
```

## 📈 Expected Performance

With the 10K configuration:

- **Connection Success Rate**: ≥99%
- **Message Latency**: <50ms
- **Memory Usage**: <4GB per container
- **CPU Usage**: <80% per container
- **Connection Rate**: 100+ connections/second
- **Message Throughput**: 10,000+ messages/second

## 🎯 Summary

To scale to 10,000 concurrent connections:

1. **Update UVICORN_WORKERS** from 6 to 10
2. **Increase resource limits** (memory: 4GB, CPU: 4 cores)
3. **Set file descriptor limits** to 65536
4. **Optimize Redis configuration** for 20K clients
5. **Update load testing** defaults to 10K
6. **Monitor performance** and adjust as needed

This configuration provides a solid foundation for handling 10,000 concurrent WebSocket connections with good performance and reliability.
