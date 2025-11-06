# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DevMind Pipeline is an AI-Enhanced DevOps automation platform that combines:
- **Python ML Services** (FastAPI) for build optimization, failure prediction, and test intelligence
- **Go Pipeline Engine** (planned/stub) for high-performance execution with Tekton/ArgoCD
- **React Dashboard** (planned/stub) for visualizations
- **Kubernetes deployment** with monitoring (Prometheus/Grafana)

This is currently a **demonstration/portfolio project** - the Python ML services are functional API endpoints with placeholder ML implementations, while Go and React components are minimal stubs.

## Development Commands

### Python ML Services (Primary Component)

```bash
# Navigate to Python source
cd src

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov pytest-asyncio black mypy

# Run the ML service locally
python -m uvicorn main:app --reload
# Access at http://localhost:8000/docs

# Run with specific configuration
python main.py
```

### Code Quality & Testing

```bash
# Format code with Black (line length: 100)
cd src
black .
black --check .  # Check without modifying

# Type checking (currently lenient)
mypy . --ignore-missing-imports

# Run tests (when test suite exists)
pytest tests/ -v
pytest tests/ --cov=. --cov-report=html

# Security scanning
pip install safety bandit
safety check -r requirements.txt
bandit -r . -f json
```

### Kubernetes Deployment

```bash
# Deploy to local Kubernetes (OrbStack/minikube)
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/

# Wait for services to be ready
kubectl wait --for=condition=ready pod -l app=devmind-ml-service -n devmind-pipeline --timeout=600s

# Port forward to access services
./start-dashboards.sh
# Or manually:
kubectl port-forward -n devmind-pipeline svc/devmind-ml-service 8000:8000 &
kubectl port-forward -n devmind-pipeline svc/grafana 3000:3000 &
kubectl port-forward -n devmind-pipeline svc/prometheus 9090:9090 &

# Check service status
kubectl get pods -n devmind-pipeline
kubectl logs -n devmind-pipeline -l app=devmind-ml-service -f
```

## Architecture

### Service Structure

The Python ML services follow a layered architecture:

```
src/
├── main.py                    # FastAPI app entry point, lifespan management
├── core/                      # Core infrastructure
│   ├── config.py             # Settings, ML model configs, K8s config
│   ├── logging.py            # Structured logging setup (structlog)
│   └── monitoring.py         # Prometheus metrics setup
├── api/routers/              # API endpoints
│   ├── build_optimizer.py   # Build optimization endpoints
│   ├── failure_predictor.py # Failure prediction endpoints
│   └── test_intelligence.py # Test selection endpoints
└── services/                 # Business logic & ML services
    ├── ml_service_manager.py # Orchestrates all ML services
    └── build_optimizer.py    # XGBoost-based build optimizer (detailed impl)
```

### Key Design Patterns

1. **Lifespan Management**: `main.py` uses FastAPI's `@asynccontextmanager` lifespan to initialize `MLServiceManager` and monitoring on startup, cleanup on shutdown

2. **Settings Management**: `core/config.py` uses Pydantic `BaseSettings` with:
   - `Settings` class for app config (reads from environment variables)
   - `MLModelConfig` class for model-specific hyperparameters
   - `KubernetesConfig` class for K8s pod metadata
   - `@lru_cache()` on `get_settings()` for singleton pattern

3. **ML Service Architecture**:
   - Each ML service (e.g., `BuildOptimizer`) is initialized by `MLServiceManager`
   - Services implement caching, feature engineering, and model lifecycle
   - Health checks exposed via `/health` and `/models/status` endpoints
   - Model retraining triggered via `/models/retrain/{model_name}` endpoint

4. **Structured Logging**: Uses `structlog` throughout for JSON-formatted logs with contextual fields

5. **API Routers**: Each router defines Pydantic request/response models and is included with versioned prefix `/api/v1/{service}`

### ML Models Configuration

Defined in `src/core/config.py:MLModelConfig`:
- **Build Optimizer**: XGBoost regressor predicting build times (features: dependency_count, code_change_size, etc.)
- **Failure Predictor**: PyTorch neural network predicting pipeline failures
- **Test Intelligence**: Random Forest classifier for test selection

Configuration includes hyperparameters, feature columns, and training settings.

### External Integrations

The platform is designed to integrate with:
- **Tekton**: Pipeline execution (namespace: `tekton-pipelines`)
- **ArgoCD**: GitOps deployments (requires `ARGOCD_TOKEN`)
- **MLflow**: Model registry (default: `http://localhost:5000`)
- **Prometheus**: Metrics collection (scraped from `/metrics` endpoint)
- **Jaeger**: Distributed tracing (optional, via `JAEGER_ENDPOINT`)

