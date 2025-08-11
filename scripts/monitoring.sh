#!/bin/bash

# Monitoring Stack Management Script
# This script provides comprehensive management of the Prometheus and Grafana
# monitoring infrastructure for WebSocket service observability.
#
# The monitoring stack enables real-time metrics collection, alerting,
# and performance analysis for production deployments.

set -e

case "$1" in
    start)
        echo "Initializing monitoring infrastructure..."
        echo "Starting Prometheus and Grafana services..."
        cd docker
        docker compose -f simple-monitoring.yml up -d
        echo "Monitoring services started successfully"
        
        echo "Waiting for Grafana service initialization..."
        sleep 10
        
        echo "Importing monitoring dashboards..."
        cd ..
        ./scripts/import_dashboard.sh
        
        echo ""
        echo "Monitoring Infrastructure Access:"
        echo "  Grafana Dashboard: http://localhost:3000 (admin/admin123)"
        echo "  Prometheus Metrics: http://localhost:9090"
        echo ""
        echo "WebSocket service metrics are now being collected automatically."
        echo "Review the dashboards for real-time performance monitoring."
        ;;
    stop)
        echo "Shutting down monitoring infrastructure..."
        cd docker
        docker compose -f simple-monitoring.yml down
        echo "Monitoring services stopped successfully"
        ;;
    restart)
        echo "Restarting monitoring infrastructure..."
        cd docker
        docker compose -f simple-monitoring.yml restart
        echo "Monitoring services restarted successfully"
        ;;
    status)
        echo "Monitoring Infrastructure Status:"
        echo "=================================="
        cd docker
        docker compose -f simple-monitoring.yml ps
        echo ""
        echo "Prometheus Target Health Check:"
        curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job, health, lastError}' 2>/dev/null || echo "Prometheus service not accessible"
        ;;
    logs)
        echo "Displaying monitoring service logs..."
        cd docker
        docker compose -f simple-monitoring.yml logs -f
        ;;
    import)
        echo "Importing monitoring dashboards..."
        ./scripts/import_dashboard.sh
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|import}"
        echo ""
        echo "Available Commands:"
        echo "  start   - Initialize and start the monitoring stack"
        echo "  stop    - Shutdown monitoring services gracefully"
        echo "  restart - Restart monitoring services"
        echo "  status  - Display service status and health information"
        echo "  logs    - Show real-time logs from monitoring services"
        echo "  import  - Import dashboards manually"
        echo ""
        echo "Service Access Information:"
        echo "  Grafana Dashboard: http://localhost:3000 (admin/admin123)"
        echo "  Prometheus Metrics: http://localhost:9090"
        echo ""
        echo "The monitoring stack provides comprehensive observability"
        echo "for WebSocket service performance and health metrics."
        exit 1
        ;;
esac
