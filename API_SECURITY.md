# DevMind Pipeline API Security - API Key Authentication

## Overview

The DevMind Pipeline API is now protected with API key authentication. All API endpoints (except health checks and metrics) require a valid X-API-Key header.

## Security Architecture

### Public Endpoints (No Authentication Required)
These endpoints remain public for internal monitoring:
- `GET /` - Service info
- `GET /internal-health` - Internal health status (for Kubernetes probes)
- `GET /metrics` - Prometheus metrics

### Protected Endpoints (API Key Required)
All endpoints requiring authentication must include the `X-API-Key` header:
- `GET /health` - Health status (external dashboards)
- `POST /api/v1/test-intelligence/select` - Test selection
- `POST /api/v1/failure-predictor/predict` - Failure prediction
- `POST /api/v1/build-optimizer/*` - Build optimization
- `GET /models/status` - Model status
- `POST /models/retrain/{model_name}` - Model retraining

## API Key

**Secure API Key:** `WZhzpA-JLYAv3IMfQF9HSeb49iLipgGWRnHDWdJKgmw`

### Storage Locations

1. **Kubernetes Secret** (Production)
   ```bash
   kubectl get secret devmind-ml-secrets -n devmind-pipeline
   kubectl get secret devmind-ml-secrets -n devmind-pipeline -o jsonpath='{.data.DEVMIND_API_KEY}' | base64 -d
   ```

2. **GitHub Actions Secrets**
   - `devmind-pipeline` repository: `DEVMIND_API_KEY`
   - `sentinel-mesh` repository: `DEVMIND_API_KEY`
   - `cloudops-central` repository: `DEVMIND_API_KEY`

3. **Environment Variables**
   - Kubernetes: `DEVMIND_API_KEY` env var from secret
   - GitHub Actions: `${{ secrets.DEVMIND_API_KEY }}`

## Usage Examples

### Without API Key (Public Endpoints)
```bash
# Internal health check (for K8s)
curl https://devmind.georg-nikola.com/internal-health

# Service info and metrics
curl https://devmind.georg-nikola.com/
curl https://devmind.georg-nikola.com/metrics
```

### With API Key (Protected Endpoints)
```bash
# Health status (external dashboards)
curl -H "X-API-Key: WZhzpA-JLYAv3IMfQF9HSeb49iLipgGWRnHDWdJKgmw" \
  https://devmind.georg-nikola.com/health

# Test selection
curl -X POST https://devmind.georg-nikola.com/api/v1/test-intelligence/select \
  -H "X-API-Key: WZhzpA-JLYAv3IMfQF9HSeb49iLipgGWRnHDWdJKgmw" \
  -H "Content-Type: application/json" \
  -d '{
    "changed_files": ["src/main.py"],
    "all_tests": ["test_main.py", "test_config.py"],
    "project_name": "devmind-pipeline",
    "commit_hash": "abc123"
  }'
```

### GitHub Actions Usage
The workflows automatically include the API key from secrets:
```yaml
env:
  DEVMIND_API_KEY: ${{ secrets.DEVMIND_API_KEY }}

steps:
  - name: Call DevMind API
    run: |
      curl -X POST "$DEVMIND_API/api/v1/test-intelligence/select" \
        -H "X-API-Key: $DEVMIND_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$PAYLOAD"
```

## Implementation Details

### Authentication Flow

1. **Request** arrives at DevMind API with or without `X-API-Key` header
2. **Middleware** (in `main.py`) checks if endpoint requires authentication
3. **Public endpoints** (`/health`, `/metrics`, `/`) bypass auth
4. **Protected endpoints** (`/api/*`, `/models/*`) validate the API key:
   - If header missing → HTTP 401 (Unauthorized)
   - If key invalid → HTTP 403 (Forbidden)
5. **Valid requests** proceed to the endpoint handler

### Code Changes

#### New Files
- `src/core/auth.py` - APIKeyAuth class for API key validation

#### Modified Files
- `src/core/config.py` - Added `API_KEY` setting from `DEVMIND_API_KEY` env var
- `src/main.py` - Added authentication middleware
- `k8s/base/deployment.yaml` - Added `DEVMIND_API_KEY` secret reference
- `.github/workflows/devmind-integration.yml` - Updated in all 3 repos to use API key

## Key Rotation

To rotate the API key:

1. **Generate new key:**
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Update Kubernetes secret:**
   ```bash
   kubectl patch secret devmind-ml-secrets -n devmind-pipeline \
     -p '{"data":{"DEVMIND_API_KEY":"'"$(echo -n '<NEW_KEY>' | base64)"'"}}'
   ```

3. **Restart deployment:**
   ```bash
   kubectl rollout restart deployment/devmind-pipeline -n devmind-pipeline
   ```

4. **Update GitHub Actions secrets:**
   ```bash
   gh secret set DEVMIND_API_KEY -b '<NEW_KEY>' -R devmind-pipeline
   gh secret set DEVMIND_API_KEY -b '<NEW_KEY>' -R sentinel-mesh
   gh secret set DEVMIND_API_KEY -b '<NEW_KEY>' -R cloudops-central
   ```

