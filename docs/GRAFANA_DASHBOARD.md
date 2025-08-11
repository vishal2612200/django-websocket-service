# Grafana Dashboard Documentation

## Overview

This document provides comprehensive documentation for the WebSocket Service monitoring dashboard, designed for production environments with enterprise-grade observability requirements.

## Table of Contents

- [Dashboard Overview](#dashboard-overview)
- [Architecture & Design](#architecture--design)
- [Panel Specifications](#panel-specifications)
- [Metrics & Queries](#metrics--queries)
- [Alerting Integration](#alerting-integration)
- [Customization Guide](#customization-guide)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)
- [Maintenance & Updates](#maintenance--updates)

## Dashboard Overview

### Primary Dashboard: WebSocket Service - Comprehensive Dashboard

**Dashboard ID**: `d323749f-135e-455a-aa74-4915a52ef0b9`  
**Version**: 2.1.0  
**Last Updated**: 2024-01-15  
**Refresh Rate**: 10 seconds (configurable)  
**Time Range**: Last 1 hour (default, adjustable)  
**Theme**: Dark mode (production optimized)

### Dashboard Features

| Feature | Description | Business Value |
|---------|-------------|----------------|
| **Real-time Monitoring** | Live metrics with 10-second refresh | Immediate incident detection |
| **Multi-dimensional Views** | Connection, performance, and system metrics | Comprehensive service health |
| **Alert Integration** | Visual alert status and history | Proactive incident management |
| **Performance Analytics** | Trend analysis and anomaly detection | Capacity planning and optimization |
| **Operational Insights** | Service status and scrape performance | Infrastructure reliability |

## Architecture & Design

### Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────┐
│                    WebSocket Service Dashboard                  │
├─────────────────────────────────────────────────────────────────┤
│  [Active Connections] [Total Messages] [Error Count] [Sessions] │
├─────────────────────────────────────────────────────────────────┤
│  [Message Rate]                    [Error Rate]                 │
├─────────────────────────────────────────────────────────────────┤
│  [Connection Trends]              [Connection Events]           │
├─────────────────────────────────────────────────────────────────┤
│  [System Health]                  [Shutdown Performance]       │
├─────────────────────────────────────────────────────────────────┤
│  [Service Status] [Target Health] [Scrape Performance] [Alerts] │
└─────────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Information Hierarchy**: Critical metrics at the top, detailed views below
2. **Color Coding**: Consistent threshold-based color schemes
3. **Responsive Layout**: Adapts to different screen sizes
4. **Performance Focus**: Optimized queries and refresh rates
5. **Operational Readiness**: Quick status assessment capabilities

## Panel Specifications

### Row 1: Key Metrics (Critical KPIs)

#### Active Connections Panel
- **Panel Type**: Gauge/Stat
- **Metric**: `app_active_connections`
- **Description**: Current number of active WebSocket connections
- **Thresholds**:
  - 🔴 Critical: 0 connections (service down)
  - 🟡 Warning: 1-9 connections (low activity)
  - 🟢 Healthy: 10+ connections (normal operation)
- **Business Impact**: Direct measure of service availability
- **Alert Integration**: Triggers critical alert when zero

#### Total Messages Panel
- **Panel Type**: Counter/Stat with trend
- **Metric**: `app_messages_total`
- **Description**: Cumulative messages processed since service start
- **Visualization**: Area graph showing growth over time
- **Business Impact**: Service utilization and throughput indicator
- **Trend Analysis**: Growth rate indicates service adoption

#### Error Count Panel
- **Panel Type**: Counter/Stat with color coding
- **Metric**: `app_errors_total`
- **Description**: Total errors encountered during operation
- **Thresholds**:
  - 🟢 Healthy: 0 errors
  - 🟡 Warning: 1-9 errors
  - 🔴 Critical: 10+ errors
- **Business Impact**: Service reliability and quality indicator
- **Alert Integration**: Triggers warning and critical alerts

#### Sessions Tracked Panel
- **Panel Type**: Gauge/Stat
- **Metric**: `app_sessions_tracked`
- **Description**: Number of user sessions currently tracked
- **Business Impact**: User engagement and session management
- **Capacity Planning**: Helps determine resource requirements

### Row 2: Performance Analytics

#### Message Rate Panel
- **Panel Type**: Time series graph
- **Metric**: `rate(app_messages_total[1m])`
- **Description**: Messages processed per second over 1-minute window
- **Unit**: Messages/second
- **Visualization**: Smooth line with area fill
- **Business Impact**: Real-time throughput measurement
- **Performance Analysis**: Identifies bottlenecks and load patterns

#### Error Rate Panel
- **Panel Type**: Time series graph
- **Metric**: `rate(app_errors_total[1m])`
- **Description**: Errors per second over 1-minute window
- **Unit**: Errors/second
- **Visualization**: Line graph with threshold markers
- **Business Impact**: Service quality and reliability tracking
- **Alert Integration**: Triggers performance degradation alerts

### Row 3: Connection Analytics

#### Active Connections Trend Panel
- **Panel Type**: Time series graph
- **Metric**: `app_active_connections`
- **Description**: Historical view of active connections over time
- **Visualization**: Smooth line with area fill
- **Business Impact**: Connection pattern analysis and capacity planning
- **Anomaly Detection**: Identifies unusual connection patterns

#### Connection Events Panel
- **Panel Type**: Time series graph (dual metrics)
- **Metrics**: 
  - `rate(app_connections_opened_total[1m])`
  - `rate(app_connections_closed_total[1m])`
- **Description**: Rate of connections being opened and closed
- **Unit**: Connections/second
- **Visualization**: Dual lines with different colors
- **Business Impact**: Connection churn analysis and stability assessment

### Row 4: System Health

#### Shutdown Duration Panel
- **Panel Type**: Time series graph
- **Metric**: `app_shutdown_duration_seconds`
- **Description**: Time taken for graceful shutdown operations
- **Unit**: Seconds
- **Visualization**: Line graph with percentile markers
- **Business Impact**: Service reliability during deployments
- **Performance Optimization**: Identifies slow shutdown patterns

#### System Health Overview Panel
- **Panel Type**: Table/Stat panels
- **Metrics**: All key metrics in tabular format
- **Description**: Quick overview of all system metrics
- **Business Impact**: At-a-glance system status assessment
- **Operational Efficiency**: Reduces time to identify issues

### Row 5: Monitoring Infrastructure

#### Service Status Panel
- **Panel Type**: Stat panel
- **Metric**: `up{job="websocket-app"}`
- **Description**: Whether the service is UP (1) or DOWN (0)
- **Visualization**: Text display with color coding
- **Business Impact**: Direct service availability indicator
- **Alert Integration**: Primary service health check

#### Target Health Panel
- **Panel Type**: Stat panel
- **Metric**: `up{job="websocket-app"}`
- **Description**: Prometheus target health status
- **Visualization**: Text display with color coding
- **Business Impact**: Monitoring infrastructure health
- **Operational Insight**: Identifies monitoring issues

#### Scrape Duration Panel
- **Panel Type**: Stat panel
- **Metric**: `scrape_duration_seconds{job="websocket-app"}`
- **Description**: Time taken for Prometheus to scrape metrics
- **Unit**: Seconds
- **Thresholds**:
  - 🟢 Healthy: < 1 second
  - 🟡 Warning: 1-5 seconds
  - 🔴 Critical: > 5 seconds
- **Business Impact**: Monitoring system performance
- **Performance Optimization**: Identifies scraping bottlenecks

#### Last Successful Scrape Panel
- **Panel Type**: Stat panel
- **Metric**: `scrape_duration_seconds{job="websocket-app"}`
- **Description**: Time since last successful metrics scrape
- **Unit**: Seconds
- **Thresholds**:
  - 🟢 Healthy: < 30 seconds
  - 🟡 Warning: 30-60 seconds
  - 🔴 Critical: > 60 seconds
- **Business Impact**: Data freshness and reliability
- **Operational Insight**: Identifies data collection issues

## Metrics & Queries

### Core Prometheus Queries

#### Basic Metrics
```promql
# Active connections (current value)
app_active_connections

# Total messages (cumulative counter)
app_messages_total

# Error count (cumulative counter)
app_errors_total

# Sessions tracked (current value)
app_sessions_tracked
```

#### Rate Calculations
```promql
# Message rate (messages per second)
rate(app_messages_total[1m])

# Error rate (errors per second)
rate(app_errors_total[1m])

# Connection open rate
rate(app_connections_opened_total[1m])

# Connection close rate
rate(app_connections_closed_total[1m])
```

#### Advanced Analytics
```promql
# Connection success rate
rate(app_connections_opened_total[5m]) / 
(rate(app_connections_opened_total[5m]) + rate(app_connections_closed_total[5m])) * 100

# Message per connection ratio
rate(app_messages_total[5m]) / app_active_connections

# Error rate percentage
rate(app_errors_total[5m]) / rate(app_messages_total[5m]) * 100
```

#### Health Checks
```promql
# Service up status
up{job="websocket-app"}

# Scrape duration
scrape_duration_seconds{job="websocket-app"}

# Target health
up{job="websocket-app"}
```

### Query Optimization

#### Performance Best Practices
```promql
# Use longer time windows for better performance
# Instead of: rate(app_messages_total[30s])
# Use: rate(app_messages_total[1m])

# Leverage recording rules for complex queries
# Create recording rule: websocket:message_rate:rate1m
# Then use: websocket:message_rate:rate1m

# Use subqueries for historical analysis
# Instead of: rate(app_messages_total[1h])
# Use: rate(app_messages_total[5m])[1h:1m]
```

#### Efficient Aggregations
```promql
# Sum across instances (if multiple)
sum(app_active_connections) by (job)

# Average across time window
avg_over_time(app_active_connections[5m])

# Percentile calculations
histogram_quantile(0.95, rate(app_shutdown_duration_seconds_bucket[5m]))
```

## Alerting Integration

### Dashboard-Alert Correlation

The dashboard is designed to work seamlessly with Prometheus alerting rules:

#### Visual Alert Status
- **Alert State Indicators**: Real-time display of active alerts
- **Severity Color Coding**: Critical (red), Warning (yellow), Info (blue)
- **Alert History**: Timeline of recent alert events
- **Resolution Tracking**: Alert acknowledgment and resolution status

#### Alert-Triggering Metrics
```promql
# Connection loss alert
app_active_connections == 0

# High error rate alert
rate(app_errors_total[2m]) > 10

# Service down alert
up{job="websocket-app"} == 0

# High memory usage alert
(process_resident_memory_bytes / process_virtual_memory_bytes) * 100 > 85
```

### Alert Response Workflow

1. **Alert Detection**: Dashboard shows alert status immediately
2. **Impact Assessment**: Use dashboard metrics to understand scope
3. **Root Cause Analysis**: Drill down into specific panels
4. **Resolution Tracking**: Monitor metrics during incident response
5. **Post-Incident Review**: Use historical data for analysis

## Customization Guide

### Adding Custom Panels

#### Step-by-Step Process
1. **Access Dashboard**: Navigate to http://localhost:3000
2. **Edit Mode**: Click "Edit" on the dashboard
3. **Add Panel**: Use "Add panel" button
4. **Configure Query**: Enter PromQL expression
5. **Set Visualization**: Choose appropriate panel type
6. **Configure Thresholds**: Set color-coded thresholds
7. **Save Changes**: Click "Save" to persist modifications

#### Custom Query Examples
```promql
# Custom message rate with longer window
rate(app_messages_total[5m])

# Connection success rate
rate(app_connections_opened_total[5m]) / 
(rate(app_connections_opened_total[5m]) + rate(app_connections_closed_total[5m])) * 100

# Memory usage percentage
(process_resident_memory_bytes / process_virtual_memory_bytes) * 100

# Custom error rate calculation
rate(app_errors_total[5m]) * 60  # Errors per minute
```

### Threshold Configuration

#### JSON Configuration
```json
{
  "thresholds": [
    {"color": "green", "value": null},
    {"color": "yellow", "value": 10},
    {"color": "red", "value": 50}
  ],
  "fieldConfig": {
    "defaults": {
      "color": {
        "mode": "thresholds"
      },
      "mappings": [],
      "thresholds": {
        "steps": [
          {"color": "green", "value": null},
          {"color": "yellow", "value": 10},
          {"color": "red", "value": 50}
        ]
      }
    }
  }
}
```

#### Dynamic Thresholds
```promql
# Adaptive threshold based on historical data
app_active_connections < avg_over_time(app_active_connections[1h]) * 0.5

# Trend-based threshold
app_active_connections < quantile_over_time(0.1, app_active_connections[1h])
```

### Dashboard Variables

#### Time Range Variables
```json
{
  "name": "timeRange",
  "type": "custom",
  "options": [
    {"text": "Last 15 minutes", "value": "15m"},
    {"text": "Last 1 hour", "value": "1h"},
    {"text": "Last 6 hours", "value": "6h"},
    {"text": "Last 24 hours", "value": "24h"}
  ]
}
```

#### Instance Variables
```json
{
  "name": "instance",
  "type": "query",
  "query": "label_values(app_active_connections, instance)",
  "refresh": 2,
  "includeAll": true
}
```

## Performance Optimization

### Query Performance

#### Optimization Strategies
1. **Use Recording Rules**: Pre-compute complex queries
2. **Optimize Time Windows**: Balance accuracy with performance
3. **Leverage Caching**: Use Grafana's query caching
4. **Reduce Cardinality**: Limit label combinations
5. **Use Subqueries**: For historical analysis

#### Performance Monitoring
```promql
# Query execution time
rate(prometheus_engine_query_duration_seconds_sum[5m]) / 
rate(prometheus_engine_query_duration_seconds_count[5m])

# Scrape duration
scrape_duration_seconds{job="websocket-app"}

# Target health
up{job="websocket-app"}
```

### Dashboard Performance

#### Refresh Rate Optimization
- **Production**: 30-60 seconds (reduces load)
- **Development**: 10-15 seconds (real-time debugging)
- **Ad-hoc Analysis**: Manual refresh (on-demand)

#### Panel Optimization
- **Limit Data Points**: Use maxDataPoints setting
- **Optimize Queries**: Use efficient PromQL expressions
- **Reduce Panels**: Focus on essential metrics
- **Use Stat Panels**: For simple metrics instead of graphs

### Resource Management

#### Memory Optimization
```ini
# Grafana configuration
[performance]
max_concurrent_shifts = 10
max_shift_duration = 24h

[metrics]
enabled = true
interval_seconds = 60
```

#### CPU Optimization
- **Query Caching**: Enable and configure appropriately
- **Background Jobs**: Optimize dashboard refresh intervals
- **Resource Limits**: Set appropriate Docker resource limits

## Troubleshooting

### Common Issues

#### No Data in Panels
**Symptoms**: Panels show "No data" or empty graphs

**Diagnosis**:
```bash
# Check if metrics are available
curl -s http://localhost:9090/api/v1/query?query=app_active_connections

# Verify Prometheus targets
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="websocket-app")'

# Check application metrics endpoint
curl -s http://localhost/metrics | grep app_active_connections
```

**Resolution**:
- Ensure WebSocket application is running
- Verify `/metrics` endpoint is accessible
- Check Prometheus configuration
- Validate network connectivity

#### Slow Dashboard Loading
**Symptoms**: Dashboard takes long time to load or panels are slow

**Diagnosis**:
```bash
# Check Prometheus performance
curl -s http://localhost:9090/api/v1/query?query=up | jq '.stats'

# Monitor resource usage
docker stats --no-stream

# Check query execution time
curl -s "http://localhost:9090/api/v1/query?query=rate(app_messages_total[1m])&debug=true"
```

**Resolution**:
- Optimize PromQL queries
- Increase scrape intervals
- Add resource limits
- Use query caching

#### Missing Panels
**Symptoms**: Expected panels are not visible

**Diagnosis**:
```bash
# Check dashboard JSON
curl -s -u admin:admin123 http://localhost:3000/api/dashboards/uid/d323749f-135e-455a-aa74-4915a52ef0b9 | jq '.dashboard.panels | length'

# Verify datasource configuration
curl -s -u admin:admin123 http://localhost:3000/api/datasources | jq '.[] | {name: .name, type: .type}'
```

**Resolution**:
- Check dashboard provisioning
- Verify datasource configuration
- Restore from backup if needed
- Recreate missing panels

### Debugging Tools

#### Prometheus Debugging
```bash
# Query debugging
curl -s "http://localhost:9090/api/v1/query?query=app_active_connections&debug=true"

# Configuration validation
docker exec prometheus promtool check config /etc/prometheus/prometheus.yml

# Metrics exploration
curl -s http://localhost:9090/api/v1/label/__name__/values | jq '.data[]' | grep app_
```

#### Grafana Debugging
```bash
# Dashboard export
curl -s -u admin:admin123 http://localhost:3000/api/dashboards/uid/d323749f-135e-455a-aa74-4915a52ef0b9 > dashboard-backup.json

# Plugin status
curl -s -u admin:admin123 http://localhost:3000/api/plugins | jq '.[] | {name: .name, enabled: .enabled}'

# User permissions
curl -s -u admin:admin123 http://localhost:3000/api/user | jq '.'
```

## Maintenance & Updates

### Regular Maintenance Tasks

#### Weekly Tasks
- **Review Alert Thresholds**: Adjust based on production patterns
- **Check Dashboard Performance**: Monitor query execution times
- **Validate Metrics**: Ensure all expected metrics are available
- **Update Documentation**: Keep runbooks current

#### Monthly Tasks
- **Update Component Versions**: Prometheus, Grafana, Alertmanager
- **Review Query Performance**: Optimize slow queries
- **Audit Access Permissions**: Review user access and roles
- **Backup Configuration**: Export dashboards and configurations

#### Quarterly Tasks
- **Capacity Planning**: Review resource usage and scaling needs
- **Feature Review**: Evaluate new monitoring features
- **Process Improvement**: Update incident response procedures
- **Training**: Update team on new features and best practices

### Backup and Recovery

#### Configuration Backup
```bash
#!/bin/bash
# Automated backup script

BACKUP_DIR="/backups/grafana"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup dashboard
curl -s -u admin:admin123 \
  http://localhost:3000/api/dashboards/uid/d323749f-135e-455a-aa74-4915a52ef0b9 \
  > "$BACKUP_DIR/dashboard_$DATE.json"

# Backup datasources
curl -s -u admin:admin123 \
  http://localhost:3000/api/datasources \
  > "$BACKUP_DIR/datasources_$DATE.json"

# Backup users
curl -s -u admin:admin123 \
  http://localhost:3000/api/admin/users \
  > "$BACKUP_DIR/users_$DATE.json"

echo "Backup completed: $BACKUP_DIR"
```

#### Recovery Procedures
```bash
# Restore dashboard
curl -X POST -H "Content-Type: application/json" \
  -u admin:admin123 \
  -d @dashboard_backup.json \
  http://localhost:3000/api/dashboards/db

# Restore datasource
curl -X POST -H "Content-Type: application/json" \
  -u admin:admin123 \
  -d @datasource_backup.json \
  http://localhost:3000/api/datasources
```

### Version Management

#### Dashboard Versioning
- **Version Control**: Store dashboard JSON in Git
- **Change Tracking**: Document all dashboard modifications
- **Rollback Capability**: Maintain previous versions
- **Testing**: Validate changes in staging environment

#### Component Updates
```bash
# Update Prometheus
docker-compose -f docker/monitoring-compose.yml pull prometheus
docker-compose -f docker/monitoring-compose.yml up -d prometheus

# Update Grafana
docker-compose -f docker/monitoring-compose.yml pull grafana
docker-compose -f docker/monitoring-compose.yml up -d grafana

# Verify updates
docker-compose -f docker/monitoring-compose.yml ps
```

### Performance Monitoring

#### Dashboard Health Metrics
```promql
# Dashboard load time
grafana_dashboard_load_duration_seconds

# Query execution time
grafana_api_request_duration_seconds

# Panel rendering time
grafana_panel_render_duration_seconds
```

#### Resource Monitoring
```bash
# Monitor Grafana resources
docker stats grafana --no-stream

# Check Prometheus performance
curl -s http://localhost:9090/api/v1/status/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# Monitor alert performance
curl -s http://localhost:9093/api/v1/status | jq '.configYAML'
```

This comprehensive dashboard documentation provides enterprise-grade guidance for monitoring WebSocket services with production-ready features, performance optimization, and operational best practices.
