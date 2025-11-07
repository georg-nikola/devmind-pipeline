"""
Tests for core configuration module
"""

import os
import pytest
from typing import List
from unittest.mock import patch, MagicMock

from core.config import (
    Settings,
    MLModelConfig,
    KubernetesConfig,
    get_settings,
    get_ml_model_config,
)


class TestSettingsBasics:
    """Test basic Settings class initialization and defaults."""

    def test_settings_defaults(self):
        """Test that Settings initializes with correct defaults."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.APP_NAME == "DevMind Pipeline ML Services"
            assert settings.VERSION == "1.0.0"
            assert settings.ENVIRONMENT == "development"
            assert settings.DEBUG is False
            assert settings.HOST == "0.0.0.0"
            assert settings.PORT == 8000
            assert settings.LOG_LEVEL == "INFO"

    def test_settings_from_env_variables(self):
        """Test that Settings reads from environment variables."""
        env_vars = {
            "ENVIRONMENT": "production",
            "DEBUG": "True",
            "HOST": "127.0.0.1",
            "PORT": "9000",
            "LOG_LEVEL": "DEBUG",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            settings = Settings()
            assert settings.ENVIRONMENT == "production"
            assert settings.DEBUG is True
            assert settings.HOST == "127.0.0.1"
            assert settings.PORT == 9000
            assert settings.LOG_LEVEL == "DEBUG"


class TestAllowedOrigins:
    """Test ALLOWED_ORIGINS configuration parsing."""

    def test_allowed_origins_default(self):
        """Test default ALLOWED_ORIGINS value."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            origins = settings.allowed_origins
            assert isinstance(origins, list)
            assert "http://localhost:3000" in origins
            assert "http://localhost:8080" in origins

    def test_allowed_origins_single_value(self):
        """Test parsing single ALLOWED_ORIGINS value."""
        with patch.dict(os.environ, {"ALLOWED_ORIGINS": "https://example.com"}, clear=False):
            settings = Settings()
            origins = settings.allowed_origins
            assert origins == ["https://example.com"]

    def test_allowed_origins_comma_separated(self):
        """Test parsing comma-separated ALLOWED_ORIGINS."""
        origins_str = "https://example.com,https://api.example.com,https://dashboard.example.com"
        with patch.dict(os.environ, {"ALLOWED_ORIGINS": origins_str}, clear=False):
            settings = Settings()
            origins = settings.allowed_origins
            assert len(origins) == 3
            assert "https://example.com" in origins
            assert "https://api.example.com" in origins
            assert "https://dashboard.example.com" in origins

    def test_allowed_origins_with_spaces(self):
        """Test that spaces are trimmed from ALLOWED_ORIGINS."""
        origins_str = "  https://example.com  ,  https://api.example.com  "
        with patch.dict(os.environ, {"ALLOWED_ORIGINS": origins_str}, clear=False):
            settings = Settings()
            origins = settings.allowed_origins
            assert origins == ["https://example.com", "https://api.example.com"]

    def test_allowed_origins_empty_string_uses_default(self):
        """Test that empty ALLOWED_ORIGINS uses default values."""
        with patch.dict(os.environ, {"ALLOWED_ORIGINS": ""}, clear=False):
            settings = Settings()
            origins = settings.allowed_origins
            assert "http://localhost:3000" in origins
            assert "http://localhost:8080" in origins

    def test_allowed_origins_whitespace_only_uses_default(self):
        """Test that whitespace-only ALLOWED_ORIGINS uses default values."""
        with patch.dict(os.environ, {"ALLOWED_ORIGINS": "   "}, clear=False):
            settings = Settings()
            origins = settings.allowed_origins
            assert "http://localhost:3000" in origins
            assert "http://localhost:8080" in origins

    def test_allowed_origins_filters_empty_entries(self):
        """Test that empty entries in comma-separated list are filtered."""
        origins_str = "https://example.com,,https://api.example.com,"
        with patch.dict(os.environ, {"ALLOWED_ORIGINS": origins_str}, clear=False):
            settings = Settings()
            origins = settings.allowed_origins
            # Should only have the non-empty entries
            assert len(origins) == 2
            assert "https://example.com" in origins
            assert "https://api.example.com" in origins