## CI/CD Pipeline

Defined in `.github/workflows/ci-cd.yml`:

**Required Status Checks** (branch protection on `main`):
- Test Python ML Services (Python 3.11)
- Test Python ML Services (Python 3.12)
- Security Scan

**Pipeline Steps**:
1. Black formatting check (`black --check .`)
2. Type checking with mypy (lenient, `|| true`)
3. Pytest with coverage (lenient, `|| true`)
4. Security scans: Trivy (filesystem), safety (dependencies), bandit (Python code)

**Note**: Tests are currently lenient (allowed to fail) as the codebase is under development.

## Development Guidelines

### Code Style

- **Python**: PEP 8, formatted with Black (100 character line length)
- **Type Hints**: Required for function signatures
- **Docstrings**: Google-style format
- **Imports**: Standard library, third-party, local (Black handles grouping)

### Contributing Workflow

This project uses a **fork-based workflow** with branch protection:
1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature-name`
3. Make changes and add tests
4. Run Black: `cd src && black .`
5. Commit with clear messages
6. Push to fork and create PR to `main`

**PR Requirements**:
- At least 1 approving review
- All CI checks must pass
- All conversations resolved
- Branch must be up-to-date with main

### Configuration Management

All configuration is managed via:
1. **Environment Variables**: For deployment-specific values (database URLs, API keys, etc.)
2. **`core/config.py`**: For application defaults and ML model configs
3. **K8s ConfigMaps/Secrets**: For Kubernetes deployments (in `k8s/` directory)

When adding new configuration:
- Add to `Settings` class with `Field(default=..., env="ENV_VAR_NAME")`
- Document in code comments
- Never commit secrets - use environment variables or K8s secrets

### Testing Strategy

When adding tests:
- Place in `src/tests/` directory (to be created)
- Use pytest with async support (`pytest-asyncio`)
- Mock external dependencies (ML models, databases, external APIs)
- Aim for >80% coverage
- Use fixtures for common test data

### Adding New ML Services

1. Create service class in `src/services/` (see `build_optimizer.py` as reference)
2. Add API router in `src/api/routers/`
3. Define Pydantic models for request/response
4. Register router in `main.py` with versioned prefix
5. Add model config to `MLModelConfig` in `core/config.py`
6. Update `ml_service_manager.py` to initialize new service
7. Add health check logic

## GitOps Deployment Strategy

This project uses **ArgoCD** for GitOps-based deployments to the production Talos Kubernetes cluster.

### Architecture

```
GitHub Repo (main branch)           ArgoCD              Production Cluster
─────────────────────────            ──────              ──────────────────
k8s/production/                       │
├── deployment-patch.yaml  ──────────►│──────────────►   devmind-pipeline namespace
├── configmap-override.yaml           │                   (Talos K8s Cluster)
├── ingressroute.yaml                 │
└── (base manifests referenced)       │
                                      │
                                Auto-sync every 3 min
                                Self-heal on drift
```

### Deployment Workflow

1. **Make changes** to Kubernetes manifests in `k8s/production/` or `k8s/base/`
2. **Commit and push** to the `main` branch on GitHub
3. **ArgoCD automatically syncs** within 3 minutes (or manual sync via UI/CLI)
4. **Changes are deployed** to production cluster

### Manual Deployment Commands

#### Option 1: GitOps (Recommended)

```bash
# 1. Make your changes
vim k8s/production/deployment-patch.yaml

# 2. Commit and push
git add k8s/
git commit -m "Update deployment configuration"
git push origin main

# 3. Wait for ArgoCD to sync (3 min) or trigger manually
argocd app sync devmind-pipeline
# Or visit: https://argocd.example.com

# 4. Verify deployment
kubectl get pods -n devmind-pipeline
```

#### Option 2: Direct kubectl (Development only)

```bash
# Deploy to local OrbStack cluster
cd scripts
./deploy-local.sh

# Access locally
kubectl port-forward -n devmind-pipeline svc/devmind-ml-service 8000:8000
# Or via NodePort: http://localhost:30800
```

### Accessing Services

#### Production (via Cloudflare Access)

After DNS and Cloudflare Access are configured:
- **API**: https://devmind.example.com
- **Docs**: https://devmind-api.example.com/docs
- **Health**: https://devmind.example.com/health

Protected by Cloudflare Zero Trust Access (email-based One-Time PIN).

#### ArgoCD Dashboard

- **URL**: https://argocd.example.com
- **Username**: admin
- **Password**: Retrieved via `kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d`

#### Monitoring

- **Grafana**: https://grafana.example.com
- **Prometheus**: https://prometheus.example.com

All metrics from `devmind-ml-service` are automatically scraped by Prometheus.

### Docker Image Build & Push

The production deployment uses images from GitHub Container Registry (GHCR):

```bash
# Build image
docker build -t devmind-ml-service:latest .

