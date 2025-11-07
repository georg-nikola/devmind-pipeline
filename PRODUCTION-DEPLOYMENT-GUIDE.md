# DevMind Pipeline - Production Deployment Guide

## Overview

This guide covers the complete production deployment of DevMind Pipeline using Helm charts and ArgoCD GitOps on a Talos Kubernetes cluster.

## Architecture

```
PUBLIC REPOSITORY                        PRIVATE REPOSITORY
─────────────────────────────────────    ──────────────────────────────
github/devmind-pipeline                  github/talos-configs (PRIVATE)
├── Dockerfile                           ├── manifests/argocd/
├── helm/devmind-pipeline/               │   ├── application-devmind.yaml
│   ├── Chart.yaml                       │   └── values/
│   ├── values.yaml (generic)            │       └── devmind-pipeline-production.yaml
│   └── templates/                       └── local-cluster-config/
│       ├── deployment.yaml
│       ├── service.yaml                 GitHub Actions CI/CD
│       ├── configmap.yaml               ─────────────────────
│       └── ...                          On Release Published:
├── .github/                             1. Build Docker image
│   └── workflows/release.yml            2. Push to GHCR
└── src/                                 3. ArgoCD auto-syncs

                                         Production Cluster
                                         ──────────────────
                                         ArgoCD (auto-sync)
                                         ├── watches public repo (Helm chart)
                                         ├── watches private repo (values)
                                         └── deploys to Talos K8s
```

## Step-by-Step Deployment

### 1. Prerequisites

- Talos Kubernetes cluster running
- kubectl configured to access the cluster
- ArgoCD installed on cluster (see talos-configs repo)
- GitHub repository (fork of devmind-pipeline)

### 2. Private Infrastructure Repository Setup

The `talos-configs` repository contains:
- ArgoCD installation manifests
- Production values overlays
- Cloudflare integration configuration

**Location**: `~/repos/talos-configs/local-cluster-config/manifests/argocd/`

Files:
- `application-devmind.yaml` - ArgoCD Application with Helm values
- `values/devmind-pipeline-production.yaml` - Production-specific overrides

### 3. Public Repository Setup

The public `devmind-pipeline` repository contains:
- Helm chart with generic values
- GitHub Actions workflows
- Application source code

**Chart location**: `helm/devmind-pipeline/`

### 4. Automated Docker Builds

Triggering a release automatically builds and pushes the Docker image:

```bash
cd ~/repos/devmind-pipeline

# Create and push a new release
gh release create v1.1.0 --title "Release v1.1.0" \
  --notes "Production-ready release with Helm chart"
```

This triggers:
1. GitHub Actions `release.yml` workflow
2. Docker build in GitHub-hosted runner
3. Image push to GHCR:
   - `ghcr.io/YOUR_USERNAME/devmind-ml-service:v1.1.0`
   - `ghcr.io/YOUR_USERNAME/devmind-ml-service:v1.1`
   - `ghcr.io/YOUR_USERNAME/devmind-ml-service:v1`
   - `ghcr.io/YOUR_USERNAME/devmind-ml-service:latest`

### 5. ArgoCD Deployment

Once the Docker image is built and pushed:

1. **ArgoCD detects the new tag** (within 3 minutes or manually)
2. **Templates the Helm chart** with production values from `talos-configs`
3. **Applies the resulting manifests** to the cluster

Monitor deployment:

```bash
# Watch ArgoCD sync status
kubectl get application devmind-pipeline -n argocd -w

# View application details
argocd app get devmind-pipeline
kubectl describe application devmind-pipeline -n argocd

# Check deployed pods
kubectl get pods -n devmind-pipeline
kubectl logs -n devmind-pipeline -l app=devmind-ml-service -f

# Check rollout status
kubectl rollout status deployment/devmind-pipeline -n devmind-pipeline
```

### 6. Accessing the Service

After successful deployment:

**API Endpoint**: `https://devmind.example.com` (via Cloudflare Tunnel)
- Protected by Cloudflare Zero Trust Access
- Swagger UI: `https://devmind.example.com/docs`
- Health check: `https://devmind.example.com/health`

**Local Port-Forward** (if needed):
```bash
kubectl port-forward -n devmind-pipeline svc/devmind-pipeline 8000:8000
# Access at http://localhost:8000
```

## Configuration Management

### Production Values Override

Located in: `talos-configs/local-cluster-config/manifests/argocd/values/devmind-pipeline-production.yaml`

Key overrides:
- **Image**: `ghcr.io/YOUR_USERNAME/devmind-ml-service:latest`
- **Replicas**: 2 (high availability)
- **Resources**:
  - Requests: 500m CPU, 512Mi memory
  - Limits: 2000m CPU, 2Gi memory