class TestSecurityConfiguration:
    """Test security-related configuration."""

    def test_secret_key_default(self):
        """Test that SECRET_KEY has a default value."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.SECRET_KEY == "dev-secret-key"

    def test_secret_key_from_env(self):
        """Test that SECRET_KEY can be set from environment."""
        secret = "my-super-secure-key-12345"
        with patch.dict(os.environ, {"SECRET_KEY": secret}, clear=False):
            settings = Settings()
            assert settings.SECRET_KEY == secret


class TestDatabaseConfiguration:
    """Test database-related configuration."""

    def test_database_url_default(self):
        """Test default DATABASE_URL."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert "postgresql://" in settings.DATABASE_URL
            assert "localhost" in settings.DATABASE_URL

    def test_database_url_from_env(self):
        """Test DATABASE_URL from environment variable."""
        db_url = "postgresql://user:pass@db.example.com:5432/mydb"
        with patch.dict(os.environ, {"DATABASE_URL": db_url}, clear=False):
            settings = Settings()
            assert settings.DATABASE_URL == db_url

    def test_redis_url_default(self):
        """Test default REDIS_URL."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.REDIS_URL == "redis://localhost:6379/0"

    def test_redis_url_from_env(self):
        """Test REDIS_URL from environment variable."""
        redis_url = "redis://redis.example.com:6379/1"
        with patch.dict(os.environ, {"REDIS_URL": redis_url}, clear=False):
            settings = Settings()
            assert settings.REDIS_URL == redis_url


class TestMLConfiguration:
    """Test ML model configuration."""

    def test_build_optimizer_config(self):
        """Test BUILD_OPTIMIZER configuration."""
        config = MLModelConfig.BUILD_OPTIMIZER
        assert config["model_type"] == "xgboost"
        assert "hyperparameters" in config
        assert config["hyperparameters"]["n_estimators"] == 100
        assert "feature_columns" in config
        assert len(config["feature_columns"]) > 0

    def test_failure_predictor_config(self):
        """Test FAILURE_PREDICTOR configuration."""
        config = MLModelConfig.FAILURE_PREDICTOR
        assert config["model_type"] == "pytorch_neural_network"
        assert "architecture" in config
        assert "training" in config
        assert config["architecture"]["input_size"] == 50

    def test_test_intelligence_config(self):
        """Test TEST_INTELLIGENCE configuration."""
        config = MLModelConfig.TEST_INTELLIGENCE
        assert config["model_type"] == "random_forest"
        assert "hyperparameters" in config
        assert config["hyperparameters"]["n_estimators"] == 200

    def test_get_ml_model_config_build_optimizer(self):
        """Test get_ml_model_config for build_optimizer."""
        config = get_ml_model_config("build_optimizer")
        assert config["model_type"] == "xgboost"

    def test_get_ml_model_config_failure_predictor(self):
        """Test get_ml_model_config for failure_predictor."""
        config = get_ml_model_config("failure_predictor")
        assert config["model_type"] == "pytorch_neural_network"

    def test_get_ml_model_config_test_intelligence(self):
        """Test get_ml_model_config for test_intelligence."""
        config = get_ml_model_config("test_intelligence")
        assert config["model_type"] == "random_forest"

    def test_get_ml_model_config_invalid_model(self):
        """Test that get_ml_model_config raises ValueError for unknown model."""
        with pytest.raises(ValueError, match="Unknown model"):
            get_ml_model_config("nonexistent_model")


class TestKubernetesConfiguration:
    """Test Kubernetes-specific configuration."""

    def test_kubernetes_config_defaults(self):
        """Test Kubernetes configuration defaults."""
        with patch.dict(os.environ, {}, clear=True):
            k8s_config = KubernetesConfig()
            assert k8s_config.NAMESPACE == "devmind-pipeline"
            assert k8s_config.POD_NAME == "ml-service"
            assert k8s_config.SERVICE_ACCOUNT == "devmind-ml-service"

    def test_kubernetes_config_from_env(self):
        """Test Kubernetes configuration from environment."""
        env_vars = {
            "POD_NAMESPACE": "custom-namespace",
            "POD_NAME": "custom-pod",
            "SERVICE_ACCOUNT": "custom-sa",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            k8s_config = KubernetesConfig()
            assert k8s_config.NAMESPACE == "custom-namespace"
            assert k8s_config.POD_NAME == "custom-pod"
            assert k8s_config.SERVICE_ACCOUNT == "custom-sa"

    def test_kubernetes_health_check_paths(self):
        """Test Kubernetes health check paths are configured."""
        k8s_config = KubernetesConfig()
        assert k8s_config.READINESS_PROBE_PATH == "/health"
        assert k8s_config.LIVENESS_PROBE_PATH == "/health"
        assert k8s_config.STARTUP_PROBE_PATH == "/health"


class TestSettingsCaching:
    """Test that settings are cached correctly."""

    def test_get_settings_returns_cached_instance(self):
        """Test that get_settings returns the same cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        # Should be the same object due to lru_cache
        assert settings1 is settings2

    def test_get_settings_singleton_behavior(self):
        """Test singleton behavior of get_settings."""
        # Clear the cache first
        get_settings.cache_clear()

        settings = get_settings()
        assert isinstance(settings, Settings)

        # Modify an attribute
        original_app_name = settings.APP_NAME

        # Get settings again - should be same instance
        settings2 = get_settings()
        assert settings2.APP_NAME == original_app_name