# Tag for GHCR
docker tag devmind-ml-service:latest ghcr.io/YOUR_GITHUB_USERNAME/devmind-ml-service:latest

# Login to GHCR (requires GitHub PAT with packages:write)
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin

# Push image
docker push ghcr.io/YOUR_GITHUB_USERNAME/devmind-ml-service:latest

# ArgoCD will automatically pull and deploy on next sync
```

### Environment-Specific Configuration

#### Local (OrbStack)
- **Manifests**: `k8s/local/`
- **Image**: `devmind-ml-service:local` (built locally)
- **Replicas**: 1
- **Access**: NodePort 30800 or port-forward

#### Production (Talos)
- **Manifests**: `k8s/production/` (overlays on `k8s/base/`)
- **Image**: `ghcr.io/YOUR_GITHUB_USERNAME/devmind-ml-service:latest`
- **Replicas**: 2 (HA)
- **Access**: Via Cloudflare Tunnel + Traefik IngressRoute

### CloudFlare Integration Setup

The production deployment requires:

1. **DNS Record** (via Terraform):
```hcl
resource "cloudflare_record" "devmind" {
  zone_id = data.cloudflare_zone.main.id
  name    = "devmind"
  content = "${var.cloudflare_tunnel_id}.cfargotunnel.com"
  type    = "CNAME"
  proxied = true
}
```

2. **Access Application** (via Terraform):
```hcl
resource "cloudflare_access_application" "devmind" {
  account_id = var.cloudflare_account_id
  name       = "DevMind Pipeline API"
  domain     = "devmind.example.com"
  type       = "self_hosted"
  session_duration = "24h"
}
```

3. **Tunnel Configuration** (add to `talos-configs` repo):
```yaml
ingress:
  - hostname: devmind.example.com
    service: http://traefik.traefik.svc.cluster.local:80
```

Apply with:
```bash
cd ~/repos/talos-configs/local-cluster-config/manifests/terraform
get_cloudflare_credentials  # Load credentials
terraform apply

cd ~/repos/talos-configs/local-cluster-config/manifests/cloudflare-tunnel
kubectl apply -f config.yaml
kubectl rollout restart deployment/cloudflared -n cloudflare-tunnel
```

### Useful Commands

```bash
# View ArgoCD application status
kubectl get application devmind-pipeline -n argocd
argocd app get devmind-pipeline

# View deployed resources
kubectl get all -n devmind-pipeline

# View logs
kubectl logs -n devmind-pipeline -l app=devmind-ml-service -f

# Describe pod for debugging
kubectl describe pod -n devmind-pipeline <pod-name>

# Manual sync in ArgoCD
argocd app sync devmind-pipeline

# Rollback in ArgoCD
argocd app history devmind-pipeline
argocd app rollback devmind-pipeline <revision>

# Port forward for testing
kubectl port-forward -n devmind-pipeline svc/devmind-ml-service 8000:8000
```

### Utility Function

Add this to your shell profile for easy Cloudflare credentials loading:

```bash
# ~/.zshrc or ~/.bashrc
get_cloudflare_credentials() {
  export CLOUDFLARE_EMAIL=$(op read "op://Personal/Global CloudFlare API Key/username")
  export CLOUDFLARE_API_KEY=$(op read "op://Personal/Global CloudFlare API Key/credential")
}
```

## Common Issues

### ArgoCD Sync Failures
- Check application status: `kubectl describe application devmind-pipeline -n argocd`
- Verify GitHub repository is accessible
- Ensure manifests are valid: `kubectl apply --dry-run=client -f k8s/production/`
- Check ArgoCD logs: `kubectl logs -n argocd -l app.kubernetes.io/name=argocd-server`

### Model Initialization Failures
- Check that `MODEL_STORAGE_PATH` exists and is writable
- Verify MLflow tracking URI is accessible
- Look for errors in service initialization logs

### Kubernetes Pod CrashLoopBackOff
- Check logs: `kubectl logs -n devmind-pipeline <pod-name>`
- Verify ConfigMaps and Secrets are applied
- Ensure resource limits are sufficient (default: 2Gi memory, 1000m CPU)
- Check image pull: `kubectl describe pod -n devmind-pipeline <pod-name>`

### Import Errors
- Ensure you're running from `src/` directory or have proper PYTHONPATH
- Verify all dependencies in `requirements.txt` are installed
- Check Python version (requires 3.11+)