- **IngressRoute**: Production domain configuration
- **Secrets**: Database URL, API keys, etc. (CHANGE BEFORE DEPLOYING)

### Making Configuration Changes

To update production configuration:

```bash
# Edit values in the private repository
vim ~/repos/talos-configs/local-cluster-config/manifests/argocd/values/devmind-pipeline-production.yaml

# Or edit the ArgoCD Application directly
vim ~/repos/talos-configs/local-cluster-config/manifests/argocd/application-devmind.yaml

# Apply the changes
kubectl apply -f ~/repos/talos-configs/local-cluster-config/manifests/argocd/application-devmind.yaml

# ArgoCD will re-sync with new values
kubectl get application devmind-pipeline -n argocd -w
```

### Making Application Code Changes

To update the application:

```bash
cd ~/repos/devmind-pipeline

# 1. Make code changes
# ... edit files ...

# 2. Create and release new version
gh release create v1.1.1 --title "v1.1.1 Release"

# GitHub Actions automatically:
# - Builds Docker image
# - Pushes to GHCR with version tags
# - ArgoCD detects new tags and syncs
```

## Monitoring & Troubleshooting

### Check Deployment Status

```bash
# View all resources in the namespace
kubectl get all -n devmind-pipeline

# Check pod status
kubectl get pods -n devmind-pipeline -o wide

# Describe pods for errors
kubectl describe pod -n devmind-pipeline <pod-name>

# View logs
kubectl logs -n devmind-pipeline -l app=devmind-ml-service -f
kubectl logs -n devmind-pipeline -l app=devmind-ml-service --previous  # previous crash
```

### Check ArgoCD Status

```bash
# View application sync status
argocd app get devmind-pipeline
kubectl get application devmind-pipeline -n argocd

# View application events
kubectl get events -n devmind-pipeline --sort-by='.lastTimestamp'

# Check ArgoCD logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller -f
```

### Common Issues

**ImagePullBackOff**:
- Check if Docker image was pushed to GHCR
- Verify image tag matches in application manifest
- Check GHCR credentials if needed

**CrashLoopBackOff**:
- Check pod logs: `kubectl logs -n devmind-pipeline <pod-name>`
- Check resource limits are sufficient
- Verify ConfigMaps and Secrets exist

**OutOfSync in ArgoCD**:
- Check GitHub repository is accessible
- Verify manifests are valid YAML
- Check ArgoCD permissions and credentials

## Rollback

If needed, rollback to a previous version:

```bash
# View version history
argocd app history devmind-pipeline
kubectl rollout history deployment/devmind-pipeline -n devmind-pipeline

# Rollback using ArgoCD
argocd app rollback devmind-pipeline <revision>

# Or using kubectl
kubectl rollout undo deployment/devmind-pipeline -n devmind-pipeline
```

## Security Considerations

1. **Secrets Management**
   - Keep secrets in private `talos-configs` repo
   - Use Kubernetes Secrets for sensitive values
   - Never commit plaintext secrets to public repos

2. **Image Registry**
   - GHCR images are private by default
   - Ensure proper GitHub credentials for pulling images
   - Use specific version tags in production (not `latest`)

3. **Network Security**
   - All traffic through Cloudflare Tunnel
   - Protected by Cloudflare Zero Trust Access
   - TLS/SSL encryption end-to-end

4. **RBAC**
   - ArgoCD has minimal permissions on cluster
   - Service accounts with least privilege
   - Regular audits of access logs

## Maintenance

### Regular Updates

1. Update dependencies in `src/requirements.txt`
2. Update Helm chart if templates change
3. Create new release to trigger builds
4. Monitor deployment and logs

### Scaling

To scale the deployment, update production values:

```yaml
# In talos-configs/values/devmind-pipeline-production.yaml
replicaCount: 3  # Increase replicas
resources:
  limits:
    cpu: 4000m      # Increase CPU limit
    memory: 4Gi     # Increase memory limit
```

Apply changes:
```bash
kubectl apply -f application-devmind.yaml
```

### Database Backups

Configure periodic backups if using PostgreSQL:
- Add PersistentVolumeClaim to deployment
- Schedule backup jobs
- Test restore procedures regularly

## References

- [Helm Documentation](https://helm.sh/docs/)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Talos Kubernetes](https://www.talos.dev/)

## Support

For issues or questions:
1. Check application logs: `kubectl logs -n devmind-pipeline ...`
2. Check ArgoCD status: `argocd app get devmind-pipeline`
3. Review CLAUDE.md for architecture details
4. Check GitHub Actions workflows for build issues

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
