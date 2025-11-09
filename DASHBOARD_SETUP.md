# Cloudflare Dashboard Configuration for DevMind Health Monitoring

## Overview

The DevMind Pipeline `/health` endpoint is now protected with API key authentication. External dashboards (including Cloudflare) can access it by providing the API key in the `X-API-Key` header.

## Health Endpoint URLs

### Internal Health (Kubernetes - No Auth Required)
```
http://devmind-pipeline.devmind-pipeline.svc.cluster.local:8000/internal-health
```

### External Health (Cloudflare Dashboards - API Key Required)
```
https://devmind.georg-nikola.com/health
```

## API Key

**API Key:** `WZhzpA-JLYAv3IMfQF9HSeb49iLipgGWRnHDWdJKgmw`

⚠️ **IMPORTANT**: Keep this API key secure and never commit it to version control.

## Cloudflare Dashboard Setup

### Option 1: Using Custom Metrics with API Key

If your Cloudflare dashboard tool supports custom HTTP headers:

```
URL: https://devmind.georg-nikola.com/health
Method: GET
Headers:
  X-API-Key: WZhzpA-JLYAv3IMfQF9HSeb49iLipgGWRnHDWdJKgmw
```

### Option 2: Using curl for Monitoring Scripts

```bash
#!/bin/bash

API_KEY="WZhzpA-JLYAv3IMfQF9HSeb49iLipgGWRnHDWdJKgmw"
ENDPOINT="https://devmind.georg-nikola.com/health"

# Get health status
RESPONSE=$(curl -s -H "X-API-Key: $API_KEY" "$ENDPOINT")

# Parse response
echo "Health Status: $RESPONSE"

# Extract health value
HEALTHY=$(echo "$RESPONSE" | jq -r '.healthy')

if [ "$HEALTHY" = "true" ]; then
  echo "✅ DevMind API is healthy"
  exit 0
else
  echo "❌ DevMind API is unhealthy"
  exit 1
fi
```

### Option 3: Using Prometheus Scrape (No Auth Required)

For Prometheus, use the public metrics endpoint (no API key needed):

```yaml
scrape_configs:
  - job_name: 'devmind-api'
    scheme: https
    static_configs:
      - targets: ['devmind.georg-nikola.com:443']
    metrics_path: '/metrics'
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: devmind.georg-nikola.com:443
```

## Response Format

### Success Response (HTTP 200)
```json
{
  "healthy": true,
  "models_loaded": 3,
  "models": [
    "build_optimizer",
    "failure_predictor",
    "test_selector"
  ]
}
```

### Unauthorized Response (HTTP 401)
```json
{
  "detail": "Missing X-API-Key header"
}
```

### Forbidden Response (HTTP 403)
```json
{
  "detail": "Invalid API key"
}
```

### Service Unavailable Response (HTTP 503)
```json
{
  "detail": "ML services not initialized"
}
```

## Testing

### Test with curl
```bash
# Without API key (should fail)
curl -i https://devmind.georg-nikola.com/health

# With API key (should succeed)
curl -H "X-API-Key: WZhzpA-JLYAv3IMfQF9HSeb49iLipgGWRnHDWdJKgmw" \
  https://devmind.georg-nikola.com/health
```

### Test with Python
```python
import requests

API_KEY = "WZhzpA-JLYAv3IMfQF9HSeb49iLipgGWRnHDWdJKgmw"
ENDPOINT = "https://devmind.georg-nikola.com/health"

headers = {"X-API-Key": API_KEY}
response = requests.get(ENDPOINT, headers=headers)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

### Test with JavaScript/Node.js
```javascript
const apiKey = "WZhzpA-JLYAv3IMfQF9HSeb49iLipgGWRnHDWdJKgmw";
const endpoint = "https://devmind.georg-nikola.com/health";

fetch(endpoint, {
  method: 'GET',
  headers: {
    'X-API-Key': apiKey
  }
})
  .then(response => response.json())
  .then(data => {
    console.log('Health Status:', data);
    if (data.healthy) {
      console.log('✅ DevMind API is healthy');
    } else {
      console.log('❌ DevMind API is unhealthy');
    }
  })
  .catch(error => console.error('Error:', error));
