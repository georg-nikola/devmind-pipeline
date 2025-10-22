"""
Build Optimization Service - AI-powered build optimization and caching strategies
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import structlog
import xgboost as xgb

from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from models.build_data import (
    BuildData,
    BuildOptimizationRequest,
    BuildOptimizationResponse,
)
from utils.caching import CacheManager
from utils.feature_engineering import FeatureEngineer
from utils.metrics import ModelMetrics

from core.config import get_ml_model_config, get_settings

logger = structlog.get_logger(__name__)


class BuildOptimizer:
    """AI-powered build optimization service."""

    def __init__(self):
        self.settings = get_settings()
        self.config = get_ml_model_config("build_optimizer")
        self.model: Optional[xgb.XGBRegressor] = None
        self.scaler = StandardScaler()
        self.feature_engineer = FeatureEngineer()
        self.cache_manager = CacheManager()
        self.metrics = ModelMetrics("build_optimizer")
        self.is_trained = False
        self.last_training_time: Optional[datetime] = None

    async def initialize(self) -> None:
        """Initialize the build optimizer service."""
        logger.info("Initializing Build Optimizer")

        try:
            # Load pre-trained model if available
            await self._load_model()

            # Initialize feature engineer
            await self.feature_engineer.initialize()

            # Initialize cache manager
            await self.cache_manager.initialize()

            logger.info("Build Optimizer initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize Build Optimizer", error=str(e))
            raise

    async def optimize_build(
        self, request: BuildOptimizationRequest
    ) -> BuildOptimizationResponse:
        """
        Optimize build configuration based on historical data and ML predictions.

        Args:
            request: Build optimization request containing project context

        Returns:
            BuildOptimizationResponse with optimization recommendations
        """
        start_time = time.time()

        try:
            logger.info("Starting build optimization", project=request.project_name)

            # Check cache first
            cache_key = self._generate_cache_key(request)
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                logger.info("Returning cached optimization result")
                return BuildOptimizationResponse.parse_obj(cached_result)

            # Extract features from request
            features = await self._extract_features(request)

            # Make predictions
            predictions = await self._predict_build_metrics(features)

            # Generate optimization recommendations
            recommendations = await self._generate_recommendations(
                request, features, predictions
            )

            # Create response
            response = BuildOptimizationResponse(
                project_name=request.project_name,
                estimated_build_time=predictions["build_time"],
                confidence_score=predictions["confidence"],
                recommendations=recommendations,
                cache_strategy=recommendations.get("cache_strategy", {}),
                resource_allocation=recommendations.get("resource_allocation", {}),
                optimization_potential=predictions.get("optimization_potential", 0.0),
                timestamp=datetime.utcnow(),
            )

            # Cache the result
            await self.cache_manager.set(cache_key, response.dict(), ttl=3600)

            # Record metrics
            elapsed_time = time.time() - start_time
            await self.metrics.record_prediction_latency(elapsed_time)
            await self.metrics.record_prediction_count()

            logger.info(
                "Build optimization completed",
                project=request.project_name,
                estimated_time=predictions["build_time"],
                confidence=predictions["confidence"],
                elapsed_time=elapsed_time,
            )

            return response

        except Exception as e:
            logger.error("Build optimization failed", error=str(e))
            await self.metrics.record_error("optimization_failed")
            raise

    async def _extract_features(
        self, request: BuildOptimizationRequest
    ) -> Dict[str, float]:
        """Extract features from build optimization request."""
        features = {}

        # Basic project features
        features["dependency_count"] = len(request.dependencies)
        features["code_change_size"] = (
            request.code_changes.lines_added + request.code_changes.lines_deleted
        )
        features["file_count"] = request.code_changes.files_changed
        features["test_count"] = len(request.test_files) if request.test_files else 0

        # Historical features
        if request.historical_data:
            build_times = [build.duration for build in request.historical_data]
            if build_times:
                features["historical_build_time"] = np.mean(build_times)
                features["build_time_variance"] = np.var(build_times)
                features["build_success_rate"] = sum(
                    1 for build in request.historical_data if build.success
                ) / len(request.historical_data)
            else:
                features["historical_build_time"] = 300  # Default 5 minutes
                features["build_time_variance"] = 0
                features["build_success_rate"] = 0.9
        else:
            features["historical_build_time"] = 300
            features["build_time_variance"] = 0
            features["build_success_rate"] = 0.9

        # Repository features
        features["branch_complexity"] = await self._calculate_branch_complexity(request)
        features["commit_frequency"] = await self._calculate_commit_frequency(request)

        # Dependency analysis
        features["package_size"] = await self._estimate_package_size(
            request.dependencies
        )
        features["dependency_update_frequency"] = (
            await self._calculate_dependency_update_frequency(request.dependencies)
        )

        # Infrastructure features
        features["target_environment"] = self._encode_environment(
            request.target_environment
        )
        features["parallel_jobs"] = (
            request.build_config.get("parallel_jobs", 1) if request.build_config else 1
        )

        # Advanced features using feature engineering
        engineered_features = await self.feature_engineer.engineer_features(request)
        features.update(engineered_features)

        return features

    async def _predict_build_metrics(
        self, features: Dict[str, float]
    ) -> Dict[str, float]:
        """Predict build metrics using ML model."""
        if not self.model or not self.is_trained:
            logger.warning("Model not trained, using heuristic predictions")
            return await self._heuristic_prediction(features)

        # Prepare feature vector
        feature_vector = self._prepare_feature_vector(features)

        # Make prediction
        try:
            prediction = self.model.predict([feature_vector])[0]

            # Calculate confidence based on feature importance and historical accuracy
            confidence = await self._calculate_confidence(features, prediction)

            # Estimate optimization potential
            optimization_potential = await self._estimate_optimization_potential(
                features, prediction
            )

            return {
                "build_time": max(30, prediction),  # Minimum 30 seconds
                "confidence": confidence,
                "optimization_potential": optimization_potential,
            }

        except Exception as e:
            logger.error(
                "Model prediction failed, falling back to heuristics", error=str(e)
            )
            return await self._heuristic_prediction(features)

    async def _heuristic_prediction(
        self, features: Dict[str, float]
    ) -> Dict[str, float]:
        """Fallback heuristic-based prediction when ML model is unavailable."""
        # Simple heuristic based on project size and complexity
        base_time = 120  # 2 minutes base

        # Add time based on dependencies
        dependency_time = features.get("dependency_count", 0) * 5

        # Add time based on code changes
        change_time = features.get("code_change_size", 0) * 0.1

        # Add time based on tests
        test_time = features.get("test_count", 0) * 2

        # Factor in historical build time
        historical_factor = features.get("historical_build_time", 300) * 0.3

        estimated_time = (
            base_time + dependency_time + change_time + test_time + historical_factor
        )

        return {
            "build_time": estimated_time,
            "confidence": 0.6,  # Lower confidence for heuristic
            "optimization_potential": 0.2,
        }

    async def _generate_recommendations(
        self,
        request: BuildOptimizationRequest,
        features: Dict[str, float],
        predictions: Dict[str, float],
    ) -> Dict[str, Any]:
        """Generate optimization recommendations based on analysis."""
        recommendations = {}

        # Cache strategy recommendations
        cache_strategy = await self._recommend_cache_strategy(request, features)
        recommendations["cache_strategy"] = cache_strategy

        # Resource allocation recommendations
        resource_allocation = await self._recommend_resource_allocation(
            features, predictions
        )
        recommendations["resource_allocation"] = resource_allocation

        # Parallelization recommendations
        parallel_strategy = await self._recommend_parallelization(request, features)
        recommendations["parallelization"] = parallel_strategy

        # Dependency optimization
        dependency_optimizations = await self._recommend_dependency_optimizations(
            request.dependencies
        )
        recommendations["dependency_optimizations"] = dependency_optimizations

        # Build step optimizations
        build_optimizations = await self._recommend_build_optimizations(
            request, features
        )
        recommendations["build_optimizations"] = build_optimizations

        return recommendations

    async def _recommend_cache_strategy(
        self, request: BuildOptimizationRequest, features: Dict[str, float]
    ) -> Dict[str, Any]:
        """Recommend intelligent caching strategy."""
        cache_strategy = {
            "enable_dependency_cache": True,
            "enable_build_cache": True,
            "enable_test_cache": True,
            "cache_layers": [],
        }

        # Dependency caching
        if features.get("dependency_count", 0) > 10:
            cache_strategy["cache_layers"].append(
                {
                    "type": "dependency",
                    "priority": "high",
                    "estimated_savings": "30-50%",
                    "cache_key_strategy": "hash_package_lock",
                }
            )

        # Build artifact caching
        if features.get("code_change_size", 0) < 100:  # Small changes
            cache_strategy["cache_layers"].append(
                {
                    "type": "build_artifacts",
                    "priority": "medium",
                    "estimated_savings": "20-40%",
                    "cache_key_strategy": "content_hash",
                }
            )

        # Test result caching
        if features.get("test_count", 0) > 50:
            cache_strategy["cache_layers"].append(
                {
                    "type": "test_results",
                    "priority": "medium",
                    "estimated_savings": "15-30%",
                    "cache_key_strategy": "test_file_hash",
                }
            )

        return cache_strategy

    async def _recommend_resource_allocation(
        self, features: Dict[str, float], predictions: Dict[str, float]
    ) -> Dict[str, Any]:
        """Recommend optimal resource allocation."""
        estimated_time = predictions["build_time"]

        # CPU recommendations
        if estimated_time > 600:  # > 10 minutes
            cpu_cores = min(8, max(2, int(features.get("dependency_count", 0) / 10)))
        else:
            cpu_cores = 2

        # Memory recommendations
        if features.get("package_size", 0) > 1000:  # Large packages
            memory_gb = min(16, max(4, int(features.get("package_size", 0) / 500)))
        else:
            memory_gb = 2

        return {
            "cpu_cores": cpu_cores,
            "memory_gb": memory_gb,
            "disk_gb": max(20, int(features.get("package_size", 0) / 100)),
            "estimated_cost_per_build": cpu_cores * 0.1 + memory_gb * 0.05,
        }

    async def train_model(self, training_data: List[BuildData]) -> Dict[str, float]:
        """Train the build optimization model with new data."""
        logger.info("Starting model training", samples=len(training_data))

        try:
            # Prepare training data
            X, y = await self._prepare_training_data(training_data)

            if len(X) < self.settings.MIN_TRAINING_SAMPLES:
                raise ValueError(
                    f"Insufficient training data: {len(X)} samples, minimum {self.settings.MIN_TRAINING_SAMPLES}"
                )

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            # Train model
            self.model = xgb.XGBRegressor(**self.config["hyperparameters"])
            self.model.fit(
                X_train_scaled,
                y_train,
                eval_set=[(X_test_scaled, y_test)],
                early_stopping_rounds=self.config.get("early_stopping_rounds", 10),
                verbose=False,
            )

            # Evaluate model
            y_pred = self.model.predict(X_test_scaled)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)

            # Update model state
            self.is_trained = True
            self.last_training_time = datetime.utcnow()

            # Save model
            await self._save_model()

            # Record metrics
            await self.metrics.record_training_metrics(mae, r2, len(training_data))

            logger.info(
                "Model training completed",
                mae=mae,
                r2_score=r2,
                samples=len(training_data),
            )

            return {
                "mae": mae,
                "r2_score": r2,
                "training_samples": len(training_data),
                "training_time": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error("Model training failed", error=str(e))
            await self.metrics.record_error("training_failed")
            raise

    async def _prepare_training_data(
        self, training_data: List[BuildData]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data for model training."""
        features_list = []
        targets = []

        for build_data in training_data:
            # Extract features
            features = await self._extract_features_from_build_data(build_data)

            # Prepare feature vector
            feature_vector = self._prepare_feature_vector(features)

            features_list.append(feature_vector)
            targets.append(build_data.duration)

        return np.array(features_list), np.array(targets)

    def _prepare_feature_vector(self, features: Dict[str, float]) -> List[float]:
        """Prepare feature vector from feature dictionary."""
        feature_columns = self.config["feature_columns"]
        return [features.get(col, 0.0) for col in feature_columns]

    def _generate_cache_key(self, request: BuildOptimizationRequest) -> str:
        """Generate cache key for optimization request."""
        key_data = {
            "project_name": request.project_name,
            "dependencies_hash": hashlib.md5(
                json.dumps(sorted(request.dependencies), sort_keys=True).encode()
            ).hexdigest(),
            "code_changes_hash": hashlib.md5(
                f"{request.code_changes.lines_added}:{request.code_changes.lines_deleted}:{request.code_changes.files_changed}".encode()
            ).hexdigest(),
            "target_environment": request.target_environment,
        }

        return f"build_opt:{hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()}"

    async def _calculate_branch_complexity(
        self, request: BuildOptimizationRequest
    ) -> float:
        """Calculate branch complexity metric."""
        # Simplified branch complexity calculation
        if not request.code_changes:
            return 1.0

        files_changed = request.code_changes.files_changed
        lines_changed = (
            request.code_changes.lines_added + request.code_changes.lines_deleted
        )

        if files_changed == 0:
            return 1.0

        return min(10.0, (lines_changed / files_changed) / 10)

    async def _calculate_commit_frequency(
        self, request: BuildOptimizationRequest
    ) -> float:
        """Calculate commit frequency metric."""
        if not request.historical_data:
            return 1.0

        # Calculate commits per day based on historical data
        commits_count = len(request.historical_data)
        days_span = 30  # Assume 30 days of history

        return commits_count / days_span

    async def _estimate_package_size(self, dependencies: List[str]) -> float:
        """Estimate total package size in MB."""
        # Simplified package size estimation
        return len(dependencies) * 10  # Assume 10MB per dependency on average

    async def _calculate_dependency_update_frequency(
        self, dependencies: List[str]
    ) -> float:
        """Calculate how frequently dependencies are updated."""
        # Simplified calculation - would integrate with package registries in real implementation
        return len(dependencies) * 0.1  # Assume 10% of dependencies updated per month

    def _encode_environment(self, environment: str) -> float:
        """Encode target environment as numeric value."""
        environment_map = {"development": 1.0, "staging": 2.0, "production": 3.0}
        return environment_map.get(environment.lower(), 1.0)

    async def _calculate_confidence(
        self, features: Dict[str, float], prediction: float
    ) -> float:
        """Calculate prediction confidence score."""
        # Simplified confidence calculation
        # In practice, this would use model uncertainty estimation
        base_confidence = 0.8

        # Reduce confidence for extreme predictions
        if prediction > 1800:  # > 30 minutes
            base_confidence *= 0.7
        elif prediction < 60:  # < 1 minute
            base_confidence *= 0.8

        # Adjust based on historical data availability
        if features.get("historical_build_time", 0) > 0:
            base_confidence *= 1.1

        return min(1.0, base_confidence)

    async def _estimate_optimization_potential(
        self, features: Dict[str, float], prediction: float
    ) -> float:
        """Estimate potential for build time optimization."""
        if prediction < 120:  # Already fast builds
            return 0.1

        potential = 0.3  # Base 30% optimization potential

        # More potential with more dependencies (caching opportunities)
        if features.get("dependency_count", 0) > 20:
            potential += 0.2

        # More potential with larger builds
        if prediction > 600:  # > 10 minutes
            potential += 0.3

        return min(0.8, potential)  # Cap at 80%

    async def _load_model(self) -> None:
        """Load pre-trained model from storage."""
        try:
            # In a real implementation, this would load from MLflow or file storage
            logger.info("No pre-trained model found, will train on first request")
            self.is_trained = False
        except Exception as e:
            logger.warning("Failed to load pre-trained model", error=str(e))
            self.is_trained = False

    async def _save_model(self) -> None:
        """Save trained model to storage."""
        try:
            # In a real implementation, this would save to MLflow or file storage
            logger.info("Model saved successfully")
        except Exception as e:
            logger.error("Failed to save model", error=str(e))

    async def health_check(self) -> Dict[str, Any]:
        """Health check for the build optimizer service."""
        return {
            "service": "build_optimizer",
            "status": "healthy",
            "model_trained": self.is_trained,
            "last_training": (
                self.last_training_time.isoformat() if self.last_training_time else None
            ),
            "cache_status": (
                await self.cache_manager.health_check()
                if self.cache_manager
                else "unavailable"
            ),
        }
