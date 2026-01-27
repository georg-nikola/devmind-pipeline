# DevMind Pipeline - Local Kubernetes Deployment

## 🎉 Deployment Status: RUNNING

All services have been successfully deployed to OrbStack Kubernetes and are now accessible.

## 📊 Available Dashboards & Services

### 🤖 ML API Service
- **URL**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Status**: ✅ Running (3 ML models loaded)

**Available Endpoints:**
- `POST /build/optimize` - AI-powered build optimization
- `POST /predict/failure` - Pipeline failure prediction
- `GET /predict/anomalies/{pipeline_id}` - Anomaly detection
- `POST /test/select` - Intelligent test selection
- `GET /test/flaky-tests/{project_name}` - Flaky test detection
- `GET /test/coverage-analysis/{project_name}` - Coverage analysis

### 📈 Grafana Dashboard
- **URL**: http://localhost:3000
- **Username**: `admin`
- **Password**: `admin`
- **Status**: ✅ Running
- **Datasource**: Prometheus (pre-configured)

### 📊 Prometheus Metrics
- **URL**: http://localhost:9090
- **Status**: ✅ Running
- **Targets**: DevMind ML Service

### 🗄️ PostgreSQL Database
- **Host**: `localhost:5432`
- **Database**: `devmind`
- **Username**: `devmind`
- **Password**: `devmind123`
- **Status**: ✅ Running

### 🔴 Redis Cache
- **Host**: `localhost:6379`
- **Status**: ✅ Running

## 🚀 Quick Start

### Start All Services
```bash docs-drift:skip
cd /path/to/devmind-pipeline
./start-dashboards.sh
```

### Test the ML API
```bash docs-drift:skip
# Health check
curl http://localhost:8000/health

# Build optimization
curl -X POST http://localhost:8000/build/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "my-project",
    "commit_hash": "abc123",
    "build_history": []
  }'

# Failure prediction
curl -X POST http://localhost:8000/predict/failure \
  -H "Content-Type: application/json" \
  -d '{
    "pipeline_id": "pipeline-123",
    "commit_hash": "abc123"
  }'

# Test selection
curl -X POST http://localhost:8000/test/select \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "my-project",
    "commit_hash": "abc123",
    "changed_files": ["src/main.py", "src/utils.py"]
  }'
```

### View Metrics in Grafana
1. Open http://localhost:3000
2. Login with `admin` / `admin`
3. Navigate to Explore → Select "Prometheus" datasource
4. Query example metrics:
   - `ml_service_requests_total`
   - `ml_service_request_duration_seconds`
   - `ml_models_loaded`

## 📦 Deployed Resources

### Kubernetes Resources
```bash docs-drift:skip
# View all resources
kubectl get all -n devmind-pipeline

# View pods
kubectl get pods -n devmind-pipeline

# View logs
kubectl logs -n devmind-pipeline -l app=devmind-ml-service -f

# Port-forward services (already running)
kubectl port-forward -n devmind-pipeline svc/devmind-ml-service 8000:8000
kubectl port-forward -n devmind-pipeline svc/grafana 3000:3000
kubectl port-forward -n devmind-pipeline svc/prometheus 9090:9090
```

### Service Architecture
```
┌─────────────────┐
│   Client/User   │
└────────┬────────┘
         │
    ┌────▼────┐
    │  Nginx  │ (Optional - not deployed)
    └────┬────┘
         │
    ┌────▼──────────┐
    │  ML Service   │ :8000
    │  (FastAPI)    │
    └───┬───┬───┬───┘
        │   │   │
        │   │   └──────┐
        │   │          │
   ┌────▼────┐  ┌──────▼────────┐  ┌─────▼──────┐
   │ Postgres│  │  Prometheus   │  │   Redis    │
   │  :5432  │  │     :9090     │  │   :6379    │
   └─────────┘  └───────┬───────┘  └────────────┘
                        │
                  ┌─────▼──────┐
                  │  Grafana   │ :3000
                  └────────────┘
```

## 🛠️ Troubleshooting

### Port-forwards not working
```bash docs-drift:skip
# Kill all port-forwards and restart
pkill -f "kubectl port-forward"
./start-dashboards.sh
```

### Check pod status
```bash docs-drift:skip
kubectl get pods -n devmind-pipeline
kubectl describe pod -n devmind-pipeline <pod-name>
kubectl logs -n devmind-pipeline <pod-name>
```

### Rebuild ML Service
```bash docs-drift:skip
kubectl delete pod -n devmind-pipeline -l app=devmind-ml-service
# Wait for new pod to start
kubectl get pods -n devmind-pipeline -w
```

## 📝 Notes

- ML service takes ~3-5 minutes to start (installing dependencies)
- Grafana dashboards need to be created manually (datasource is pre-configured)
- PostgreSQL data is stored in emptyDir (will be lost on pod restart)
- Redis data is ephemeral (stored in memory only)

## 🔗 Related Files

- `k8s/` - Kubernetes manifests
- `start-dashboards.sh` - Port-forward script
- `QUICKSTART.md` - API usage guide
- `demo.sh` - Interactive API demo
