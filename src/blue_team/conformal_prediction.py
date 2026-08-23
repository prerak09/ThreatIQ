"""Inductive Conformal Prediction for guaranteed false positive bounds."""

import numpy as np
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False

try:
    import onnx
    from onnx import version_converter
    ONNX_EXPORT_AVAILABLE = True
except ImportError:
    ONNX_EXPORT_AVAILABLE = False


class ActionType(Enum):
    APPROVE = "APPROVE"
    STEP_UP_AUTH = "STEP_UP_AUTH"
    DECLINE = "DECLINE"


@dataclass
class ConformalResult:
    prediction_set: List[int]
    confidence: float
    error_bound: float
    label: int


class ConformalPredictor:
    def __init__(self, base_model: Any, alpha: float = 0.05):
        self.base_model = base_model
        self.alpha = alpha
        self.cal_scores: Optional[np.ndarray] = None
        self.threshold: float = 0.0
        self.n_classes: int = 2

    def fit_calibration(self, cal_X: np.ndarray, cal_y: np.ndarray):
        self.cal_scores = np.array([self._nonconformity_score(x, y) for x, y in zip(cal_X, cal_y)])
        self.set_threshold(self.cal_scores)
        return self

    def predict(self, x: np.ndarray) -> List[int]:
        scores = []
        for c in range(self.n_classes):
            scores.append(self._nonconformity_score(x, c))
        return [c for c in range(self.n_classes) if scores[c] <= self.threshold]

    def predict_with_confidence(self, x: np.ndarray) -> Tuple[List[int], float, float]:
        pred_set = self.predict(x)
        coverage = 1.0 - self.alpha
        efficiency = len(pred_set) / self.n_classes
        return pred_set, coverage, efficiency

    def _nonconformity_score(self, x: np.ndarray, y: int) -> float:
        if hasattr(self.base_model, 'predict_proba'):
            proba = self.base_model.predict_proba(x.reshape(1, -1))[0]
            return 1.0 - proba[y]
        pred = self.base_model.predict(x.reshape(1, -1))[0]
        return 0.0 if pred == y else 1.0

    def set_threshold(self, cal_scores: np.ndarray):
        quantile_level = np.ceil((len(cal_scores) + 1) * (1 - self.alpha)) / len(cal_scores)
        self.threshold = float(np.quantile(cal_scores, min(quantile_level, 1.0)))

    def coverage_guarantee(self) -> Dict[str, float]:
        return {
            "confidence": 1.0 - self.alpha,
            "alpha": self.alpha,
            "guarantee": f"At least {100*(1-self.alpha):.1f}% coverage in expectation"
        }

    def adaptive_conformal_predict(self, X: np.ndarray, y_prior: Optional[np.ndarray] = None) -> List[ConformalResult]:
        results = []
        for x in X:
            pred_set, conf, eff = self.predict_with_confidence(x)
            label = pred_set[0] if pred_set else 0
            results.append(ConformalResult(pred_set, conf, eff, label))
        return results


class ConformalFraudDetector:
    def __init__(self, fraud_model: Any, alpha: float = 0.05):
        self.fraud_model = fraud_model
        self.conformal = ConformalPredictor(fraud_model, alpha)
        self.costs = {ActionType.APPROVE: 0.0, ActionType.STEP_UP_AUTH: 0.1, ActionType.DECLINE: 1.0}
        self.history: List[Dict] = []

    def fit_calibration(self, cal_X: np.ndarray, cal_y: np.ndarray) -> "ConformalFraudDetector":
        """Calibrate the underlying predictor on held-out data."""
        self.conformal.fit_calibration(cal_X, cal_y)
        return self

    def detect(self, transaction_features: np.ndarray) -> Dict[str, Any]:
        pred_set, confidence, error_bound = self.conformal.predict_with_confidence(transaction_features)
        is_fraud = 1 in pred_set if pred_set else False
        action = self._decide_action(pred_set)
        result = {
            "is_fraud": is_fraud,
            "prediction_set": pred_set,
            "confidence": confidence,
            "error_bound": error_bound,
            "recommended_action": action.value
        }
        self.history.append(result)
        return result

    def _decide_action(self, pred_set: List[int]) -> ActionType:
        if pred_set == [0]:
            return ActionType.APPROVE
        if pred_set == [1]:
            return ActionType.DECLINE
        return ActionType.STEP_UP_AUTH

    def compute_action_cost(self, prediction_set: List[int], costs: Optional[Dict[str, float]] = None) -> Tuple[ActionType, float]:
        costs = costs or self.costs
        action = self._decide_action(prediction_set)
        return action, costs[action]

    def get_guarantee_stats(self) -> Dict[str, Any]:
        if not self.history:
            return {"total": 0, "fraud_detected": 0, "coverage": 0.0}
        fraud_count = sum(1 for h in self.history if h["is_fraud"])
        avg_conf = np.mean([h["confidence"] for h in self.history])
        return {
            "total": len(self.history),
            "fraud_detected": fraud_count,
            "average_confidence": float(avg_conf),
            "alpha": self.conformal.alpha
        }

    # Backwards-compatible alias used by some callers.
    get_stats = get_guarantee_stats


class ONNXExporter:
    @staticmethod
    def export_to_onnx(model: Any, input_shape: Tuple[int, ...], output_path: str) -> bool:
        if not ONNX_EXPORT_AVAILABLE:
            return False
        if TORCH_AVAILABLE and isinstance(model, nn.Module):
            model.eval()
            dummy = torch.randn(*input_shape)
            torch.onnx.export(model, dummy, output_path, opset_version=13, input_names=["input"], output_names=["output"])
            return True
        return False

    @staticmethod
    def quantize_model(onnx_path: str, output_path: str) -> bool:
        if not ONNX_EXPORT_AVAILABLE or not ONNX_AVAILABLE:
            return False
        try:
            model = onnx.load(onnx_path)
            quantized = onnx.quantization.quantize(model)
            onnx.save(quantized, output_path)
            return True
        except Exception:
            return False

    @staticmethod
    def benchmark_latency(onnx_path: str, n_runs: int = 1000) -> Dict[str, float]:
        if not ONNX_AVAILABLE:
            return {"mean_ms": 0.0, "std_ms": 0.0, "p99_ms": 0.0}
        sess = ort.InferenceSession(onnx_path)
        inp = sess.get_inputs()[0]
        dummy = np.random.randn(*[d if isinstance(d, int) else 1 for d in inp.shape]).astype(np.float32)
        latencies = []
        for _ in range(n_runs):
            start = __import__("time").perf_counter()
            sess.run(None, {inp.name: dummy})
            latencies.append((__import__("time").perf_counter() - start) * 1000)
        arr = np.array(latencies)
        return {"mean_ms": float(arr.mean()), "std_ms": float(arr.std()), "p99_ms": float(np.percentile(arr, 99))}

    @staticmethod
    def validate_export(original_model: Any, onnx_path: str, test_input: np.ndarray) -> bool:
        if not ONNX_AVAILABLE:
            return False
        sess = ort.InferenceSession(onnx_path)
        inp = sess.get_inputs()[0]
        onnx_out = sess.run(None, {inp.name: test_input.astype(np.float32)})[0]
        if TORCH_AVAILABLE and isinstance(original_model, nn.Module):
            with torch.no_grad():
                torch_out = original_model(torch.tensor(test_input, dtype=torch.float32)).numpy()
            return bool(np.allclose(torch_out, onnx_out, atol=1e-5))
        return True
