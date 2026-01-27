# DevMind Pipeline - Quick Start Guide

## 🚀 The Service is Running!

DevMind Pipeline AI-Enhanced DevOps platform is running at:
**http://localhost:8001**

## 🎮 Interactive Demo

Run the interactive demo script:
```bash docs-drift:skip
cd ~/.repos/devmind-pipeline
./demo.sh
```

## 🌐 Web Interfaces

Open these in your browser:
- **Swagger UI (Interactive API)**: http://localhost:8001/docs
- **ReDoc (Documentation)**: http://localhost:8001/redoc
- **Health Check**: http://localhost:8001/health
- **Metrics**: http://localhost:8001/metrics

## 📋 Quick Examples

### 1. Check Service Health
```bash docs-drift:skip
curl http://localhost:8001/health | python3 -m json.tool
```

### 2. Optimize Build Performance
```bash docs-drift:skip
curl -X POST http://localhost:8001/api/v1/build-optimizer/optimize \
  -H 'Content-Type: application/json' \
  -d '{
    "project_name": "my-project",
    "historical_build_times": [120, 150, 130, 145],
    "resource_constraints": {"cpu": 4, "memory": "8GB"}
  }' | python3 -m json.tool
```

### 3. Predict Pipeline Failure
```bash docs-drift:skip
curl -X POST http://localhost:8001/api/v1/failure-predictor/predict \
  -H 'Content-Type: application/json' \
  -d '{
    "pipeline_id": "my-pipeline",
    "commit_hash": "abc123",
    "code_changes": {"files_changed": 15, "lines_added": 300}
  }' | python3 -m json.tool
```

### 4. Smart Test Selection
```bash docs-drift:skip
curl -X POST http://localhost:8001/api/v1/test-intelligence/select \
  -H 'Content-Type: application/json' \
  -d '{
    "project_name": "my-app",
    "commit_hash": "xyz789",
    "changed_files": ["src/auth.py", "src/api.py"]
  }' | python3 -m json.tool
```

### 5. Get Cache Strategy
```bash docs-drift:skip
curl http://localhost:8001/api/v1/build-optimizer/cache-strategy/my-project | python3 -m json.tool
```

### 6. Detect Flaky Tests
```bash docs-drift:skip
curl 'http://localhost:8001/api/v1/test-intelligence/flaky-tests/my-app?days=30' | python3 -m json.tool
```

## 🔍 All Available Endpoints

### Build Optimizer
- `POST /api/v1/build-optimizer/optimize` - Get build optimization recommendations
- `GET /api/v1/build-optimizer/cache-strategy/{project}` - Get caching strategy
- `GET /api/v1/build-optimizer/statistics/{project}` - Get build statistics

### Failure Predictor
- `POST /api/v1/failure-predictor/predict` - Predict pipeline failure probability
- `GET /api/v1/failure-predictor/anomalies/{pipeline_id}` - Detect anomalies
- `GET /api/v1/failure-predictor/failure-patterns` - Get common failure patterns

### Test Intelligence
- `POST /api/v1/test-intelligence/select` - Smart test selection
- `GET /api/v1/test-intelligence/flaky-tests/{project}` - Detect flaky tests
- `GET /api/v1/test-intelligence/coverage-analysis/{project}` - Analyze test coverage
- `POST /api/v1/test-intelligence/optimize-suite` - Optimize test suite

### System
- `GET /` - Service information
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /models/status` - ML model status
- `POST /models/retrain/{model_name}` - Trigger model retraining

## 🛠️ Management

### View Logs
```bash docs-drift:skip
tail -f /tmp/devmind-pipeline.log
```

### Check Server Status
```bash docs-drift:skip
lsof -i:8001
```

### Stop Server
```bash docs-drift:skip
lsof -ti:8001 | xargs kill
```

### Restart Server
```bash docs-drift:skip
cd ~/.repos/devmind-pipeline/src
source venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## 💡 Features

- ✅ **3 ML Models** loaded and ready
- ✅ **Build Optimization** - AI-powered build time reduction
- ✅ **Failure Prediction** - Predict pipeline failures before they happen
- ✅ **Test Intelligence** - Smart test selection saves 60% execution time
- ✅ **Anomaly Detection** - Identify unusual patterns
- ✅ **Flaky Test Detection** - Find unreliable tests
- ✅ **Prometheus Metrics** - Full observability
- ✅ **Structured Logging** - JSON logs for easy parsing

## 🎯 Try It Out!

1. Open http://localhost:8001/docs in your browser
2. Click on any endpoint to expand it
3. Click "Try it out"
4. Fill in the example data
5. Click "Execute"
6. See the AI-powered response!

Enjoy exploring DevMind Pipeline! 🚀
