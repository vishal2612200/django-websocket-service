# Comprehensive Monitoring Setup Guide

A production-grade monitoring and observability solution for WebSocket applications using the **Prometheus + Grafana + Alertmanager** stack with enterprise-level features and best practices.

## Table of Contents

- [Overview](#overview)
- [Architecture & Design](#architecture--design)
- [Deployment Options](#deployment-options)
- [Configuration Management](#configuration-management)
- [Metrics & Observability](#metrics--observability)
- [Alerting & Incident Management](#alerting--incident-management)
- [Dashboard Management](#dashboard-management)
- [Operations & Maintenance](#operations--maintenance)
- [Troubleshooting & Debugging](#troubleshooting--debugging)
- [Production Hardening](#production-hardening)
- [Performance Optimization](#performance-optimization)

## Overview

This monitoring stack provides enterprise-grade observability with:

- **Comprehensive metrics collection** via Prometheus with configurable retention
- **Advanced visualization** through Grafana with pre-built dashboards
- **Intelligent alerting** with Alertmanager for incident response
- **High availability** design with redundancy and failover capabilities
- **Security-first** approach with authentication, authorization, and encryption
- **Scalable architecture** supporting thousands of metrics and alerts

### Key Features

| Feature | Description | Benefit |
|---------|-------------|---------|
| **Real-time Monitoring** | Sub-second metric collection and alerting | Immediate incident detection |
| **Historical Analysis** | Long-term data retention and trend analysis | Capacity planning and optimization |
| **Multi-dimensional Alerting** | Context-aware alerts with severity levels | Reduced false positives |
| **Auto-discovery** | Dynamic target discovery and configuration | Reduced operational overhead |
| **Integration Ready** | Webhook support for external systems | Seamless DevOps integration |

## Architecture & Design

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Load Balancer                           │
│                    (nginx/traefik)                             │
└─────────────────────┬───────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
┌───────▼──────┐ ┌────▼────┐ ┌─────▼─────┐
│   Grafana    │ │Prometheus│ │Alertmanager│
│   (UI/API)   │ │(Metrics) │ │ (Alerts)  │
└──────────────┘ └──────────┘ └───────────┘
        │             │             │
        └─────────────┼─────────────┘
                      │
              ┌───────▼──────┐
              │  WebSocket   │
              │ Application  │
              │  (Target)    │
              └──────────────┘
```

### Component Responsibilities

| Component | Port | Purpose | Configuration | Resource Requirements |
|-----------|------|---------|---------------|----------------------|
| **Prometheus** | 9090 | Metrics collection, storage, querying | `prometheus.yml` | 2-4 CPU, 8-16GB RAM |
| **Grafana** | 3000 | Dashboard visualization, alerting UI | Auto-provisioned | 1-2 CPU, 2-4GB RAM |
| **Alertmanager** | 9093 | Alert routing, deduplication, silencing | `alertmanager.yml` | 1 CPU, 1-2GB RAM |
| **WebSocket App** | 80 | Application metrics exposure | Built-in `/metrics` | Application dependent |

### Data Flow

1. **Metrics Collection**: Prometheus scrapes `/metrics` endpoint every 10s
2. **Data Storage**: Time-series data stored in Prometheus with configurable retention
3. **Alert Evaluation**: Prometheus evaluates alert rules against collected metrics
4. **Alert Routing**: Alertmanager receives alerts and routes to appropriate channels
5. **Visualization**: Grafana queries Prometheus for dashboard rendering

## Deployment Options

### Option 1: Automated Deployment (Recommended)

```bash
# Run the comprehensive setup script
./scripts/setup_monitoring.sh

# Verify deployment
./scripts/setup_monitoring.sh verify

# Check service health
./scripts/setup_monitoring.sh health
```

### Option 2: Manual Deployment

```bash
# Navigate to docker directory
cd docker

# Deploy with production configuration
docker-compose -f monitoring-compose.yml up -d

# Verify all services are running
docker-compose -f monitoring-compose.yml ps

# Check service logs
docker-compose -f monitoring-compose.yml logs -f
```

### Option 3: Kubernetes Deployment

```bash
# Apply monitoring stack to Kubernetes
kubectl apply -f k8s/monitoring/

# Verify deployment
kubectl get pods -n monitoring

# Port forward for local access
kubectl port-forward -n monitoring svc/grafana 3000:3000
kubectl port-forward -n monitoring svc/prometheus 9090:9090
```

## Configuration Management

### Service Access & Security

| Service | URL | Credentials | Purpose | Security Level |
|---------|-----|-------------|---------|----------------|
| **Grafana** | http://localhost:3000 | `admin/admin123` | Dashboard & visualization | Basic auth |
| **Prometheus** | http://localhost:9090 | None | Metrics querying | Network isolation |
| **Alertmanager** | http://localhost:9093 | None | Alert management | Network isolation |

### Environment Configuration

```bash
# Grafana Configuration
export GF_SECURITY_ADMIN_PASSWORD=admin123
export GF_USERS_ALLOW_SIGN_UP=false
export GF_SERVER_DOMAIN=localhost
export GF_SERVER_ROOT_URL=http://localhost:3000

# Prometheus Configuration
export PROMETHEUS_CONFIG_FILE=/etc/prometheus/prometheus.yml
export PROMETHEUS_STORAGE_TSDB_RETENTION_TIME=30d
export PROMETHEUS_STORAGE_TSDB_RETENTION_SIZE=50GB

# Alertmanager Configuration
export ALERTMANAGER_CONFIG_FILE=/etc/alertmanager/alertmanager.yml
export ALERTMANAGER_STORAGE_PATH=/alertmanager
```

### Configuration Files Structure

```
docker/
├── monitoring-compose.yml          # Main Docker Compose file
├── prometheus.yml                  # Prometheus configuration
├── alert_rules.yml                 # Alerting rules
├── alertmanager.yml                # Alertmanager configuration
└── grafana/
    ├── provisioning/
    │   ├── dashboards/             # Dashboard definitions
    │   └── datasources/            # Data source configurations
    └── dashboards/                 # Dashboard JSON files
```

## Metrics & Observability

### Core Application Metrics

The WebSocket application exposes comprehensive Prometheus metrics:

#### Connection Metrics
```promql
# Active WebSocket connections
app_active_connections

# Connection lifecycle events
app_connections_opened_total
app_connections_closed_total
app_connections_duration_seconds

# Session management
app_sessions_tracked
app_sessions_active
app_sessions_expired_total
```

#### Performance Metrics
```promql
# Message processing
app_messages_total
app_messages_processed_total
app_messages_failed_total
rate(app_messages_total[1m])  # Messages per second

# Error tracking
app_errors_total
app_errors_by_type_total
rate(app_errors_total[1m])    # Error rate

# Latency metrics
app_message_latency_seconds
app_connection_latency_seconds
```

#### System Metrics
```promql
# Process metrics (auto-collected)
process_cpu_seconds_total
process_resident_memory_bytes
process_virtual_memory_bytes
process_open_fds
process_max_fds

# Go runtime metrics (if applicable)
go_goroutines
go_threads
go_memstats_alloc_bytes
```

### Key Performance Indicators (KPIs)

| Metric Category | KPI | Healthy Range | Warning Threshold | Critical Threshold |
|----------------|-----|---------------|-------------------|-------------------|
| **Availability** | Service uptime | > 99.9% | < 99.5% | < 99.0% |
| **Performance** | Message latency (95th percentile) | < 100ms | 100-500ms | > 500ms |
| **Throughput** | Messages per second | > 1000 msg/sec | 100-1000 msg/sec | < 100 msg/sec |
| **Reliability** | Error rate | < 0.1% | 0.1-1% | > 1% |
| **Capacity** | Active connections | < 80% of max | 80-90% | > 90% |

### Advanced Metrics Queries

#### Business Metrics
```promql
# User engagement
rate(app_messages_total[5m]) / app_active_connections

# Connection churn rate
rate(app_connections_closed_total[5m]) / app_active_connections

# Message success rate
rate(app_messages_processed_total[5m]) / rate(app_messages_total[5m]) * 100
```

#### Operational Metrics
```promql
# Memory utilization
(process_resident_memory_bytes / process_virtual_memory_bytes) * 100

# CPU utilization
rate(process_cpu_seconds_total[5m]) * 100

# File descriptor usage
process_open_fds / process_max_fds * 100
```

#### Predictive Metrics
```promql
# Connection growth rate
deriv(app_active_connections[10m])

# Error trend
deriv(rate(app_errors_total[5m])[10m])

# Capacity forecasting
predict_linear(app_active_connections[1h], 3600)
```

## Alerting & Incident Management

### Alert Strategy

The alerting system follows a **three-tier approach**:

1. **Critical Alerts**: Immediate response required (P0)
2. **Warning Alerts**: Attention needed within 30 minutes (P1)
3. **Info Alerts**: Monitoring and trend analysis (P2)

### Pre-configured Alert Rules

#### Critical Alerts (P0)

```yaml
# Service Down Alert
- alert: WebSocketServiceDown
  expr: up{job="websocket-app"} == 0
  for: 30s
  labels:
    severity: critical
    team: websocket
    priority: p0
  annotations:
    summary: "WebSocket service is down"
    description: "Service {{ $labels.instance }} has been down for more than 30 seconds"
    runbook_url: "https://wiki.company.com/runbooks/websocket-service-down"

# No Active Connections
- alert: NoActiveConnections
  expr: app_active_connections == 0
  for: 60s
  labels:
    severity: critical
    team: websocket
    priority: p0
  annotations:
    summary: "No active WebSocket connections"
    description: "No active connections for more than 60 seconds"
    impact: "Users cannot connect to the service"

# High Error Rate
- alert: HighErrorRate
  expr: rate(app_errors_total[2m]) > 10
  for: 2m
  labels:
    severity: critical
    team: websocket
    priority: p0
  annotations:
    summary: "High error rate detected"
    description: "Error rate is {{ $value }} errors per second"
    threshold: "10 errors per second"
```

#### Warning Alerts (P1)

```yaml
# High Memory Usage
- alert: HighMemoryUsage
  expr: (process_resident_memory_bytes / process_virtual_memory_bytes) * 100 > 85
  for: 5m
  labels:
    severity: warning
    team: websocket
    priority: p1
  annotations:
    summary: "High memory usage"
    description: "Memory usage is {{ $value }}%"
    recommendation: "Consider scaling or memory optimization"

# Slow Message Processing
- alert: SlowMessageProcessing
  expr: histogram_quantile(0.95, rate(app_message_latency_seconds_bucket[5m])) > 0.5
  for: 5m
  labels:
    severity: warning
    team: websocket
    priority: p1
  annotations:
    summary: "Slow message processing"
    description: "95th percentile latency is {{ $value }} seconds"
    threshold: "0.5 seconds"
```

#### Info Alerts (P2)

```yaml
# High Connection Count
- alert: HighConnectionCount
  expr: app_active_connections > 1000
  for: 10m
  labels:
    severity: info
    team: websocket
    priority: p2
  annotations:
    summary: "High connection count"
    description: "{{ $value }} active connections"
    note: "Monitor for capacity planning"

# Deployment Detected
- alert: DeploymentDetected
  expr: changes(app_active_connections[5m]) > 0
  labels:
    severity: info
    team: websocket
    priority: p2
  annotations:
    summary: "Deployment detected"
    description: "Service activity change detected"
```

### Alert Routing Configuration

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m
  slack_api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'

route:
  group_by: ['alertname', 'severity', 'team']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'websocket-team'
  routes:
    - match:
        severity: critical
      receiver: 'pager-duty-critical'
      continue: true
    - match:
        severity: warning
      receiver: 'slack-warnings'
      continue: true

receivers:
  - name: 'websocket-team'
    slack_configs:
      - channel: '#websocket-alerts'
        title: '{{ template "slack.title" . }}'
        text: '{{ template "slack.text" . }}'
        send_resolved: true

  - name: 'pager-duty-critical'
    pagerduty_configs:
      - routing_key: 'YOUR_PAGERDUTY_KEY'
        description: '{{ template "pagerduty.description" . }}'
        severity: '{{ if eq .GroupLabels.severity "critical" }}critical{{ else }}warning{{ end }}'

  - name: 'slack-warnings'
    slack_configs:
      - channel: '#websocket-warnings'
        title: '{{ template "slack.title" . }}'
        text: '{{ template "slack.text" . }}'
        send_resolved: true
```

### Incident Response Workflow

1. **Alert Detection**: Alertmanager receives alert from Prometheus
2. **Alert Grouping**: Similar alerts are grouped to prevent spam
3. **Notification Routing**: Alerts routed based on severity and team
4. **Escalation**: Critical alerts escalate to PagerDuty for immediate response
5. **Resolution**: Team acknowledges and resolves the incident
6. **Post-mortem**: Incident review and process improvement

## Dashboard Management

### Pre-built Dashboards

#### WebSocket Comprehensive Overview

**Dashboard ID**: `d323749f-135e-455a-aa74-4915a52ef0b9`

**Key Features**:
- **Real-time metrics** with 10-second refresh rate
- **Multi-panel layout** for comprehensive monitoring
- **Color-coded thresholds** for quick status assessment
- **Interactive elements** for drill-down analysis

**Panel Categories**:

1. **Key Metrics (Top Row)**
   - Active Connections Gauge
   - Total Messages Counter
   - Error Count with Trend
   - Sessions Tracked

2. **Performance Analytics (Second Row)**
   - Message Rate Time Series
   - Error Rate Analysis
   - Connection Event Rate
   - Latency Distribution

3. **System Health (Third Row)**
   - Memory Utilization
   - CPU Usage
   - File Descriptor Usage
   - Process Metrics

4. **Operational Insights (Fourth Row)**
   - Service Status
   - Target Health
   - Scrape Performance
   - Alert Status

### Dashboard Customization

#### Creating Custom Dashboards

1. **Access Grafana**: http://localhost:3000
2. **Create Dashboard**: Click "+" → "Dashboard"
3. **Add Data Source**: Select Prometheus
4. **Configure Panels**: Add panels with PromQL queries
5. **Set Thresholds**: Configure color-coded thresholds
6. **Save Dashboard**: Save with descriptive name

#### Advanced Panel Configuration

```json
{
  "title": "Message Processing Rate",
  "type": "timeseries",
  "targets": [
    {
      "expr": "rate(app_messages_total[1m])",
      "legendFormat": "Messages/sec"
    }
  ],
  "fieldConfig": {
    "defaults": {
      "color": {
        "mode": "palette-classic"
      },
      "custom": {
        "thresholds": {
          "steps": [
            {"color": "green", "value": null},
            {"color": "yellow", "value": 100},
            {"color": "red", "value": 500}
          ]
        }
      }
    }
  }
}
```

#### Dashboard Variables

```json
{
  "variables": [
    {
      "name": "instance",
      "type": "query",
      "query": "label_values(app_active_connections, instance)",
      "refresh": 2
    },
    {
      "name": "severity",
      "type": "custom",
      "options": [
        {"text": "All", "value": ".*"},
        {"text": "Critical", "value": "critical"},
        {"text": "Warning", "value": "warning"}
      ]
    }
  ]
}
```

### Dashboard Provisioning

```yaml
# grafana/provisioning/dashboards/dashboard.yml
apiVersion: 1

providers:
  - name: 'websocket-dashboards'
    orgId: 1
    folder: 'WebSocket Monitoring'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
```

## Operations & Maintenance

### Daily Operations

#### Health Checks

```bash
# Automated health check script
#!/bin/bash

echo "=== Monitoring Stack Health Check ==="
echo "Timestamp: $(date)"

# Check Prometheus
echo -n "Prometheus: "
if curl -s http://localhost:9090/api/v1/query?query=up | grep -q "1"; then
    echo " Healthy"
else
    echo " Unhealthy"
fi

# Check Grafana
echo -n "Grafana: "
if curl -s -u admin:admin123 http://localhost:3000/api/health | grep -q "ok"; then
    echo " Healthy"
else
    echo " Unhealthy"
fi

# Check Alertmanager
echo -n "Alertmanager: "
if curl -s http://localhost:9093/api/v1/status | grep -q "ready"; then
    echo " Healthy"
else
    echo " Unhealthy"
fi

# Check application metrics
echo -n "Application Metrics: "
if curl -s http://localhost:9090/api/v1/query?query=app_active_connections | grep -q "result"; then
    echo " Available"
else
    echo " Missing"
fi

echo "=== Health Check Complete ==="
```

#### Performance Monitoring

```bash
# Monitor resource usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# Check Prometheus performance
curl -s http://localhost:9090/api/v1/query?query=scrape_duration_seconds | jq '.data.result[0].value[1]'

# Monitor Grafana performance
curl -s -u admin:admin123 http://localhost:3000/api/admin/stats | jq '.dashboard_count'
```

### Weekly Maintenance

#### Alert Review

```bash
# Review active alerts
curl -s http://localhost:9093/api/v1/alerts | jq '.[] | {alertname: .labels.alertname, severity: .labels.severity, status: .status.state}'

# Check alert history
curl -s http://localhost:9093/api/v1/alerts/groups | jq '.[] | {name: .name, alerts: [.alerts[] | {alertname: .labels.alertname, severity: .labels.severity}]}'
```

#### Metrics Audit

```bash
# List all available metrics
curl -s http://localhost:9090/api/v1/label/__name__/values | jq '.data[]' | grep "app_"

# Check metric cardinality
curl -s http://localhost:9090/api/v1/status/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health, lastError: .lastError}'
```

### Monthly Maintenance

#### Configuration Updates

```bash
# Backup current configuration
tar -czf monitoring-config-$(date +%Y%m%d).tar.gz \
  docker/prometheus.yml \
  docker/alert_rules.yml \
  docker/alertmanager.yml \
  docker/grafana/

# Update component versions
docker-compose -f docker/monitoring-compose.yml pull
docker-compose -f docker/monitoring-compose.yml up -d
```

#### Performance Optimization

```bash
# Analyze query performance
curl -s http://localhost:9090/api/v1/query?query=rate(app_messages_total[1m]) | jq '.stats'

# Check storage usage
du -sh /var/lib/prometheus/data/
du -sh /var/lib/grafana/
```

## Troubleshooting & Debugging

### Common Issues & Solutions

#### 1. Prometheus Scraping Failures

**Symptoms**: No data in dashboards, empty targets page

**Diagnosis**:
```bash
# Check target status
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="websocket-app")'

# Test metrics endpoint
curl -v http://localhost/metrics

# Check Prometheus logs
docker-compose -f docker/monitoring-compose.yml logs prometheus
```

**Resolution**:
- Verify application is running and accessible
- Check network connectivity between containers
- Validate Prometheus configuration syntax
- Ensure `/metrics` endpoint returns valid Prometheus format

#### 2. Grafana Connection Issues

**Symptoms**: "No data" in dashboard panels, datasource errors

**Diagnosis**:
```bash
# Test Prometheus connectivity from Grafana
docker exec grafana wget -qO- http://prometheus:9090/api/v1/query?query=up

# Check datasource configuration
curl -s -u admin:admin123 http://localhost:3000/api/datasources | jq '.[] | {name: .name, type: .type, url: .url}'

# Verify Grafana logs
docker-compose -f docker/monitoring-compose.yml logs grafana
```

**Resolution**:
- Restart Grafana service
- Verify Prometheus URL in datasource configuration
- Check network connectivity
- Validate datasource provisioning

#### 3. Alertmanager Issues

**Symptoms**: Alerts not being sent, notification failures

**Diagnosis**:
```bash
# Check Alertmanager status
curl -s http://localhost:9093/api/v1/status | jq '.configYAML'

# Test notification channels
curl -s http://localhost:9093/api/v1/testReceivers | jq '.'

# Review Alertmanager logs
docker-compose -f docker/monitoring-compose.yml logs alertmanager
```

**Resolution**:
- Validate Alertmanager configuration
- Check notification channel credentials
- Verify network connectivity to external services
- Test notification templates

#### 4. High Resource Usage

**Symptoms**: Slow dashboard loading, high CPU/memory consumption

**Diagnosis**:
```bash
# Monitor resource usage
docker stats --no-stream

# Check Prometheus performance
curl -s http://localhost:9090/api/v1/query?query=scrape_duration_seconds | jq '.data.result[0].value[1]'

# Analyze query performance
curl -s http://localhost:9090/api/v1/query?query=rate(app_messages_total[1m]) | jq '.stats'
```

**Resolution**:
- Optimize scrape intervals
- Reduce query complexity
- Implement query caching
- Scale resources or components

### Debugging Tools

#### Prometheus Debugging

```bash
# Query debugging
curl -s "http://localhost:9090/api/v1/query?query=app_active_connections&debug=true"

# Configuration validation
docker exec prometheus promtool check config /etc/prometheus/prometheus.yml

# Rule validation
docker exec prometheus promtool check rules /etc/prometheus/alert_rules.yml
```

#### Grafana Debugging

```bash
# Enable debug logging
docker-compose -f docker/monitoring-compose.yml exec grafana grafana-cli admin reset-admin-password

# Check plugin status
curl -s -u admin:admin123 http://localhost:3000/api/plugins | jq '.[] | {name: .name, enabled: .enabled}'

# Export dashboard for analysis
curl -s -u admin:admin123 http://localhost:3000/api/dashboards/uid/d323749f-135e-455a-aa74-4915a52ef0b9 | jq '.dashboard'
```

#### Alertmanager Debugging

```bash
# Test alert routing
curl -X POST http://localhost:9093/api/v1/alerts -d '[
  {
    "labels": {
      "alertname": "TestAlert",
      "severity": "critical"
    },
    "annotations": {
      "summary": "Test alert",
      "description": "This is a test alert"
    }
  }
]'

# Check silence status
curl -s http://localhost:9093/api/v1/silences | jq '.[] | {id: .id, status: .status.state}'
```

## Production Hardening

### Security Configuration

#### Authentication & Authorization

```yaml
# Grafana security configuration
security:
  admin_user: admin
  admin_password: ${GF_SECURITY_ADMIN_PASSWORD}
  disable_initial_admin_creation: false
  allow_embedding: false
  cookie_secure: true
  cookie_samesite: strict

auth:
  disable_signout_menu: false
  oauth_auto_login: false
  login_cookie_name: grafana_session
```

#### Network Security

```yaml
# Docker Compose network configuration
networks:
  monitoring:
    driver: bridge
    internal: true
    ipam:
      config:
        - subnet: 172.20.0.0/16

services:
  prometheus:
    networks:
      - monitoring
    ports:
      - "127.0.0.1:9090:9090"  # Bind to localhost only
```

#### TLS Configuration

```yaml
# Prometheus TLS configuration
tls_config:
  ca_file: /etc/prometheus/certs/ca.crt
  cert_file: /etc/prometheus/certs/prometheus.crt
  key_file: /etc/prometheus/certs/prometheus.key
  server_name: prometheus.example.com
```

### Data Persistence

#### Volume Configuration

```yaml
# Docker Compose volumes
volumes:
  prometheus_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/prometheus
  grafana_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/grafana
  alertmanager_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/alertmanager
```

#### Backup Strategy

```bash
#!/bin/bash
# Automated backup script

BACKUP_DIR="/backups/monitoring"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup Prometheus data
docker run --rm -v prometheus_data:/data -v "$BACKUP_DIR":/backup alpine tar czf "/backup/prometheus_$DATE.tar.gz" -C /data .

# Backup Grafana data
docker run --rm -v grafana_data:/data -v "$BACKUP_DIR":/backup alpine tar czf "/backup/grafana_$DATE.tar.gz" -C /data .

# Backup configuration
tar czf "$BACKUP_DIR/config_$DATE.tar.gz" \
  docker/prometheus.yml \
  docker/alert_rules.yml \
  docker/alertmanager.yml \
  docker/grafana/

# Cleanup old backups (keep 30 days)
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR"
```

### High Availability

#### Prometheus Federation

```yaml
# Federated Prometheus configuration
scrape_configs:
  - job_name: 'federate'
    honor_labels: true
    metrics_path: '/federate'
    params:
      'match[]':
        - '{job="websocket-app"}'
    static_configs:
      - targets:
        - 'prometheus-1:9090'
        - 'prometheus-2:9090'
```

#### Grafana Clustering

```yaml
# Grafana clustering configuration
[database]
type = postgres
host = postgres:5432
name = grafana
user = grafana
password = ${DB_PASSWORD}

[session]
provider = postgres
provider_config = "user=grafana password=${DB_PASSWORD} host=postgres dbname=grafana sslmode=disable"
```

#### Load Balancing

```nginx
# Nginx configuration for load balancing
upstream grafana {
    server grafana-1:3000;
    server grafana-2:3000;
    server grafana-3:3000;
}

upstream prometheus {
    server prometheus-1:9090;
    server prometheus-2:9090;
}

server {
    listen 80;
    server_name monitoring.example.com;

    location /grafana/ {
        proxy_pass http://grafana/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /prometheus/ {
        proxy_pass http://prometheus/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Performance Optimization

### Prometheus Optimization

#### Storage Optimization

```yaml
# Prometheus storage configuration
storage:
  tsdb:
    retention.time: 30d
    retention.size: 50GB
    wal:
      retention.period: 12h
    out_of_order_time_window: 10m
```

#### Query Optimization

```promql
# Optimized queries for better performance
# Instead of: rate(app_messages_total[1m])
# Use: rate(app_messages_total[5m])

# Instead of: histogram_quantile(0.95, rate(app_latency_bucket[1m]))
# Use: histogram_quantile(0.95, rate(app_latency_bucket[5m]))
```

#### Scrape Optimization

```yaml
# Optimized scrape configuration
scrape_configs:
  - job_name: 'websocket-app'
    scrape_interval: 15s
    scrape_timeout: 10s
    honor_labels: true
    metrics_path: /metrics
    static_configs:
      - targets: ['host.docker.internal:80']
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: 'app_.*'
        action: keep
```

### Grafana Optimization

#### Dashboard Optimization

```json
{
  "refresh": "30s",
  "time": {
    "from": "now-1h",
    "to": "now"
  },
  "templating": {
    "list": []
  },
  "panels": [
    {
      "targets": [
        {
          "expr": "rate(app_messages_total[5m])",
          "interval": "30s",
          "legendFormat": "Messages/sec"
        }
      ]
    }
  ]
}
```

#### Query Caching

```ini
# Grafana query caching configuration
[query_cache]
enabled = true
max_memory = 1GB
max_disk = 10GB
ttl = 5m
```

### Resource Optimization

#### Docker Resource Limits

```yaml
# Resource limits for production
services:
  prometheus:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 16G
        reservations:
          cpus: '2'
          memory: 8G

  grafana:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

  alertmanager:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
```

#### Monitoring Stack Health

```bash
#!/bin/bash
# Comprehensive health check script

echo "=== Monitoring Stack Health Report ==="
echo "Generated: $(date)"
echo ""

# System resources
echo "=== System Resources ==="
echo "CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "Memory Usage: $(free | grep Mem | awk '{printf("%.2f%%", $3/$2 * 100.0)}')"
echo "Disk Usage: $(df / | tail -1 | awk '{print $5}')"
echo ""

# Service health
echo "=== Service Health ==="
services=("prometheus" "grafana" "alertmanager")
for service in "${services[@]}"; do
    if docker ps | grep -q "$service"; then
        echo " $service: Running"
    else
        echo " $service: Not running"
    fi
done
echo ""

# Metrics availability
echo "=== Metrics Availability ==="
if curl -s http://localhost:9090/api/v1/query?query=up | grep -q "1"; then
    echo " Prometheus: Healthy"
    echo " Application metrics: Available"
else
    echo " Prometheus: Unhealthy"
    echo " Application metrics: Unavailable"
fi
echo ""

# Alert status
echo "=== Alert Status ==="
active_alerts=$(curl -s http://localhost:9093/api/v1/alerts | jq 'length')
echo "Active alerts: $active_alerts"
echo ""

echo "=== Health Report Complete ==="
```

This comprehensive monitoring setup provides enterprise-grade observability with production-ready features, security hardening, and performance optimization. The system is designed to scale with your application while maintaining reliability and ease of operation.
