# Deployment and Operations Guide

## Overview

This document provides comprehensive guidance for deploying and operating the Django WebSocket Service in production environments, following enterprise-grade practices and SRE principles. The deployment strategy focuses on zero-downtime deployments, high availability, and operational excellence.

## Deployment Strategy

### Blue/Green Deployment Architecture

**Problem Statement**: Traditional deployment strategies require downtime and carry significant risk of service disruption during updates. This creates operational challenges and impacts user experience.

**Solution**: Implement a zero-downtime deployment strategy that ensures continuous service availability while maintaining high reliability.

**Implementation Approach**:
- Deploy new version to inactive environment (blue/green)
- Run comprehensive health checks and validation
- Atomically switch traffic via load balancer
- Gracefully terminate old environment
- Implement automatic rollback on failures

**Expected Outcomes**:
- Zero downtime deployments
- Sub-100ms traffic switching
- Automatic rollback capability
- 99.99% uptime during deployments

## Infrastructure Setup

### Production Environment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Production Environment                   │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │   Load Balancer │    │   Monitoring    │                    │
│  │   (Traefik)     │    │   Stack         │                    │
│  │   Port 80/443   │    │   (Prometheus,  │                    │
│  └─────────────────┘    │    Grafana)     │                    │
│          │              └─────────────────┘                    │
│          ▼                                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                Application Layer                        │    │
│  │                                                         │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │    │
│  │  │   Blue      │  │   Green     │  │   Shared    │     │    │
│  │  │ Environment │  │ Environment │  │  Services   │     │    │
│  │  │             │  │             │  │             │     │    │
│  │  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────┐ │     │    │
│  │  │ │Django   │ │  │ │Django   │ │  │ │Redis    │ │     │    │
│  │  │ │App      │ │  │ │App      │ │  │ │Cache    │ │     │    │
│  │  │ │(3 pods) │ │  │ │(3 pods) │ │  │ │Layer    │ │     │    │
│  │  │ └─────────┘ │  │ └─────────┘ │  │ └─────────┘ │     │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐                    │
│  │   Database      │    │   Storage       │                    │
│  │   (PostgreSQL)  │    │   (Persistent   │                    │
│  │                 │    │    Volumes)     │                    │
│  └─────────────────┘    └─────────────────┘                    │
└─────────────────────────────────────────────────────────────────┘
```

### Infrastructure Requirements

| Component | Specification | Purpose |
|-----------|---------------|---------|
| **Load Balancer** | Traefik v3 with SSL termination | Traffic routing and SSL |
| **Application Servers** | 4+ CPU cores, 8GB+ RAM | Django + Uvicorn workers |
| **Cache Layer** | Redis 7.x with persistence | Channel layer and sessions |
| **Database** | PostgreSQL 14+ with replication | Data persistence |
| **Monitoring** | Prometheus + Grafana | Metrics and alerting |
| **Storage** | SSD with 100GB+ | Logs and static files |

## Deployment Configuration

### Docker Compose for Production

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  traefik:
    image: traefik:v3.0
    container_name: traefik
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik/traefik.yml:/etc/traefik/traefik.yml:ro
      - ./traefik/dynamic:/etc/traefik/dynamic:ro
      - ./ssl:/etc/ssl:ro
    networks:
      - websocket-network
    restart: unless-stopped

  app_blue:
    build: .
    container_name: app_blue
    environment:
      - DJANGO_SETTINGS_MODULE=app.settings
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://user:pass@postgres:5432/websocket
    volumes:
      - ./logs:/app/logs
    networks:
      - websocket-network
    restart: unless-stopped
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.app-blue.rule=Host(`api.example.com`)"
      - "traefik.http.routers.app-blue.service=app-blue"
      - "traefik.http.services.app-blue.loadbalancer.server.port=8000"

  app_green:
    build: .
    container_name: app_green
    environment:
      - DJANGO_SETTINGS_MODULE=app.settings
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://user:pass@postgres:5432/websocket
    volumes:
      - ./logs:/app/logs
    networks:
      - websocket-network
    restart: unless-stopped
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.app-green.rule=Host(`api.example.com`)"
      - "traefik.http.routers.app-green.service=app-green"
      - "traefik.http.services.app-green.loadbalancer.server.port=8000"

  redis:
    image: redis:7-alpine
    container_name: redis
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    networks:
      - websocket-network
    restart: unless-stopped

  postgres:
    image: postgres:14-alpine
    container_name: postgres
    environment:
      - POSTGRES_DB=websocket
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - websocket-network
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    networks:
      - websocket-network
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
    networks:
      - websocket-network
    restart: unless-stopped

volumes:
  redis_data:
  postgres_data:
  prometheus_data:
  grafana_data:

networks:
  websocket-network:
    driver: bridge
```

