"""
Monitoring and metrics configuration for DevMind Pipeline.
Provides Prometheus metrics for ML services and pipeline execution.
"""

from prometheus_client import Counter, Histogram, Gauge, Info
import structlog

logger = structlog.get_logger(__name__)

# ML Model Metrics
model_prediction_total = Counter(
    'devmind_model_predictions_total',
    'Total ML model predictions',
    ['model_name', 'status']
)

model_prediction_duration = Histogram(
    'devmind_model_prediction_duration_seconds',
    'ML model prediction duration',
    ['model_name']
)

model_accuracy = Gauge(
    'devmind_model_accuracy',
    'Current model accuracy',
    ['model_name']
)

model_training_duration = Histogram(
    'devmind_model_training_duration_seconds',
    'Model training duration',
    ['model_name']
)

# Pipeline Metrics
pipeline_executions_total = Counter(
    'devmind_pipeline_executions_total',
    'Total pipeline executions',
    ['pipeline_name', 'status']
)

pipeline_duration = Histogram(
    'devmind_pipeline_duration_seconds',
    'Pipeline execution duration',
    ['pipeline_name']
)

build_optimization_savings = Gauge(
    'devmind_build_optimization_savings_seconds',
    'Time saved through build optimization',
    ['project']
)

test_selection_reduction = Gauge(
    'devmind_test_selection_reduction_percent',
    'Percentage reduction in test execution time',
    ['project']
)

failure_predictions_total = Counter(
    'devmind_failure_predictions_total',
    'Total failure predictions made',
    ['prediction', 'actual']
)

# Application Info
app_info = Info('devmind_pipeline', 'DevMind Pipeline application info')


def setup_monitoring() -> None:
    """Initialize monitoring and set application info."""
    logger.info("Setting up monitoring and metrics")

    app_info.info({
        'version': '1.0.0',
        'environment': 'production',
        'service': 'devmind-pipeline'
    })

    logger.info("Monitoring setup complete")


def record_prediction(model_name: str, duration: float, status: str = "success") -> None:
    """Record ML model prediction metrics."""
    model_prediction_total.labels(model_name=model_name, status=status).inc()
    model_prediction_duration.labels(model_name=model_name).observe(duration)


def update_model_accuracy(model_name: str, accuracy: float) -> None:
    """Update model accuracy metric."""
    model_accuracy.labels(model_name=model_name).set(accuracy)


def record_pipeline_execution(pipeline_name: str, duration: float, status: str) -> None:
    """Record pipeline execution metrics."""
    pipeline_executions_total.labels(pipeline_name=pipeline_name, status=status).inc()
    pipeline_duration.labels(pipeline_name=pipeline_name).observe(duration)
