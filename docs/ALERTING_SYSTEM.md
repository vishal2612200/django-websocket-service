# Alerting System Documentation

## Overview

The WebSocket application includes a comprehensive alerting system built on **Prometheus + Alertmanager** that provides real-time monitoring and incident response capabilities for production environments.

## Table of Contents

- [Architecture](#architecture)
- [Alert Rules](#alert-rules)
- [Alert Severity Levels](#alert-severity-levels)
- [Alert Routing](#alert-routing)
- [Notification Channels](#notification-channels)
- [Alert Management](#alert-management)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Architecture

### Alert Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Prometheus    │    │   Alertmanager  │    │   Notification  │
│   (Alert Rules) │───▶│   (Routing)     │───▶│   Channels      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
   ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
   │   Metrics   │       │   Alerts    │       │   Slack     │
   │   Collection│       │   Status    │       │   PagerDuty │
   └─────────────┘       └─────────────┘       └─────────────┘
```

### Components

| Component | Port | Purpose | Configuration |
|-----------|------|---------|---------------|
| **Prometheus** | 9090 | Alert rule evaluation and firing | `prometheus.yml` + `alert_rules.yml` |
| **Alertmanager** | 9093 | Alert routing and deduplication | `alertmanager.yml` |
| **Grafana** | 3000 | Alert visualization and history | Dashboard integration |

## Alert Rules

### Critical Alerts (P0 - Immediate Response)

#### 1. NoActiveConnections
```yaml
alert: NoActiveConnections
expr: app_active_connections == 0
for: 60s
labels:
  severity: critical
  team: websocket
annotations:
  summary: "No active WebSocket connections"
  description: "Service may be down or experiencing issues. No active connections for 60 seconds."
  runbook_url: "https://wiki.company.com/runbooks/websocket-connection-loss"
```

**Trigger Conditions:**
- No active WebSocket connections for 60 seconds
- Indicates service is down or experiencing connectivity issues

**Business Impact:**
- Users cannot connect to the WebSocket service
- Real-time communication is completely unavailable

**Response Actions:**
1. Check if WebSocket application is running
2. Verify network connectivity and load balancer status
3. Check application logs for errors
4. Restart service if necessary

#### 2. HighErrorRate
```yaml
alert: HighErrorRate
expr: rate(app_errors_total[5m]) > 10
for: 2m
labels:
  severity: critical
  team: websocket
annotations:
  summary: "High error rate detected"
  description: "Error rate is {{ $value }} errors per minute"
  runbook_url: "https://wiki.company.com/runbooks/high-error-rate"
```

**Trigger Conditions:**
- Error rate exceeds 10 errors per minute for 2 minutes
- Indicates application is experiencing frequent failures

**Business Impact:**
- Poor user experience due to frequent errors
- Potential data loss or corruption
- Service degradation

**Response Actions:**
1. Check application logs for error patterns
2. Monitor system resources (CPU, memory, disk)
3. Check database connectivity and performance
4. Review recent deployments for issues

#### 3. ServiceDown
```yaml
alert: ServiceDown
expr: up{job="websocket-app"} == 0
for: 30s
labels:
  severity: critical
  team: websocket
annotations:
  summary: "WebSocket service is down"
  description: "The WebSocket application is not responding to health checks"
  runbook_url: "https://wiki.company.com/runbooks/service-down"
```

**Trigger Conditions:**
- Prometheus cannot scrape metrics from the application
- Health check endpoint is not responding
- Service process has crashed or stopped

**Business Impact:**
- Complete service outage
- No real-time communication possible
- All WebSocket connections are lost

**Response Actions:**
1. Check if application container is running
2. Verify application process status
3. Check system resources and logs
4. Restart application service

### Warning Alerts (P1 - Attention Required)

#### 4. HighMemoryUsage
```yaml
alert: HighMemoryUsage
expr: (process_resident_memory_bytes / process_virtual_memory_bytes) * 100 > 85
for: 5m
labels:
  severity: warning
  team: websocket
annotations:
  summary: "High memory usage"
  description: "Memory usage is {{ $value }}%"
  runbook_url: "https://wiki.company.com/runbooks/high-memory-usage"
```

**Trigger Conditions:**
- Memory usage exceeds 85% for 5 minutes
- Indicates potential memory leak or insufficient resources

**Business Impact:**
- Potential service degradation
- Risk of out-of-memory crashes
- Poor performance for users

**Response Actions:**
1. Check for memory leaks in application
2. Monitor memory usage trends
3. Consider scaling up resources
4. Review application memory allocation

#### 5. SlowShutdownTime
```yaml
alert: SlowShutdownTime
expr: histogram_quantile(0.95, rate(app_shutdown_duration_seconds_bucket[5m])) > 5
for: 5m
labels:
  severity: warning
  team: websocket
annotations:
  summary: "Slow shutdown time"
  description: "95th percentile shutdown time is {{ $value }}s"
  runbook_url: "https://wiki.company.com/runbooks/slow-shutdown-time"
```

**Trigger Conditions:**
- 95th percentile shutdown time exceeds 5 seconds
- Indicates graceful shutdown is taking too long

**Business Impact:**
- Longer deployment times
- Potential connection loss during deployments
- Resource cleanup issues

**Response Actions:**
1. Review shutdown procedures
2. Check for hanging connections or processes
3. Optimize graceful shutdown logic
4. Monitor shutdown performance

#### 6. LowMessageThroughput
```yaml
alert: LowMessageThroughput
expr: rate(app_messages_total[5m]) < 1
for: 10m
labels:
  severity: warning
  team: websocket
annotations:
  summary: "Low message throughput"
  description: "Message throughput is {{ $value }} messages per second"
  runbook_url: "https://wiki.company.com/runbooks/low-throughput"
```

**Trigger Conditions:**
- Message throughput below 1 message per second for 10 minutes
- Indicates low activity or performance issues

**Business Impact:**
- Poor user experience
- Potential service degradation
- Low utilization of resources

**Response Actions:**
1. Check if this is expected low activity period
2. Verify application performance
3. Check for client connectivity issues
4. Monitor user activity patterns

#### 7. HighConnectionChurn
```yaml
alert: HighConnectionChurn
expr: rate(app_connections_opened_total[5m]) > 100
for: 5m
labels:
  severity: warning
  team: websocket
annotations:
  summary: "High connection churn"
  description: "Connection rate is {{ $value }} connections per second"
  runbook_url: "https://wiki.company.com/runbooks/high-connection-churn"
```

**Trigger Conditions:**
- Connection rate exceeds 100 connections per second for 5 minutes
- Indicates connection stability issues

**Business Impact:**
- Poor user experience due to frequent disconnections
- Increased resource usage
- Potential DoS attack or client issues

**Response Actions:**
1. Check for client-side connection issues
2. Monitor for potential DoS attacks
3. Review connection timeout settings
4. Check network stability

### Info Alerts (P2 - Monitoring)

#### 8. DeploymentCompleted
```yaml
alert: DeploymentCompleted
expr: changes(app_active_connections[5m]) > 0
labels:
  severity: info
  team: websocket
annotations:
  summary: "Service deployment detected"
  description: "Service activity detected, possible deployment or restart"
```

**Trigger Conditions:**
- Changes detected in active connections over 5 minutes
- Indicates service restart or deployment

**Business Impact:**
- Normal operational activity
- Useful for tracking deployments

**Response Actions:**
1. Verify deployment was intentional
2. Monitor service health after deployment
3. Check deployment logs

#### 9. HighSessionCount
```yaml
alert: HighSessionCount
expr: app_sessions_tracked > 1000
for: 5m
labels:
  severity: info
  team: websocket
annotations:
  summary: "High session count"
  description: "{{ $value }} sessions are currently tracked"
```

**Trigger Conditions:**
- More than 1000 sessions tracked for 5 minutes
- Indicates high user activity

**Business Impact:**
- High resource utilization
- Good user engagement
- May require capacity planning

**Response Actions:**
1. Monitor resource usage
2. Consider scaling if needed
3. Review session cleanup policies

### System Alerts

#### 10. HighCPUUsage
```yaml
alert: HighCPUUsage
expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
for: 5m
labels:
  severity: warning
  team: infrastructure
annotations:
  summary: "High CPU usage"
  description: "CPU usage is {{ $value }}%"
```

#### 11. HighDiskUsage
```yaml
alert: HighDiskUsage
expr: (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100 < 10
for: 5m
labels:
  severity: warning
  team: infrastructure
annotations:
  summary: "High disk usage"
  description: "Disk usage is {{ $value }}%"
```

## Alert Severity Levels

### Critical (P0) - Immediate Response
- **Response Time**: Immediate (within 5 minutes)
- **Notification**: Slack + PagerDuty
- **Examples**: Service down, no connections, high error rate
- **Business Impact**: Service unavailable or severely degraded

### Warning (P1) - Attention Required
- **Response Time**: 30 minutes
- **Notification**: Slack
- **Examples**: High memory usage, slow performance, low throughput
- **Business Impact**: Service degradation, poor user experience

### Info (P2) - Monitoring
- **Response Time**: Monitor and document
- **Notification**: Slack
- **Examples**: Deployment detected, high session count
- **Business Impact**: Operational awareness, capacity planning

## Alert Routing

### Alert Flow
1. **Prometheus** evaluates alert rules against metrics
2. **Alertmanager** receives fired alerts
3. **Alertmanager** routes alerts based on severity and team
4. **Notifications** sent to appropriate channels

### Routing Configuration
```yaml
route:
  group_by: ['alertname', 'severity', 'team']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'websocket-team'
  routes:
    - match:
        severity: critical
      receiver: 'websocket-oncall'
      continue: true
    - match:
        severity: warning
      receiver: 'websocket-team'
      continue: true
    - match:
        team: infrastructure
      receiver: 'infrastructure-team'
      continue: true
```

### Alert Grouping
- **Group Wait**: 30 seconds before sending first alert
- **Group Interval**: 5 minutes between grouped alerts
- **Repeat Interval**: 4 hours for unacknowledged alerts
- **Group By**: Alert name, severity, and team

## Notification Channels

### Slack Notifications

#### Critical Alerts
- **Channel**: `#websocket-oncall`
- **Icon**: 🚨 (rotating light)
- **Title**: `🚨 CRITICAL: {{ template "slack.title" . }}`
- **Escalation**: PagerDuty integration

#### Warning Alerts
- **Channel**: `#websocket-alerts`
- **Icon**: ⚠️ (warning)
- **Title**: `{{ template "slack.title" . }}`

#### Infrastructure Alerts
- **Channel**: `#infrastructure-alerts`
- **Icon**: ⚙️ (gear)
- **Title**: `{{ template "slack.title" . }}`

### PagerDuty Integration
- **Routing Key**: Configurable
- **Severity**: Critical alerts only
- **Description**: `{{ template "pagerduty.description" . }}`

## Alert Management

### Accessing Alerts

#### From UI
1. **Active Alerts**: Click "🚨 Active Alerts" button
2. **Alertmanager**: Click "🔔 Alertmanager" button
3. **Alert Status**: View in header indicator

#### From Command Line
```bash
# Check alert status
./scripts/monitor.sh check-alerts

# Open Alertmanager UI
./scripts/monitor.sh alerts

# View alert details
curl -s http://localhost:9093/api/v1/alerts | jq '.'
```

#### Direct URLs
- **Alertmanager**: http://localhost:9093
- **Prometheus Alerts**: http://localhost:9090/alerts
- **Alert Rules**: http://localhost:9090/rules

### Alert States

#### Active
- Alert is firing and requires attention
- Notification sent to appropriate channels
- Requires acknowledgment or resolution

#### Pending
- Alert condition met but not yet firing
- Waiting for `for` duration to expire
- No notification sent yet

#### Resolved
- Alert condition no longer met
- Notification sent to channels
- Can be silenced or acknowledged

### Alert Actions

#### Acknowledgment
- Mark alert as acknowledged
- Prevents repeat notifications
- Add notes for team context

#### Silencing
- Temporarily suppress alert notifications
- Useful for planned maintenance
- Configurable duration and scope

#### Resolution
- Alert condition resolved
- Automatic when metrics return to normal
- Manual resolution available

## Troubleshooting

### Common Issues

#### 1. Alerts Not Firing
**Symptoms**: No alerts in Prometheus or Alertmanager

**Diagnosis**:
```bash
# Check Prometheus alert rules
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[] | select(.name=="websocket_alerts")'

# Check Alertmanager configuration
curl -s http://localhost:9093/api/v1/status | jq '.configYAML'

# Check metrics availability
curl -s http://localhost/metrics | grep app_active_connections
```

**Resolution**:
- Verify alert rules are loaded in Prometheus
- Check Alertmanager configuration
- Ensure metrics are being collected

#### 2. Alerts Not Reaching Alertmanager
**Symptoms**: Alerts in Prometheus but not in Alertmanager

**Diagnosis**:
```bash
# Check Prometheus alerting configuration
curl -s http://localhost:9090/api/v1/status/config | jq '.data.alerting'

# Check Alertmanager connectivity
curl -s http://localhost:9093/api/v1/status
```

**Resolution**:
- Verify Alertmanager URL in Prometheus config
- Check network connectivity between services
- Restart Prometheus to reload configuration

#### 3. Notifications Not Sent
**Symptoms**: Alerts in Alertmanager but no notifications

**Diagnosis**:
```bash
# Check Alertmanager logs
./scripts/monitor.sh logs alertmanager

# Check notification configuration
curl -s http://localhost:9093/api/v1/status | jq '.configYAML'
```

**Resolution**:
- Verify notification channel configuration
- Check Slack webhook URLs and PagerDuty keys
- Review Alertmanager logs for errors

#### 4. False Positives
**Symptoms**: Alerts firing when service is healthy

**Diagnosis**:
```bash
# Check current metric values
curl -s http://localhost:9090/api/v1/query?query=app_active_connections

# Review alert rule expressions
cat docker/alert_rules.yml
```

**Resolution**:
- Adjust alert thresholds
- Review alert rule logic
- Add additional conditions to prevent false positives

### Debugging Commands

#### Check Alert Status
```bash
# All active alerts
curl -s http://localhost:9093/api/v1/alerts | jq '.[] | {alertname: .labels.alertname, severity: .labels.severity, state: .status.state}'

# Critical alerts only
curl -s http://localhost:9093/api/v1/alerts | jq '[.[] | select(.labels.severity == "critical")]'

# Alert details
curl -s http://localhost:9093/api/v1/alerts | jq '.[] | {alertname: .labels.alertname, summary: .annotations.summary, description: .annotations.description}'
```

#### Check Alert Rules
```bash
# Prometheus alert rules
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[] | select(.name=="websocket_alerts") | .rules[] | {name: .name, state: .state, health: .health}'

# Alert rule evaluation
curl -s http://localhost:9090/api/v1/query?query=up{job="websocket-app"}
```

#### Check Configuration
```bash
# Prometheus configuration
curl -s http://localhost:9090/api/v1/status/config | jq '.data.alerting'

# Alertmanager configuration
curl -s http://localhost:9093/api/v1/status | jq '.configYAML'
```

## Best Practices

### Alert Design

#### 1. Meaningful Names
- Use descriptive alert names
- Include service and component identifiers
- Follow consistent naming conventions

#### 2. Appropriate Thresholds
- Set thresholds based on historical data
- Consider business impact
- Avoid overly sensitive thresholds

#### 3. Clear Descriptions
- Provide actionable descriptions
- Include runbook URLs
- Explain business impact

### Alert Management

#### 1. Regular Review
- Weekly alert threshold review
- Monthly false positive analysis
- Quarterly alert rule optimization

#### 2. Documentation
- Maintain runbooks for each alert
- Document resolution procedures
- Keep alert history for analysis

#### 3. Testing
- Test alert rules in staging
- Validate notification channels
- Simulate alert conditions

### Performance Optimization

#### 1. Efficient Queries
- Use recording rules for complex queries
- Optimize time windows
- Minimize cardinality

#### 2. Alert Grouping
- Group related alerts
- Use appropriate group intervals
- Avoid alert spam

#### 3. Notification Management
- Use appropriate channels for severity
- Implement escalation procedures
- Monitor notification delivery

### Monitoring the Monitor

#### 1. Self-Monitoring
- Monitor Prometheus and Alertmanager health
- Track alert rule evaluation performance
- Monitor notification delivery success

#### 2. Alert Metrics
- Track alert firing rates
- Monitor false positive rates
- Measure time to resolution

#### 3. Continuous Improvement
- Regular alert effectiveness review
- Update thresholds based on trends
- Optimize alert rules and routing

## Configuration Files

### Alert Rules (`docker/alert_rules.yml`)
- Contains all alert rule definitions
- Organized by severity and team
- Includes annotations and labels

### Alertmanager Config (`docker/alertmanager.yml`)
- Defines notification channels
- Configures alert routing
- Sets up escalation procedures

### Prometheus Config (`docker/prometheus.yml`)
- References alert rules file
- Configures Alertmanager endpoint
- Sets evaluation intervals

## Integration with Monitoring Stack

### Grafana Integration
- Alert status displayed in dashboards
- Historical alert data visualization
- Alert correlation with metrics

### Log Aggregation
- Alert correlation with application logs
- Centralized logging for incident response
- Log-based alerting for specific events

### Incident Management
- Integration with PagerDuty for escalation
- Slack integration for team notifications
- Runbook integration for resolution procedures

This comprehensive alerting system provides production-ready monitoring and incident response capabilities for the WebSocket application, ensuring high availability and quick response to issues.
