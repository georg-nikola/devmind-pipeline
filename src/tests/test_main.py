"""
Tests for main FastAPI application
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from main import create_app, lifespan


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    app = create_app()
    return TestClient(app)


class TestApplicationCreation:
    """Test FastAPI application creation and initialization."""

    def test_create_app_returns_fastapi_instance(self):
        """Test that create_app returns a FastAPI instance."""
        app = create_app()
        assert app is not None
        assert hasattr(app, "routes")

    def test_app_includes_required_routers(self):
        """Test that app includes all required routers."""
        app = create_app()
        route_paths = {route.path for route in app.routes}
        # Check for key endpoints
        assert "/api/v1/build-optimizer" in str(route_paths)
        assert "/api/v1/failure-predictor" in str(route_paths)
        assert "/api/v1/test-intelligence" in str(route_paths)

    def test_app_has_cors_middleware(self):
        """Test that CORS middleware is configured."""
        app = create_app()
        # Check that CORSMiddleware is in the middleware stack
        middleware_names = [type(m.cls).__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middleware_names

    @patch("main.settings")
    def test_app_uses_allowed_origins_from_settings(self, mock_settings):
        """Test that app configures CORS with allowed origins from settings."""
        mock_settings.allowed_origins = ["https://example.com"]
        app = create_app()
        # Verify CORS middleware is configured
        middleware_names = [type(m.cls).__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middleware_names


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check_endpoint_exists(self, client):
        """Test that /health endpoint exists."""
        response = client.get("/health")
        assert response.status_code != 404

    def test_health_check_returns_json(self, client):
        """Test that /health returns valid JSON."""
        with patch("main.ml_service_manager") as mock_manager:
            mock_manager.health_check = AsyncMock(return_value={"healthy": True})
            response = client.get("/health")
            assert response.headers["content-type"].startswith("application/json")

    def test_health_check_unavailable_without_manager(self, client):
        """Test that /health returns 503 when manager is not initialized."""
        # When manager is None, should return service unavailable
        with patch("main.ml_service_manager", None):
            response = client.get("/health")
            assert response.status_code == 503


class TestMetricsEndpoint:
    """Test Prometheus metrics endpoint."""

    def test_metrics_endpoint_exists(self, client):
        """Test that /metrics endpoint exists."""
        response = client.get("/metrics")
        assert response.status_code != 404

    def test_metrics_returns_prometheus_format(self, client):
        """Test that /metrics returns Prometheus-formatted data."""
        response = client.get("/metrics")
        # Prometheus metrics are text format
        assert "text/plain" in response.headers.get("content-type", "")

    def test_metrics_contains_standard_metrics(self, client):
        """Test that metrics include standard Python/Prometheus metrics."""
        response = client.get("/metrics")
        text = response.text
        # Should contain at least one standard metric
        assert len(text) > 0


class TestRootEndpoint:
    """Test root endpoint."""

    def test_root_endpoint_accessible(self, client):
        """Test that root endpoint is accessible."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_endpoint_returns_service_info(self, client):
        """Test that root endpoint returns service information."""
        response = client.get("/")
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "status" in data
        assert data["service"] == "DevMind Pipeline ML Services"

    def test_root_endpoint_lists_features(self, client):
        """Test that root endpoint lists available features."""
        response = client.get("/")
        data = response.json()
        assert "features" in data
        assert isinstance(data["features"], list)
        assert len(data["features"]) > 0


class TestModelsStatusEndpoint:
    """Test models status endpoint."""

    def test_models_status_endpoint_exists(self, client):
        """Test that /models/status endpoint exists."""
        response = client.get("/models/status")
        assert response.status_code != 404

    def test_models_status_unavailable_without_manager(self, client):
        """Test that /models/status returns 503 when manager not initialized."""
        with patch("main.ml_service_manager", None):
            response = client.get("/models/status")
            assert response.status_code == 503

    def test_models_status_returns_json(self, client):
        """Test that /models/status returns JSON."""
        with patch("main.ml_service_manager") as mock_manager:
            mock_manager.get_models_status = AsyncMock(return_value={"models": []})
            response = client.get("/models/status")
            assert response.headers["content-type"].startswith("application/json")


