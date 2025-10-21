"""
Failure Prediction Model - PyTorch Neural Network for pipeline failure prediction
"""

import asyncio
import json
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
import structlog

from core.config import get_settings, get_ml_model_config


logger = structlog.get_logger(__name__)


class FailurePredictionNetwork(nn.Module):
    """PyTorch Neural Network for failure prediction."""
    
    def __init__(self, input_size: int, hidden_layers: List[int], dropout: float = 0.2):
        super(FailurePredictionNetwork, self).__init__()
        
        self.layers = nn.ModuleList()
        
        # Input layer
        prev_size = input_size
        
        # Hidden layers
        for hidden_size in hidden_layers:
            self.layers.append(nn.Linear(prev_size, hidden_size))
            self.layers.append(nn.ReLU())
            self.layers.append(nn.Dropout(dropout))
            prev_size = hidden_size
        
        # Output layer (binary classification)
        self.layers.append(nn.Linear(prev_size, 1))
        self.layers.append(nn.Sigmoid())
    
    def forward(self, x):
        for layer in self.layers:
            x = layer(x)
        return x


class FailurePredictor:
    """AI-powered pipeline failure prediction service."""
    
    def __init__(self):
        self.settings = get_settings()
        self.config = get_ml_model_config("failure_predictor")
        self.model: Optional[FailurePredictionNetwork] = None
        self.scaler = StandardScaler()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.is_trained = False
        self.last_training_time: Optional[datetime] = None
        self.feature_names: List[str] = []
        self.model_metrics: Dict[str, float] = {}
        
    async def initialize(self) -> None:
        """Initialize the failure predictor."""
        logger.info("Initializing Failure Predictor", device=str(self.device))
        
        try:
            # Load pre-trained model if available
            await self._load_model()
            
            # Initialize feature names
            self.feature_names = self.config["feature_columns"]
            
            logger.info("Failure Predictor initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Failure Predictor", error=str(e))
            raise
    
    async def predict_failure(self, pipeline_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict pipeline failure probability.
        
        Args:
            pipeline_metrics: Dictionary containing pipeline metrics and context
            
        Returns:
            Dictionary with failure probability and risk factors
        """
        try:
            logger.info("Predicting pipeline failure")
            
            # Extract features
            features = await self._extract_features(pipeline_metrics)
            
            # Make prediction
            prediction_result = await self._make_prediction(features)
            
            # Analyze risk factors
            risk_factors = await self._analyze_risk_factors(features, prediction_result)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(features, prediction_result, risk_factors)
            
            result = {
                "failure_probability": prediction_result["probability"],
                "confidence": prediction_result["confidence"],
                "risk_level": prediction_result["risk_level"],
                "risk_factors": risk_factors,
                "recommendations": recommendations,
                "timestamp": datetime.utcnow().isoformat(),
                "model_version": self._get_model_version()
            }
            
            logger.info(
                "Failure prediction completed",
                probability=prediction_result["probability"],
                risk_level=prediction_result["risk_level"]
            )
            
            return result
            
        except Exception as e:
            logger.error("Failure prediction failed", error=str(e))
            raise
    
    async def _extract_features(self, pipeline_metrics: Dict[str, Any]) -> Dict[str, float]:
        """Extract features from pipeline metrics."""
        features = {}
        
        # Pipeline duration statistics
        duration_history = pipeline_metrics.get("duration_history", [])
        if duration_history:
            features["pipeline_duration_mean"] = np.mean(duration_history)
            features["pipeline_duration_std"] = np.std(duration_history)
            features["pipeline_duration_trend"] = self._calculate_trend(duration_history)
        else:
            features["pipeline_duration_mean"] = 300.0  # Default 5 minutes
            features["pipeline_duration_std"] = 50.0
            features["pipeline_duration_trend"] = 0.0
        
        # Failure rate statistics
        failure_history = pipeline_metrics.get("failure_history", [])
        if failure_history:
            recent_failures = failure_history[-20:]  # Last 20 builds
            features["failure_rate_7d"] = sum(recent_failures) / len(recent_failures)
            features["failure_trend"] = self._calculate_trend(recent_failures)
        else:
            features["failure_rate_7d"] = 0.05  # Default 5% failure rate
            features["failure_trend"] = 0.0
        
        # Code change metrics
        code_metrics = pipeline_metrics.get("code_metrics", {})
        features["code_churn"] = code_metrics.get("lines_changed", 0)
        features["files_changed"] = code_metrics.get("files_changed", 0)
        features["complexity_delta"] = code_metrics.get("complexity_change", 0)
        
        # Test metrics
        test_metrics = pipeline_metrics.get("test_metrics", {})
        features["test_coverage"] = test_metrics.get("coverage_percentage", 80.0)
        features["test_count"] = test_metrics.get("test_count", 0)
        features["test_duration"] = test_metrics.get("test_duration", 0)
        features["flaky_test_count"] = test_metrics.get("flaky_tests", 0)
        
        # Deployment metrics
        deployment_metrics = pipeline_metrics.get("deployment_metrics", {})
        features["deployment_frequency"] = deployment_metrics.get("deployments_per_day", 1.0)
        features["deployment_success_rate"] = deployment_metrics.get("success_rate", 0.95)
        
        # Infrastructure metrics
        infra_metrics = pipeline_metrics.get("infrastructure_metrics", {})
        features["error_rate"] = infra_metrics.get("error_rate", 0.01)
        features["response_time_p95"] = infra_metrics.get("response_time_p95", 200.0)
        features["resource_utilization"] = infra_metrics.get("cpu_utilization", 50.0)
        features["memory_utilization"] = infra_metrics.get("memory_utilization", 60.0)
        
        # Environmental factors
        env_metrics = pipeline_metrics.get("environment_metrics", {})
        features["time_of_day"] = self._encode_time_of_day(env_metrics.get("timestamp"))
        features["day_of_week"] = self._encode_day_of_week(env_metrics.get("timestamp"))
        features["is_weekend"] = self._is_weekend(env_metrics.get("timestamp"))
        
        # Dependency metrics
        dependency_metrics = pipeline_metrics.get("dependency_metrics", {})
        features["dependency_count"] = dependency_metrics.get("total_dependencies", 0)
        features["outdated_dependencies"] = dependency_metrics.get("outdated_count", 0)
        features["security_vulnerabilities"] = dependency_metrics.get("vulnerability_count", 0)
        
        return features
    
    async def _make_prediction(self, features: Dict[str, float]) -> Dict[str, Any]:
        """Make failure prediction using the trained model."""
        if not self.model or not self.is_trained:
            logger.warning("Model not trained, using heuristic prediction")
            return await self._heuristic_prediction(features)
        
        try:
            # Prepare feature vector
            feature_vector = self._prepare_feature_vector(features)
            feature_tensor = torch.FloatTensor([feature_vector]).to(self.device)
            
            # Make prediction
            self.model.eval()
            with torch.no_grad():
                prediction = self.model(feature_tensor)
                probability = prediction.item()
            
            # Calculate confidence
            confidence = await self._calculate_confidence(features, probability)
            
            # Determine risk level
            risk_level = self._determine_risk_level(probability)
            
            return {
                "probability": probability,
                "confidence": confidence,
                "risk_level": risk_level
            }
            
        except Exception as e:
            logger.error("Model prediction failed, falling back to heuristics", error=str(e))
            return await self._heuristic_prediction(features)
    
    async def _heuristic_prediction(self, features: Dict[str, float]) -> Dict[str, Any]:
        """Fallback heuristic-based prediction."""
        risk_score = 0.0
        
        # Historical failure rate
        failure_rate = features.get("failure_rate_7d", 0.05)
        risk_score += failure_rate * 0.3
        
        # Code change risk
        code_churn = features.get("code_churn", 0)
        if code_churn > 1000:  # Large changes
            risk_score += 0.2
        elif code_churn > 500:
            risk_score += 0.1
        
        # Test coverage risk
        test_coverage = features.get("test_coverage", 80.0)
        if test_coverage < 70:
            risk_score += 0.15
        elif test_coverage < 80:
            risk_score += 0.1
        
        # Infrastructure issues
        error_rate = features.get("error_rate", 0.01)
        if error_rate > 0.05:  # > 5% error rate
            risk_score += 0.2
        
        # Flaky tests
        flaky_tests = features.get("flaky_test_count", 0)
        if flaky_tests > 5:
            risk_score += 0.15
        
        # Resource utilization
        cpu_util = features.get("resource_utilization", 50.0)
        memory_util = features.get("memory_utilization", 60.0)
        if cpu_util > 90 or memory_util > 90:
            risk_score += 0.1
        
        probability = min(0.95, risk_score)
        
        return {
            "probability": probability,
            "confidence": 0.6,  # Lower confidence for heuristic
            "risk_level": self._determine_risk_level(probability)
        }
    
    def _determine_risk_level(self, probability: float) -> str:
        """Determine risk level based on failure probability."""
        if probability < 0.1:
            return "low"
        elif probability < 0.3:
            return "medium"
        elif probability < 0.6:
            return "high"
        else:
            return "critical"
    
    async def _analyze_risk_factors(self, features: Dict[str, float], prediction: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze and rank risk factors."""
        risk_factors = []
        
        # High failure rate
        if features.get("failure_rate_7d", 0) > 0.2:
            risk_factors.append({
                "factor": "high_failure_rate",
                "severity": "high",
                "value": features.get("failure_rate_7d", 0),
                "description": "Recent builds have high failure rate",
                "impact": 0.3
            })
        
        # Large code changes
        if features.get("code_churn", 0) > 1000:
            risk_factors.append({
                "factor": "large_code_changes",
                "severity": "medium",
                "value": features.get("code_churn", 0),
                "description": "Large number of code changes increases risk",
                "impact": 0.2
            })
        
        # Low test coverage
        if features.get("test_coverage", 80) < 70:
            risk_factors.append({
                "factor": "low_test_coverage",
                "severity": "high",
                "value": features.get("test_coverage", 80),
                "description": "Test coverage below recommended threshold",
                "impact": 0.25
            })
        
        # High error rate
        if features.get("error_rate", 0.01) > 0.05:
            risk_factors.append({
                "factor": "high_error_rate",
                "severity": "high",
                "value": features.get("error_rate", 0.01),
                "description": "Application error rate is elevated",
                "impact": 0.3
            })
        
        # Flaky tests
        if features.get("flaky_test_count", 0) > 3:
            risk_factors.append({
                "factor": "flaky_tests",
                "severity": "medium",
                "value": features.get("flaky_test_count", 0),
                "description": "Multiple flaky tests detected",
                "impact": 0.15
            })
        
        # Security vulnerabilities
        if features.get("security_vulnerabilities", 0) > 0:
            risk_factors.append({
                "factor": "security_vulnerabilities",
                "severity": "high",
                "value": features.get("security_vulnerabilities", 0),
                "description": "Security vulnerabilities in dependencies",
                "impact": 0.2
            })
        
        # Sort by impact
        risk_factors.sort(key=lambda x: x["impact"], reverse=True)
        
        return risk_factors
    
    async def _generate_recommendations(
        self, 
        features: Dict[str, float], 
        prediction: Dict[str, Any], 
        risk_factors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on risk analysis."""
        recommendations = []
        
        if prediction["risk_level"] in ["high", "critical"]:
            recommendations.append({
                "type": "immediate",
                "priority": "high",
                "action": "Consider manual review before deployment",
                "reason": f"High failure probability ({prediction['probability']:.2%})"
            })
        
        # Recommendations based on risk factors
        for factor in risk_factors:
            if factor["factor"] == "high_failure_rate":
                recommendations.append({
                    "type": "process",
                    "priority": "high",
                    "action": "Review recent failures and implement fixes",
                    "reason": "Failure rate trending upward"
                })
            
            elif factor["factor"] == "low_test_coverage":
                recommendations.append({
                    "type": "quality",
                    "priority": "medium",
                    "action": "Increase test coverage before proceeding",
                    "reason": f"Coverage at {factor['value']:.1f}%, target >80%"
                })
            
            elif factor["factor"] == "flaky_tests":
                recommendations.append({
                    "type": "quality",
                    "priority": "medium",
                    "action": "Fix or quarantine flaky tests",
                    "reason": f"{factor['value']} flaky tests detected"
                })
            
            elif factor["factor"] == "security_vulnerabilities":
                recommendations.append({
                    "type": "security",
                    "priority": "high",
                    "action": "Address security vulnerabilities",
                    "reason": f"{factor['value']} vulnerabilities found"
                })
        
        # General recommendations
        if features.get("deployment_frequency", 1) < 0.5:  # Less than every 2 days
            recommendations.append({
                "type": "process",
                "priority": "low",
                "action": "Consider increasing deployment frequency",
                "reason": "More frequent deployments reduce risk"
            })
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    async def train_model(self, training_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Train the failure prediction model."""
        logger.info("Starting failure prediction model training", samples=len(training_data))
        
        try:
            # Prepare training data
            X, y = await self._prepare_training_data(training_data)
            
            if len(X) < self.settings.MIN_TRAINING_SAMPLES:
                raise ValueError(f"Insufficient training data: {len(X)} samples")
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Convert to tensors
            X_train_tensor = torch.FloatTensor(X_train_scaled).to(self.device)
            y_train_tensor = torch.FloatTensor(y_train.reshape(-1, 1)).to(self.device)
            X_test_tensor = torch.FloatTensor(X_test_scaled).to(self.device)
            y_test_tensor = torch.FloatTensor(y_test.reshape(-1, 1)).to(self.device)
            
            # Create data loaders
            train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
            train_loader = DataLoader(train_dataset, batch_size=self.config["training"]["batch_size"], shuffle=True)
            
            # Initialize model
            architecture = self.config["architecture"]
            self.model = FailurePredictionNetwork(
                input_size=len(self.feature_names),
                hidden_layers=architecture["hidden_layers"],
                dropout=architecture["dropout"]
            ).to(self.device)
            
            # Training setup
            criterion = nn.BCELoss()
            optimizer = optim.Adam(
                self.model.parameters(),
                lr=self.config["training"]["learning_rate"],
                weight_decay=self.config["training"]["weight_decay"]
            )
            
            # Training loop
            best_loss = float('inf')
            patience_counter = 0
            patience = self.config["training"]["early_stopping_patience"]
            
            for epoch in range(self.config["training"]["epochs"]):
                # Training phase
                self.model.train()
                train_loss = 0.0
                
                for batch_X, batch_y in train_loader:
                    optimizer.zero_grad()
                    outputs = self.model(batch_X)
                    loss = criterion(outputs, batch_y)
                    loss.backward()
                    optimizer.step()
                    train_loss += loss.item()
                
                # Validation phase
                self.model.eval()
                with torch.no_grad():
                    val_outputs = self.model(X_test_tensor)
                    val_loss = criterion(val_outputs, y_test_tensor)
                
                # Early stopping
                if val_loss < best_loss:
                    best_loss = val_loss
                    patience_counter = 0
                    await self._save_model()  # Save best model
                else:
                    patience_counter += 1
                    if patience_counter >= patience:
                        logger.info(f"Early stopping at epoch {epoch}")
                        break
                
                if epoch % 10 == 0:
                    logger.info(f"Epoch {epoch}: train_loss={train_loss/len(train_loader):.4f}, val_loss={val_loss:.4f}")
            
            # Evaluate model
            self.model.eval()
            with torch.no_grad():
                y_pred_proba = self.model(X_test_tensor).cpu().numpy().flatten()
                y_pred = (y_pred_proba > 0.5).astype(int)
            
            # Calculate metrics
            precision = precision_score(y_test, y_pred)
            recall = recall_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)
            auc = roc_auc_score(y_test, y_pred_proba)
            
            # Update model state
            self.is_trained = True
            self.last_training_time = datetime.utcnow()
            self.model_metrics = {
                "precision": precision,
                "recall": recall,
                "f1_score": f1,
                "auc_score": auc
            }
            
            logger.info(
                "Model training completed",
                precision=precision,
                recall=recall,
                f1_score=f1,
                auc_score=auc
            )
            
            return self.model_metrics
            
        except Exception as e:
            logger.error("Model training failed", error=str(e))
            raise
    
    async def _prepare_training_data(self, training_data: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data for model training."""
        features_list = []
        targets = []
        
        for data_point in training_data:
            # Extract features
            features = await self._extract_features(data_point["metrics"])
            feature_vector = self._prepare_feature_vector(features)
            
            features_list.append(feature_vector)
            targets.append(1.0 if data_point["failed"] else 0.0)
        
        return np.array(features_list), np.array(targets)
    
    def _prepare_feature_vector(self, features: Dict[str, float]) -> List[float]:
        """Prepare feature vector from feature dictionary."""
        return [features.get(col, 0.0) for col in self.feature_names]
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend in a series of values."""
        if len(values) < 2:
            return 0.0
        
        x = np.arange(len(values))
        y = np.array(values)
        
        # Simple linear regression slope
        try:
            slope = np.polyfit(x, y, 1)[0]
            return slope
        except:
            return 0.0
    
    def _encode_time_of_day(self, timestamp: Optional[str]) -> float:
        """Encode time of day as cyclic feature."""
        if not timestamp:
            return 0.0
        
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            # Convert to 0-1 scale
            return dt.hour / 24.0
        except:
            return 0.0
    
    def _encode_day_of_week(self, timestamp: Optional[str]) -> float:
        """Encode day of week as cyclic feature."""
        if not timestamp:
            return 0.0
        
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            # Convert to 0-1 scale (Monday=0, Sunday=6)
            return dt.weekday() / 6.0
        except:
            return 0.0
    
    def _is_weekend(self, timestamp: Optional[str]) -> float:
        """Check if timestamp is weekend."""
        if not timestamp:
            return 0.0
        
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return 1.0 if dt.weekday() >= 5 else 0.0  # Saturday=5, Sunday=6
        except:
            return 0.0
    
    async def _calculate_confidence(self, features: Dict[str, float], probability: float) -> float:
        """Calculate prediction confidence."""
        base_confidence = 0.8
        
        # Reduce confidence for edge cases
        if probability < 0.05 or probability > 0.95:
            base_confidence *= 0.8
        
        # Adjust based on data quality
        if features.get("failure_rate_7d", 0) == 0:  # No historical data
            base_confidence *= 0.7
        
        return min(1.0, base_confidence)
    
    def _get_model_version(self) -> str:
        """Get current model version."""
        if self.last_training_time:
            return f"v{self.last_training_time.strftime('%Y%m%d_%H%M%S')}"
        return "v0.0.0"
    
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
            model_path = Path(self.settings.MODEL_STORAGE_PATH) / "failure_predictor"
            model_path.mkdir(parents=True, exist_ok=True)
            
            # Save model state dict
            torch.save(self.model.state_dict(), model_path / "model.pth")
            
            # Save scaler
            with open(model_path / "scaler.pkl", "wb") as f:
                pickle.dump(self.scaler, f)
            
            # Save metadata
            metadata = {
                "feature_names": self.feature_names,
                "model_metrics": self.model_metrics,
                "training_time": self.last_training_time.isoformat() if self.last_training_time else None,
                "config": self.config
            }
            
            with open(model_path / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)
            
            logger.info("Model saved successfully", path=str(model_path))
            
        except Exception as e:
            logger.error("Failed to save model", error=str(e))
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the failure predictor."""
        return {
            "service": "failure_predictor",
            "status": "healthy",
            "model_trained": self.is_trained,
            "device": str(self.device),
            "last_training": self.last_training_time.isoformat() if self.last_training_time else None,
            "model_metrics": self.model_metrics
        }