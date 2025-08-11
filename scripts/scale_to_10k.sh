#!/usr/bin/env bash
set -euo pipefail

# Scaling to 10,000 Connections Configuration Script
# This script applies all necessary configuration changes to scale from 5K to 10K connections

echo "🚀 Scaling Configuration to 10,000 Connections"
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "docker/compose.yml" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Backup original files
echo "📋 Creating backups..."
cp docker/compose.yml docker/compose.yml.backup
cp scripts/load_test.py scripts/load_test.py.backup

# 1. Update Docker Compose Configuration
echo "🔧 Updating Docker Compose configuration..."
sed -i.bak 's/UVICORN_WORKERS=6/UVICORN_WORKERS=10/g' docker/compose.yml

# Add resource limits and ulimits to app services
echo "📦 Adding resource limits to app services..."

# Function to add resource configuration to a service
add_resource_config() {
    local service_name=$1
    local temp_file=$(mktemp)
    
    # Create the resource configuration block
    cat > "$temp_file" << 'EOF'
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
EOF

    # Insert the configuration after the environment section
    awk -v service="$service_name" -v config_file="$temp_file" '
    /^  '"$service_name"':/ { in_service=1 }
    in_service && /^    environment:/ { in_env=1 }
    in_env && /^    depends_on:/ { 
        # Print the resource config before depends_on
        system("cat " config_file)
        in_env=0
    }
    { print }
    ' docker/compose.yml > docker/compose.yml.tmp
    
    mv docker/compose.yml.tmp docker/compose.yml
    rm "$temp_file"
}

# Add resource configuration to app_blue and app_green
add_resource_config "app_blue"
add_resource_config "app_green"

# 2. Update Redis Configuration
echo "🔴 Updating Redis configuration..."
sed -i.bak 's/redis-server --appendonly yes --save 60 1000/redis-server --appendonly yes --save 60 1000 --maxclients 20000 --tcp-keepalive 300/g' docker/compose.yml

# Add resource limits to Redis services
echo "📦 Adding resource limits to Redis services..."

# Function to add Redis resource configuration
add_redis_resource_config() {
    local service_name=$1
    local temp_file=$(mktemp)
    
    cat > "$temp_file" << 'EOF'
  # Add resource limits for high concurrency
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: '2.0'
  # Increase ulimit for file descriptors
  ulimits:
    nofile:
      soft: 65536
      hard: 65536
EOF

    awk -v service="$service_name" -v config_file="$temp_file" '
    /^  '"$service_name"':/ { in_service=1 }
    in_service && /^    volumes:/ { 
        # Print the resource config before volumes
        system("cat " config_file)
    }
    in_service && /^    image:/ && !/volumes:/ { 
        # Print the resource config after image if no volumes
        system("cat " config_file)
    }
    { print }
    ' docker/compose.yml > docker/compose.yml.tmp
    
    mv docker/compose.yml.tmp docker/compose.yml
    rm "$temp_file"
}

add_redis_resource_config "redis_blue"
add_redis_resource_config "redis_green"
add_redis_resource_config "redis_shared"

# 3. Update Load Test Configuration
echo "🧪 Updating load test configuration..."
sed -i.bak 's/default=int(os.environ.get("N", "1000")/default=int(os.environ.get("N", "10000")/g' scripts/load_test.py

# 4. Create system optimization file
echo "⚙️  Creating system optimization configuration..."
mkdir -p docker/system
cat > docker/system/sysctl.conf << 'EOF'
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
EOF

# 5. Update Dockerfile if it exists
if [ -f "docker/Dockerfile" ]; then
    echo "🐳 Updating Dockerfile optimizations..."
    cp docker/Dockerfile docker/Dockerfile.backup
    
    # Add system optimizations to Dockerfile
    cat >> docker/Dockerfile << 'EOF'

# System optimizations for high concurrency
RUN echo "* soft nofile 65536" >> /etc/security/limits.conf && \
    echo "* hard nofile 65536" >> /etc/security/limits.conf && \
    echo "session required pam_limits.so" >> /etc/pam.d/common-session

# Optimize Python for high concurrency
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONOPTIMIZE=2

# Increase default thread pool size
ENV UVICORN_THREAD_POOL_SIZE=8
EOF
fi

# 6. Create deployment script
echo "📜 Creating deployment script..."
cat > scripts/deploy_10k.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Deploying 10K Configuration..."

# Stop current deployment
echo "🛑 Stopping current deployment..."
make dev-down

# Apply system optimizations
echo "⚙️  Applying system optimizations..."
if [ -f "docker/system/sysctl.conf" ]; then
    sudo sysctl -p docker/system/sysctl.conf || true
fi

# Increase file descriptor limits
echo "📁 Increasing file descriptor limits..."
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Rebuild with new configuration
echo "🔨 Rebuilding containers..."
docker compose -f docker/compose.yml build

# Start with new configuration
echo "▶️  Starting with new configuration..."
make dev-up

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Verify deployment
echo "✅ Verifying deployment..."
make logs

echo "🎉 10K Configuration deployed successfully!"
echo "🧪 Test with: N=10000 make load-test"
EOF

chmod +x scripts/deploy_10k.sh

# 7. Create monitoring script
echo "📊 Creating monitoring script..."
cat > scripts/monitor_10k.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail

echo "📊 10K Connection Monitoring"
echo "============================"

# Check active connections
echo "🔗 Active Connections:"
curl -s http://localhost/metrics | grep app_active_connections || echo "No active connections found"

# Check container resources
echo -e "\n📦 Container Resources:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

# Check Redis connections
echo -e "\n🔴 Redis Connections:"
docker compose -f docker/compose.yml exec -T redis_blue redis-cli info clients | grep connected_clients || echo "Redis not accessible"

# Check file descriptors
echo -e "\n📁 File Descriptors:"
docker compose -f docker/compose.yml exec -T app_blue cat /proc/sys/fs/file-nr 2>/dev/null || echo "Cannot check file descriptors"

# Check network connections
echo -e "\n🌐 Network Connections:"
docker compose -f docker/compose.yml exec -T app_blue netstat -an | wc -l 2>/dev/null || echo "Cannot check network connections"
EOF

chmod +x scripts/monitor_10k.sh

echo ""
echo "✅ Configuration updates completed!"
echo ""
echo "📋 Summary of changes:"
echo "  • UVICORN_WORKERS increased from 6 to 10"
echo "  • Resource limits added (4GB RAM, 4 CPU cores per app container)"
echo "  • File descriptor limits set to 65536"
echo "  • Redis maxclients increased to 20000"
echo "  • Load test default increased to 10000"
echo "  • System optimizations configured"
echo ""
echo "🚀 Next steps:"
echo "  1. Run: ./scripts/deploy_10k.sh"
echo "  2. Test: N=10000 make load-test"
echo "  3. Monitor: ./scripts/monitor_10k.sh"
echo ""
echo "📚 For detailed information, see: docs/SCALING_TO_10000.md"
echo ""
echo "⚠️  Note: This configuration requires at least 8GB RAM and 8 CPU cores"
echo "   for optimal performance with 10,000 concurrent connections."
