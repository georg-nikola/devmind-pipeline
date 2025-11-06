# DevMind Pipeline Helm Chart

This Helm chart deploys the DevMind Pipeline ML Services to Kubernetes.

## Installation

### Using Helm directly

```bash
helm install devmind-pipeline ./helm/devmind-pipeline \
  --namespace devmind-pipeline \
  --create-namespace \
  --values my-values.yaml
```

### Using ArgoCD with private values overlay

The recommended approach is to use ArgoCD with a private values repository:

1. **Public repo** (this repo): Contains the Helm chart with default/generic values
2. **Private repo**: Contains environment-specific values files

ArgoCD Application example:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: devmind-pipeline
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/YOUR_ORG/devmind-pipeline
    targetRevision: main
    path: helm/devmind-pipeline
    helm:
      valueFiles:
        - values.yaml
      # Values from private repo (mounted via volume or ConfigMap)
      values: |
        # Production overrides here
  destination:
    server: https://kubernetes.default.svc
    namespace: devmind-pipeline
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

## Configuration

See `values.yaml` for all configuration options.

### Key Configuration Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| `image.registry` | Container registry | `ghcr.io` |
| `image.repository` | Image repository | `YOUR_GITHUB_USERNAME/devmind-ml-service` |
| `image.tag` | Image tag | `latest` |
| `replicaCount` | Number of replicas | `1` |
| `resources.requests.memory` | Memory request | `512Mi` |
| `resources.limits.memory` | Memory limit | `2Gi` |
| `ingressRoute.enabled` | Enable Traefik IngressRoute | `false` |

### Example Production Values

```yaml
image:
  repository: myorg/devmind-ml-service
  tag: "v1.2.3"

replicaCount: 3

environment: production

config:
  logLevel: "warning"
  workers: "4"
  enableDistributedTracing: "true"

resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 2000m
    memory: 4Gi

ingressRoute:
  enabled: true
  routes:
    - match: Host(`ml-api.mycompany.com`)
      kind: Rule

secrets:
  databaseUrl: "postgresql://..."
  redisUrl: "redis://..."
```

## Upgrading

```bash
helm upgrade devmind-pipeline ./helm/devmind-pipeline \
  --namespace devmind-pipeline \
  --values my-values.yaml
```

## Uninstalling

```bash
helm uninstall devmind-pipeline --namespace devmind-pipeline
```