class TestFeatureFlags:
    """Test feature flag configuration."""

    def test_prometheus_metrics_enabled_by_default(self):
        """Test that Prometheus metrics are enabled by default."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.ENABLE_PROMETHEUS_METRICS is True

    def test_distributed_tracing_enabled_by_default(self):
        """Test that distributed tracing is enabled by default."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.ENABLE_DISTRIBUTED_TRACING is True

    def test_model_explanations_enabled_by_default(self):
        """Test that model explanations are enabled by default."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.ENABLE_MODEL_EXPLANATIONS is True

    def test_feature_flags_from_env(self):
        """Test that feature flags can be disabled via environment."""
        env_vars = {
            "ENABLE_PROMETHEUS_METRICS": "false",
            "ENABLE_DISTRIBUTED_TRACING": "false",
            "ENABLE_MODEL_EXPLANATIONS": "false",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            settings = Settings()
            assert settings.ENABLE_PROMETHEUS_METRICS is False
            assert settings.ENABLE_DISTRIBUTED_TRACING is False
            assert settings.ENABLE_MODEL_EXPLANATIONS is False


class TestPerformanceSettings:
    """Test performance-related configuration."""

    def test_max_concurrent_predictions_default(self):
        """Test default MAX_CONCURRENT_PREDICTIONS."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.MAX_CONCURRENT_PREDICTIONS == 100

    def test_prediction_timeout_default(self):
        """Test default PREDICTION_TIMEOUT."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.PREDICTION_TIMEOUT == 30

    def test_cache_ttl_default(self):
        """Test default CACHE_TTL (1 hour)."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.CACHE_TTL == 3600

    def test_max_batch_size_default(self):
        """Test default MAX_BATCH_SIZE."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.MAX_BATCH_SIZE == 1000


class TestLoggingConfiguration:
    """Test logging configuration."""

    def test_log_level_default(self):
        """Test default log level."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.LOG_LEVEL == "INFO"

    def test_log_format_default(self):
        """Test default log format."""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.LOG_FORMAT == "json"

    def test_log_configuration_from_env(self):
        """Test log configuration from environment."""
        env_vars = {
            "LOG_LEVEL": "DEBUG",
            "LOG_FORMAT": "text",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            settings = Settings()
            assert settings.LOG_LEVEL == "DEBUG"
            assert settings.LOG_FORMAT == "text"
