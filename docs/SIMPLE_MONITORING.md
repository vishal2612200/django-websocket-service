# Simple Monitoring Setup

A production-ready monitoring solution for WebSocket applications using **Prometheus** and **Grafana** with minimal configuration overhead.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Metrics & Observability](#metrics--observability)
- [Dashboard Features](#dashboard-features)
- [Management & Operations](#management--operations)
- [Troubleshooting](#troubleshooting)
- [Production Considerations](#production-considerations)

## Overview

This monitoring stack provides comprehensive observability for WebSocket applications with:

- **Real-time metrics collection** via Prometheus
- **Advanced visualization** through Grafana dashboards
- **Automated provisioning** with zero manual configuration
- **Production-ready alerting** with configurable thresholds
- **Minimal resource footprint** optimized for development and staging environments

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WebSocket     │    │    Prometheus   │    │     Grafana     │
│   Application   │───▶│   (Metrics      │───▶│   (Dashboard    │
│   (Port 80)     │    │   Collection)   │    │   & Alerts)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
   ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
   │   /metrics  │       │   Port 9090 │       │   Port 3000 │
   │   Endpoint  │       │   (Query)   │       │   (UI)      │
   └─────────────┘       └─────────────┘       └─────────────┘
```

### Component Responsibilities

| Component | Port | Purpose | Configuration |
|-----------|------|---------|---------------|
| **Prometheus** | 9090 | Metrics collection, storage, and querying | `simple-prometheus.yml` |
| **Grafana** | 3000 | Dashboard visualization and alerting | Auto-provisioned |
| **WebSocket App** | 80 | Application metrics exposure | Built-in `/metrics` endpoint |

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Ports 3000, 9090 available
- WebSocket application running on port 80

### Automated Deployment

```bash
# Start the complete monitoring stack
./scripts/monitoring.sh start

# Verify deployment
./scripts/monitoring.sh status

# Access dashboards
open http://localhost:3000
```

### Manual Deployment

```bash
# Navigate to docker directory
cd docker

# Deploy monitoring stack
docker compose -f simple-monitoring.yml up -d

# Verify services
docker compose -f simple-monitoring.yml ps
```

## Configuration

### Service Access

| Service | URL | Credentials | Purpose |
|---------|-----|-------------|---------|
| **Grafana Dashboard** | http://localhost:3000/d/d323749f-135e-455a-aa74-4915a52ef0b9/websocket-service-comprehensive-dashboard | `admin/admin123` | Primary monitoring dashboard |
| **Grafana Home** | http://localhost:3000 | `admin/admin123` | Dashboard management and configuration |
| **Prometheus** | http://localhost:9090 | None | Metrics querying and target management |

### Environment Variables

```bash
# Grafana Configuration
GF_SECURITY_ADMIN_PASSWORD=admin123
GF_USERS_ALLOW_SIGN_UP=false

# Prometheus Configuration
PROMETHEUS_CONFIG_FILE=/etc/prometheus/prometheus.yml
```

## Metrics & Observability

### Core Application Metrics

The WebSocket application automatically exposes these Prometheus metrics:

#### Connection Metrics
```promql
# Active WebSocket connections
app_active_connections

# Total connections opened/closed
app_connections_opened_total
app_connections_closed_total

# Session tracking
app_sessions_tracked
```

#### Performance Metrics
```promql
# Message processing
app_messages_total
rate(app_messages_total[1m])  # Messages per second

# Error tracking
app_errors_total
rate(app_errors_total[1m])    # Error rate

# Shutdown performance
app_shutdown_duration_seconds
```

#### System Metrics
```promql
# Process metrics (auto-collected)
process_cpu_seconds_total
process_resident_memory_bytes
process_virtual_memory_bytes
```

### Key Performance Indicators (KPIs)

| Metric | Description | Healthy Range | Alert Threshold |
|--------|-------------|---------------|-----------------|
| **Active Connections** | Current WebSocket connections | > 0 | 0 for 60s |
| **Message Rate** | Messages processed per second | > 0.1 msg/sec | < 0.1 for 10m |
| **Error Rate** | Errors per minute | < 1 error/min | > 10 for 2m |
| **Shutdown Time** | Graceful shutdown duration | < 5s (95th percentile) | > 5s |

## Dashboard Features

### Comprehensive WebSocket Dashboard

The pre-configured dashboard includes:

#### Real-time Metrics
- **Connection Status**: Live gauge showing active connections with color-coded thresholds
- **Message Throughput**: Time-series graph of message processing rate
- **Error Monitoring**: Error count and rate with alerting integration
- **Session Tracking**: Current session count and trends

#### Performance Analytics
- **Connection Trends**: Historical view of connection patterns
- **Message Flow**: Message rate analysis with anomaly detection
- **System Health**: Memory and CPU utilization monitoring
- **Shutdown Performance**: Graceful shutdown timing distribution

#### Operational Insights
- **Service Status**: Prometheus target health monitoring
- **Scrape Performance**: Metrics collection timing and reliability
- **Alert Status**: Current alert state and history

### Dashboard Customization

#### Adding Custom Panels

1. **Access Grafana**: http://localhost:3000
2. **Edit Dashboard**: Click "Edit" on the dashboard
3. **Add Panel**: Use "Add panel" button
4. **Configure Query**: Use PromQL expressions:

```promql
# Custom message rate calculation
rate(app_messages_total[5m])

# Connection success rate
rate(app_connections_opened_total[5m]) / 
(rate(app_connections_opened_total[5m]) + rate(app_connections_closed_total[5m])) * 100

# Memory usage percentage
(process_resident_memory_bytes / process_virtual_memory_bytes) * 100
```

#### Threshold Configuration

```json
{
  "thresholds": [
    {"color": "green", "value": null},
    {"color": "yellow", "value": 10},
    {"color": "red", "value": 50}
  ]
}
```

## Management & Operations

### Service Management

```bash
# Complete lifecycle management
./scripts/monitoring.sh start      # Deploy monitoring stack
./scripts/monitoring.sh stop       # Graceful shutdown
./scripts/monitoring.sh restart    # Restart all services
./scripts/monitoring.sh status     # Health check
./scripts/monitoring.sh logs       # View service logs
```

### Health Verification

```bash
# Verify Prometheus targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="websocket-app")'

# Check metrics availability
curl -s http://localhost:9090/api/v1/query?query=app_active_connections

# Validate Grafana connectivity
curl -s -u admin:admin123 http://localhost:3000/api/health
```

### Log Management

```bash
# View all monitoring logs
./scripts/monitoring.sh logs

# Follow specific service logs
docker compose -f docker/simple-monitoring.yml logs -f prometheus
docker compose -f docker/simple-monitoring.yml logs -f grafana

# Export logs for analysis
docker compose -f docker/simple-monitoring.yml logs > monitoring-logs-$(date +%Y%m%d).log
```

## Troubleshooting

### Common Issues

#### 1. Prometheus Can't Scrape Metrics

**Symptoms**: No data in Grafana, empty targets page

**Diagnosis**:
```bash
# Check if application is exposing metrics
curl http://localhost/metrics

# Verify Prometheus configuration
curl http://localhost:9090/api/v1/targets
```

**Resolution**:
- Ensure WebSocket application is running on port 80
- Verify `/metrics` endpoint is accessible
- Check Prometheus target configuration in `simple-prometheus.yml`

#### 2. Grafana Can't Connect to Prometheus

**Symptoms**: "No data" in dashboard panels

**Diagnosis**:
```bash
# Check Prometheus connectivity
curl http://localhost:9090/api/v1/query?query=up

# Verify Grafana datasource
curl -u admin:admin123 http://localhost:3000/api/datasources
```

**Resolution**:
- Restart Grafana: `docker compose -f simple-monitoring.yml restart grafana`
- Check network connectivity between containers
- Verify datasource configuration

#### 3. High Resource Usage

**Symptoms**: Slow dashboard loading, high CPU/memory

**Diagnosis**:
```bash
# Check resource usage
docker stats

# Monitor scrape duration
curl http://localhost:9090/api/v1/query?query=scrape_duration_seconds
```

**Resolution**:
- Increase scrape interval in Prometheus config
- Optimize PromQL queries in dashboard
- Consider resource limits in docker-compose

### Performance Optimization

#### Prometheus Configuration

```yaml
# Optimize for development environments
global:
  scrape_interval: 30s      # Reduce from 10s for lower resource usage
  evaluation_interval: 30s

scrape_configs:
  - job_name: 'websocket-app'
    scrape_interval: 30s    # Match global interval
    scrape_timeout: 10s     # Prevent hanging scrapes
```

#### Grafana Optimization

```ini
# grafana.ini optimizations
[performance]
max_concurrent_shifts = 10
max_shift_duration = 24h

[metrics]
enabled = true
interval_seconds = 60
```

## Production Considerations

### Security Hardening

```bash
# Change default passwords
export GF_SECURITY_ADMIN_PASSWORD=$(openssl rand -base64 32)
export PROMETHEUS_BASIC_AUTH_PASSWORD=$(openssl rand -base64 32)

# Enable authentication
docker compose -f simple-monitoring.yml up -d
```

### Data Persistence

```yaml
# Add persistent volumes
volumes:
  prometheus_data:
    driver: local
  grafana_data:
    driver: local

services:
  prometheus:
    volumes:
      - prometheus_data:/prometheus
  grafana:
    volumes:
      - grafana_data:/var/lib/grafana
```

### High Availability

For production environments, consider:

1. **Prometheus Federation**: Centralized metrics aggregation
2. **Grafana Clustering**: Multiple Grafana instances with shared database
3. **Load Balancing**: Reverse proxy for service distribution
4. **Backup Strategy**: Automated configuration and data backups
5. **Monitoring the Monitor**: Self-monitoring of the monitoring stack

### Scaling Considerations

| Component | Scaling Strategy | Resource Requirements |
|-----------|------------------|----------------------|
| **Prometheus** | Vertical scaling (more CPU/memory) | 2-4 CPU cores, 8-16GB RAM |
| **Grafana** | Horizontal scaling with shared DB | 1-2 CPU cores, 2-4GB RAM |
| **Storage** | External time-series database | Depends on retention policy |

### Backup and Recovery

```bash
# Backup configuration
tar -czf monitoring-config-$(date +%Y%m%d).tar.gz \
  docker/simple-prometheus.yml \
  docker/simple-grafana-provisioning/ \
  scripts/monitoring.sh

# Backup data (if using persistent volumes)
docker run --rm -v prometheus_data:/data -v $(pwd):/backup alpine tar czf /backup/prometheus-data-$(date +%Y%m%d).tar.gz -C /data .
```

## Support and Maintenance

### Regular Maintenance Tasks

- **Weekly**: Review alert thresholds and dashboard performance
- **Monthly**: Update Prometheus and Grafana versions
- **Quarterly**: Audit metrics and remove unused ones
- **Annually**: Review and update monitoring strategy

### Monitoring Stack Health

```bash
# Automated health check script
#!/bin/bash
echo "Checking monitoring stack health..."

# Check Prometheus
if curl -s http://localhost:9090/api/v1/query?query=up | grep -q "1"; then
    echo " Prometheus: Healthy"
else
    echo " Prometheus: Unhealthy"
fi

# Check Grafana
if curl -s -u admin:admin123 http://localhost:3000/api/health | grep -q "ok"; then
    echo " Grafana: Healthy"
else
    echo " Grafana: Unhealthy"
fi

# Check application metrics
if curl -s http://localhost:9090/api/v1/query?query=app_active_connections | grep -q "result"; then
    echo " Application Metrics: Available"
else
    echo " Application Metrics: Missing"
fi
```

This monitoring setup provides a solid foundation for observability while maintaining simplicity for development and staging environments. For production deployments, consider implementing the security and scaling recommendations outlined above.