```

## Cloudflare Workers Example

If you use Cloudflare Workers to check health status:

```javascript
async function handleRequest(request) {
  const apiKey = "WZhzpA-JLYAv3IMfQF9HSeb49iLipgGWRnHDWdJKgmw";
  const endpoint = "https://devmind.georg-nikola.com/health";

  try {
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: {
        'X-API-Key': apiKey,
        'User-Agent': 'CloudflareWorker/1.0'
      }
    });

    const data = await response.json();

    return new Response(JSON.stringify({
      timestamp: new Date().toISOString(),
      devmind_status: data.healthy ? 'healthy' : 'unhealthy',
      models_loaded: data.models_loaded,
      models: data.models
    }), {
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'max-age=30'  // Cache for 30 seconds
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({
      timestamp: new Date().toISOString(),
      error: error.message
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});
```

## Monitoring Dashboard Integration

### Grafana

Add a new data source in Grafana:

1. **Type**: HTTP API
2. **URL**: `https://devmind.georg-nikola.com/health`
3. **Custom HTTP Headers**: Add header `X-API-Key: WZhzpA-JLYAv3IMfQF9HSeb49iLipgGWRnHDWdJKgmw`
4. **Access**: Server (proxy)

Then create a dashboard panel with query:
```
GET /health
Parse JSON response
Display $.healthy as boolean status
```

### Datadog

Add a custom API check in Datadog:

```yaml
init_config:
  - instances:
    - name: devmind_health
      url: https://devmind.georg-nikola.com/health
      method: GET
      headers:
        X-API-Key: WZhzpA-JLYAv3IMfQF9HSeb49iLipgGWRnHDWdJKgmw
      tags:
        - service:devmind
        - env:production
```

### CloudWatch (AWS)

If using AWS for monitoring:

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name devmind-health-check \
  --alarm-description "DevMind API Health Status" \
  --metric-name HealthCheckStatus \
  --namespace Custom/DevMind \
  --statistic Average \
  --period 300 \
  --threshold 1 \
  --comparison-operator LessThanThreshold
```

## Security Considerations

1. **API Key Management**
   - Store API key in secure secret management system (e.g., Cloudflare Vault)
   - Never hardcode in client-side code
   - Rotate key regularly (monthly recommended)
   - Log access attempts

2. **HTTPS Only**
   - Always use HTTPS when accessing the health endpoint
   - Cloudflare provides automatic HTTPS

3. **Rate Limiting**
   - Consider implementing rate limits on monitoring requests
   - Suggest checking health every 30-60 seconds

4. **Network Security**
   - Endpoint is publicly accessible via Cloudflare
   - Authorized through API key only
   - No IP whitelisting needed (Cloudflare provides DDoS protection)

## Troubleshooting

### 401 Unauthorized
- Verify API key is correct
- Check header name is exactly `X-API-Key` (case-sensitive)
- Ensure header is being sent with the request

### 403 Forbidden
- API key is invalid or expired
- Regenerate the API key if rotated

### 503 Service Unavailable
- ML services not initialized
- Check pod logs: `kubectl logs -n devmind-pipeline -l app=devmind-pipeline -f`
- Verify deployment is running: `kubectl get pods -n devmind-pipeline`

### Connection Timeout
- Check DNS resolution: `nslookup devmind.georg-nikola.com`
- Verify Cloudflare tunnel is active: `cloudflared tunnel list`
- Check network connectivity to devmind.georg-nikola.com

## API Key Rotation

To rotate the API key:

1. Generate new key:
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. Update Kubernetes secret:
   ```bash
   kubectl patch secret devmind-ml-secrets -n devmind-pipeline \
     -p '{"data":{"DEVMIND_API_KEY":"'"$(echo -n '<NEW_KEY>' | base64)"'"}}'
   ```

3. Restart deployment:
   ```bash
   kubectl rollout restart deployment/devmind-pipeline -n devmind-pipeline
   ```

4. Update all dashboards to use new API key

5. Verify new key works before removing old one

## Dashboard Checklist

- [ ] API endpoint configured: `https://devmind.georg-nikola.com/health`
- [ ] API key added to dashboard: `WZhzpA-JLYAv3IMfQF9HSeb49iLipgGWRnHDWdJKgmw`
- [ ] Custom header `X-API-Key` configured
- [ ] Test connection successful (HTTP 200)
- [ ] Health status showing "healthy: true"
- [ ] Models loaded count showing 3
- [ ] Monitoring alerts configured
- [ ] Documentation updated for your team
