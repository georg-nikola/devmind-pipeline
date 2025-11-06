#!/bin/bash
set -e

echo "🚀 Deploying DevMind Pipeline to Local OrbStack Cluster"
echo "========================================================"
echo ""

# Verify we're on OrbStack context
CURRENT_CONTEXT=$(kubectl config current-context)
if [ "$CURRENT_CONTEXT" != "orbstack" ]; then
    echo "⚠️  Warning: Current kubectl context is '$CURRENT_CONTEXT', not 'orbstack'"
    read -p "Switch to orbstack context? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kubectl config use-context orbstack
        echo "✅ Switched to orbstack context"
    else
        echo "❌ Deployment cancelled. Please switch to orbstack context first."
        exit 1
    fi
fi

# Verify OrbStack is running
if ! kubectl get nodes | grep -q "orbstack"; then
    echo "❌ OrbStack cluster not accessible. Is OrbStack running?"
    exit 1
fi

echo "📦 Building Docker image locally..."
cd "$(dirname "$0")/.."
docker build -t devmind-ml-service:local .

echo ""
echo "🔧 Creating namespace..."
kubectl apply -f k8s/base/namespace.yaml

echo ""
echo "⚙️  Applying base manifests..."
kubectl apply -f k8s/base/secret.yaml
kubectl apply -f k8s/local/configmap-override.yaml
kubectl apply -f k8s/base/service.yaml
kubectl apply -f k8s/local/service-nodeport.yaml

echo ""
echo "🚀 Deploying application..."
# Apply base deployment then patch with local overrides
kubectl apply -f k8s/base/deployment.yaml
kubectl patch deployment devmind-ml-service -n devmind-pipeline --patch-file k8s/local/deployment-patch.yaml

echo ""
echo "⏳ Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/devmind-ml-service -n devmind-pipeline

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Service Status:"
kubectl get pods -n devmind-pipeline
echo ""
kubectl get svc -n devmind-pipeline
echo ""
echo "🌐 Access points:"
echo "  - API: http://localhost:30800"
echo "  - Docs: http://localhost:30800/docs"
echo "  - Health: http://localhost:30800/health"
echo ""
echo "📝 View logs:"
echo "  kubectl logs -n devmind-pipeline -l app=devmind-ml-service -f"
echo ""
echo "🔍 Port forward (alternative to NodePort):"
echo "  kubectl port-forward -n devmind-pipeline svc/devmind-ml-service 8000:8000"
echo ""
