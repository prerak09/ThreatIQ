"""Closed-loop adversarial feedback and active learning module.

Monitors detection performance, flags missed detections, generates
retraining data, and triggers model retraining when performance degrades.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple

import numpy as np

try:
    from sklearn.metrics import (
        precision_score,
        recall_score,
        roc_auc_score,
        f1_score,
        confusion_matrix,
    )
except ImportError as exc:
    raise ImportError(
        "scikit-learn is required: pip install scikit-learn"
    ) from exc

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class FinancialLossEstimate:
    """Estimated financial impact of detection decisions."""

    false_negative_cost: float = 0.0
    false_positive_cost: float = 0.0
    total_cost: float = 0.0
    avg_fraud_loss: float = 0.0
    avg_false_alarm_cost: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        """Serialise to dictionary."""
        return {
            "false_negative_cost": self.false_negative_cost,
            "false_positive_cost": self.false_positive_cost,
            "total_cost": self.total_cost,
            "avg_fraud_loss": self.avg_fraud_loss,
            "avg_false_alarm_cost": self.avg_false_alarm_cost,
        }


@dataclass
class PerformanceMetrics:
    """Aggregated classification metrics."""

    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    roc_auc: float = 0.0
    false_positive_rate: float = 0.0
    detection_rate: float = 0.0
    n_samples: int = 0
    n_false_negatives: int = 0
    n_false_positives: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialise to dictionary."""
        return {
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "roc_auc": self.roc_auc,
            "false_positive_rate": self.false_positive_rate,
            "detection_rate": self.detection_rate,
            "n_samples": self.n_samples,
            "n_false_negatives": self.n_false_negatives,
            "n_false_positives": self.n_false_positives,
        }


@dataclass
class ReplayBufferEntry:
    """A single entry in the replay buffer."""

    transaction: Dict[str, Any]
    true_label: int
    predicted_label: int
    fraud_probability: float
    timestamp: float
    feature_vector: Optional[np.ndarray] = None
    retraining_sample: bool = False


# ---------------------------------------------------------------------------
# Active Learning Loop
# ---------------------------------------------------------------------------


