#!/bin/bash

# DevMind Pipeline - Start All Dashboards
# This script sets up port-forwards to access all services and dashboards

echo "🚀 Starting DevMind Pipeline Dashboards..."
echo ""

# Kill any existing port-forwards
pkill -f "kubectl port-forward" 2>/dev/null

# Function to start port-forward in background
start_port_forward() {
    local service=$1
    local namespace=$2
    local local_port=$3
    local remote_port=$4
    local name=$5

    kubectl port-forward -n $namespace svc/$service $local_port:$remote_port > /dev/null 2>&1 &
    echo "✅ $name: http://localhost:$local_port"
}

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
kubectl wait --for=condition=ready pod -l app=grafana -n devmind-pipeline --timeout=300s
kubectl wait --for=condition=ready pod -l app=prometheus -n devmind-pipeline --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n devmind-pipeline --timeout=300s
kubectl wait --for=condition=ready pod -l app=postgres -n devmind-pipeline --timeout=300s

# Note: ML service might take longer due to dependency installation
echo "⏳ Waiting for ML service (this may take a few minutes)..."
kubectl wait --for=condition=ready pod -l app=devmind-ml-service -n devmind-pipeline --timeout=600s

echo ""
echo "🌐 Starting port-forwards..."
echo ""

# Start port-forwards
start_port_forward "devmind-ml-service" "devmind-pipeline" "8000" "8000" "DevMind ML API"
start_port_forward "grafana" "devmind-pipeline" "3000" "3000" "Grafana Dashboard"
start_port_forward "prometheus" "devmind-pipeline" "9090" "9090" "Prometheus Metrics"
start_port_forward "postgres" "devmind-pipeline" "5432" "5432" "PostgreSQL Database"
start_port_forward "redis" "devmind-pipeline" "6379" "6379" "Redis Cache"

echo ""
echo "📊 All dashboards are now accessible:"
echo ""
echo "  🤖 ML API:            http://localhost:8000"
echo "     - Swagger Docs:    http://localhost:8000/docs"
echo "     - Health Check:    http://localhost:8000/health"
echo ""
echo "  📈 Grafana:          http://localhost:3000"
echo "     - Username: admin"
echo "     - Password: admin"
echo ""
echo "  📊 Prometheus:       http://localhost:9090"
echo ""
echo "  🗄️  PostgreSQL:       localhost:5432"
echo "     - Database: devmind"
echo "     - User: devmind"
echo "     - Password: devmind123"
echo ""
echo "  🔴 Redis:            localhost:6379"
echo ""
echo "💡 Press Ctrl+C to stop all port-forwards"
echo ""

# Wait for interrupt
wait
