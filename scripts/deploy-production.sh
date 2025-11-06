#!/bin/bash
set -e

echo "🚀 Deploying DevMind Pipeline to Production Talos Cluster"
echo "=========================================================="
echo ""

# Verify we're on Talos context (update with your cluster context)
CURRENT_CONTEXT=$(kubectl config current-context)
EXPECTED_CONTEXT="admin@your-talos-cluster"  # Update this with your cluster context
if [ "$CURRENT_CONTEXT" != "$EXPECTED_CONTEXT" ]; then
    echo "⚠️  Warning: Current kubectl context is '$CURRENT_CONTEXT'"
    echo "    Expected: '$EXPECTED_CONTEXT'"
    read -p "Switch to production Talos context? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kubectl config use-context "$EXPECTED_CONTEXT"
        echo "✅ Switched to Talos production context"
    else
        echo "❌ Deployment cancelled. Please switch to correct context first."
        exit 1
    fi
fi

# Verify we're on the right cluster
echo "✅ Current cluster nodes:"
kubectl get nodes

echo "✅ Connected to Talos production cluster"
echo ""

# Check if image exists (update with your GitHub username)
IMAGE_NAME="ghcr.io/YOUR_GITHUB_USERNAME/devmind-ml-service:latest"
echo "📦 Using image: $IMAGE_NAME"
echo "⚠️  Make sure you've built and pushed the image first!"
echo ""
read -p "Continue with deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

cd "$(dirname "$0")/.."

echo "🔧 Creating namespace..."
kubectl apply -f k8s/base/namespace.yaml

echo ""
echo "🔐 Setting up secrets..."
echo "⚠️  You should create production secrets manually or using a secret manager"
echo ""
read -p "Have you created the production secret 'devmind-ml-secrets'? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Creating secret from template (⚠️  NOT FOR PRODUCTION USE)..."
    echo "Please update the secret with real production values!"
    kubectl apply -f k8s/base/secret.yaml
    echo ""
    echo "🚨 IMPORTANT: Update the secret with production values:"
    echo "  kubectl edit secret devmind-ml-secrets -n devmind-pipeline"
    echo ""
    read -p "Press Enter to continue after updating the secret..."
fi

echo ""
echo "⚙️  Applying production configuration..."
kubectl apply -f k8s/production/configmap-override.yaml
kubectl apply -f k8s/base/service.yaml

echo ""
echo "🚀 Deploying application..."
# Apply base deployment then patch with production overrides
kubectl apply -f k8s/base/deployment.yaml
kubectl patch deployment devmind-ml-service -n devmind-pipeline --patch-file k8s/production/deployment-patch.yaml

echo ""
echo "🌐 Creating IngressRoute..."
kubectl apply -f k8s/production/ingressroute.yaml

echo ""
echo "⏳ Waiting for deployment to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/devmind-ml-service -n devmind-pipeline || true

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Service Status:"
kubectl get pods -n devmind-pipeline
echo ""
kubectl get svc -n devmind-pipeline
echo ""
kubectl get ingressroute -n devmind-pipeline
echo ""
echo "🌐 Public URLs (after Cloudflare Access setup):"
echo "  - API: https://devmind.example.com"
echo "  - Docs: https://devmind-api.example.com/docs"
echo ""
echo "📝 View logs:"
echo "  kubectl logs -n devmind-pipeline -l app=devmind-ml-service -f"
echo ""
echo "🔍 Monitor with Grafana:"
echo "  https://grafana.example.com"
echo ""
echo ""
echo "⚠️  NEXT STEPS:"
echo "  1. Set up Cloudflare Access for devmind.example.com"
echo "  2. Update Cloudflare Tunnel config to route devmind.example.com"
echo "  3. Verify Prometheus is scraping metrics"
echo "  4. Test the deployment"
echo ""