class ActiveLearningLoop:
    """Manages the closed-loop adversarial feedback cycle.

    Responsibilities:
    - Evaluate incoming batches against ground truth.
    - Track false negatives (missed frauds) and false positives.
    - Maintain a replay buffer of recent transactions.
    - Generate retraining samples prioritising missed detections.
    - Trigger retraining when detection rate falls below a threshold.
    - Estimate financial losses from different error types.

    Parameters
    ----------
    detection_threshold : float
        Minimum detection rate before retraining is triggered.
    replay_buffer_size : int
        Maximum entries in the replay buffer.
    avg_fraud_cost : float
        Estimated average loss per undetected fraudulent transaction.
    avg_false_alarm_cost : float
        Estimated cost of a false positive (investigation, decline).
    retrain_cooldown_seconds : float
        Minimum seconds between retraining triggers.
    retrain_callback : callable | None
        Function called to perform retraining.  Signature:
        ``callback(X: np.ndarray, y: np.ndarray) -> dict``.
    """

    def __init__(
        self,
        detection_threshold: float = 0.85,
        replay_buffer_size: int = 10_000,
        avg_fraud_cost: float = 500.0,
        avg_false_alarm_cost: float = 15.0,
        retrain_cooldown_seconds: float = 3_600.0,
        retrain_callback: Optional[Callable[[np.ndarray, np.ndarray], Dict[str, Any]]] = None,
    ) -> None:
        self.detection_threshold = detection_threshold
        self.avg_fraud_cost = avg_fraud_cost
        self.avg_false_alarm_cost = avg_false_alarm_cost
        self.retrain_cooldown_seconds = retrain_cooldown_seconds
        self.retrain_callback = retrain_callback

        # Replay buffer (FIFO)
        self._replay_buffer: Deque[ReplayBufferEntry] = deque(maxlen=replay_buffer_size)

        # Running totals
        self._total_predictions: int = 0
        self._total_false_negatives: int = 0
        self._total_false_positives: int = 0
        self._last_retrain_time: float = 0.0

        # History for trend analysis
        self._batch_metrics_history: List[PerformanceMetrics] = []

    # ------------------------------------------------------------------
    # Core evaluation
    # ------------------------------------------------------------------

    def evaluate_batch(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_proba: np.ndarray,
        transactions: Optional[List[Dict[str, Any]]] = None,
        timestamps: Optional[np.ndarray] = None,
    ) -> PerformanceMetrics:
        """Evaluate a batch and update internal state.

        Parameters
        ----------
        y_true : np.ndarray
            Ground-truth binary labels.
        y_pred : np.ndarray
            Predicted binary labels.
        y_proba : np.ndarray
            Predicted fraud probabilities.
        transactions : list[dict] | None
            Raw transactions to store in the replay buffer.
        timestamps : np.ndarray | None
            Unix timestamps for each transaction.

        Returns
        -------
        PerformanceMetrics
        """
        y_true = np.asarray(y_true, dtype=int)
        y_pred = np.asarray(y_pred, dtype=int)
        y_proba = np.asarray(y_proba, dtype=float)

        n = len(y_true)
        self._total_predictions += n

        # Compute confusion matrix components
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
        self._total_false_negatives += int(fn)
        self._total_false_positives += int(fp)

        # Metrics
        precision = float(precision_score(y_true, y_pred, zero_division=0))
        recall = float(recall_score(y_true, y_pred, zero_division=0))
        f1_val = float(f1_score(y_true, y_pred, zero_division=0))
        fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
        detection_rate = recall

        try:
            roc_auc = float(roc_auc_score(y_true, y_proba))
        except ValueError:
            roc_auc = 0.0

        metrics = PerformanceMetrics(
            precision=precision,
            recall=recall,
            f1=f1_val,
            roc_auc=roc_auc,
            false_positive_rate=fpr,
            detection_rate=detection_rate,
            n_samples=n,
            n_false_negatives=int(fn),
            n_false_positives=int(fp),
        )
        self._batch_metrics_history.append(metrics)

        # Populate replay buffer
        self._populate_replay_buffer(
            y_true, y_pred, y_proba, transactions, timestamps
        )

        logger.info(
            "Batch evaluated: precision=%.3f recall=%.3f f1=%.3f "
            "auc=%.3f fn=%d fp=%d",
            precision,
            recall,
            f1_val,
            roc_auc,
            fn,
            fp,
        )
        return metrics

    def _populate_replay_buffer(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_proba: np.ndarray,
        transactions: Optional[List[Dict[str, Any]]],
        timestamps: Optional[np.ndarray],
    ) -> None:
        """Add entries to the replay buffer, flagging false negatives."""
        n = len(y_true)
        fn_mask = (y_true == 1) & (y_pred == 0)

        for i in range(n):
            txn: Dict[str, Any] = transactions[i] if transactions else {"index": int(i)}
            ts = float(timestamps[i]) if timestamps is not None else time.time()

            # Keep the exact feature vector used at inference time (if the
            # caller supplied one) so retraining data has the right shape.
            feat_vec = txn.get("features") if isinstance(txn, dict) else None
            feature_vector: Optional[np.ndarray] = None
            if isinstance(feat_vec, dict) and feat_vec:
                try:
                    feature_vector = np.asarray(list(feat_vec.values()), dtype=np.float64)
                except (TypeError, ValueError):
                    feature_vector = None

            entry = ReplayBufferEntry(
                transaction=txn,
                true_label=int(y_true[i]),
                predicted_label=int(y_pred[i]),
                fraud_probability=float(y_proba[i]),
                timestamp=ts,
                feature_vector=feature_vector,
                retraining_sample=bool(fn_mask[i]),
            )
            self._replay_buffer.append(entry)

    # ------------------------------------------------------------------
    # Missed detection tracking
    # ------------------------------------------------------------------

    def flag_missed_detections(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_proba: np.ndarray,
        transactions: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Identify and return details of false negatives.

        Parameters
        ----------
        y_true : np.ndarray
            Ground-truth labels.
        y_pred : np.ndarray
            Predicted labels.
        y_proba : np.ndarray
            Predicted probabilities.
        transactions : list[dict] | None
            Raw transaction dicts (same order as labels).

        Returns
        -------
        list[dict]
            List of flagged missed detections with indices and scores.
        """
        y_true = np.asarray(y_true, dtype=int)
        y_pred = np.asarray(y_pred, dtype=int)
        fn_mask = (y_true == 1) & (y_pred == 0)
        indices = np.where(fn_mask)[0]

        flagged: List[Dict[str, Any]] = []
        for idx in indices:
            entry: Dict[str, Any] = {
                "index": int(idx),
                "true_label": 1,
                "predicted_label": 0,
                "fraud_probability": float(y_proba[idx]),
            }
            if transactions and idx < len(transactions):
                entry["transaction"] = transactions[idx]
            flagged.append(entry)

        logger.info("Flagged %d missed detections", len(flagged))
        return flagged

    # ------------------------------------------------------------------
    # Retraining data generation
    # ------------------------------------------------------------------

    def generate_retraining_data(
        self,
        min_fraud_ratio: float = 0.3,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Generate training data from the replay buffer.

        Prioritises false negatives (missed frauds) and balances with
        true negatives / correct detections.

        Parameters
        ----------
        min_fraud_ratio : float
            Minimum fraction of fraud samples in the output.

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            ``(X, y)`` arrays ready for model retraining.
        """
        if not self._replay_buffer:
            return np.array([]), np.array([])

        # Separate by category
        fn_samples = [
            e for e in self._replay_buffer
            if e.true_label == 1 and e.predicted_label == 0
        ]
        tp_samples = [
            e for e in self._replay_buffer
            if e.true_label == 1 and e.predicted_label == 1
        ]
        tn_samples = [
            e for e in self._replay_buffer
            if e.true_label == 0 and e.predicted_label == 0
        ]

        # Use the stored inference-time feature vectors so the retraining
        # data matches the model's expected input dimensionality. Fall back
        # to a 2-column [amount, probability] proxy only when no vector was
        # captured (and log it — that shape will not serve correctly).
        have_vectors = all(
            e.feature_vector is not None
            for e in (fn_samples + tp_samples + tn_samples)
        )
        if not have_vectors:
            logger.warning(
                "Replay buffer entries lack feature vectors — falling back "
                "to 2-column proxy features; retraining quality will suffer."
            )

        def _to_features(entry: ReplayBufferEntry) -> List[float]:
            if entry.feature_vector is not None:
                return entry.feature_vector.tolist()
            amount = entry.transaction.get("amount", 0.0)
            return [amount, entry.fraud_probability]

        rows: List[List[float]] = []
        labels: List[int] = []

        # All false negatives (critical)
        for s in fn_samples:
            rows.append(_to_features(s))
            labels.append(1)

        # Sample TPs to maintain fraud ratio
        n_fn = len(fn_samples)
        if n_fn > 0 and tp_samples:
            n_tp = max(0, int(n_fn * (1.0 - min_fraud_ratio) / min_fraud_ratio) - n_fn)
            tp_sampled = list(np.random.choice(
                len(tp_samples), size=min(n_tp, len(tp_samples)), replace=False
            ))
            for i in tp_sampled:
                rows.append(_to_features(tp_samples[i]))
                labels.append(1)

        # True negatives to fill remaining slots
        total_fraud = labels.count(1)
        n_tn_desired = int(total_fraud * (1.0 - min_fraud_ratio) / min_fraud_ratio)
        tn_sampled = list(np.random.choice(
            len(tn_samples), size=min(n_tn_desired, len(tn_samples)), replace=False
        ))
        for i in tn_sampled:
            rows.append(_to_features(tn_samples[i]))
            labels.append(0)

        if not rows:
            return np.array([]), np.array([])

        X = np.array(rows, dtype=np.float64)
        y = np.array(labels, dtype=int)

        logger.info(
            "Generated retraining data: %d samples (%d fraud, %d legit)",
            len(y), int(y.sum()), int(len(y) - y.sum()),
        )
        return X, y

    # ------------------------------------------------------------------
    # Financial loss estimation
    # ------------------------------------------------------------------

    def estimate_financial_loss(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        transaction_amounts: Optional[np.ndarray] = None,
    ) -> FinancialLossEstimate:
        """Estimate financial losses from detection errors.

        Parameters
        ----------
        y_true : np.ndarray
            Ground-truth labels.
        y_pred : np.ndarray
            Predicted labels.
        transaction_amounts : np.ndarray | None
            Dollar amount per transaction. If ``None``, uses
            ``avg_fraud_cost`` / ``avg_false_alarm_cost`` defaults.

        Returns
        -------
        FinancialLossEstimate
        """
        y_true = np.asarray(y_true, dtype=int)
        y_pred = np.asarray(y_pred, dtype=int)

        tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

        if transaction_amounts is not None and len(transaction_amounts) == len(y_true):
            amounts = np.asarray(transaction_amounts, dtype=float)
            fn_mask = (y_true == 1) & (y_pred == 0)
            fp_mask = (y_true == 0) & (y_pred == 1)
            fn_cost = float(amounts[fn_mask].sum()) if fn_mask.any() else 0.0
            fp_cost = float(amounts[fp_mask].sum()) if fp_mask.any() else 0.0
            avg_fn = float(amounts[fn_mask].mean()) if fn_mask.any() else 0.0
            avg_fp = float(amounts[fp_mask].mean()) if fp_mask.any() else 0.0
        else:
            fn_cost = fn * self.avg_fraud_cost
            fp_cost = fp * self.avg_false_alarm_cost
            avg_fn = self.avg_fraud_cost
            avg_fp = self.avg_false_alarm_cost

        return FinancialLossEstimate(
            false_negative_cost=fn_cost,
            false_positive_cost=fp_cost,
            total_cost=fn_cost + fp_cost,
            avg_fraud_loss=avg_fn,
            avg_false_alarm_cost=avg_fp,
        )

    # ------------------------------------------------------------------
    # Retraining trigger
    # ------------------------------------------------------------------

    def trigger_retrain(
        self,
        current_metrics: Optional[PerformanceMetrics] = None,
    ) -> bool:
        """Check if retraining should be triggered and execute it.

        Conditions for retraining:
        1. Detection rate is below ``detection_threshold``.
        2. Cooldown period has elapsed since the last retrain.

        Parameters
        ----------
        current_metrics : PerformanceMetrics | None
            If not provided, the most recent batch metrics are used.

        Returns
        -------
        bool
            ``True`` if retraining was triggered.
        """
        if current_metrics is None:
            if not self._batch_metrics_history:
                return False
            current_metrics = self._batch_metrics_history[-1]

        now = time.time()
        cooldown_elapsed = (now - self._last_retrain_time) >= self.retrain_cooldown_seconds

        if current_metrics.detection_rate >= self.detection_threshold:
            logger.info(
                "Detection rate %.3f above threshold %.3f — no retrain needed",
                current_metrics.detection_rate,
                self.detection_threshold,
            )
            return False

        if not cooldown_elapsed:
            remaining = self.retrain_cooldown_seconds - (now - self._last_retrain_time)
            logger.info("Retrain cooldown active (%.0fs remaining)", remaining)
            return False

        logger.warning(
            "Detection rate %.3f below threshold %.3f — triggering retrain",
            current_metrics.detection_rate,
            self.detection_threshold,
        )

        if self.retrain_callback is not None:
            X, y = self.generate_retraining_data()
            if len(y) > 0:
                result = self.retrain_callback(X, y)
                logger.info("Retrain callback completed: %s", result)
            else:
                logger.warning("No retraining data available")
        else:
            logger.warning("No retrain_callback registered — skipping actual retrain")

        self._last_retrain_time = now
        return True

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def get_summary(self) -> Dict[str, Any]:
        """Return a summary of all tracked metrics."""
        return {
            "total_predictions": self._total_predictions,
            "total_false_negatives": self._total_false_negatives,
            "total_false_positives": self._total_false_positives,
            "replay_buffer_size": len(self._replay_buffer),
            "retraining_samples": sum(
                1 for e in self._replay_buffer if e.retraining_sample
            ),
            "batches_evaluated": len(self._batch_metrics_history),
            "last_retrain_time": self._last_retrain_time,
            "detection_threshold": self.detection_threshold,
        }

    def get_detection_rate_trend(self) -> List[float]:
        """Return historical detection rates for trend analysis."""
        return [m.detection_rate for m in self._batch_metrics_history]

    def reset(self) -> None:
        """Clear all tracked state."""
        self._replay_buffer.clear()
        self._total_predictions = 0
        self._total_false_negatives = 0
        self._total_false_positives = 0
        self._last_retrain_time = 0.0
        self._batch_metrics_history.clear()
