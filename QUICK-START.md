# DevMind Pipeline - Quick Start Guide

## 📋 One-Minute Summary

You have a **fully automated production deployment pipeline**. To deploy:

```bash
# 1. Make code changes
# 2. Create release (this triggers automated build + deployment)
cd /path/to/devmind-pipeline
gh release create v1.3.0
# 3. Done! ✅
```

## 🚀 First Time Setup

### Prerequisites
- GitHub repository (fork of devmind-pipeline)
- Talos Kubernetes cluster
- ArgoCD installed (via Helm)
- kubectl configured
- gh CLI installed

### Setup Steps

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/devmind-pipeline
cd devmind-pipeline

# 2. Update deployment references (YOUR_USERNAME)
cd /path/to/private-talos-configs
vim local-cluster-config/manifests/argocd/application-devmind.yaml
# Update: repository: ghcr.io/YOUR_USERNAME/devmind-ml-service

# 3. Apply ArgoCD application
kubectl apply -f local-cluster-config/manifests/argocd/application-devmind.yaml

# 4. Verify ArgoCD is watching your repo
kubectl get application devmind-pipeline -n argocd
```

## 📦 Common Tasks

### Deploy New Version
```bash
# Create release with version tag
gh release create v1.3.0 \
  --title "Release v1.3.0" \
  --notes "## Features\n- Your changes here"

# Automated workflow:
# ✅ Builds Docker image
# ✅ Pushes to GHCR
# ✅ ArgoCD detects change
# ✅ Deploys to cluster
```

### Monitor Deployment
```bash
# Watch pods
kubectl get pods -n devmind-pipeline -w

# View logs
kubectl logs -n devmind-pipeline -l app=devmind-ml-service -f

# Check ArgoCD status
kubectl get application devmind-pipeline -n argocd

# Test health
kubectl port-forward -n devmind-pipeline svc/devmind-pipeline 8000:8000
curl http://localhost:8000/health
```

### Update Configuration
```bash
# Edit production values in private repo
vim /path/to/private-talos-configs/local-cluster-config/manifests/argocd/values/devmind-pipeline-production.yaml

# Common updates:
# - replicaCount: 2 (scaling)
# - image.tag: v1.3.0 (specific version)
# - resources.limits.memory: 4Gi (resource limits)

# Apply changes
kubectl apply -f /path/to/private-talos-configs/local-cluster-config/manifests/argocd/application-devmind.yaml

# ArgoCD syncs within 3 minutes
```

### Scale Deployment
```bash
# Edit values to increase replicas
replicaCount: 3  # was 2

# Apply
kubectl apply -f application-devmind.yaml

# Watch scaling
kubectl rollout status deployment/devmind-pipeline -n devmind-pipeline
```

### Rollback to Previous Version
```bash
# View version history
kubectl rollout history deployment/devmind-pipeline -n devmind-pipeline

# Rollback to previous
kubectl rollout undo deployment/devmind-pipeline -n devmind-pipeline

# Or to specific revision
kubectl rollout undo deployment/devmind-pipeline -n devmind-pipeline --to-revision=2
```

## 🔍 Troubleshooting

### Pods in ImagePullBackOff
```bash
# Check if image was pushed
docker pull ghcr.io/YOUR_USERNAME/devmind-ml-service:v1.2.0

# If not found, GitHub Actions build may still be running
cd devmind-pipeline
gh run list --workflow="Build and Push Docker Image" --limit 1

# Trigger manual sync
kubectl patch application devmind-pipeline -n argocd \
  --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/compare-result":""}}}'
```

### ArgoCD Shows OutOfSync
```bash
# This is normal during deployments. Options:

# Wait for auto-sync (3 minutes)
kubectl get application devmind-pipeline -n argocd -w

# Or force manual sync
kubectl patch application devmind-pipeline -n argocd \
  --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/compare-result":""}}}'
```

### Application Not Accessible
```bash
# Verify service exists
kubectl get svc -n devmind-pipeline

# Verify IngressRoute
kubectl get ingressroute -n devmind-pipeline

# Test port-forward
kubectl port-forward -n devmind-pipeline svc/devmind-pipeline 8000:8000
curl http://localhost:8000/health

# Check pod logs for errors
kubectl logs -n devmind-pipeline -l app=devmind-ml-service
```

## 📚 Full Documentation

- **DEPLOYMENT-COMPLETE.md** - Complete setup and architecture
- **PRODUCTION-DEPLOYMENT-GUIDE.md** - Detailed deployment steps
- **CLAUDE.md** - Architecture and development guide
- **helm/devmind-pipeline/README.md** - Helm chart documentation

## 🔑 Key Concepts

### Public vs Private Repository

**Public (devmind-pipeline)**:
- Application code in `src/`
- Dockerfile for containerization
- Helm chart in `helm/devmind-pipeline/` (generic, no secrets)
- GitHub Actions workflows in `.github/workflows/`
- No personal information or secrets

**Private (talos-configs)**:
- ArgoCD application definitions
- Production values overlays
- Cluster secrets and configuration
- Cloudflare integration settings
- All sensitive data kept private

### How Deployment Works

```
1. Create Release
   └─→ GitHub Actions triggered
       └─→ Build Docker image
           └─→ Push to GHCR
               └─→ Webhook to ArgoCD (or manual sync)
                   └─→ ArgoCD templates Helm chart
                       └─→ ArgoCD applies manifests
                           └─→ Kubernetes rolls out new version
                               └─→ Service updated ✅
```

## ✨ Deployment Lifecycle

### Time Expected for Full Deployment

| Step | Time | Status |
|------|------|--------|
| Create release | 0s | Instant |
| GitHub Actions build | 10-15 min | Auto |
| Push to GHCR | 1-2 min | Auto |
| ArgoCD sync | <3 min | Auto |
| Pod startup | 2-5 min | Auto |
| Service ready | 20-25 min total | ✅ Done |

## 🎯 Best Practices

✅ **Use semantic versioning** for releases (v1.2.3)

✅ **Write meaningful** release notes

✅ **Never manually** edit deployed resources (ArgoCD will correct them)

✅ **Keep secrets** in private repository only

✅ **Monitor deployments** with: `kubectl get pods -n devmind-pipeline -w`

✅ **Test locally** before releasing: `docker build -t test .`

✅ **Review changes** before creating releases

✅ **Backup values** before making production changes

## 🆘 When Something Goes Wrong

```bash
# Check everything
kubectl get all -n devmind-pipeline
kubectl describe application devmind-pipeline -n argocd
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller

# See recent events
kubectl get events -n devmind-pipeline --sort-by='.lastTimestamp'

# Check pod details
kubectl describe pod -n devmind-pipeline <pod-name>

# Force sync
kubectl patch application devmind-pipeline -n argocd \
  --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/compare-result":""}}}'

# Restart deployment
kubectl rollout restart deployment/devmind-pipeline -n devmind-pipeline
```

## 📞 Need Help?

1. Check the **DEPLOYMENT-COMPLETE.md** for comprehensive guides
2. Review **PRODUCTION-DEPLOYMENT-GUIDE.md** for detailed steps
3. See **CLAUDE.md** for architecture details
4. Check pod logs: `kubectl logs -n devmind-pipeline <pod-name>`
5. View application status: `kubectl describe application devmind-pipeline -n argocd`

## 🎉 You're Ready!

Your deployment pipeline is set up. To start:

```bash
cd /path/to/devmind-pipeline
gh release create v1.3.0 --title "First release"
# Everything else happens automatically! 🚀
```

---

**Happy Deploying!** 🎯

🤖 Generated with [Claude Code](https://claude.com/claude-code)
