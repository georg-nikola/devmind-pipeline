"""
Core configuration management for DevMind Pipeline ML Services
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    APP_NAME: str = "DevMind Pipeline ML Services"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Server
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    WORKERS: int = Field(default=4, env="WORKERS")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")
    
    # Security
    SECRET_KEY: str = Field(default="dev-secret-key", env="SECRET_KEY")
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="ALLOWED_ORIGINS"
    )
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:password@localhost:5432/devmind_pipeline",
        env="DATABASE_URL"
    )
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    
    # ML Model Configuration
    MODEL_REGISTRY_URL: str = Field(
        default="http://localhost:5000",
        env="MLFLOW_TRACKING_URI"
    )
    MODEL_STORAGE_PATH: str = Field(
        default="./models",
        env="MODEL_STORAGE_PATH"
    )
    
    # AI/ML Settings
    BUILD_OPTIMIZER_MODEL_NAME: str = "build_optimizer"
    FAILURE_PREDICTOR_MODEL_NAME: str = "failure_predictor"
    TEST_INTELLIGENCE_MODEL_NAME: str = "test_intelligence"
    
    # Model Training
    AUTO_RETRAIN: bool = Field(default=True, env="AUTO_RETRAIN")
    RETRAIN_THRESHOLD: float = Field(default=0.05, env="RETRAIN_THRESHOLD")
    MIN_TRAINING_SAMPLES: int = Field(default=1000, env="MIN_TRAINING_SAMPLES")
    
    # Pipeline Engine Integration
    PIPELINE_ENGINE_URL: str = Field(
        default="http://pipeline-engine:8080",
        env="PIPELINE_ENGINE_URL"
    )
    PIPELINE_ENGINE_API_KEY: Optional[str] = Field(
        default=None,
        env="PIPELINE_ENGINE_API_KEY"
    )
    
    # Tekton Integration
    TEKTON_NAMESPACE: str = Field(default="tekton-pipelines", env="TEKTON_NAMESPACE")
    TEKTON_DASHBOARD_URL: str = Field(
        default="http://tekton-dashboard:9097",
        env="TEKTON_DASHBOARD_URL"
    )
    
    # ArgoCD Integration
    ARGOCD_SERVER: str = Field(
        default="argocd-server:443",
        env="ARGOCD_SERVER"
    )
    ARGOCD_TOKEN: Optional[str] = Field(default=None, env="ARGOCD_TOKEN")
    
    # Monitoring & Observability
    PROMETHEUS_URL: str = Field(
        default="http://prometheus:9090",
        env="PROMETHEUS_URL"
    )
    JAEGER_ENDPOINT: str = Field(
        default="http://jaeger:14268/api/traces",
        env="JAEGER_ENDPOINT"
    )
    
    # Feature Flags
    ENABLE_PROMETHEUS_METRICS: bool = Field(default=True, env="ENABLE_PROMETHEUS_METRICS")
    ENABLE_DISTRIBUTED_TRACING: bool = Field(default=True, env="ENABLE_DISTRIBUTED_TRACING")
    ENABLE_MODEL_EXPLANATIONS: bool = Field(default=True, env="ENABLE_MODEL_EXPLANATIONS")
    
    # Performance Settings
    MAX_CONCURRENT_PREDICTIONS: int = Field(default=100, env="MAX_CONCURRENT_PREDICTIONS")
    PREDICTION_TIMEOUT: int = Field(default=30, env="PREDICTION_TIMEOUT")
    CACHE_TTL: int = Field(default=3600, env="CACHE_TTL")  # 1 hour
    
    # Data Processing
    MAX_BATCH_SIZE: int = Field(default=1000, env="MAX_BATCH_SIZE")
    FEATURE_EXTRACTION_TIMEOUT: int = Field(default=300, env="FEATURE_EXTRACTION_TIMEOUT")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


class MLModelConfig:
    """ML Model specific configurations."""
    
    BUILD_OPTIMIZER = {
        "model_type": "xgboost",
        "hyperparameters": {
            "n_estimators": 100,
            "max_depth": 6,
            "learning_rate": 0.1,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "random_state": 42
        },
        "feature_columns": [
            "dependency_count",
            "code_change_size",
            "file_count",
            "test_count",
            "historical_build_time",
            "branch_complexity",
            "commit_frequency",
            "package_size"
        ],
        "target_column": "build_time_seconds",
        "validation_split": 0.2,
        "early_stopping_rounds": 10
    }
    
    FAILURE_PREDICTOR = {
        "model_type": "pytorch_neural_network",
        "architecture": {
            "input_size": 50,
            "hidden_layers": [128, 64, 32],
            "output_size": 1,
            "dropout": 0.2,
            "activation": "relu"
        },
        "training": {
            "batch_size": 32,
            "epochs": 100,
            "learning_rate": 0.001,
            "weight_decay": 1e-4,
            "early_stopping_patience": 10
        },
        "feature_columns": [
            "pipeline_duration_mean",
            "pipeline_duration_std",
            "failure_rate_7d",
            "code_churn",
            "test_coverage",
            "deployment_frequency",
            "error_rate",
            "response_time_p95",
            "resource_utilization"
        ],
        "target_column": "failure_probability"
    }
    
    TEST_INTELLIGENCE = {
        "model_type": "random_forest",
        "hyperparameters": {
            "n_estimators": 200,
            "max_depth": 10,
            "min_samples_split": 5,
            "min_samples_leaf": 2,
            "random_state": 42
        },
        "feature_columns": [
            "file_change_overlap",
            "test_execution_time",
            "test_failure_history",
            "code_coverage_impact",
            "dependency_impact",
            "test_age",
            "flakiness_score"
        ],
        "target_column": "should_run_test",
        "class_weight": "balanced"
    }


class KubernetesConfig:
    """Kubernetes-specific configurations."""
    
    NAMESPACE = os.getenv("POD_NAMESPACE", "devmind-pipeline")
    POD_NAME = os.getenv("POD_NAME", "ml-service")
    SERVICE_ACCOUNT = os.getenv("SERVICE_ACCOUNT", "devmind-ml-service")
    
    # Resource limits
    MEMORY_LIMIT = os.getenv("MEMORY_LIMIT", "2Gi")
    CPU_LIMIT = os.getenv("CPU_LIMIT", "1000m")
    
    # Health check settings
    READINESS_PROBE_PATH = "/health"
    LIVENESS_PROBE_PATH = "/health"
    STARTUP_PROBE_PATH = "/health"


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


def get_ml_model_config(model_name: str) -> dict:
    """Get ML model configuration by name."""
    configs = {
        "build_optimizer": MLModelConfig.BUILD_OPTIMIZER,
        "failure_predictor": MLModelConfig.FAILURE_PREDICTOR,
        "test_intelligence": MLModelConfig.TEST_INTELLIGENCE
    }
    
    if model_name not in configs:
        raise ValueError(f"Unknown model: {model_name}")
    
    return configs[model_name]


def get_kubernetes_config() -> KubernetesConfig:
    """Get Kubernetes configuration."""
    return KubernetesConfig()