### Traefik Configuration

```yaml
# traefik/traefik.yml
api:
  dashboard: true
  insecure: false

entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entrypoint:
          to: websecure
          scheme: https
  websecure:
    address: ":443"

providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false
  file:
    directory: "/etc/traefik/dynamic"
    watch: true

certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@example.com
      storage: /etc/traefik/acme/acme.json
      httpChallenge:
        entryPoint: web

log:
  level: INFO

accessLog:
  filePath: "/var/log/traefik/access.log"
  format: json
```

### Dynamic Configuration

```yaml
# traefik/dynamic/active.yml
http:
  routers:
    app:
      rule: "Host(`api.example.com`)"
      service: app-blue
      tls:
        certResolver: letsencrypt
      middlewares:
        - rate-limit
        - cors
        - security-headers

  services:
    app-blue:
      loadBalancer:
        servers:
          - url: "http://app_blue:8000"
        healthCheck:
          path: "/healthz"
          interval: "10s"
          timeout: "5s"
    app-green:
      loadBalancer:
        servers:
          - url: "http://app_green:8000"
        healthCheck:
          path: "/healthz"
          interval: "10s"
          timeout: "5s"

  middlewares:
    rate-limit:
      rateLimit:
        burst: 100
        average: 50
    cors:
      headers:
        accessControlAllowOriginList:
          - "https://example.com"
        accessControlAllowMethods:
          - GET
          - POST
          - OPTIONS
    security-headers:
      headers:
        frameDeny: true
        sslRedirect: true
        browserXssFilter: true
        contentTypeNosniff: true
        forceSTSHeader: true
        stsIncludeSubdomains: true
        stsPreload: true
        stsSeconds: 31536000
```

## Deployment Process

### Pre-Deployment Checklist

**Environment Preparation**:
- [ ] Verify all infrastructure components are healthy
- [ ] Ensure sufficient disk space and memory
- [ ] Validate SSL certificates and domain configuration
- [ ] Check monitoring and alerting systems
- [ ] Review recent error logs and metrics

**Application Preparation**:
- [ ] Run comprehensive test suite
- [ ] Perform security scan on container images
- [ ] Validate configuration files
- [ ] Check database migrations
- [ ] Verify Redis connectivity

**Deployment Team Preparation**:
- [ ] Assign deployment lead and backup
- [ ] Schedule deployment window
- [ ] Prepare rollback procedures
- [ ] Notify stakeholders
- [ ] Set up monitoring dashboards

### Blue/Green Deployment Steps

**Phase 1: Environment Preparation**

```bash
# 1. Build new application image
docker build -t websocket-app:v2.0.0 .

# 2. Deploy to inactive environment (green)
docker-compose -f docker-compose.prod.yml up -d app_green

# 3. Run health checks on new environment
curl -f http://app_green:8000/healthz
curl -f http://app_green:8000/readyz

# 4. Run smoke tests
./scripts/smoke_test.sh app_green
```

**Phase 2: Traffic Switching**

```bash
# 1. Update Traefik configuration to route traffic to green
cp traefik/dynamic/green.yml traefik/dynamic/active.yml

# 2. Reload Traefik configuration
docker exec traefik kill -HUP 1

# 3. Monitor health metrics during switch
./scripts/monitor_deployment.sh

# 4. Verify traffic is flowing to green environment
curl -H "Host: api.example.com" http://localhost/healthz
```

**Phase 3: Verification**

```bash
# 1. Monitor application metrics
./scripts/check_metrics.sh

# 2. Run end-to-end tests
./scripts/e2e_test.sh

# 3. Check error rates and performance
./scripts/performance_check.sh

# 4. Validate user experience
./scripts/user_experience_test.sh
```

