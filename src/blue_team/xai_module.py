"""Explainable AI module for fraud detection decisions.

Provides SHAP-based explanations, human-readable narratives, and
FinCEN-compliant SAR (Suspicious Activity Report) generation.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

try:
    import shap as _shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    _shap = None

try:
    from sklearn.inspection import permutation_importance as _perm_importance
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


# ---------------------------------------------------------------------------
# 1. SHAPExplainer
# ---------------------------------------------------------------------------

class SHAPExplainer:
    """SHAP wrapper with permutation-importance fallback."""

    def __init__(self, model: Any, background_data: Optional[np.ndarray] = None) -> None:
        self.model = model
        self.background_data = background_data
        self._explainer: Any = None
        self._use_shap = False
        if SHAP_AVAILABLE and _shap is not None:
            try:
                if background_data is not None:
                    self._explainer = _shap.KernelExplainer(
                        model.predict_proba, background_data[:100])
                elif hasattr(model, "predict_proba"):
                    self._explainer = _shap.TreeExplainer(model)
                self._use_shap = self._explainer is not None
            except Exception:
                logger.warning("SHAP init failed, using permutation fallback")

    def explain_prediction(self, features: np.ndarray,
                           feature_names: Optional[List[str]] = None) -> np.ndarray:
        """Compute feature importance for a single prediction.

        Returns a 1-D array with one attribution per feature. SHAP's output
        shape depends on version and model type — a list per class in older
        releases, and ``(n_samples, n_features, n_classes)`` in newer ones for
        binary classifiers. Returning that unreduced produced a 2-D array and
        made every downstream call (`get_top_features`, waterfall, force plot,
        SAR generation) raise ``TypeError: only integer scalar arrays can be
        converted to a scalar index``.
        """
        x = features.reshape(1, -1) if features.ndim == 1 else features
        if self._use_shap and self._explainer is not None:
            try:
                return self._to_1d(self._explainer.shap_values(x), x.shape[1])
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("SHAP explanation failed (%s); using permutation fallback", exc)
        return np.asarray(self._permutation_fallback(x)).reshape(-1)[: x.shape[1]]

    @staticmethod
    def _to_1d(vals: Any, n_features: int) -> np.ndarray:
        """Reduce any SHAP output shape to one attribution per feature."""
        # Older SHAP: list of per-class arrays. Take the positive class.
        if isinstance(vals, list):
            vals = vals[1] if len(vals) > 1 else vals[0]
        arr = np.asarray(vals, dtype=float)

        # (n_samples, n_features, n_classes) -> positive class of first sample
        if arr.ndim == 3:
            arr = arr[0, :, -1]
        # (n_samples, n_features) -> first sample
        elif arr.ndim == 2:
            arr = arr[0] if arr.shape[0] == 1 else arr[:, -1]
        arr = arr.reshape(-1)

        if arr.size != n_features:
            arr = np.resize(arr, n_features)
        return arr

    def explain_batch(self, X_batch: np.ndarray,
                      feature_names: Optional[List[str]] = None) -> np.ndarray:
        """Compute feature importance for a batch."""
        if self._use_shap and self._explainer is not None:
            try:
                vals = self._explainer.shap_values(X_batch)
                if isinstance(vals, list):
                    vals = vals[1] if len(vals) > 1 else vals[0]
                arr = np.asarray(vals, dtype=float)
                if arr.ndim == 3:          # (n, features, classes)
                    arr = arr[:, :, -1]
                return arr
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("SHAP batch explanation failed (%s); using fallback", exc)
        return self._permutation_fallback(X_batch)

    def get_top_features(self, shap_values: np.ndarray,
                         feature_names: Optional[List[str]] = None,
                         n: int = 10) -> List[Tuple[str, float]]:
        """Return top-n features by absolute importance."""
        vals = np.asarray(shap_values, dtype=float).reshape(-1)
        if feature_names is None:
            feature_names = [f"f{i}" for i in range(len(vals))]
        indices = np.argsort(np.abs(vals))[::-1][:n]
        return [(feature_names[int(i)], float(vals[int(i)])) for i in indices
                if int(i) < len(feature_names)]

    def plot_waterfall(self, shap_values: np.ndarray,
                       feature_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Return waterfall plot data dict for JS visualization."""
        vals = np.asarray(shap_values, dtype=float).reshape(-1)
        if feature_names is None:
            feature_names = [f"f{i}" for i in range(len(vals))]
        sorted_idx = [int(i) for i in np.argsort(np.abs(vals))[::-1]
                      if int(i) < len(feature_names)]
        return {"features": [feature_names[i] for i in sorted_idx],
                "values": [float(vals[i]) for i in sorted_idx],
                "base_value": 0.0}

    def plot_force(self, shap_values: np.ndarray,
                   feature_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """Return force plot data dict for JS visualization."""
        vals = np.asarray(shap_values, dtype=float).reshape(-1)
        if feature_names is None:
            feature_names = [f"f{i}" for i in range(len(vals))]
        n = min(len(vals), len(feature_names))
        return {"features": {feature_names[i]: float(vals[i]) for i in range(n)},
                "base_value": 0.0}

    def _permutation_fallback(self, X: np.ndarray) -> np.ndarray:
        """Fallback: permutation importance or mean-absolute heuristic."""
        if SKLEARN_AVAILABLE and hasattr(self.model, "predict"):
            try:
                result = _perm_importance(self.model, X, n_repeats=5, random_state=42)
                return result.importances_mean
            except Exception:
                pass
        return np.mean(np.abs(X), axis=0) if X.ndim == 2 else np.abs(X)


# ---------------------------------------------------------------------------
# 2. FraudExplanation
# ---------------------------------------------------------------------------
@dataclass
class FraudExplanation:
    """Structured explanation for a fraud prediction."""
    transaction_id: str
    is_fraud: bool
    confidence: float
    top_features: List[Tuple[str, float]] = field(default_factory=list)
    explanation_text: str = ""
    recommended_action: str = "MONITOR"
    risk_factors: List[Dict[str, str]] = field(default_factory=list)
    graph_context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to a JSON-compatible dictionary."""
        return asdict(self)

    def to_narrative(self) -> str:
        """Generate a human-readable explanation string."""
        verdict = "SUSPICIOUS" if self.is_fraud else "LEGITIMATE"
        lines = [f"Transaction {self.transaction_id} classified as {verdict} "
                 f"(confidence: {self.confidence:.1%})."]
        if self.top_features:
            lines.append("Key contributing features:")
            for name, value in self.top_features[:5]:
                direction = "increases" if value > 0 else "decreases"
                lines.append(f"  - {name}: {direction} fraud risk ({value:+.4f})")
        if self.risk_factors:
            lines.append("Risk factors:")
            for rf in self.risk_factors:
                lines.append(f"  [{rf.get('severity','LOW')}] "
                             f"{rf.get('description', rf.get('feature',''))}")
        if self.recommended_action:
            lines.append(f"Recommended action: {self.recommended_action}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# 3. ExplanationEngine
# ---------------------------------------------------------------------------

class ExplanationEngine:
    """Orchestrates SHAP explainers, risk factors, and narrative generation."""

    def __init__(self, shap_explainer: SHAPExplainer, feature_names: List[str]) -> None:
        self.shap_explainer = shap_explainer
        self.feature_names = feature_names

    def explain_transaction(self, transaction_features: np.ndarray,
                            transaction_id: str) -> FraudExplanation:
        """Produce a full explanation for a single transaction."""
        shap_vals = self.shap_explainer.explain_prediction(
            transaction_features, self.feature_names)
        top = self.shap_explainer.get_top_features(shap_vals, self.feature_names, n=10)
        risk_factors = self.generate_risk_factors(transaction_features)
        confidence = float(np.clip(abs(float(np.sum(shap_vals))), 0.0, 1.0))
        is_fraud = confidence >= 0.5
        action = ("DECLINE" if confidence >= 0.8 else
                  "STEP_UP_AUTH" if confidence >= 0.5 else "APPROVE")
        explanation_text = (f"Transaction flagged with score {confidence:.4f}. "
                            f"Top drivers: {', '.join(n for n, _ in top[:3])}.")
        return FraudExplanation(transaction_id=transaction_id, is_fraud=is_fraud,
                                confidence=confidence, top_features=top,
                                explanation_text=explanation_text,
                                recommended_action=action, risk_factors=risk_factors)

    def explain_fraud_ring(self, ring_transactions: List[Dict[str, Any]],
                           graph_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Explain a detected fraud ring using transaction and graph data."""
        total_amount = sum(t.get("amount", 0) for t in ring_transactions)
        unique_cards = len({t.get("card_id") for t in ring_transactions})
        unique_ips = len({t.get("ip_address") for t in ring_transactions})
        return {
            "ring_id": graph_metrics.get("ring_id", str(uuid.uuid4())[:8]),
            "transaction_count": len(ring_transactions),
            "total_amount": total_amount, "unique_cards": unique_cards,
            "unique_ips": unique_ips,
            "modularity": graph_metrics.get("modularity", 0.0),
            "risk_score": min(1.0, graph_metrics.get("density", 0.0) * 1.5),
            "narrative": (f"Fraud ring of {len(ring_transactions)} transactions across "
                          f"{unique_cards} card(s) and {unique_ips} IP(s). "
                          f"Total amount: ${total_amount:,.2f}. "
                          f"Graph modularity: {graph_metrics.get('modularity', 0):.3f}."),
        }

    def generate_risk_factors(self, features: np.ndarray) -> List[Dict[str, str]]:
        """Extract and categorise risk factors from feature values."""
        shap_vals = self.shap_explainer.explain_prediction(features, self.feature_names)
        factors: List[Dict[str, str]] = []
        for i, name in enumerate(self.feature_names):
            value = float(features[i]) if i < len(features) else 0.0
            sv = float(shap_vals[i]) if i < len(shap_vals) else 0.0
            severity = self._categorize_risk(name, value, sv)
            if severity != "NONE":
                factors.append({"feature": name, "value": f"{value:.4f}",
                                "shap_value": f"{sv:+.4f}", "severity": severity,
                                "description": f"{name} = {value:.4f} ({severity})"})
        factors.sort(key=lambda f: ["HIGH", "MEDIUM", "LOW", "NONE"].index(f["severity"]))
        return factors

    def _categorize_risk(self, feature_name: str, value: float,
                         shap_value: float) -> str:
        """Categorise a feature's risk level based on its name and SHAP value."""
        abs_sv = abs(shap_value)
        low_kw = ("temporal_is_weekend", "temporal_hour", "geo_latitude")
        if any(kw in feature_name.lower() for kw in low_kw):
            return "NONE"
        if abs_sv > 0.3:
            return "HIGH"
        if abs_sv > 0.1:
            return "MEDIUM"
        if abs_sv > 0.02:
            return "LOW"
        return "NONE"


# ---------------------------------------------------------------------------
# 4. SARGenerator
# ---------------------------------------------------------------------------
class SARGenerator:
    """Generates FinCEN-compliant Suspicious Activity Reports."""

    def __init__(self, explanation_engine: ExplanationEngine) -> None:
        self.engine = explanation_engine

    def generate_sar(self, transaction_data: Dict[str, Any],
                     explanation: FraudExplanation,
                     graph_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build a full SAR document dict."""
        sar_id = str(uuid.uuid4())[:12].upper()
        return {"sar_id": sar_id,
                "header": self._compile_sar_header(sar_id),
                "subject": self._compile_subject_info(transaction_data),
                "narrative": self._compile_suspicious_activity_narrative(explanation),
                "transactions": self._compile_transaction_history(transaction_data),
                "graph_evidence": self._compile_graph_evidence(graph_context),
                "recommendation": self._compile_recommendation(explanation),
                "generated_at": datetime.now(timezone.utc).isoformat()}

    def _compile_sar_header(self, sar_id: str) -> Dict[str, Any]:
        """SAR header with filing information."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return {"sar_id": sar_id, "filing_type": "INITIAL",
                "filing_institution": "Mastercard AI Monitoring",
                "activity_period_start": today, "activity_period_end": today,
                "filing_date": today, "prepared_by": "Automated SAR System",
                "system_version": "xai_module_v1"}

    def _compile_subject_info(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract subject information from transaction."""
        return {"card_number_last_four": transaction_data.get("card_id", "N/A")[-4:],
                "transaction_amount": transaction_data.get("amount", 0.0),
                "transaction_date": transaction_data.get(
                    "timestamp", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
                "merchant_category": transaction_data.get("mcc", "UNKNOWN"),
                "country": transaction_data.get("country_code", "UNKNOWN"),
                "ip_address": transaction_data.get("ip_address", "N/A"),
                "device_id": transaction_data.get("device_id", "N/A")}

    def _compile_suspicious_activity_narrative(self, explanation: FraudExplanation
                                               ) -> Dict[str, str]:
        """The narrative section describing suspicious activity."""
        return {"summary": explanation.explanation_text,
                "detailed_narrative": explanation.to_narrative(),
                "risk_level": "HIGH" if explanation.confidence >= 0.8 else "MEDIUM",
                "indicators": [rf.get("description", "") for rf in explanation.risk_factors
                               if rf.get("severity") in ("HIGH", "MEDIUM")]}

    def _compile_transaction_history(self, transaction_data: Dict[str, Any]
                                     ) -> List[Dict[str, Any]]:
        """List related transactions."""
        return [{"transaction_id": transaction_data.get("transaction_id", "N/A"),
                 "amount": transaction_data.get("amount", 0.0),
                 "timestamp": transaction_data.get("timestamp", ""),
                 "card_id": transaction_data.get("card_id", "N/A"),
                 "status": "FLAGGED"}]

    def _compile_graph_evidence(self, graph_context: Optional[Dict[str, Any]]
                                ) -> Dict[str, Any]:
        """Fraud ring evidence from graph analysis."""
        if graph_context is None:
            return {"available": False}
        return {"available": True, "ring_id": graph_context.get("ring_id", "N/A"),
                "connected_entities": graph_context.get("connected_entities", []),
                "modularity": graph_context.get("modularity", 0.0),
                "density": graph_context.get("density", 0.0),
                "risk_score": graph_context.get("risk_score", 0.0)}

    def _compile_recommendation(self, explanation: FraudExplanation) -> Dict[str, Any]:
        """Recommended actions based on explanation."""
        return {"action": explanation.recommended_action,
                "escalate": explanation.confidence >= 0.8,
                "block_card": explanation.recommended_action == "DECLINE",
                "file_sar": explanation.confidence >= 0.7,
                "monitor_related": True,
                "rationale": explanation.explanation_text}

    def to_xml(self, sar_data: Dict[str, Any]) -> str:
        """Export SAR as FinCEN-format XML string."""
        try:
            from lxml import etree
        except ImportError:
            logger.warning("lxml unavailable, returning JSON-based XML fallback")
            return f"<SARReport>{json.dumps(sar_data)}</SARReport>"
        root = etree.Element("SARReport")
        for section in ("header", "subject", "narrative", "recommendation"):
            elem = etree.SubElement(root, section)
            self._dict_to_xml(elem, sar_data.get(section, {}))
        txn_list = etree.SubElement(root, "transactionHistory")
        for txn in sar_data.get("transactions", []):
            txn_elem = etree.SubElement(txn_list, "transaction")
            self._dict_to_xml(txn_elem, txn)
        self._dict_to_xml(etree.SubElement(root, "graphEvidence"),
                          sar_data.get("graph_evidence", {}))
        return etree.tostring(root, pretty_print=True, encoding="unicode")

    def to_json(self, sar_data: Dict[str, Any]) -> str:
        """Export SAR as formatted JSON string."""
        return json.dumps(sar_data, indent=2, default=str)

    @staticmethod
    def _dict_to_xml(parent: Any, data: Dict[str, Any]) -> None:
        """Recursively build XML elements from a dict."""
        from lxml import etree
        for key, value in data.items():
            if isinstance(value, dict):
                SARGenerator._dict_to_xml(
                    etree.SubElement(parent, key), value)
            elif isinstance(value, list):
                list_elem = etree.SubElement(parent, key)
                for item in value:
                    if isinstance(item, dict):
                        SARGenerator._dict_to_xml(
                            etree.SubElement(list_elem, "item"), item)
                    else:
                        etree.SubElement(list_elem, "item").text = str(item)
            else:
                etree.SubElement(parent, key).text = str(value) if value is not None else ""


# ---------------------------------------------------------------------------
# 5. SARQueue
# ---------------------------------------------------------------------------
class SARQueue:
    """Manages a queue of SARs pending filing."""
    def __init__(self, max_queue_size: int = 1000) -> None:
        self.max_queue_size = max_queue_size
        self._pending: List[Dict[str, Any]] = []
        self._filed: List[Dict[str, Any]] = []
        self._generation_times: List[float] = []

    def add_sar(self, sar_data: Dict[str, Any]) -> str:
        """Add a SAR to the pending queue. Returns the SAR id."""
        sar_id = sar_data.get("sar_id", str(uuid.uuid4())[:12].upper())
        sar_data["_queued_at"] = time.time()
        if len(self._pending) >= self.max_queue_size:
            evicted = self._pending.pop(0)
            logger.warning("SAR queue full, evicted %s", evicted.get("sar_id"))
        self._pending.append(sar_data)
        return sar_id

    def get_pending_sars(self) -> List[Dict[str, Any]]:
        """Return list of SARs awaiting filing."""
        return list(self._pending)

    def mark_filed(self, sar_id: str) -> bool:
        """Mark a SAR as filed. Returns True if found and moved."""
        for i, sar in enumerate(self._pending):
            if sar.get("sar_id") == sar_id:
                filed = self._pending.pop(i)
                filed["_filed_at"] = time.time()
                gen_time = filed["_filed_at"] - filed.get("_queued_at", 0)
                self._generation_times.append(gen_time)
                self._filed.append(filed)
                return True
        return False

    def get_statistics(self) -> Dict[str, Any]:
        """Return queue statistics."""
        gen_times = (np.array(self._generation_times)
                     if self._generation_times else np.array([0.0]))
        return {"pending": len(self._pending), "filed": len(self._filed),
                "total_ever_received": len(self._pending) + len(self._filed),
                "avg_generation_time_s": float(np.mean(gen_times)),
                "max_queue_size": self.max_queue_size,
                "utilisation": len(self._pending) / self.max_queue_size}