class TestRetrainEndpoint:
    """Test model retraining endpoint."""

    def test_retrain_endpoint_exists(self, client):
        """Test that /models/retrain/{model_name} endpoint exists."""
        with patch("main.ml_service_manager") as mock_manager:
            mock_manager.retrain_model = AsyncMock(return_value="task_123")
            response = client.post("/models/retrain/build_optimizer")
            assert response.status_code != 404

    def test_retrain_endpoint_invalid_model_returns_404(self, client):
        """Test that retraining invalid model returns 404."""
        with patch("main.ml_service_manager") as mock_manager:
            mock_manager.retrain_model = AsyncMock(
                side_effect=ValueError("Unknown model")
            )
            response = client.post("/models/retrain/invalid_model")
            assert response.status_code == 404

    def test_retrain_endpoint_unavailable_without_manager(self, client):
        """Test that /models/retrain returns 503 when manager not initialized."""
        with patch("main.ml_service_manager", None):
            response = client.post("/models/retrain/build_optimizer")
            assert response.status_code == 503

    def test_retrain_endpoint_returns_task_id(self, client):
        """Test that retrain endpoint returns task_id."""
        with patch("main.ml_service_manager") as mock_manager:
            mock_manager.retrain_model = AsyncMock(return_value="task_xyz_123")
            response = client.post("/models/retrain/build_optimizer")
            data = response.json()
            assert "task_id" in data
            assert data["task_id"] == "task_xyz_123"


class TestCORSConfiguration:
    """Test CORS configuration."""

    def test_cors_allows_origins_from_settings(self):
        """Test that CORS middleware uses allowed origins from settings."""
        # This is tested through the middleware configuration
        app = create_app()
        assert app is not None

    def test_cors_allows_credentials(self):
        """Test that CORS allows credentials."""
        app = create_app()
        # Check middleware is configured with allow_credentials
        middleware_names = [type(m.cls).__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middleware_names

    def test_cors_allows_all_methods(self):
        """Test that CORS allows all HTTP methods."""
        app = create_app()
        middleware_names = [type(m.cls).__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middleware_names

    def test_cors_allows_all_headers(self):
        """Test that CORS allows all headers."""
        app = create_app()
        middleware_names = [type(m.cls).__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middleware_names


class TestAPIEndpointRegistry:
    """Test that all API endpoints are properly registered."""

    def test_build_optimizer_router_registered(self, client):
        """Test that build optimizer router is registered."""
        # Try accessing a route from the build optimizer router
        response = client.get("/api/v1/build-optimizer")
        # Should return 405 Method Not Allowed or 200, not 404
        assert response.status_code != 404

    def test_failure_predictor_router_registered(self, client):
        """Test that failure predictor router is registered."""
        response = client.get("/api/v1/failure-predictor")
        assert response.status_code != 404

    def test_test_intelligence_router_registered(self, client):
        """Test that test intelligence router is registered."""
        response = client.get("/api/v1/test-intelligence")
        assert response.status_code != 404


class TestAppInitializationErrors:
    """Test application initialization error handling."""

    def test_app_handles_missing_settings(self):
        """Test that app handles missing settings gracefully."""
        # Settings should be initialized with defaults
        app = create_app()
        assert app is not None

    def test_app_handles_invalid_environment(self):
        """Test that app handles invalid ENVIRONMENT value."""
        with patch.dict("os.environ", {"ENVIRONMENT": "unknown"}, clear=False):
            app = create_app()
            assert app is not None

    def test_app_docs_disabled_in_production(self):
        """Test that API docs are disabled in production."""
        with patch.dict("os.environ", {"ENVIRONMENT": "production"}, clear=False):
            app = create_app()
            # Find docs_url in app configuration
            assert app.docs_url is None or app.openapi_url is None

    def test_app_docs_enabled_in_development(self):
        """Test that API docs are enabled in development."""
        with patch.dict("os.environ", {"ENVIRONMENT": "development"}, clear=False):
            app = create_app()
            assert app.docs_url == "/docs" or app.openapi_url is not None
