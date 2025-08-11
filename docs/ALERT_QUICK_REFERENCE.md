# Alerting System Quick Reference

## 🚨 Alert Status Check

### Check All Services
```bash
./scripts/monitor.sh status
```

### Check Active Alerts
```bash
./scripts/monitor.sh check-alerts
```

### View Alert Details
```bash
curl -s http://localhost:9093/api/v1/alerts | jq '.[] | {alertname: .labels.alertname, severity: .labels.severity, state: .status.state}'
```

## 🔗 Quick Access URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Alertmanager** | http://localhost:9093 | Alert management and routing |
| **Prometheus Alerts** | http://localhost:9090/alerts | View active alerts |
| **Prometheus Rules** | http://localhost:9090/rules | Alert rule definitions |
| **Prometheus Targets** | http://localhost:9090/targets | Service health status |
| **Grafana Dashboard** | http://localhost:3000 | Monitoring dashboards |

## 📊 Alert Severity Levels

| Severity | Response Time | Notification | Examples |
|----------|---------------|--------------|----------|
| **Critical** | 5 minutes | Slack + PagerDuty | Service down, no connections |
| **Warning** | 30 minutes | Slack | High memory, low throughput |
| **Info** | Monitor | Slack | Deployment detected |

## 🚨 Critical Alerts (P0)

### NoActiveConnections
- **Trigger**: `app_active_connections == 0` for 60s
- **Impact**: No WebSocket connections available
- **Action**: Check application status and restart if needed

### HighErrorRate
- **Trigger**: `rate(app_errors_total[5m]) > 10` for 2m
- **Impact**: Frequent application errors
- **Action**: Check logs and system resources

### ServiceDown
- **Trigger**: `up{job="websocket-app"} == 0` for 30s
- **Impact**: Complete service outage
- **Action**: Restart application service

## ⚠️ Warning Alerts (P1)

### HighMemoryUsage
- **Trigger**: Memory usage > 85% for 5m
- **Action**: Check for memory leaks, consider scaling

### SlowShutdownTime
- **Trigger**: 95th percentile shutdown > 5s
- **Action**: Review shutdown procedures

### LowMessageThroughput
- **Trigger**: Message rate < 1/sec for 10m
- **Action**: Check application performance

### HighConnectionChurn
- **Trigger**: Connection rate > 100/sec for 5m
- **Action**: Check client connectivity issues

## ℹ️ Info Alerts (P2)

### DeploymentCompleted
- **Trigger**: Changes in active connections
- **Action**: Verify deployment was intentional

### HighSessionCount
- **Trigger**: > 1000 sessions for 5m
- **Action**: Monitor resource usage

## 🛠️ Troubleshooting Commands

### Check Alert Rules
```bash
# View loaded alert rules
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[] | select(.name=="websocket_alerts")'

# Check rule health
curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[].rules[] | {name: .name, health: .health}'
```

### Check Metrics
```bash
# Current active connections
curl -s http://localhost:9090/api/v1/query?query=app_active_connections

# Error rate
curl -s http://localhost:9090/api/v1/query?query=rate(app_errors_total[5m])

# Service health
curl -s http://localhost:9090/api/v1/query?query=up{job="websocket-app"}
```

### Check Configuration
```bash
# Prometheus alerting config
curl -s http://localhost:9090/api/v1/status/config | jq '.data.alerting'

# Alertmanager config
curl -s http://localhost:9093/api/v1/status | jq '.configYAML'
```

## 📝 Alert Management

### Acknowledge Alert
1. Go to http://localhost:9093
2. Find the alert in the UI
3. Click "Acknowledge"
4. Add notes and set duration

### Silence Alert
1. Go to http://localhost:9093
2. Click "Silence" tab
3. Create new silence
4. Set matchers and duration

### View Alert History
1. Go to http://localhost:9093
2. Click "Silences" tab
3. View active and expired silences

## 🔧 Service Management

### Restart Monitoring Stack
```bash
cd docker
docker compose -f monitoring-compose.yml restart
```

### View Service Logs
```bash
# Prometheus logs
./scripts/monitor.sh logs prometheus

# Alertmanager logs
./scripts/monitor.sh logs alertmanager

# Grafana logs
./scripts/monitor.sh logs grafana
```

### Check Service Health
```bash
# All services
docker ps | grep -E "(prometheus|grafana|alertmanager)"

# Service status
docker compose -f docker/monitoring-compose.yml ps
```

## 📈 Alert Metrics

### Key Metrics to Monitor
- `app_active_connections` - Current WebSocket connections
- `app_errors_total` - Total error count
- `app_messages_total` - Total message count
- `up{job="websocket-app"}` - Service health status

### Performance Metrics
- `rate(app_messages_total[5m])` - Message throughput
- `rate(app_errors_total[5m])` - Error rate
- `process_resident_memory_bytes` - Memory usage

## 🚀 Quick Actions

### Emergency Response
1. **Service Down**: Restart application
2. **No Connections**: Check application and network
3. **High Errors**: Check logs and resources
4. **Memory Issues**: Scale resources or restart

### Maintenance Mode
1. Silence relevant alerts
2. Perform maintenance
3. Monitor service health
4. Remove silences when complete

### Post-Incident
1. Acknowledge resolved alerts
2. Review alert history
3. Update runbooks if needed
4. Document lessons learned

## 📞 Escalation

### Critical Alerts
- **Immediate**: Check service status
- **5 minutes**: Escalate to on-call
- **15 minutes**: Escalate to team lead
- **30 minutes**: Escalate to management

### Warning Alerts
- **30 minutes**: Initial investigation
- **1 hour**: Escalate if unresolved
- **4 hours**: Escalate to team lead

### Info Alerts
- **Monitor**: Track for patterns
- **Document**: Record for analysis
- **Review**: Weekly review of trends

---

**For detailed documentation, see [ALERTING_SYSTEM.md](ALERTING_SYSTEM.md)**