5. **Update environment variables** anywhere else the key is used

## Testing

### Test Health Endpoint Authentication
```bash
# Without API key (should fail)
curl -i https://devmind.georg-nikola.com/health

# Expected: HTTP 401 Unauthorized
# Response: {"detail":"Missing X-API-Key header"}

# With API key (should succeed)
curl -H "X-API-Key: WZhzpA-JLYAv3IMfQF9HSeb49iLipgGWRnHDWdJKgmw" \
  https://devmind.georg-nikola.com/health

# Expected: HTTP 200 OK
# Response: {"healthy":true,"models_loaded":3,...}
```

### Test API Endpoint Without Authentication (Should Fail)
```bash
curl -X POST https://devmind.georg-nikola.com/api/v1/test-intelligence/select \
  -H "Content-Type: application/json" \
  -d '{"changed_files":["test.py"],"all_tests":["test1"]}'

# Expected: HTTP 401 Unauthorized
# Response: {"detail":"Missing X-API-Key header"}
```

### Test With Invalid Key (Should Fail)
```bash
curl -X POST https://devmind.georg-nikola.com/api/v1/test-intelligence/select \
  -H "X-API-Key: invalid-key" \
  -H "Content-Type: application/json" \
  -d '{"changed_files":["test.py"],"all_tests":["test1"]}'

# Expected: HTTP 403 Forbidden
# Response: {"detail":"Invalid API key"}
```

### Test API Endpoint With Valid Key (Should Proceed)
```bash
curl -X POST https://devmind.georg-nikola.com/api/v1/test-intelligence/select \
  -H "X-API-Key: WZhzpA-JLYAv3IMfQF9HSeb49iLipgGWRnHDWdJKgmw" \
  -H "Content-Type: application/json" \
  -d '{
    "changed_files": ["src/main.py"],
    "all_tests": ["test_main.py"],
    "project_name": "test",
    "commit_hash": "abc123"
  }'

# Expected: HTTP 200 or 422 (validation error, but auth passed)
```

### Test Internal Health Endpoint (Kubernetes)
```bash
# Internal health endpoint is public (no API key needed)
curl https://devmind.georg-nikola.com/internal-health

# Expected: HTTP 200 OK
# Response: {"healthy":true,"models_loaded":3,...}
```

## Security Best Practices

1. **Never commit the API key** to version control
2. **Use GitHub Actions Secrets** for CI/CD pipelines
3. **Use Kubernetes Secrets** for containerized deployments
4. **Rotate keys regularly** (e.g., monthly)
5. **Monitor authentication failures** in logs
6. **Use HTTPS only** for all API communications
7. **Consider rate limiting** on the API key

## Troubleshooting

### Authentication Not Working
1. Verify the Kubernetes secret exists:
   ```bash
   kubectl get secret devmind-ml-secrets -n devmind-pipeline
   ```

2. Check the environment variable is set:
   ```bash
   kubectl exec -it -n devmind-pipeline deployment/devmind-pipeline -- env | grep DEVMIND_API_KEY
   ```

3. Verify the API key value:
   ```bash
   kubectl get secret devmind-ml-secrets -n devmind-pipeline -o jsonpath='{.data.DEVMIND_API_KEY}' | base64 -d
   ```

4. Check pod logs:
   ```bash
   kubectl logs -n devmind-pipeline -l app=devmind-pipeline -f
   ```

### GitHub Actions Secret Not Found
1. Verify secret is set:
   ```bash
   gh secret list -R devmind-pipeline | grep DEVMIND_API_KEY
   ```

2. Verify workflow is using correct reference:
   ```yaml
   DEVMIND_API_KEY: ${{ secrets.DEVMIND_API_KEY }}
   ```

3. Re-set the secret if needed:
   ```bash
   gh secret set DEVMIND_API_KEY -b '<KEY>' -R <REPO>
   ```

## Next Steps

1. **Rebuild Docker image** with authentication code:
   ```bash
   cd devmind-pipeline
   docker build -t devmind-ml-service:latest .
   docker tag devmind-ml-service:latest ghcr.io/<username>/devmind-ml-service:latest
   docker push ghcr.io/<username>/devmind-ml-service:latest
   ```

2. **Wait for ArgoCD to sync** the new image, or manually trigger:
   ```bash
   argocd app sync devmind-pipeline
   ```

3. **Verify authentication works** with test curl commands above

4. **Monitor CI/CD workflows** to ensure they work with the API key

## References

- **Authentication Code**: `src/core/auth.py`
- **Configuration**: `src/core/config.py:33-35`
- **Middleware**: `src/main.py:83-107`
- **Kubernetes Deployment**: `k8s/base/deployment.yaml:123-127`
- **GitHub Workflows**: `.github/workflows/devmind-integration.yml`