**Phase 4: Cleanup**

```bash
# 1. Terminate old environment (blue)
docker-compose -f docker-compose.prod.yml stop app_blue
docker-compose -f docker-compose.prod.yml rm -f app_blue

# 2. Clean up old images
docker image prune -f

# 3. Update monitoring configuration
./scripts/update_monitoring.sh

# 4. Document deployment results
./scripts/document_deployment.sh
```

### Rollback Procedure

**Automatic Rollback Triggers**:
- Health check failures (>3 consecutive failures)
- Error rate exceeding 5%
- Response time degradation (>2x baseline)
- Memory usage exceeding 90%

**Manual Rollback Process**:

```bash
# 1. Immediately switch traffic back to blue
cp traefik/dynamic/blue.yml traefik/dynamic/active.yml
docker exec traefik kill -HUP 1

# 2. Verify traffic is flowing to blue
curl -H "Host: api.example.com" http://localhost/healthz

# 3. Terminate problematic green environment
docker-compose -f docker-compose.prod.yml stop app_green
docker-compose -f docker-compose.prod.yml rm -f app_green

# 4. Investigate and document issues
./scripts/investigate_rollback.sh

# 5. Notify stakeholders
./scripts/notify_rollback.sh
```

## Monitoring and Observability

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'websocket-app'
    static_configs:
      - targets: ['app_blue:8000', 'app_green:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
    scrape_interval: 30s

  - job_name: 'traefik'
    static_configs:
      - targets: ['traefik:8080']
    scrape_interval: 10s
```

### Alert Rules

```yaml
# alert_rules.yml
groups:
  - name: websocket_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(websocket_errors_total[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      - alert: HighConnectionCount
        expr: websocket_active_connections > 8000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High connection count"
          description: "Active connections: {{ $value }}"

      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanizePercentage }}"

      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service is down"
          description: "Service {{ $labels.instance }} is down"
```

### Grafana Dashboards

**WebSocket Overview Dashboard**:
- Active connections per instance
- Message throughput and latency
- Error rates by type
- Connection establishment metrics
- System resource utilization

**Application Performance Dashboard**:
- Request/response times
- Database query performance
- Redis operation metrics
- Memory and CPU usage
- Network I/O statistics

**Infrastructure Health Dashboard**:
- Container health status
- Disk and memory usage
- Network connectivity
- SSL certificate status
- Load balancer metrics

## Operational Procedures

### Daily Operations

**Morning Health Check**:
```bash
# 1. Check system health
./scripts/health_check.sh

# 2. Review overnight metrics
./scripts/review_metrics.sh

# 3. Check error logs
./scripts/check_errors.sh

# 4. Validate backup status
./scripts/check_backups.sh
```

**Performance Monitoring**:
```bash
# 1. Monitor key metrics
./scripts/monitor_performance.sh

# 2. Check resource utilization
./scripts/check_resources.sh

# 3. Analyze slow queries
./scripts/analyze_queries.sh

# 4. Review connection patterns
./scripts/analyze_connections.sh
```

### Incident Response

**Incident Classification**:
- **P0 (Critical)**: Service completely down, data loss
- **P1 (High)**: Major functionality broken, high error rates
- **P2 (Medium)**: Minor functionality issues, performance degradation
- **P3 (Low)**: Cosmetic issues, minor bugs

**Incident Response Process**:

1. **Detection and Alerting**
   - Automated monitoring detects issues
   - Alerts sent to on-call engineer
   - Initial assessment and classification

2. **Response and Mitigation**
   - Immediate mitigation steps
   - Communication to stakeholders
   - Escalation if needed

3. **Investigation and Resolution**
   - Root cause analysis
   - Implementation of fix
   - Verification of resolution

4. **Post-Incident Review**
   - Documentation of incident
   - Lessons learned discussion
   - Process improvements

**Common Incident Scenarios**:

**High Error Rate**:
```bash
# 1. Check application logs
docker logs app_blue --tail 100

# 2. Check system resources
docker stats

# 3. Restart application if needed
docker-compose restart app_blue

# 4. Monitor recovery
./scripts/monitor_recovery.sh
```

**Memory Exhaustion**:
```bash
# 1. Check memory usage
docker stats --format "table {{.Container}}\t{{.MemUsage}}"

# 2. Restart with increased memory
docker-compose -f docker-compose.prod.yml up -d --scale app_blue=2

# 3. Investigate memory leaks
./scripts/analyze_memory.sh
```

**Database Connectivity Issues**:
```bash
# 1. Check database status
docker exec postgres pg_isready

# 2. Check connection pool
./scripts/check_db_connections.sh

# 3. Restart database if needed
docker-compose restart postgres
```

## Backup and Recovery

### Backup Strategy

**Database Backups**:
```bash
# Daily full backup
docker exec postgres pg_dump -U user websocket > backup_$(date +%Y%m%d).sql

# Hourly incremental backup
docker exec postgres pg_dump -U user websocket --data-only > incremental_$(date +%Y%m%d_%H).sql
```

**Redis Persistence**:
```bash
# Enable AOF persistence
docker exec redis redis-cli CONFIG SET appendonly yes

# Create snapshot
docker exec redis redis-cli BGSAVE
```

**Configuration Backups**:
```bash
# Backup configuration files
tar -czf config_backup_$(date +%Y%m%d).tar.gz traefik/ docker/

# Backup SSL certificates
cp -r ssl/ ssl_backup_$(date +%Y%m%d)/
```

### Recovery Procedures

**Database Recovery**:
```bash
# 1. Stop application
docker-compose stop app_blue app_green

# 2. Restore database
docker exec -i postgres psql -U user websocket < backup_20240101.sql

# 3. Restart application
docker-compose start app_blue app_green

# 4. Verify data integrity
./scripts/verify_data.sh
```

**Configuration Recovery**:
```bash
# 1. Restore configuration
tar -xzf config_backup_20240101.tar.gz

# 2. Restore SSL certificates
cp -r ssl_backup_20240101/* ssl/

# 3. Reload Traefik
docker exec traefik kill -HUP 1

# 4. Verify configuration
./scripts/verify_config.sh
```

## Security Considerations

### SSL/TLS Configuration

**Certificate Management**:
- Use Let's Encrypt for automatic certificate renewal
- Implement certificate pinning for critical domains
- Monitor certificate expiration dates
- Maintain certificate revocation lists

**Security Headers**:
```yaml
# Traefik security headers
security-headers:
  headers:
    frameDeny: true
    sslRedirect: true
    browserXssFilter: true
    contentTypeNosniff: true
    forceSTSHeader: true
    stsIncludeSubdomains: true
    stsPreload: true
    stsSeconds: 31536000
```

### Access Control

**Network Security**:
- Implement firewall rules to restrict access
- Use VPN for administrative access
- Monitor network traffic for anomalies
- Implement DDoS protection

**Application Security**:
- Regular security updates and patches
- Input validation and sanitization
- Rate limiting and abuse prevention
- Audit logging for security events

## Performance Optimization

### Application Tuning

**Django Settings Optimization**:
```python
# settings.py
DEBUG = False
ALLOWED_HOSTS = ['api.example.com']

# Database optimization
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'websocket',
        'USER': 'user',
        'PASSWORD': 'pass',
        'HOST': 'postgres',
        'PORT': '5432',
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'MAX_CONNS': 20,
        }
    }
}

# Redis optimization
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('redis', 6379)],
            "capacity": 1500,
            "expiry": 10,
        },
    },
}
```

**Uvicorn Configuration**:
```bash
# uvicorn configuration
uvicorn app.asgi:application \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --access-log \
    --log-level info
```

### Infrastructure Optimization

**Resource Allocation**:
- Monitor and adjust CPU/memory limits
- Implement auto-scaling based on metrics
- Optimize disk I/O with SSD storage
- Use connection pooling for databases

**Network Optimization**:
- Implement CDN for static assets
- Use HTTP/2 for improved performance
- Optimize DNS resolution
- Implement connection keep-alive

This deployment guide provides comprehensive coverage of production deployment procedures, monitoring strategies, and operational best practices. Regular review and updates of this documentation ensure continued operational excellence and system reliability.
