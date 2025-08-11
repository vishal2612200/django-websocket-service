# Django WebSocket Service - Real-Time Communication Platform

[![CI/CD Pipeline](https://github.com/vishal2612200/django-websocket-service/actions/workflows/ci.yml/badge.svg)](https://github.com/vishal2612200/django-websocket-service/actions)
[![Docker Image](https://img.shields.io/docker/pulls/vishal2612200/django-websocket-service)](https://hub.docker.com/r/vishal2612200/django-websocket-service)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django 4.2+](https://img.shields.io/badge/django-4.2+-green.svg)](https://www.djangoproject.com/)

A production-ready, WebSocket communication platform built with Django Channels, featuring zero-downtime deployments, comprehensive observability, and a modern React frontend. Designed for high-availability real-time applications with enterprise-level reliability, scalability, and operational excellence.

## 🎥 Loom Demo — Click Below to Watch

[![▶ Watch Full Video Walkthrough](https://cdn.loom.com/sessions/thumbnails/464529825aa3429c9a54add84b1ae7c9-565ec8b15f6854a5-full.jpg)](https://www.loom.com/share/464529825aa3429c9a54add84b1ae7c9?sid=931cb8d9-d5cb-4078-bb35-b3bd9508bdcd)


## ⚡ Quick Reference

```bash
# Spin up full stack
git clone https://github.com/vishal2612200/django-websocket-service.git && cd django-websocket-service && make dev-up

# Load testing
make load-test                    # 6000 concurrent connections (default)
N=5000 make load-test            # Custom concurrency
N=10000 make load-test           # Scale to 10,000 connections
```

# Blue/Green deployment
make blue-up && make promote     # Deploy and switch to blue
make green-up && make promote    # Deploy and switch to green

# Scaling to 10K connections
./scripts/scale_to_10k.sh        # Apply 10K configuration
./scripts/deploy_10k.sh          # Deploy with 10K settings

# Monitoring stack
docker compose -f docker/monitoring-compose.yml up -d  # Start monitoring
open http://localhost:3000/      # Grafana (admin/admin123)
open http://localhost:9090/      # Prometheus
open http://localhost:9093/      # Alert Manager
```

## 🎯 Executive Summary

This platform addresses the critical need for reliable, scalable real-time communication in modern web applications. It provides a robust foundation for building WebSocket-based features like live chat, real-time notifications, collaborative editing, and live dashboards with enterprise-grade reliability and operational practices.

### Key Business Value
- **Zero Downtime Deployments**: Eliminate service interruptions during updates
- **High Availability**: 99.9%+ uptime with automatic failover capabilities
- **Real-Time Performance**: Sub-100ms message delivery with 5000+ concurrent connections
- **Operational Excellence**: Comprehensive monitoring, alerting, and incident response
- **Developer Experience**: Modern tooling, clear documentation, and streamlined workflows

## 🚀 Quick Start

### Essential Commands

#### **One-Liner to Spin Up Full Stack**
```bash
git clone https://github.com/vishal2612200/django-websocket-service.git && cd django-websocket-service && make dev-up
```

#### **Load Testing (Locust/Autobahn)**
```bash
make load-test                    # Default: 6000 concurrent connections
N=5000 make load-test            # Custom: 5000 concurrent connections
N=10000 make load-test           # Scale to 10,000 connections
make test-performance            # Performance test with 6000 connections
```

#### **Blue/Green Deployment**
```bash
make blue-up                     # Deploy blue environment
make promote                     # Switch traffic to blue
make green-up                    # Deploy green environment  
make promote                     # Switch traffic to green
make logs                        # Monitor deployment health
```

#### **Scaling to 10,000 Connections**
```bash
./scripts/scale_to_10k.sh        # Apply 10K configuration
./scripts/deploy_10k.sh          # Deploy with 10K settings
N=10000 make load-test           # Test with 10K connections
./scripts/monitor_10k.sh         # Monitor 10K performance
```

#### **Monitoring & Observability**
```bash
# Start monitoring stack
docker compose -f docker/monitoring-compose.yml up -d

# Access monitoring dashboards
open http://localhost:3000/      # Grafana (admin/admin123)
open http://localhost:9090/      # Prometheus
open http://localhost:9093/      # Alert Manager

# Check monitoring status
./scripts/monitor.sh status

# View alerts and metrics
./scripts/monitor.sh check-alerts
./scripts/monitor.sh grafana
./scripts/monitor.sh prometheus
```

### Development Environment
```bash
# Clone and setup
git clone https://github.com/vishal2612200/django-websocket-service.git
cd django-websocket-service

# Start development environment
make dev-up

# Access the application
open http://localhost/
```

### Monitoring Stack Setup
```bash
# Install and start monitoring stack (Prometheus, Grafana, Alert Manager)
docker compose -f docker/monitoring-compose.yml up -d

# Or use the monitoring script
./scripts/monitor.sh start

# Access monitoring dashboards
open http://localhost:3000/     # Grafana (admin/admin123)
open http://localhost:9090/     # Prometheus
open http://localhost:9093/     # Alert Manager

# Check monitoring stack status
./scripts/monitor.sh status

# View monitoring logs
./scripts/monitor.sh logs prometheus
./scripts/monitor.sh logs grafana
./scripts/monitor.sh logs alertmanager
```

### Load Testing
```bash
# Run Locust/Autobahn load test with default concurrency (1000)
make load-test

# Run with custom concurrency
N=5000 make load-test

# Run performance test with 5000 concurrent connections
make test-performance
```

### Blue/Green Deployment
```bash
# Deploy blue environment
make blue-up

# Promote blue to active (switch traffic)
make promote

# Deploy green environment
make green-up

# Promote green to active (switch traffic back)
make promote

# Monitor deployment health
make logs
```

### Production Deployment
```bash
# Deploy with zero downtime
make blue-up    # Deploy blue environment
make promote    # Switch traffic to blue
make green-up   # Deploy green environment
make promote    # Switch traffic to green

# Monitor deployment health
make logs
```

## 📋 Table of Contents

- [Architecture & Design](#architecture--design)
- [Core Capabilities](#core-capabilities)
- [Technology Stack](#technology-stack)
- [API Reference](#api-reference)
- [Deployment Strategies](#deployment-strategies)
- [Observability & Monitoring](#observability--monitoring)
- [Development Workflow](#development-workflow)
- [Production Operations](#production-operations)
- [Performance & Scalability](#performance--scalability)
- [Troubleshooting Guide](#troubleshooting-guide)
- [Contributing Guidelines](#contributing-guidelines)

## 🏗️ Architecture & Design

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Applications                      │
│                    (Web, Mobile, Desktop)                      │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                    Traefik v3 (Load Balancer)                  │
│              Dynamic Routing & SSL Termination                 │
└─────────────────────┬───────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
┌───────▼──────┐ ┌────▼────┐ ┌─────▼─────┐
│   Blue App   │ │ Green   │ │   Redis   │
│   (Active)   │ │ App     │ │  Cluster  │
│   Port 8000  │ │ (Standby)│ │  Port 6379│
└──────────────┘ └──────────┘ └───────────┘
        │             │             │
        └─────────────┼─────────────┘
                      │
              ┌───────▼──────┐
              │   React UI   │
              │  (Static)    │
              │  Port 80     │
              └──────────────┘
                      │
              ┌───────▼──────┐
              │ Monitoring   │
              │ Stack        │
              │ (Prometheus, │
              │  Grafana,    │
              │  Alertmanager)│
              └──────────────┘
```

### Design Principles

1. **High Availability**: Multi-environment deployment with automatic failover
2. **Zero Downtime**: Blue/green deployment strategy with atomic traffic switching
3. **Observability**: Comprehensive metrics, logging, and alerting
4. **Scalability**: Horizontal scaling with Redis-based session management
5. **Reliability**: Graceful shutdown, connection recovery, and error handling
6. **Developer Experience**: Modern tooling, clear documentation, and streamlined workflows

### Component Responsibilities

| Component | Technology | Purpose | Key Features |
|-----------|------------|---------|--------------|
| **WebSocket Server** | Django Channels | Real-time communication | ASGI, multiple workers, connection management |
| **Load Balancer** | Traefik v3 | Traffic routing | Dynamic configuration, health checks, SSL termination |
| **Session Store** | Redis 7.x | State management | Persistence, TTL, clustering support |
| **Frontend** | React + Vite | User interface | Real-time updates, modern UX, responsive design |
| **Monitoring** | Prometheus + Grafana | Observability | Metrics collection, visualization, alerting |
| **Containerization** | Docker + Compose | Deployment | Consistent environments, easy scaling |

## 🎯 Core Capabilities

### 1. Zero-Downtime Deployments

**Challenge**: Traditional deployments cause service interruptions, impacting user experience and business continuity.

**Solution**: Blue/green deployment strategy with atomic traffic switching.

**Implementation**:
- Deploy new version to inactive environment
- Run comprehensive health checks and smoke tests
- Atomically switch traffic via Traefik configuration
- Gracefully terminate old environment with connection draining

**Results**:
- Zero service interruption during deployments
- Automatic rollback capability on health check failures
- Traffic switching in <100ms
- Comprehensive validation before promotion

```bash
# Deploy with confidence
make promote

# Monitor deployment health
make status

# Rollback if needed
make rollback
```

### 2. Real-Time Communication

**Challenge**: Building reliable, scalable real-time features with low latency and high throughput.

**Solution**: Django Channels with ASGI and Redis-based session management.

**Features**:
- **WebSocket Connections**: Persistent, bidirectional communication
- **Message Broadcasting**: Efficient group messaging and notifications
- **Session Persistence**: Redis-backed session storage with TTL
- **Connection Recovery**: Automatic reconnection with state restoration
- **Rate Limiting**: Protection against abuse and DoS attacks

**Performance Metrics**:
- **Latency**: <100ms message delivery
- **Throughput**: 5000+ concurrent connections
- **Reliability**: 99.9%+ uptime
- **Scalability**: Horizontal scaling with Redis clustering

### 3. Comprehensive Observability

**Challenge**: Limited visibility into system health, performance, and user experience.

**Solution**: End-to-end monitoring with Prometheus, Grafana, and Alertmanager.

**Capabilities**:
- **Metrics Collection**: Real-time performance and business metrics
- **Dashboard Visualization**: Custom Grafana dashboards for operational insights
- **Alert Management**: Multi-level alerting with escalation procedures
- **Log Aggregation**: Centralized logging with correlation
- **Health Monitoring**: Proactive health checks and incident detection

**Monitoring Stack**:
- **Prometheus**: Metrics collection and alert rule evaluation
- **Grafana**: Dashboard visualization and alert management
- **Alertmanager**: Alert routing and notification delivery
- **Node Exporter**: System-level metrics collection

### 4. Session Management & Persistence

**Challenge**: Maintaining user state across deployments, restarts, and network interruptions.

**Solution**: Multi-tier session persistence with Redis and localStorage.

**Features**:
- **Redis Persistence**: Server-side session storage with configurable TTL
- **localStorage Backup**: Client-side state preservation
- **Session Recovery**: Automatic state restoration on reconnection
- **Individual Preferences**: Per-session persistence configuration
- **Graceful Degradation**: Fallback mechanisms for storage failures

## 🛠️ Technology Stack

### Backend Technologies

| Technology | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| **Python** | 3.11+ | Runtime environment | Performance, ecosystem, maintainability |
| **Django** | 4.2+ | Web framework | Maturity, ecosystem |
| **Django Channels** | 4.0+ | WebSocket support | ASGI compatibility, Redis backend |
| **Uvicorn** | 0.24+ | ASGI server | Performance, multiple workers, graceful shutdown |
| **Redis** | 7.x | Session store | Performance, persistence, clustering |

### Frontend Technologies

| Technology | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| **React** | 18.x | UI framework | Component reusability, ecosystem |
| **TypeScript** | 5.x | Type safety | Developer experience, maintainability |
| **Vite** | 5.x | Build tool | Fast development, optimized builds |
| **Material-UI** | 5.x | Component library | Design consistency, accessibility |

### Infrastructure & Operations

| Technology | Version | Purpose | Rationale |
|------------|---------|---------|-----------|
| **Docker** | Latest | Containerization | Consistency, portability, scaling |
| **Traefik** | v3.x | Load balancer | Dynamic configuration, health checks |
| **Prometheus** | Latest | Metrics collection | Time-series data, alerting |
| **Grafana** | Latest | Visualization | Dashboard creation, alert management |
| **Alertmanager** | Latest | Alert routing | Notification delivery, escalation |

## 📡 API Reference

### WebSocket Endpoints

#### Connect to WebSocket
```javascript
const ws = new WebSocket('ws://localhost/ws/chat/');
```

#### Message Format
```json
{
  "type": "chat_message",
  "message": "Hello, world!",
  "session_id": "uuid-string",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Connection Events
- `connect`: WebSocket connection established
- `message`: New message received
- `disconnect`: Connection lost
- `reconnect`: Automatic reconnection successful

### HTTP Endpoints

#### Health Checks
```bash
# Application health
GET /healthz

# Readiness check
GET /readyz

# Metrics endpoint
GET /metrics
```

#### Session Management
```bash
# Get session info
GET /chat/api/sessions/{session_id}/

# Create new session
POST /chat/api/sessions/

# Delete session
DELETE /chat/api/sessions/{session_id}/
```

## 🚀 Deployment Strategies

### Blue/Green Deployment

**Overview**: Deploy new versions to inactive environment, validate, then switch traffic atomically.

**Process**:
1. **Deploy Blue**: Build and deploy new version to blue environment
2. **Health Validation**: Run comprehensive health checks and smoke tests
3. **Traffic Switch**: Atomically switch traffic from green to blue
4. **Green Deployment**: Deploy new version to green environment
5. **Traffic Switch**: Switch traffic back to green

**Benefits**:
- Zero downtime deployments
- Automatic rollback capability
- Comprehensive validation
- Atomic traffic switching

### Environment Management

```bash
# Deploy blue environment
make blue-up

# Deploy green environment
make green-up

# Promote blue to active
make promote

# Check deployment status
make status

# View deployment logs
make logs
```

### Production Checklist

- [ ] **Pre-deployment**
  - [ ] Run full test suite
  - [ ] Update documentation
  - [ ] Notify stakeholders
  - [ ] Backup current state

- [ ] **Deployment**
  - [ ] Deploy to inactive environment
  - [ ] Run health checks
  - [ ] Execute smoke tests
  - [ ] Switch traffic atomically
  - [ ] Monitor metrics

- [ ] **Post-deployment**
  - [ ] Verify functionality
  - [ ] Monitor error rates
  - [ ] Check performance metrics
  - [ ] Update runbooks if needed

## 📊 Observability & Monitoring

### Metrics Collection

**Application Metrics**:
- `app_active_connections`: Current WebSocket connections
- `app_messages_total`: Total messages processed
- `app_errors_total`: Error count and rate
- `app_sessions_tracked`: Active session count

**System Metrics**:
- `process_cpu_seconds_total`: CPU utilization
- `process_resident_memory_bytes`: Memory usage
- `up{job="websocket-app"}`: Service health status

**Business Metrics**:
- Message throughput and latency
- Connection success/failure rates
- User engagement patterns
- Session duration and churn

### Alerting System

**Critical Alerts (P0)**:
- Service down or unresponsive
- No active WebSocket connections
- High error rate (>10 errors/minute)

**Warning Alerts (P1)**:
- High memory usage (>85%)
- Low message throughput (<1 msg/sec)
- Slow shutdown time (>5 seconds)

**Info Alerts (P2)**:
- Deployment detection
- High session count (>1000)

### Dashboard Access

- **Grafana**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **Alertmanager**: http://localhost:9093

### Complete Monitoring Stack Installation

#### Prerequisites
```bash
# Ensure Docker and Docker Compose are installed
docker --version
docker compose version

# Ensure you have sufficient resources
# Recommended: 4GB RAM, 2 CPU cores for monitoring stack
```

#### Step-by-Step Installation

**1. Start the Monitoring Stack**
```bash
# Option 1: Using Docker Compose directly
docker compose -f docker/monitoring-compose.yml up -d

# Option 2: Using the monitoring script
./scripts/monitor.sh start

# Option 3: Start with the full application stack
make dev-up  # This includes monitoring stack
```

**2. Verify Installation**
```bash
# Check if all services are running
docker compose -f docker/monitoring-compose.yml ps

# Check service health
./scripts/monitor.sh status

# Verify Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check Grafana health
curl http://localhost:3000/api/health
```

**3. Configure Grafana (First Time Setup)**
```bash
# Access Grafana
open http://localhost:3000

# Login with default credentials
# Username: admin
# Password: admin123

# Add Prometheus as a data source
# URL: http://prometheus:9090
# Access: Server (default)

# Import dashboards (optional)
# Dashboard IDs: 1860, 315, 7249
```

**4. Configure Alert Manager**
```bash
# Access Alert Manager
open http://localhost:9093

# Default configuration is pre-loaded
# Check alert rules in Prometheus
open http://localhost:9090/rules
```

#### Monitoring Stack Components

| Component | Port | Purpose | Default Credentials |
|-----------|------|---------|-------------------|
| **Prometheus** | 9090 | Metrics collection & alerting | None |
| **Grafana** | 3000 | Dashboard visualization | admin/admin123 |
| **Alert Manager** | 9093 | Alert routing & notification | None |

#### Troubleshooting Monitoring Stack

**Common Issues**:
```bash
# Check if ports are available
netstat -tulpn | grep -E ':(3000|9090|9093)'

# Restart monitoring stack
docker compose -f docker/monitoring-compose.yml restart

# View logs for specific service
./scripts/monitor.sh logs prometheus
./scripts/monitor.sh logs grafana
./scripts/monitor.sh logs alertmanager

# Reset monitoring data (if needed)
docker compose -f docker/monitoring-compose.yml down -v
docker compose -f docker/monitoring-compose.yml up -d
```

### Monitoring Commands

```bash
# Check service status
./scripts/monitor.sh status

# View active alerts
./scripts/monitor.sh check-alerts

# Access monitoring UIs
./scripts/monitor.sh grafana
./scripts/monitor.sh prometheus
./scripts/monitor.sh alerts
```

## 👨‍💻 Development Workflow

### Local Development

```bash
# Start development environment
make dev-up

# Run tests
make test

# Check code quality
make lint

# Format code
make format

# Access development tools
open http://localhost/          # Application
open http://localhost:3000/     # Grafana
open http://localhost:9090/     # Prometheus
```

### Code Quality

**Linting & Formatting**:
- Black for Python code formatting
- ESLint for JavaScript/TypeScript
- Prettier for code formatting
- MyPy for type checking

**Testing Strategy**:
- Unit tests for business logic
- Integration tests for API endpoints
- End-to-end tests for user workflows
- Performance tests for scalability

**CI/CD Pipeline**:
- Automated testing on pull requests
- Code quality checks
- Automated deployment to staging

### Development Guidelines

1. **Code Standards**:
   - Follow PEP 8 for Python
   - Use TypeScript for frontend code
   - Write comprehensive tests
   - Document public APIs

2. **Git Workflow**:
   - Feature branches from main
   - Descriptive commit messages
   - Pull request reviews
   - Squash commits before merge

3. **Testing**:
   - Write tests for new features
   - Maintain test coverage >80%
   - Run tests before committing
   - Update tests when changing behavior

## 🏭 Production Operations

### Monitoring & Alerting

**Real-time Monitoring**:
- Service health and availability
- Performance metrics and trends
- Error rates and patterns
- User experience metrics

**Alert Management**:
- Multi-level alerting (Critical, Warning, Info)
- Escalation procedures
- On-call rotation
- Incident response playbooks

**Operational Tools**:
- Centralized logging
- Distributed tracing
- Performance profiling
- Capacity planning

### Incident Response

**Response Process**:
1. **Detection**: Automated alerting and monitoring
2. **Assessment**: Quick impact assessment
3. **Response**: Execute runbook procedures
4. **Resolution**: Fix root cause and verify
5. **Post-mortem**: Document lessons learned

**Common Incidents**:
- Service unavailability
- Performance degradation
- High error rates
- Deployment failures

## 📈 Performance & Scalability

### Performance Benchmarks

**Connection Capacity**:
- 5000+ concurrent WebSocket connections
- <100ms message delivery latency
- 99.9%+ uptime availability
- <1s connection establishment time

**Throughput Metrics**:
- 10,000+ messages per second
- <50ms end-to-end latency
- 99.99% message delivery reliability
- <1% connection failure rate

### Scaling Strategies

**Horizontal Scaling**:
- Multiple application instances
- Redis clustering for session storage
- Load balancer distribution
- Database read replicas

**Vertical Scaling**:
- CPU and memory optimization
- Connection pooling
- Caching strategies
- Database optimization

**Capacity Planning**:
- Monitor resource utilization
- Plan for growth projections
- Set up auto-scaling policies
- Regular performance testing

### Optimization Techniques

**Application Level**:
- Async/await for I/O operations
- Connection pooling
- Message batching
- Efficient serialization

**Infrastructure Level**:
- CDN for static assets
- Database indexing
- Redis optimization
- Network optimization

## 🛠️ Troubleshooting Guide

### Common Issues

**Connection Problems**:
```bash
# Check service health
curl http://localhost/healthz

# Verify WebSocket endpoint
curl -I http://localhost/ws/chat/

# Check Redis connectivity
docker exec redis redis-cli ping
```

**Performance Issues**:
```bash
# Monitor resource usage
docker stats

# Check application metrics
curl http://localhost/metrics

# View application logs
make logs
```

**Deployment Issues**:
```bash
# Check deployment status
make status

# View deployment logs
make logs

```

### Debugging Tools

**Application Debugging**:
- Django debug toolbar
- Logging and tracing
- Performance profiling
- Memory leak detection

**Infrastructure Debugging**:
- Docker container inspection
- Network connectivity testing
- Resource monitoring
- Configuration validation

**Monitoring Debugging**:
- Prometheus query debugging
- Alert rule validation
- Dashboard troubleshooting
- Notification delivery testing

## 🤝 Contributing Guidelines

### Getting Started

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Write tests**
5. **Submit a pull request**

### Development Setup

```bash
# Clone your fork
git clone https://github.com/vishal2612200/django-websocket-service.git
cd django-websocket-service

# Set up development environment
make dev-setup

# Run tests
make test

# Start development server
make dev-up
```

### Contribution Areas

**Code Contributions**:
- Bug fixes and improvements
- New features and enhancements
- Performance optimizations
- Documentation updates

**Documentation**:
- API documentation
- Deployment guides
- Troubleshooting guides
- Best practices

**Testing**:
- Unit test coverage
- Integration tests
- Performance tests

### Code Review Process

1. **Automated Checks**:
   - Code formatting
   - Linting and style checks
   - Test coverage

2. **Manual Review**:
   - Code quality assessment
   - Architecture review
   - Performance impact

3. **Approval Process**:
   - At least one approval required
   - All checks must pass
   - Documentation updated
   - Tests included

## 📚 Documentation

### Core Documentation
- [API Documentation](docs/API.md) - Complete API reference and integration guide
- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment and operations
- [Design Documentation](docs/DESIGN.md) - System architecture and design decisions
- [Observability Guide](docs/OBSERVABILITY.md) - Monitoring, metrics, and alerting
- [Alerting System](docs/ALERTING_SYSTEM.md) - Comprehensive alert rules and incident response

### Feature Documentation
📖 **Detailed Guide**: [Session Resumption Documentation](docs/SESSION_RESUMPTION.md)
📖 **Detailed Guide**: [SIGTERM Handling Documentation](docs/SIGTERM_HANDLING.md)
📖 **Detailed Guide**: [Reconnect Functionality Documentation](docs/RECONNECT_FUNCTIONALITY.md)
📖 **Detailed Guide**: [Duplicate Messages Fix Documentation](docs/DUPLICATE_MESSAGES_FIX.md)
📖 **Detailed Guide**: [Performance Analysis Documentation](docs/PERFORMANCE_ANALYSIS.md)
📖 **Detailed Guide**: [Alerting System Documentation](docs/ALERTING_SYSTEM.md)

### Quick References
- [Alert Quick Reference](docs/ALERT_QUICK_REFERENCE.md) - Essential alerting commands and procedures
- [Monitoring Setup](docs/MONITORING_SETUP.md) - Monitoring stack configuration
- [Grafana Dashboard](docs/GRAFANA_DASHBOARD.md) - Dashboard configuration and usage

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Django Channels** team for the excellent WebSocket support
- **Traefik** community for the powerful load balancer
- **Prometheus** and **Grafana** teams for the monitoring ecosystem
- **React** and **Material-UI** communities for the frontend framework

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/vishal2612200/django-websocket-service/issues)
- **Discussions**: [GitHub Discussions](https://github.com/vishal2612200/django-websocket-service/discussions)

---
