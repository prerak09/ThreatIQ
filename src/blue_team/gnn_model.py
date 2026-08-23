"""Dual-engine fraud detection model with optional GNN support.

Provides FraudDetectionModel combining Isolation Forest (fast anomaly
screening) with XGBoost (high-precision classification) and optional
LightGBM and Graph Neural Network engines.
"""

from __future__ import annotations

import json
import logging
import os
import pickle
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import (
        precision_score,
        recall_score,
        roc_auc_score,
        f1_score,
    )
except ImportError as exc:
    raise ImportError(
        "scikit-learn is required: pip install scikit-learn"
    ) from exc

try:
    import xgboost as xgb
except ImportError:
    xgb = None

try:
    import lightgbm as lgb
except ImportError:
    lgb = None

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch_geometric.nn import GCNConv, global_mean_pool
    from torch_geometric.data import Data, Batch

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class PredictionResult:
    """Structured output from fraud prediction."""

    transaction_id: str
    fraud_probability: float
    is_fraud: bool
    engine_scores: Dict[str, float] = field(default_factory=dict)
    latency_ms: float = 0.0
    model_version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a JSON-compatible dictionary."""
        return asdict(self)


# ---------------------------------------------------------------------------
# Graph Neural Network (optional)
# ---------------------------------------------------------------------------

if TORCH_AVAILABLE:

    class TransactionGNN(nn.Module):
        """Graph convolutional network for transaction-relationship analysis.

        Nodes represent entities (cards, IPs, devices) and edges represent
        shared transaction links. The model learns embeddings that capture
        structural fraud patterns.
        """

        def __init__(
            self,
            in_channels: int,
            hidden_channels: int = 64,
            out_channels: int = 32,
            num_classes: int = 2,
            dropout: float = 0.3,
        ) -> None:
            super().__init__()
            self.conv1 = GCNConv(in_channels, hidden_channels)
            self.conv2 = GCNConv(hidden_channels, hidden_channels)
            self.conv3 = GCNConv(hidden_channels, out_channels)
            self.classifier = nn.Linear(out_channels, num_classes)
            self.dropout = dropout

        def forward(
            self,
            x: torch.Tensor,
            edge_index: torch.Tensor,
            batch: Optional[torch.Tensor] = None,
        ) -> torch.Tensor:
            """Forward pass through GCN layers."""
            x = F.relu(self.conv1(x, edge_index))
            x = F.dropout(x, p=self.dropout, training=self.training)
            x = F.relu(self.conv2(x, edge_index))
            x = F.dropout(x, p=self.dropout, training=self.training)
            x = self.conv3(x, edge_index)

            if batch is not None:
                x = global_mean_pool(x, batch)

            return self.classifier(x)

else:
    TransactionGNN = None  # type: ignore[misc,assignment]


# ---------------------------------------------------------------------------
# Fraud Detection Model
# ---------------------------------------------------------------------------


class FraudDetectionModel:
    """Dual-engine fraud detection combining anomaly detection and classification.

    Architecture
    ------------
    1. **Isolation Forest** – unsupervised anomaly flag in < 15 ms.
    2. **XGBoost** – high-precision supervised classifier.
    3. *(optional)* **LightGBM** – second gradient-boosted engine.
    4. *(optional)* **TransactionGNN** – graph-based feature extractor.

    Parameters
    ----------
    contamination : float
        Expected fraction of fraud in training data for Isolation Forest.
    xgb_params : dict | None
        Custom XGBoost hyper-parameters.
    lgb_params : dict | None
        Custom LightGBM hyper-parameters.
    use_gnn : bool
        Whether to attach a GNN feature head (requires PyTorch Geometric).
    gnn_in_channels : int
        Input feature dimension for the GNN.
    model_dir : str | Path
        Directory used by save_model / load_model.
    """

    def __init__(
        self,
        contamination: float = 0.01,
        xgb_params: Optional[Dict[str, Any]] = None,
        lgb_params: Optional[Dict[str, Any]] = None,
        use_gnn: bool = False,
        gnn_in_channels: int = 16,
        model_dir: Union[str, Path] = "models",
    ) -> None:
        self.contamination = contamination
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

        # Scalability
        self._scaler = StandardScaler()
        self._fitted = False

        # --- Isolation Forest (fast path) ---
        self._iforest = IsolationForest(
            contamination=contamination,
            n_estimators=200,
            max_samples="auto",
            random_state=42,
            n_jobs=-1,
        )

        # --- XGBoost ---
        default_xgb = {
            "n_estimators": 300,
            "max_depth": 6,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "scale_pos_weight": 10,
            "eval_metric": "auc",
            "early_stopping_rounds": 50,
            "random_state": 42,
            "n_jobs": -1,
        }
        if xgb_params:
            default_xgb.update(xgb_params)
        self._xgb_params = default_xgb
        self._xgb_model: Optional[Any] = None

        # --- LightGBM (optional) ---
        self._use_lgb = lgb is not None and lgb_params is not False
        default_lgb = {
            "n_estimators": 300,
            "max_depth": 6,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "is_unbalance": True,
            "random_state": 42,
            "n_jobs": -1,
            "verbose": -1,
        }
        if isinstance(lgb_params, dict):
            default_lgb.update(lgb_params)
        self._lgb_params = default_lgb
        self._lgb_model: Optional[Any] = None

        # --- GNN (optional) ---
        self._use_gnn = use_gnn and TORCH_AVAILABLE and TransactionGNN is not None
        self._gnn_model: Optional[Any] = None
        self._gnn_in_channels = gnn_in_channels
        if self._use_gnn:
            self._gnn_model = TransactionGNN(
                in_channels=gnn_in_channels,
                hidden_channels=64,
                out_channels=32,
            )
            self._gnn_model.eval()

        # Metadata
        self._version = "1.0"
        self._training_time: float = 0.0
        self._feature_names: List[str] = []

        # Isolation Forest score calibration range (captured on training data
        # so single-sample predictions are normalised consistently).
        self._if_lo: float = 0.0
        self._if_hi: float = 1.0

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(
        self,
        X: np.ndarray,
        y: Optional[np.ndarray] = None,
        feature_names: Optional[List[str]] = None,
        xgb_eval_pct: float = 0.1,
    ) -> Dict[str, Any]:
        """Fit all enabled engines.

        Parameters
        ----------
        X : np.ndarray
            Training features of shape ``(n_samples, n_features)``.
        y : np.ndarray | None
            Binary labels (1 = fraud).  Required for XGBoost / LightGBM.
        feature_names : list[str] | None
            Names for interpretability.
        xgb_eval_pct : float
            Fraction of data used as XGBoost eval set for early stopping.

        Returns
        -------
        dict
            Training summary (timings, metrics).
        """
        t0 = time.perf_counter()
        self._feature_names = feature_names or [
            f"f{i}" for i in range(X.shape[1])
        ]

        X_scaled = self._scaler.fit_transform(X)

        # Shuffle so the XGBoost eval split is not biased by row ordering.
        rng = np.random.default_rng(42)
        order = rng.permutation(len(X_scaled))
        X_shuffled = X_scaled[order]
        y_shuffled = y[order] if y is not None else None

        # 1) Isolation Forest — calibrate score normalisation on training data
        logger.info("Fitting Isolation Forest …")
        self._iforest.fit(X_shuffled)
        raw_train = self._iforest.decision_function(X_shuffled)
        self._if_lo = float(raw_train.min())
        self._if_hi = float(raw_train.max())

        # 2) XGBoost
        metrics: Dict[str, Any] = {}
        if y is not None and xgb is not None:
            logger.info("Fitting XGBoost …")
            n_eval = max(1, int(len(X_shuffled) * xgb_eval_pct))
            X_tr, X_ev = X_shuffled[:-n_eval], X_shuffled[-n_eval:]
            if y_shuffled is None:
                y_tr, y_ev = None, None
            else:
                y_tr, y_ev = y_shuffled[:-n_eval], y_shuffled[-n_eval:]

            self._xgb_model = xgb.XGBClassifier(**self._xgb_params)
            self._xgb_model.fit(
                X_tr,
                y_tr,
                eval_set=[(X_ev, y_ev)],
                verbose=False,
            )
            y_pred = self._xgb_model.predict(X_ev)
            y_proba = self._xgb_model.predict_proba(X_ev)[:, 1]
            metrics["xgb_precision"] = float(precision_score(y_ev, y_pred, zero_division=0))
            metrics["xgb_recall"] = float(recall_score(y_ev, y_pred, zero_division=0))
            metrics["xgb_f1"] = float(f1_score(y_ev, y_pred, zero_division=0))
            try:
                metrics["xgb_auc"] = float(roc_auc_score(y_ev, y_proba))
            except ValueError:
                metrics["xgb_auc"] = 0.0

        # 3) LightGBM
        if y is not None and self._use_lgb and lgb is not None:
            logger.info("Fitting LightGBM …")
            self._lgb_model = lgb.LGBMClassifier(**self._lgb_params)
            self._lgb_model.fit(X_scaled, y)

        self._fitted = True
        self._training_time = time.perf_counter() - t0
        metrics["training_seconds"] = round(self._training_time, 3)
        metrics["n_samples"] = len(X)
        metrics["n_features"] = X.shape[1]
        logger.info("Training completed in %.2f s", self._training_time)
        return metrics

    # ------------------------------------------------------------------
    # Prediction helpers
    # ------------------------------------------------------------------

    def _score_isolation_forest(self, X: np.ndarray) -> np.ndarray:
        """Return anomaly scores in [0, 1] (higher = more anomalous).

        Normalisation uses the min/max decision_function range captured on
        the *training* data, so scores are consistent regardless of how many
        samples are scored at once.
        """
        raw = self._iforest.decision_function(X)
        lo, hi = self._if_lo, self._if_hi
        span = (hi - lo) if hi > lo else 1e-12
        return np.clip(1.0 - (raw - lo) / span, 0.0, 1.0)

    def _score_xgb(self, X: np.ndarray) -> Optional[np.ndarray]:
        if self._xgb_model is None:
            return None
        return self._xgb_model.predict_proba(X)[:, 1]

    def _score_lgb(self, X: np.ndarray) -> Optional[np.ndarray]:
        if self._lgb_model is None:
            return None
        return self._lgb_model.predict_proba(X)[:, 1]

    def _score_gnn(
        self, X: np.ndarray, edge_index: Optional[np.ndarray] = None
    ) -> Optional[np.ndarray]:
        """Run GNN if a graph structure is provided."""
        if not self._use_gnn or self._gnn_model is None:
            return None
        if edge_index is None:
            # Fallback: use a simple fully-connected graph
            n = X.shape[0]
            src = np.repeat(np.arange(n), n - 1)
            dst = np.tile(np.delete(np.arange(n), 0), n)
            edge_index = np.stack([src, dst], axis=0)

        if not TORCH_AVAILABLE:
            return None

        self._gnn_model.eval()
        with torch.no_grad():
            x_t = torch.tensor(X, dtype=torch.float32)
            ei_t = torch.tensor(edge_index, dtype=torch.long)
            out = self._gnn_model(x_t, ei_t)
            proba = F.softmax(out, dim=-1)[:, 1].numpy()
        return proba

    def _ensemble_score(
        self, scores: Dict[str, np.ndarray], weights: Optional[Dict[str, float]] = None
    ) -> np.ndarray:
        """Weighted average of available engine scores."""
        if weights is None:
            weights = {"iforest": 0.2, "xgb": 0.4, "lgb": 0.25, "gnn": 0.15}

        total_w = 0.0
        combined: Optional[np.ndarray] = None
        for name, score in scores.items():
            if score is None:
                continue
            w = weights.get(name, 0.25)
            if combined is None:
                combined = score * w
            else:
                combined = combined + score * w
            total_w += w

        if combined is None:
            raise RuntimeError("No engine produced scores")

        return combined / (total_w + 1e-12)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def predict(
        self,
        features: np.ndarray,
        threshold: float = 0.5,
        edge_index: Optional[np.ndarray] = None,
        transaction_id: str = "unknown",
    ) -> PredictionResult:
        """Score a single transaction.

        Parameters
        ----------
        features : np.ndarray
            Feature vector of shape ``(1, n_features)`` or ``(n_features,)``.
        threshold : float
            Ensemble probability threshold for fraud label.
        edge_index : np.ndarray | None
            Graph edges for the GNN engine.
        transaction_id : str
            Identifier carried through to the result.

        Returns
        -------
        PredictionResult
        """
        if not self._fitted:
            raise RuntimeError("Model has not been trained. Call train() first.")

        x = features.reshape(1, -1) if features.ndim == 1 else features
        t0 = time.perf_counter()

        X_scaled = self._scaler.transform(x)

        engine_scores: Dict[str, float] = {}
        score_map: Dict[str, np.ndarray] = {}

        iforest_score = self._score_isolation_forest(X_scaled)
        score_map["iforest"] = iforest_score
        engine_scores["iforest"] = float(iforest_score[0])

        xgb_score = self._score_xgb(X_scaled)
        if xgb_score is not None:
            score_map["xgb"] = xgb_score
            engine_scores["xgb"] = float(xgb_score[0])

        lgb_score = self._score_lgb(X_scaled)
        if lgb_score is not None:
            score_map["lgb"] = lgb_score
            engine_scores["lgb"] = float(lgb_score[0])

        gnn_score = self._score_gnn(X_scaled, edge_index)
        if gnn_score is not None:
            score_map["gnn"] = gnn_score
            engine_scores["gnn"] = float(gnn_score[0])

        ensemble = self._ensemble_score(score_map)
        proba = float(ensemble[0])
        latency = (time.perf_counter() - t0) * 1000

        return PredictionResult(
            transaction_id=transaction_id,
            fraud_probability=proba,
            is_fraud=proba >= threshold,
            engine_scores=engine_scores,
            latency_ms=round(latency, 3),
            model_version=self._version,
        )

    def predict_proba(self, features: np.ndarray, edge_index: Optional[np.ndarray] = None) -> np.ndarray:
        """Ensemble fraud probabilities for sklearn-style consumption.

        Parameters
        ----------
        features : np.ndarray
            Feature matrix ``(n_samples, n_features)`` or a single vector.
        edge_index : np.ndarray | None
            Optional graph edges for the GNN engine.

        Returns
        -------
        np.ndarray
            Class probabilities of shape ``(n_samples, 2)`` —
            column 0 = legitimate, column 1 = fraud.
        """
        if not self._fitted:
            raise RuntimeError("Model has not been trained. Call train() first.")

        X = features.reshape(1, -1) if features.ndim == 1 else features
        X_scaled = self._scaler.transform(X)

        score_map: Dict[str, np.ndarray] = {
            "iforest": self._score_isolation_forest(X_scaled)
        }
        for scorer in (self._score_xgb, self._score_lgb):
            s = scorer(X_scaled)
            if s is not None:
                score_map["xgb" if scorer is self._score_xgb else "lgb"] = s
        gnn_score = self._score_gnn(X_scaled, edge_index)
        if gnn_score is not None:
            score_map["gnn"] = gnn_score

        fraud_proba = self._ensemble_score(score_map)
        fraud_proba = np.clip(fraud_proba, 0.0, 1.0)
        return np.stack([1.0 - fraud_proba, fraud_proba], axis=1)

    def predict_batch(
        self,
        features: np.ndarray,
        threshold: float = 0.5,
        transaction_ids: Optional[List[str]] = None,
    ) -> List[PredictionResult]:
        """Score a batch of transactions.

        Parameters
        ----------
        features : np.ndarray
            Feature matrix ``(n_samples, n_features)``.
        threshold : float
            Fraud probability threshold.
        transaction_ids : list[str] | None
            One id per row.

        Returns
        -------
        list[PredictionResult]
        """
        if not self._fitted:
            raise RuntimeError("Model has not been trained. Call train() first.")

        n = features.shape[0]
        if transaction_ids is None:
            transaction_ids = [f"txn_{i}" for i in range(n)]

        t0 = time.perf_counter()
        X_scaled = self._scaler.transform(features)

        score_map: Dict[str, np.ndarray] = {}

        iforest_score = self._score_isolation_forest(X_scaled)
        score_map["iforest"] = iforest_score

        xgb_score = self._score_xgb(X_scaled)
        if xgb_score is not None:
            score_map["xgb"] = xgb_score

        lgb_score = self._score_lgb(X_scaled)
        if lgb_score is not None:
            score_map["lgb"] = lgb_score

        ensemble = self._ensemble_score(score_map)
        latency = (time.perf_counter() - t0) * 1000

        results: List[PredictionResult] = []
        for i in range(n):
            engine_scores: Dict[str, float] = {}
            for name, arr in score_map.items():
                engine_scores[name] = float(arr[i])

            results.append(
                PredictionResult(
                    transaction_id=transaction_ids[i],
                    fraud_probability=float(ensemble[i]),
                    is_fraud=float(ensemble[i]) >= threshold,
                    engine_scores=engine_scores,
                    latency_ms=round(latency / n, 3),
                    model_version=self._version,
                )
            )
        return results

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save_model(self, path: Optional[Union[str, Path]] = None) -> Path:
        """Serialise the entire model to disk.

        Parameters
        ----------
        path : str | Path | None
            File path. Defaults to ``<model_dir>/fraud_model.pkl``.

        Returns
        -------
        Path
            Actual path written.
        """
        if path is None:
            path = self.model_dir / "fraud_model.pkl"
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        state = {
            "version": self._version,
            "contamination": self.contamination,
            "scaler": self._scaler,
            "iforest": self._iforest,
            "if_lo": self._if_lo,
            "if_hi": self._if_hi,
            "xgb_model": self._xgb_model,
            "lgb_model": self._lgb_model,
            "xgb_params": self._xgb_params,
            "lgb_params": self._lgb_params,
            "use_gnn": self._use_gnn,
            "gnn_in_channels": self._gnn_in_channels,
            "fitted": self._fitted,
            "feature_names": self._feature_names,
        }

        with open(path, "wb") as fh:
            pickle.dump(state, fh, protocol=pickle.HIGHEST_PROTOCOL)
        logger.info("Model saved to %s", path)

        # Also save sidecar metadata
        meta_path = path.with_suffix(".meta.json")
        meta_path.write_text(
            json.dumps(
                {
                    "version": self._version,
                    "fitted": self._fitted,
                    "n_features": len(self._feature_names),
                },
                indent=2,
            )
        )
        return path

    def load_model(self, path: Optional[Union[str, Path]] = None) -> None:
        """Deserialise a previously saved model.

        Parameters
        ----------
        path : str | Path | None
            File path. Defaults to ``<model_dir>/fraud_model.pkl``.
        """
        if path is None:
            path = self.model_dir / "fraud_model.pkl"
        path = Path(path)

        with open(path, "rb") as fh:
            state = pickle.load(fh)  # noqa: S301

        self._version = state["version"]
        self.contamination = state["contamination"]
        self._scaler = state["scaler"]
        self._iforest = state["iforest"]
        self._if_lo = state.get("if_lo", 0.0)
        self._if_hi = state.get("if_hi", 1.0)
        self._xgb_model = state["xgb_model"]
        self._lgb_model = state["lgb_model"]
        self._xgb_params = state["xgb_params"]
        self._lgb_params = state["lgb_params"]
        self._use_gnn = state["use_gnn"]
        self._gnn_in_channels = state["gnn_in_channels"]
        self._fitted = state["fitted"]
        self._feature_names = state["feature_names"]
        logger.info("Model loaded from %s (version %s)", path, self._version)
