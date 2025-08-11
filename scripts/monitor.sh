#!/bin/bash

# Monitoring Tools Access Script
# Provides easy access to Prometheus, Grafana, Alertmanager, and logs

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  WebSocket Monitoring Tools${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Function to check if a service is running
check_service() {
    local service=$1
    local port=$2
    local url=$3
    
    if curl -s "$url" > /dev/null 2>&1; then
        echo -e "${GREEN} ${NC} $service is running on port $port"
        return 0
    else
        echo -e "${RED} ${NC} $service is not running on port $port"
        return 1
    fi
}

# Function to open URL in browser
open_url() {
    local url=$1
    local description=$2
    
    print_status "Opening $description..."
    if command -v open > /dev/null 2>&1; then
        open "$url"
    elif command -v xdg-open > /dev/null 2>&1; then
        xdg-open "$url"
    else
        print_warning "Could not open browser automatically. Please visit: $url"
    fi
}

# Function to show service logs
show_logs() {
    local service=$1
    local compose_file=$2
    
    print_status "Showing logs for $service..."
    if [ -f "$compose_file" ]; then
        docker compose -f "$compose_file" logs -f "$service"
    else
        print_error "Compose file not found: $compose_file"
    fi
}

# Function to check alert status
check_alerts() {
    print_status "Checking alert status..."
    
    # Check Alertmanager
    if curl -s "http://localhost:9093/api/v1/alerts" > /dev/null 2>&1; then
        local alerts=$(curl -s "http://localhost:9093/api/v1/alerts" | jq 'length' 2>/dev/null || echo "0")
        local critical=$(curl -s "http://localhost:9093/api/v1/alerts" | jq '[.[] | select(.labels.severity == "critical" and .status.state == "active")] | length' 2>/dev/null || echo "0")
        
        echo -e "${CYAN}📊 Alert Status:${NC}"
        echo -e "  Total Active Alerts: $alerts"
        echo -e "  Critical Alerts: $critical"
        
        if [ "$critical" -gt 0 ]; then
            echo -e "${RED}🚨 CRITICAL ALERTS DETECTED!${NC}"
            curl -s "http://localhost:9093/api/v1/alerts" | jq -r '.[] | select(.labels.severity == "critical" and .status.state == "active") | "  - " + .labels.alertname + ": " + .annotations.summary' 2>/dev/null || echo "  Unable to fetch alert details"
        fi
    else
        print_warning "Alertmanager is not running or not accessible"
    fi
}

# Function to show monitoring status
show_status() {
    print_header
    echo
    
    print_status "Checking monitoring services..."
    echo
    
    # Check each service
    check_service "Prometheus" "9090" "http://localhost:9090/api/v1/status/targets"
    check_service "Grafana" "3000" "http://localhost:3000/api/health"
    check_service "Alertmanager" "9093" "http://localhost:9093/api/v1/status"
    
    echo
    check_alerts
    echo
    
    # Check application metrics
    if curl -s "http://localhost/metrics" > /dev/null 2>&1; then
        echo -e "${GREEN} ${NC} Application metrics endpoint is accessible"
        local connections=$(curl -s "http://localhost/metrics" | grep "app_active_connections" | cut -d' ' -f2 || echo "0")
        echo -e "  Active Connections: $connections"
    else
        echo -e "${RED} ${NC} Application metrics endpoint is not accessible"
    fi
}

# Function to start monitoring stack
start_monitoring() {
    print_status "Starting monitoring stack..."
    if [ -f "docker/monitoring-compose.yml" ]; then
        docker compose -f docker/monitoring-compose.yml up -d
        print_status "Monitoring stack started successfully!"
        echo
        print_status "Waiting for services to be ready..."
        sleep 5
        show_status
    else
        print_error "Monitoring compose file not found: docker/monitoring-compose.yml"
        exit 1
    fi
}

# Function to show help
show_help() {
    print_header
    echo
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  start           Start monitoring stack"
    echo "  status          Show monitoring services status"
    echo "  grafana         Open Grafana dashboard"
    echo "  prometheus      Open Prometheus UI"
    echo "  alerts          Open Alertmanager UI"
    echo "  targets         Open Prometheus targets page"
    echo "  rules           Open Prometheus alert rules page"
    echo "  logs [service]  Show logs for monitoring services"
    echo "  check-alerts    Check current alert status"
    echo "  help            Show this help message"
    echo
    echo "Examples:"
    echo "  $0 start                     # Start monitoring stack"
    echo "  $0 status                    # Check all services"
    echo "  $0 grafana                   # Open Grafana"
    echo "  $0 logs prometheus           # Show Prometheus logs"
    echo "  $0 logs grafana              # Show Grafana logs"
    echo "  $0 logs alertmanager         # Show Alertmanager logs"
    echo
}

# Main script logic
case "${1:-status}" in
    "start")
        start_monitoring
        ;;
    "status")
        show_status
        ;;
    "grafana")
        open_url "http://localhost:3000" "Grafana Dashboard"
        ;;
    "prometheus")
        open_url "http://localhost:9090" "Prometheus UI"
        ;;
    "alerts")
        open_url "http://localhost:9093" "Alertmanager UI"
        ;;
    "targets")
        open_url "http://localhost:9090/targets" "Prometheus Targets"
        ;;
    "rules")
        open_url "http://localhost:9090/rules" "Prometheus Alert Rules"
        ;;
    "logs")
        case "$2" in
            "prometheus")
                show_logs "prometheus" "docker/monitoring-compose.yml"
                ;;
            "grafana")
                show_logs "grafana" "docker/monitoring-compose.yml"
                ;;
            "alertmanager")
                show_logs "alertmanager" "docker/monitoring-compose.yml"
                ;;
            "simple-prometheus")
                show_logs "prometheus" "docker/simple-monitoring.yml"
                ;;
            "simple-grafana")
                show_logs "grafana" "docker/simple-monitoring.yml"
                ;;
            *)
                print_error "Unknown service: $2"
                echo "Available services: prometheus, grafana, alertmanager, simple-prometheus, simple-grafana"
                exit 1
                ;;
        esac
        ;;
    "check-alerts")
        check_alerts
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo
        show_help
        exit 1
        ;;
esac
