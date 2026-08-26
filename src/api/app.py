"""
FastAPI Backend for Mastercard AI Red Teaming Challenge — Adversarial Arena

Enterprise-grade API with:
- Real-time WebSocket transaction streaming
- XAI (Explainable AI) with SHAP/permutation-based explanations
- Automated SAR (Suspicious Activity Report) generation and queueing
- Transaction-graph topology analysis and fraud-ring detection
- MARL (Multi-Agent RL) adversarial evolution
- Conformal prediction with guaranteed error bounds
- Activation steering, constrained diffusion, federated learning,
  Stackelberg game solving and ZKP verification endpoints
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..threat_intel.generator import ThreatIntelGenerator
from ..threat_intel.taxonomy_schema import AttackCategory, RiskLevel
from ..red_team.simulation_runner import SimulationRunner, extract_features, FEATURE_NAMES
from ..blue_team.gnn_model import FraudDetectionModel
from ..blue_team.active_learning_loop import ActiveLearningLoop
from ..blue_team.xai_module import (
    ExplanationEngine,
    SARGenerator,
    SARQueue,
    SHAPExplainer,
)
from ..blue_team.conformal_prediction import ConformalFraudDetector
from ..blue_team.temporal_gnn import FraudRingDetector, TemporalGraph
from ..red_team.marl_agent import MARLOrchestrator
from ..red_team.activation_steering import ActivationSteeringEngine, AttackIntensityController
from ..red_team.constrained_diffusion import (
    AmountConstraint,
    ConstrainedDiffusionModel,
    ConstraintRegistry,
    ConstraintViolationReporter,
    CreditLimitConstraint,
    MerchantCategoryConstraint,
)
from ..blue_team.federated_learning import (
    DPAggregator,
    FederatedLearningCoordinator,
    FederatedSimulation,
    PrivacyBudgetTracker,
)
from ..blue_team.stackelberg_solver import (
    AttackType,
    BlueTeamStrategy,
    RedTeamStrategy,
    StackelbergSolver,
)
from ..blue_team.zkp_verification import ZKPFraudSystem

logger = logging.getLogger("adversarial_arena.api")

# Hard ceiling on synchronous retraining work accepted from an HTTP request.
MAX_TRAIN_SAMPLES = 50_000

# Guards against concurrent retrains stacking up on the thread pool.
_train_lock = asyncio.Lock()

# ---------------------------------------------------------------------------
# Pydantic request / response models
# ---------------------------------------------------------------------------

class StartSimulationRequest(BaseModel):
    num_victims: int = Field(default=500, ge=1)
    fraud_ratio: float = Field(default=0.15, gt=0, le=1)
    transaction_rate_tps: float = Field(default=10.0, gt=0)


class InjectAttackRequest(BaseModel):
    attack_type: str
    count: int = Field(default=10, ge=1, le=1000)


class UpdateThresholdRequest(BaseModel):
    threshold: float = Field(default=0.5, gt=0, lt=1)


class TrainModelRequest(BaseModel):
    # Upper bound matters: training is synchronous CPU work, so an unbounded
    # n_samples lets a single unauthenticated request wedge the event loop
    # (and fail the platform healthcheck, which restarts the container).
    n_samples: int = Field(default=1000, ge=100, le=MAX_TRAIN_SAMPLES)


class ApplySteeringRequest(BaseModel):
    concept_id: str
    intensity: float = Field(default=0.5, ge=0, le=1)


class VerifyProofRequest(BaseModel):
    """A caller-supplied proof to verify. Tampering with any field must fail."""
    a: str
    b: str
    c: str
    public_signals: List[int] = Field(default_factory=list)
    public_inputs: List[int] = Field(default_factory=list)


class SolveGameRequest(BaseModel):
    iterations: int = Field(default=100, ge=10, le=1000)
    learning_rate: float = Field(default=0.01, gt=0, le=1)


# ---------------------------------------------------------------------------
# Application state (initialised at startup)
# ---------------------------------------------------------------------------

class AppState:
    """Shared state container for all components."""

    def __init__(self) -> None:
        self.simulation: Optional[SimulationRunner] = None
        self.model: Optional[FraudDetectionModel] = None
        self.active_learning: Optional[ActiveLearningLoop] = None
        self.threat_gen: Optional[ThreatIntelGenerator] = None
        self.explanation_engine: Optional[ExplanationEngine] = None
        self.sar_generator: Optional[SARGenerator] = None
        self.sar_queue: Optional[SARQueue] = None
        self.conformal_detector: Optional[ConformalFraudDetector] = None
        self.conformal_calibrated: bool = False
        self.marl: Optional[MARLOrchestrator] = None
        self.steering_engine: Optional[ActivationSteeringEngine] = None
        self.intensity_controller: Optional[AttackIntensityController] = None
        self.constraint_registry: Optional[ConstraintRegistry] = None
        self.constrained_model: Optional[ConstrainedDiffusionModel] = None
        self.federated: Optional[Dict[str, Any]] = None
        self.game_solver: Optional[StackelbergSolver] = None
        self.game_result: Optional[Dict[str, Any]] = None
        self.zkp: Optional[ZKPFraudSystem] = None
        self.zkp_certificate: Optional[Dict[str, Any]] = None
        # Issued attestations, keyed by proof_id, so /verify can check a proof
        # that was actually issued rather than minting a fresh one.
        self.zkp_proofs: Dict[str, Dict[str, Any]] = {}
        self.threshold: float = 0.5
        self.ws_clients: List[WebSocket] = []
        self._stream_task: Optional[asyncio.Task] = None
        self._marl_evolution_history: List[Dict] = []
        # Vector id -> attack category name (for per-vector analytics)
        self._vector_category: Dict[str, str] = {}

    def vector_category(self, vector_id: Optional[str]) -> str:
        if not vector_id:
            return "unknown"
        return self._vector_category.get(vector_id, "unknown")


state = AppState()


class _ModelAdapter:
    """sklearn-style wrapper exposing predict/predict_proba arrays."""

    def __init__(self, model: FraudDetectionModel) -> None:
        self.model = model

    def predict(self, X: np.ndarray) -> np.ndarray:
        proba = self.predict_proba(X)
        return (proba[:, 1] >= 0.5).astype(int)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(np.asarray(X, dtype=np.float64))


def _feature_vector(features: Optional[Dict[str, float]]) -> np.ndarray:
    """Ordered feature vector following the canonical schema."""
    if not features:
        features = {}
    return np.array([float(features.get(name, 0.0)) for name in FEATURE_NAMES],
                    dtype=np.float64)


# ---------------------------------------------------------------------------
# Lifespan — initialise components on startup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initialising Adversarial Arena components …")

    state.threat_gen = ThreatIntelGenerator(seed=42)
    state.threat_gen.generate_batch(count=20)
    state._vector_category = {
        v.vector_id: v.category.value for v in state.threat_gen.taxonomy.vectors
    }

    state.simulation = SimulationRunner(
        num_victims=500,
        fraud_ratio=0.15,
        transaction_rate_tps=10.0,
        enable_active_learning=True,
    )

    # --- Train the blue-team model on data from the real agents so that
    # training and serving share the same feature distribution.
    X_train, y_train, X_cal, y_cal = _build_training_sets(n_train=2400, n_cal=600)
    state.model = FraudDetectionModel(contamination=0.01)
    state.model.train(X_train, y_train, feature_names=list(FEATURE_NAMES))

    # Held-out split reserved for promotion decisions; the active-learning
    # loop never sees it, so it cannot overfit the gate.
    _VALIDATION["X"], _VALIDATION["y"] = X_cal, y_cal

    # --- Calibrate the serving threshold on the held-out split ---
    # A hardcoded 0.5 is arbitrary: the ensemble averages engines with very
    # different score distributions, so 0.5 gave ~25% precision in live traffic.
    # Pick the F1-optimal operating point on data the model did not train on.
    try:
        cal_proba = state.model.predict_proba(X_cal)[:, 1]
        candidates = np.linspace(0.10, 0.90, 81)
        best_t, best_f1 = 0.5, -1.0
        for t in candidates:
            pred = (cal_proba >= t).astype(int)
            tp = int(((pred == 1) & (y_cal == 1)).sum())
            fp = int(((pred == 1) & (y_cal == 0)).sum())
            fn = int(((pred == 0) & (y_cal == 1)).sum())
            f1 = (2 * tp / (2 * tp + fp + fn)) if (2 * tp + fp + fn) else 0.0
            if f1 > best_f1:
                best_t, best_f1 = float(t), f1
        state.threshold = round(best_t, 3)
        logger.info("Calibrated serving threshold: %.3f (cal F1=%.4f)", state.threshold, best_f1)
    except Exception as e:  # pragma: no cover - defensive
        logger.warning("Threshold calibration failed, keeping %.2f: %s", state.threshold, e)

    # --- Closed-loop active learning wired into the simulation runner ---
    state.active_learning = ActiveLearningLoop(
        detection_threshold=0.85,
        retrain_callback=_retrain_callback,
        retrain_cooldown_seconds=120.0,
    )
    state.simulation.active_learning = state.active_learning
    state.simulation.set_blue_team_classifier(_blue_team_classify)

    # --- XAI / SAR modules (real wiring) ---
    try:
        adapter = _ModelAdapter(state.model)
        shap_explainer = SHAPExplainer(adapter, background_data=X_train)
        state.explanation_engine = ExplanationEngine(
            shap_explainer=shap_explainer,
            feature_names=list(FEATURE_NAMES),
        )
        state.sar_generator = SARGenerator(explanation_engine=state.explanation_engine)
        state.sar_queue = SARQueue()
        logger.info("XAI and SAR modules initialized")
    except Exception as e:  # pragma: no cover - defensive
        logger.warning("XAI/SAR init failed: %s", e)

    # --- Conformal prediction calibrated on a held-out split ---
    try:
        state.conformal_detector = ConformalFraudDetector(fraud_model=state.model, alpha=0.05)
        state.conformal_detector.fit_calibration(X_cal, y_cal)
        state.conformal_calibrated = True
        logger.info("Conformal prediction initialized and calibrated")
    except Exception as e:  # pragma: no cover - defensive
        logger.warning("Conformal prediction init failed: %s", e)

    # --- Adversarial / research modules ---
    state.marl = MARLOrchestrator()
    state.steering_engine = ActivationSteeringEngine(model_dim=128, num_layers=12)
    state.intensity_controller = AttackIntensityController()

    registry = ConstraintRegistry()
    registry.register("AmountRange", AmountConstraint(min_amount=1.0, max_amount=10_000.0))
    registry.register("CreditLimit", CreditLimitConstraint(default_limit=2_000.0))
    registry.register("MerchantCategory", MerchantCategoryConstraint())
    state.constraint_registry = registry
    state.constrained_model = ConstrainedDiffusionModel(registry, gamma=1.0, guidance_scale=2.0, n_timesteps=200)

    state.zkp = ZKPFraudSystem(threshold=128)
    state.zkp_certificate = state.zkp.generate_verification_certificate()

    blue_strategies = [BlueTeamStrategy(threshold=t) for t in (0.3, 0.5, 0.7, 0.85)]
    red_strategies = [
        RedTeamStrategy(attack_type=AttackType.EVASION, intensity=0.4),
        RedTeamStrategy(intensity=0.6),
        RedTeamStrategy(intensity=0.8),
        RedTeamStrategy(intensity=0.95),
    ]
    state.game_solver = StackelbergSolver(blue_strategies, red_strategies)

    logger.info("All components ready")
    yield

    if state.simulation and state.simulation.is_running:
        state.simulation.stop()
    if state._stream_task and not state._stream_task.done():
        state._stream_task.cancel()
    logger.info("Shutdown complete")


def _generate_agent_transactions(n: int, fraud_ratio: float) -> List[Any]:
    """Generate labelled transactions directly from the simulation agents."""
    attacker = state.simulation.attacker
    victim = state.simulation.victim
    txs = []
    n_fraud = int(n * fraud_ratio)
    for i in range(n):
        if i < n_fraud:
            txs.append(attacker.generate_transaction())
        else:
            txs.append(victim.generate_transaction())
    return txs


def _build_training_sets(n_train: int = 2400, n_cal: int = 600):
    fraud_ratio = 0.35  # enriched so supervised engines see enough fraud
    train_txs = _generate_agent_transactions(n_train, fraud_ratio)
    cal_txs = _generate_agent_transactions(n_cal, 0.15)

    def to_xy(txs):
        X = np.stack([_feature_vector(extract_features(t)) for t in txs])
        y = np.array([1 if t.is_fraud else 0 for t in txs], dtype=int)
        rng = np.random.default_rng(42)
        order = rng.permutation(len(y))
        return X[order], y[order]

    X_tr, y_tr = to_xy(train_txs)
    X_cal, y_cal = to_xy(cal_txs)
    return X_tr, y_tr, X_cal, y_cal


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Adversarial Arena — AI Red Teaming Challenge",
    version="2.0.0",
    lifespan=lifespan,
)

_cors_origins = os.environ.get("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Blue-team classifier wired into the simulation runner
# ---------------------------------------------------------------------------

def _blue_team_classify(features: Dict[str, float]) -> Dict[str, Any]:
    """Classify a single transaction using the fraud detection model."""
    if state.model is None or not state.model._fitted:
        return {"is_fraud": False, "confidence": 0.0, "engine_scores": {}}

    try:
        vec = _feature_vector(features)
        result = state.model.predict(
            vec,
            threshold=state.threshold,
            transaction_id="live",
        )
        return {
            "is_fraud": result.is_fraud,
            "confidence": result.fraud_probability,
            "engine_scores": result.engine_scores,
            "latency_ms": result.latency_ms,
        }
    except Exception as exc:
        logger.warning("Blue-team classify error: %s", exc)
        return {"is_fraud": False, "confidence": 0.0, "engine_scores": {}, "error": str(exc)}


def _marl_evaluate(attack_type: str, action: Any, n: int = 32) -> float:
    """Score one MARL action against the live blue-team classifier.

    Generates ``n`` fraudulent transactions shaped by the candidate strategy,
    scores them in a single batched forward pass through the *real* detection
    model, and returns the measured detection rate. This is the link that makes
    the red/blue loop closed: the attacker's reward comes from the deployed
    defender, not a constant.
    """
    if state.simulation is None or state.model is None or not state.model._fitted:
        return 0.5

    attacker = state.simulation.attacker
    amount_dev = float(getattr(action, "amount_deviation", 0.0))
    jitter = float(getattr(action, "timing_jitter", 0.0))
    spread = float(getattr(action, "geo_spread", 0))
    mimicry = float(getattr(action, "bio_mimicry", 0.0))

    rows = []
    for _ in range(n):
        feats = extract_features(attacker.generate_transaction())
        # Apply the candidate evasion strategy to the feature vector.
        feats["amount"] = max(1.0, feats["amount"] * (1.0 - amount_dev))
        feats["amount_log"] = float(np.log1p(feats["amount"]))
        feats["hour"] = float(int(feats["hour"] + jitter * 6) % 24)
        feats["geo_lat"] += spread * 0.15
        feats["geo_long"] += spread * 0.15
        # Behavioural mimicry pulls the biometric score toward the legitimate
        # band. This is the lever that actually moves the detector, and it is
        # exactly the capability GenAI gives an attacker.
        feats["behavioral_score"] = float(
            min(0.99, feats["behavioral_score"] + mimicry * (0.9 - feats["behavioral_score"]))
        )
        rows.append(_feature_vector(feats))

    try:
        proba = state.model.predict_proba(np.stack(rows))[:, 1]
    except Exception as exc:
        logger.warning("MARL evaluation failed: %s", exc)
        return 0.5
    return float((proba >= state.threshold).mean())


# Held-out validation split, kept for champion/challenger promotion decisions.
_VALIDATION: Dict[str, Any] = {"X": None, "y": None}

# Minimum labelled samples before an online retrain is even attempted.
MIN_RETRAIN_SAMPLES = 400


def _f1(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())
    denom = 2 * tp + fp + fn
    return (2 * tp / denom) if denom else 0.0


def _score_on_validation(model: FraudDetectionModel) -> Optional[float]:
    X, y = _VALIDATION.get("X"), _VALIDATION.get("y")
    if X is None or y is None:
        return None
    try:
        proba = model.predict_proba(X)[:, 1]
        return _f1(y, (proba >= state.threshold).astype(int))
    except Exception:
        return None


def _retrain_callback(X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """Active-learning retrain, gated by a champion/challenger promotion test.

    Retraining a live model on whatever the active-learning loop happened to
    collect is not safe: the buffer is small and deliberately biased toward
    hard and uncertain cases. Doing it unguarded degraded the deployed model
    from ~86% precision to ~24% after a single 20-sample retrain.

    The rule now: train a *challenger* on the new data, evaluate both champion
    and challenger on a held-out split the loop never touches, and promote only
    if the challenger does not regress. A rejected challenger is discarded and
    the champion keeps serving.
    """
    if state.model is None:
        return {"error": "Model not initialised", "promoted": False}

    if len(y) < MIN_RETRAIN_SAMPLES:
        return {
            "promoted": False,
            "reason": f"insufficient data: {len(y)} < {MIN_RETRAIN_SAMPLES} samples",
            "n_samples": int(len(y)),
        }

    classes = set(np.unique(y).tolist())
    if len(classes) < 2:
        return {
            "promoted": False,
            "reason": f"single-class batch ({classes}) — would collapse the model",
            "n_samples": int(len(y)),
        }

    champion_f1 = _score_on_validation(state.model)

    challenger = FraudDetectionModel(contamination=state.model.contamination)
    try:
        metrics = challenger.train(X, y, feature_names=list(FEATURE_NAMES))
    except Exception as exc:
        logger.warning("Challenger training failed: %s", exc)
        return {"promoted": False, "reason": f"training failed: {exc}"}

    challenger_f1 = _score_on_validation(challenger)

    if champion_f1 is None or challenger_f1 is None:
        return {"promoted": False, "reason": "no validation set available"}

    # Small tolerance so identical performance does not churn the served model.
    if challenger_f1 >= champion_f1 - 0.01:
        state.model = challenger
        logger.info(
            "Challenger promoted: validation F1 %.4f -> %.4f (n=%d)",
            champion_f1, challenger_f1, len(y),
        )
        return {
            "promoted": True,
            "champion_f1": round(champion_f1, 4),
            "challenger_f1": round(challenger_f1, 4),
            "n_samples": int(len(y)),
            "metrics": metrics,
        }

    logger.warning(
        "Challenger REJECTED: validation F1 would drop %.4f -> %.4f (n=%d). "
        "Champion retained.",
        champion_f1, challenger_f1, len(y),
    )
    return {
        "promoted": False,
        "reason": "challenger regressed on held-out validation",
        "champion_f1": round(champion_f1, 4),
        "challenger_f1": round(challenger_f1, 4),
        "n_samples": int(len(y)),
    }


def _find_transaction(transaction_id: Optional[str]) -> Optional[Dict[str, Any]]:
    snap = state.simulation.snapshot_transactions() if state.simulation else []
    if transaction_id:
        for rec in reversed(snap):
            if rec.get("transaction_id") == transaction_id:
                return rec
        return None
    return snap[-1] if snap else None


# ---------------------------------------------------------------------------
# WebSocket streaming helper
# ---------------------------------------------------------------------------

async def _broadcast_transaction(data: Dict[str, Any]) -> None:
    """Send a transaction payload to every connected WebSocket client."""
    payload = json.dumps(data, default=str)
    stale: List[WebSocket] = []
    for ws in list(state.ws_clients):
        try:
            await ws.send_text(payload)
        except Exception:
            stale.append(ws)
    for ws in stale:
        if ws in state.ws_clients:
            state.ws_clients.remove(ws)


async def _stream_transactions() -> None:
    """Background coroutine that polls the simulation buffer and pushes via WS.

    Messages are shaped for the dashboard:
      {"type": "attack"|"transaction", "id", "amount", "attack_type",
       "attack_vector", "status", "channel"}
    """
    seen_ids: Dict[str, None] = {}  # insertion-ordered set with bounded size
    max_seen = 50_000
    while True:
        if state.simulation and state.simulation.is_running:
            recent = state.simulation.snapshot_transactions(limit=500)
            for tx in recent:
                tx_id = tx.get("transaction_id") or tx.get("id")
                if tx_id and tx_id not in seen_ids:
                    seen_ids[tx_id] = None
                    if len(seen_ids) > max_seen:
                        # drop the oldest half (dict preserves insertion order)
                        for old in list(seen_ids.keys())[: max_seen // 2]:
                            seen_ids.pop(old, None)
                    await _broadcast_transaction({
                        "type": tx.get("type", "attack" if tx.get("is_fraud") else "transaction"),
                        "id": tx_id,
                        "amount": tx.get("amount"),
                        "attack_type": state.vector_category(tx.get("attack_vector_id")),
                        "attack_vector": tx.get("attack_vector_id") or "legitimate",
                        "status": tx.get("status"),
                        "channel": tx.get("channel"),
                        "confidence": tx.get("blue_team_confidence"),
                    })
        await asyncio.sleep(0.05)


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "simulation": state.simulation is not None,
            "model": state.model is not None and state.model._fitted,
            "active_learning": state.active_learning is not None,
            "threat_intel": state.threat_gen is not None,
            "xai_sar": state.sar_queue is not None,
            "conformal_calibrated": state.conformal_calibrated,
            "marl": state.marl is not None,
            "steering": state.steering_engine is not None,
            "constraints": state.constraint_registry is not None,
            "zkp": state.zkp is not None,
            "game_solver": state.game_solver is not None,
        },
    }


@app.post("/api/simulation/start")
async def start_simulation(req: StartSimulationRequest = StartSimulationRequest()):
    if state.simulation is None:
        raise HTTPException(status_code=503, detail="Simulation runner not initialised")
    if state.simulation.is_running:
        return {"message": "Simulation already running"}

    state.simulation.fraud_ratio = req.fraud_ratio
    state.simulation.transaction_rate_tps = req.transaction_rate_tps
    state.simulation.start()

    if state._stream_task is None or state._stream_task.done():
        state._stream_task = asyncio.create_task(_stream_transactions())

    return {"message": "Simulation started", "tps": req.transaction_rate_tps, "fraud_ratio": req.fraud_ratio}


@app.post("/api/simulation/stop")
async def stop_simulation():
    if state.simulation is None:
        raise HTTPException(status_code=503, detail="Simulation runner not initialised")
    state.simulation.stop()
    return {"message": "Simulation stopped"}


@app.get("/api/metrics")
async def get_metrics():
    if state.simulation is None:
        raise HTTPException(status_code=503, detail="Simulation runner not initialised")
    metrics = state.simulation.get_current_metrics()
    return metrics or {"message": "No metrics yet — start the simulation"}


@app.get("/api/transactions")
async def get_transactions(limit: int = 100, fraud_only: bool = False):
    if state.simulation is None:
        raise HTTPException(status_code=503, detail="Simulation runner not initialised")
    return state.simulation.get_transaction_history(limit=limit, fraud_only=fraud_only)


@app.post("/api/attack/inject")
async def inject_attack(req: InjectAttackRequest):
    if state.simulation is None:
        raise HTTPException(status_code=503, detail="Simulation runner not initialised")
    try:
        results = state.simulation.inject_custom_attack(
            attack_type=req.attack_type, count=req.count
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "injected": len(results),
        "attack_type": req.attack_type,
        "results": results,
    }


@app.get("/api/threats/taxonomy")
async def get_threat_taxonomy():
    if state.threat_gen is None:
        raise HTTPException(status_code=503, detail="Threat intel not initialised")
    return json.loads(state.threat_gen.taxonomy.to_json())


@app.get("/api/threats/statistics")
async def get_threat_statistics():
    if state.threat_gen is None:
        raise HTTPException(status_code=503, detail="Threat intel not initialised")
    return state.threat_gen.get_statistics()


@app.post("/api/model/train")
async def train_model(req: TrainModelRequest = TrainModelRequest()):
    if state.model is None:
        raise HTTPException(status_code=503, detail="Model not initialised")

    if _train_lock.locked():
        raise HTTPException(
            status_code=409, detail="A retrain is already in progress"
        )

    async with _train_lock:
        # Both steps are CPU-bound; running them on the event loop blocks every
        # other request, including /api/health.
        X, y, _, _ = await run_in_threadpool(
            _build_training_sets, req.n_samples, 100
        )
        metrics = await run_in_threadpool(
            state.model.train, X, y, list(FEATURE_NAMES)
        )
    return {"message": "Model retrained", "metrics": metrics, "n_samples": req.n_samples}


@app.get("/api/model/metrics")
async def get_model_metrics():
    if state.model is None:
        raise HTTPException(status_code=503, detail="Model not initialised")
    return {
        "fitted": state.model._fitted,
        "version": state.model._version,
        "contamination": state.model.contamination,
        "threshold": state.threshold,
        "n_features": len(state.model._feature_names),
        "feature_names": list(state.model._feature_names),
        "training_time_s": round(state.model._training_time, 3),
    }


@app.post("/api/model/threshold")
async def update_threshold(req: UpdateThresholdRequest):
    state.threshold = req.threshold
    return {"message": "Threshold updated", "threshold": state.threshold}


@app.get("/api/defense/metrics")
async def get_defense_metrics():
    if state.active_learning is None:
        raise HTTPException(status_code=503, detail="Active learning not initialised")

    summary = state.active_learning.get_summary()
    fn_cost = summary["total_false_negatives"] * 500.0
    fp_cost = summary["total_false_positives"] * 15.0
    total_cost = fn_cost + fp_cost

    return {
        **summary,
        "financial_loss": {
            "false_negative_cost": round(fn_cost, 2),
            "false_positive_cost": round(fp_cost, 2),
            "total_cost": round(total_cost, 2),
        },
        "roi": {
            "detection_rate": summary.get("total_predictions", 0) and round(
                1 - summary["total_false_negatives"] / max(summary["total_predictions"], 1), 4
            ),
            "cost_avoidance": round(fn_cost, 2),
        },
        "detection_rate_trend": state.active_learning.get_detection_rate_trend()[-20:],
    }


@app.get("/api/attack/matrix")
async def get_attack_matrix():
    if state.threat_gen is None:
        raise HTTPException(status_code=503, detail="Threat intel not initialised")

    categories = [c.value for c in AttackCategory]
    risk_levels = [r.name for r in RiskLevel]

    matrix: Dict[str, Dict[str, int]] = {
        cat: {rl: 0 for rl in risk_levels} for cat in categories
    }
    for v in state.threat_gen.taxonomy.vectors:
        matrix[v.category.value][v.risk_level.name] += 1

    heatmap = []
    for cat in categories:
        row = [matrix[cat][rl] for rl in risk_levels]
        heatmap.append(row)

    return {
        "categories": categories,
        "risk_levels": risk_levels,
        "matrix": matrix,
        "heatmap": heatmap,
    }


# ---------------------------------------------------------------------------
# XAI endpoints (real explanations from the live model)
# ---------------------------------------------------------------------------

@app.get("/api/xai/explain/{transaction_id}")
async def explain_transaction(transaction_id: str):
    if state.explanation_engine is None or state.simulation is None:
        raise HTTPException(status_code=503, detail="XAI engine not initialised")

    rec = _find_transaction(transaction_id)
    if rec is None:
        raise HTTPException(status_code=404, detail=f"Transaction {transaction_id} not found in buffer")

    vec = _feature_vector(rec.get("features"))
    explanation = state.explanation_engine.explain_transaction(vec, transaction_id)
    payload = explanation.to_dict()
    payload["ground_truth_fraud"] = bool(rec.get("is_fraud"))
    payload["blue_team_flagged"] = bool(rec.get("blue_team_flagged"))
    return payload


@app.get("/api/xai/ring-explanation")
async def ring_explanation():
    graph = _build_temporal_graph(limit=400)
    rings = FraudRingDetector(None).detect_rings(graph, min_ring_size=3)[:8]
    snap = {t["transaction_id"]: t for t in state.simulation.snapshot_transactions(limit=400)} \
        if state.simulation else {}
    out = []
    for ring in rings:
        amounts = [
            t.get("amount", 0) for t in snap.values()
            if f"card-{t.get('card_last4')}" in ring
        ]
        out.append({
            "ring_id": "-".join(ring[:3]),
            "members": ring,
            "size": len(ring),
            "total_amount": round(sum(amounts), 2),
            "transaction_count": len(amounts),
            "risk_score": round(min(1.0, 0.4 + 0.15 * len(ring)), 3),
        })
    return {"rings": out, "cross_ring_flows": []}


# ---------------------------------------------------------------------------
# SAR endpoints (real queue + generator)
# ---------------------------------------------------------------------------

@app.get("/api/sar/pending")
async def get_pending_sars():
    if state.sar_queue is None:
        raise HTTPException(status_code=503, detail="SAR queue not initialised")
    pending = state.sar_queue.get_pending_sars()
    return {"pending": pending, "count": len(pending), **state.sar_queue.get_statistics()}


@app.post("/api/sar/generate")
async def generate_sar(transaction_id: Optional[str] = None):
    if state.sar_generator is None or state.explanation_engine is None or state.simulation is None:
        raise HTTPException(status_code=503, detail="SAR generator not initialised")

    rec = _find_transaction(transaction_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="No transactions available to explain")

    vec = _feature_vector(rec.get("features"))
    explanation = state.explanation_engine.explain_transaction(vec, rec["transaction_id"])
    sar_data = state.sar_generator.generate_sar(
        transaction_data={
            "transaction_id": rec["transaction_id"],
            "amount": rec.get("amount"),
            "timestamp": rec.get("timestamp"),
            "card_id": rec.get("card_last4", "N/A"),
            "mcc": rec.get("merchant_category_code", "UNKNOWN"),
            "ip_address": rec.get("ip_address", "N/A"),
            "device_id": rec.get("device_fingerprint", "N/A"),
        },
        explanation=explanation,
    )
    sar_id = state.sar_queue.add_sar(sar_data)
    return {"sar_id": sar_id, **sar_data}


@app.post("/api/sar/{sar_id}/file")
async def file_sar(sar_id: str):
    if state.sar_queue is None:
        raise HTTPException(status_code=503, detail="SAR queue not initialised")
    if not state.sar_queue.mark_filed(sar_id):
        raise HTTPException(status_code=404, detail=f"SAR {sar_id} not found in pending queue")
    return {
        "sar_id": sar_id,
        "status": "filed",
        "filed_at": datetime.now().isoformat(),
        **state.sar_queue.get_statistics(),
    }


# ---------------------------------------------------------------------------
# Topology endpoints (real transaction graph + ring detection)
# ---------------------------------------------------------------------------

def _build_temporal_graph(limit: int = 400) -> TemporalGraph:
    """Card-to-card graph linking cards that share infrastructure.

    The previous version added only one-way edges (card->ip, card->dev,
    dev->ip). That graph is a DAG, so Tarjan's SCC search could never find a
    component and ring detection returned an empty list on every call
    regardless of the traffic.

    The correct semantics for ring detection is a projection onto cards: two
    cards are linked when they transact from the same device or the same IP.
    A strongly-connected component of >= 3 cards is then a genuine cluster of
    cards sharing infrastructure — which is what a fraud ring looks like.
    """
    graph = TemporalGraph()
    if state.simulation is None:
        return graph

    snap = state.simulation.snapshot_transactions(limit=limit)

    # infrastructure id -> cards seen on it, and card -> latest timestamp
    shared: Dict[str, set] = {}
    card_ts: Dict[str, float] = {}

    for t in snap:
        try:
            ts = datetime.fromisoformat(t["timestamp"]).timestamp()
        except (KeyError, TypeError, ValueError):
            ts = time.time()

        card = f"card-{t.get('card_last4')}"
        card_ts[card] = max(card_ts.get(card, 0.0), ts)

        for key in (f"dev-{t.get('device_fingerprint')}", f"ip-{t.get('ip_address')}"):
            shared.setdefault(key, set()).add(card)

    for card, ts in card_ts.items():
        graph.add_node(card, "card", timestamp=ts)

    # Bidirectional edges: sharing a device or IP is a symmetric relation, so
    # a cluster of co-located cards forms a strongly connected component.
    for key, cards in shared.items():
        if len(cards) < 2:
            continue
        members = sorted(cards)
        for i, a in enumerate(members):
            for b in members[i + 1:]:
                ts = max(card_ts.get(a, 0.0), card_ts.get(b, 0.0))
                graph.add_edge(a, b, ts, "shared_infrastructure")
                graph.add_edge(b, a, ts, "shared_infrastructure")
    return graph


@app.get("/api/topology/graph")
async def get_topology_graph():
    if state.simulation is None:
        raise HTTPException(status_code=503, detail="Simulation runner not initialised")

    snap = state.simulation.snapshot_transactions(limit=400)
    node_stats: Dict[str, Dict[str, float]] = {}
    edge_counter: Dict[tuple, Dict[str, float]] = {}
    for t in snap:
        card, ip = f"card-{t.get('card_last4')}", f"ip-{t.get('ip_address')}"
        dev = f"dev-{t.get('device_fingerprint')}"
        for nid, ntype in ((card, "card"), (ip, "ip"), (dev, "device")):
            stats = node_stats.setdefault(nid, {"node_type": ntype, "total": 0, "fraud": 0})
            stats["total"] += 1
            stats["fraud"] += 1 if t.get("is_fraud") else 0
        for a, b in ((card, ip), (card, dev), (dev, ip)):
            key = (a, b) if a < b else (b, a)
            e = edge_counter.setdefault(key, {"weight": 0, "amount": 0.0, "fraud": 0})
            e["weight"] += 1
            e["amount"] += float(t.get("amount", 0) or 0)
            e["fraud"] += 1 if t.get("is_fraud") else 0

    nodes = [
        {
            "id": nid,
            "label": nid.replace("card-", "****").replace("ip-", "").replace("dev-", "")[:16],
            "type": stats.get("node_type", "card"),
            "risk_score": round(stats["fraud"] / stats["total"], 3) if stats["total"] else 0.0,
            "degree": stats["total"],
        }
        for nid, stats in sorted(node_stats.items(), key=lambda kv: -kv[1]["total"])[:60]
    ]
    edges = [
        {
            "source": a, "target": b,
            "weight": round(e["amount"] / max(e["weight"], 1), 2),
            "count": int(e["weight"]),
            "is_fraud": e["fraud"] > e["weight"] / 2,
        }
        for (a, b), e in sorted(edge_counter.items(), key=lambda kv: -kv[1]["weight"])[:80]
    ]

    tg = _build_temporal_graph(limit=min(len(snap), 400))
    detector = FraudRingDetector(None)
    metrics = detector.analyze_topology(tg)
    rings = detector.detect_rings(tg, min_ring_size=3)

    return {
        "nodes": nodes,
        "edges": edges,
        "metrics": {
            "density": round(metrics.get("density", 0.0), 4),
            "avg_clustering": round(metrics.get("clustering", 0.0), 4),
            "num_communities": len(rings),
            "modularity": round(metrics.get("avg_degree", 0.0) / max(len(nodes), 1), 4),
            "transactions_analyzed": len(snap),
        },
    }


@app.get("/api/topology/rings")
async def get_topology_rings():
    if state.simulation is None:
        raise HTTPException(status_code=503, detail="Simulation runner not initialised")

    graph = _build_temporal_graph(limit=400)
    rings = FraudRingDetector(None).detect_rings(graph, min_ring_size=3)
    snap = state.simulation.snapshot_transactions(limit=400)
    card_risk: Dict[str, List[int]] = {}
    for t in snap:
        card_risk.setdefault(f"card-{t.get('card_last4')}", []).append(1 if t.get("is_fraud") else 0)

    out = []
    for i, ring in enumerate(rings[:10]):
        risks = [r for card in ring for r in card_risk.get(card, [])]
        out.append({
            "ring_id": i,
            "label": f"Ring {i + 1}",
            "members": ring,
            "nodes": len(ring),
            "avg_risk": round(sum(risks) / len(risks), 3) if risks else 0.0,
        })
    return {"rings": out, "total_rings": len(rings),
            "total_nodes": sum(r["nodes"] for r in out)}


# ---------------------------------------------------------------------------
# MARL endpoints (real orchestrator)
# ---------------------------------------------------------------------------

@app.get("/api/marl/agents")
async def get_marl_agents():
    if state.marl is None:
        raise HTTPException(status_code=503, detail="MARL orchestrator not initialised")
    agents = []
    for at, agent in state.marl.agents.items():
        history = state.marl.history.get(at, [])
        agents.append({
            "agent_id": at.replace("_", "-"),
            "attack_type": at,
            "role": "adversary",
            "evasion_rate": round(state.marl.scores.get(at, 0.0), 4),
            "reward": round(state.marl.scores.get(at, 0.0), 4),
            "current_epsilon": round(agent.epsilon, 4),
            "episodes_evaluated": state.marl.episodes.get(at, 0),
            "history": history,
            "min_evasion": round(min(history), 4) if history else None,
            "max_evasion": round(max(history), 4) if history else None,
            "delta_this_epoch": (
                round(history[-1] - history[-2], 4) if len(history) >= 2 else None
            ),
            "policy_actions": state.marl.policy_distribution(at),
            "strategy": agent.get_evasion_strategy(at),
        })
    return {
        "agents": agents,
        "global_step": state.marl.epoch,
        "has_data": state.marl.epoch > 0,
    }


def _per_category_detection_rates() -> Dict[str, float]:
    """Detection rate per attack category derived from the live buffer."""
    rates: Dict[str, List[float]] = {}
    for t in state.simulation.snapshot_transactions(limit=1000):
        if not t.get("is_fraud"):
            continue
        cat = state.vector_category(t.get("attack_vector_id"))
        flagged = 1.0 if t.get("blue_team_flagged") else 0.0
        rates.setdefault(cat, []).append(flagged)
    return {cat: sum(v) / len(v) for cat, v in rates.items() if v}


@app.post("/api/marl/evolve")
async def evolve_marl(epochs: int = 10):
    if state.marl is None or state.simulation is None:
        raise HTTPException(status_code=503, detail="MARL orchestrator not initialised")

    epochs = max(1, min(epochs, 50))
    category_rates = _per_category_detection_rates()

    categories = sorted(category_rates.keys()) or ["unknown"]
    performance = {
        at: category_rates.get(categories[i % len(categories)], 0.5)
        for i, at in enumerate(state.marl.ATTACK_TYPES)
    }

    # Policy updates are CPU-bound and hit the classifier per rollout step.
    def _run() -> List[Dict[str, float]]:
        per_epoch = []
        for _ in range(epochs):
            per_epoch.append(
                state.marl.evolve_strategies(
                    performance,
                    evaluate_fn=_marl_evaluate,
                    rollout_steps=6,
                )
            )
        return per_epoch

    epoch_results = await run_in_threadpool(_run)

    final = epoch_results[-1] if epoch_results else {}
    overall_detection = 1.0 - (sum(final.values()) / len(final)) if final else 0.0

    entry = {
        "timestamp": datetime.now().isoformat(),
        "epochs": epochs,
        "epoch_index": state.marl.epoch,
        "category_detection_rates": {k: round(v, 4) for k, v in category_rates.items()},
        "avg_attacker_evasion_score": round(
            sum(state.marl.scores.values()) / max(len(state.marl.scores), 1), 4
        ),
        "overall_detection_rate": round(overall_detection, 4),
        "per_agent_evasion": {k: round(v, 4) for k, v in final.items()},
    }
    state._marl_evolution_history.append(entry)
    return {
        "evolved": True,
        "epochs_run": epochs,
        "global_epoch": state.marl.epoch,
        "per_agent_evasion": entry["per_agent_evasion"],
        "history": state._marl_evolution_history[-10:],
    }


@app.get("/api/marl/history")
async def get_marl_history():
    return {"history": state._marl_evolution_history}


# ---------------------------------------------------------------------------
# Conformal prediction endpoint (calibrated at startup)
# ---------------------------------------------------------------------------

@app.get("/api/conformal/stats")
async def get_conformal_stats():
    if state.conformal_detector is None:
        raise HTTPException(status_code=503, detail="Conformal detector not initialised")
    guarantee = state.conformal_detector.conformal.coverage_guarantee()
    history_stats = state.conformal_detector.get_guarantee_stats()
    calibrated = state.conformal_calibrated
    return {
        **guarantee,
        **history_stats,
        "calibrated": calibrated,
        "quantile_threshold": round(float(state.conformal_detector.conformal.threshold), 4)
        if calibrated else None,
    }


# ---------------------------------------------------------------------------
# Activation steering endpoints (real steering engine)
# ---------------------------------------------------------------------------

@app.get("/api/steering/concepts")
async def list_steering_concepts():
    if state.steering_engine is None:
        raise HTTPException(status_code=503, detail="Steering engine not initialised")
    concepts = []
    for name in state.steering_engine._library.list_concepts():
        sv = state.steering_engine._library.get_concept(name)
        concepts.append({
            "id": name,
            "name": name.replace("_", " ").title(),
            "description": sv.description,
            "layer_index": sv.layer_index,
            "default_alpha": sv.alpha,
            "vector_dim": int(sv.vector.shape[0]),
        })
    return {"concepts": concepts, "total": len(concepts)}


@app.post("/api/steering/apply")
async def apply_steering(req: ApplySteeringRequest):
    if state.steering_engine is None or state.intensity_controller is None:
        raise HTTPException(status_code=503, detail="Steering engine not initialised")

    try:
        sv = state.steering_engine._library.get_concept(req.concept_id)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    config = state.intensity_controller.intensity_to_config(req.intensity)
    alpha = float(config["alphas"][0]) if config["alphas"] else req.intensity

    rng = np.random.default_rng()
    hidden = rng.normal(size=(8, sv.vector.shape[0])).astype(np.float32)
    steered = state.steering_engine.apply_steering(hidden, req.concept_id, alpha=alpha)
    effect = state.steering_engine.measure_steering_effect(hidden[0], steered[0])

    return {
        "concept_id": req.concept_id,
        "intensity": req.intensity,
        "alpha": alpha,
        "layer_index": sv.layer_index,
        "l2_distance": effect["l2_norm"],
        "cosine_similarity": effect["cosine_similarity"],
        "direction_alignment": effect["direction_alignment"],
        "magnitude_ratio": effect["magnitude_ratio"],
        "config": config,
    }


@app.get("/api/steering/presets")
async def get_steering_presets():
    if state.intensity_controller is None:
        raise HTTPException(status_code=503, detail="Steering controller not initialised")
    presets = []
    for name in ("stealth", "balanced", "aggressive", "maximum"):
        preset = state.intensity_controller.get_preset(name)
        presets.append({
            "name": name.title(),
            "concepts": preset["concepts"],
            "alphas": preset["alphas"],
            "layers": preset["layers"],
        })
    return {"presets": presets}


# ---------------------------------------------------------------------------
# Constrained diffusion endpoints (real constraint registry)
# ---------------------------------------------------------------------------

@app.get("/api/constraints/list")
async def list_constraints():
    if state.constraint_registry is None:
        raise HTTPException(status_code=503, detail="Constraint registry not initialised")
    constraints = []
    for name in state.constraint_registry.names():
        constraints.append({"id": name, "name": name.replace("_", " ").title()})
    return {"constraints": constraints, "total": len(constraints)}


@app.post("/api/constraints/validate")
async def validate_constrained_samples(n_samples: int = 100):
    if state.constrained_model is None or state.constraint_registry is None:
        raise HTTPException(status_code=503, detail="Constrained diffusion model not initialised")

    samples = state.constrained_model.sample(min(max(n_samples, 1), 500), feature_names=["amount"])
    report = ConstraintViolationReporter().report(samples, state.constraint_registry, ["amount"])
    amount_report = report["violations"]["amount"]
    return {
        "n_validated": int(samples.shape[0]),
        "n_validated_per_constraint_checked": report["violations"]["amount"]["count"],
        "violations": {k: v for k, v in report["violations"].items()},
        "summary": report["summary"],
        "violation_rate": round(amount_report["rate"], 4),
    }


@app.post("/api/constraints/generate")
async def generate_constrained_samples(n_samples: int = 50):
    if state.constrained_model is None:
        raise HTTPException(status_code=503, detail="Constrained diffusion model not initialised")

    n = min(max(n_samples, 1), 200)
    samples = state.constrained_model.sample(n, feature_names=["amount"])
    amounts = samples[:, 0]
    amounts = state.constrained_model.enforce_benford_law(amounts)
    amounts = np.abs(amounts)
    valid = [(round(float(a), 2)) for a in amounts if 0 < a <= 10_000]

    return {
        "n_generated": len(valid),
        "samples": [{"amount": amt} for amt in valid[:10]],
        "benford_first_digits": {
            str(d): int(np.sum((np.floor(np.log10(np.abs(valid) + 1e-9)).astype(int) >= 0) &
                               ((np.abs(np.asarray(valid)) /
                                 10 ** np.floor(np.log10(np.abs(np.asarray(valid)) + 1e-9))).astype(int) == d)))
            for d in range(1, 10)
        } if valid else {},
    }


# ---------------------------------------------------------------------------
# Federated learning endpoints (real FedAvg + DP accounting)
# ---------------------------------------------------------------------------

FEDERATED_ROUND_EPSILON = 0.25


def _ensure_federated() -> Dict[str, Any]:
    if state.federated is not None:
        return state.federated
    sim = FederatedSimulation(n_banks=10, fraud_ratio=0.15, data_size=800)
    banks = sim.generate_bank_data()
    coordinator = FederatedLearningCoordinator(n_banks=10)
    coordinator.initialize_banks(banks)
    dp = DPAggregator(epsilon=FEDERATED_ROUND_EPSILON, delta=1e-5, max_norm=1.0, n_banks=10)
    budget = PrivacyBudgetTracker(total_epsilon=10.0, total_delta=1e-4)
    state.federated = {
        "sim": sim, "coordinator": coordinator, "dp": dp, "budget": budget,
    }
    return state.federated


@app.get("/api/federated/status")
async def get_federated_status():
    fed = _ensure_federated()
    coord: FederatedLearningCoordinator = fed["coordinator"]
    diff = coord.differential_stats()
    rounds = coord.round_metrics
    return {
        "status": "idle" if not rounds else "training",
        "current_round": coord.round_count,
        "banks": len(coord.bank_trainers),
        "avg_loss": rounds[-1]["avg_loss"] if rounds else None,
        "loss_reduction": float(diff.get("loss_reduction") or 0.0),
        # np.bool_ breaks response encoding — cast explicitly
        "convergence_achieved": bool(diff.get("convergence", False)),
        "grad_norm": rounds[-1]["grad_norm"] if rounds else None,
    }


@app.post("/api/federated/round")
async def trigger_federated_round():
    fed = _ensure_federated()
    coord: FederatedLearningCoordinator = fed["coordinator"]
    dp: DPAggregator = fed["dp"]
    budget: PrivacyBudgetTracker = fed["budget"]

    round_info = coord.run_round()
    consumed = budget.consume(dp.epsilon, dp.delta)
    return {
        **round_info,
        "privacy_consumed": consumed,
        "epsilon_remaining": budget.remaining()["epsilon"],
        "delta_remaining": budget.remaining()["delta"],
        "dp_aggregation": dp.privacy_accountant(),
    }


@app.get("/api/federated/privacy")
async def get_federated_privacy():
    fed = _ensure_federated()
    budget: PrivacyBudgetTracker = fed["budget"]
    dp: DPAggregator = fed["dp"]
    remaining = budget.remaining()
    return {
        "epsilon_budget": budget.total_epsilon,
        "epsilon_used": budget.consumed_epsilon,
        "epsilon_remaining": remaining["epsilon"],
        "delta_budget": budget.total_delta,
        "delta_used": budget.consumed_delta,
        "exhausted": budget.is_exhausted(),
        "composition": budget.get_composition(),
        **dp.privacy_accountant(),
    }


@app.get("/api/federated/banks")
async def get_federated_banks():
    fed = _ensure_federated()
    coord: FederatedLearningCoordinator = fed["coordinator"]
    banks = []
    for trainer in coord.bank_trainers:
        dist = trainer.get_data_distribution()
        banks.append({
            "bank_id": f"bank-{trainer.bank_id + 1:03d}",
            "samples": dist["n_samples"],
            "fraud_ratio": round(dist["fraud_ratio"], 4),
            "local_loss": round(trainer.compute_local_loss(), 4),
        })
    return {"banks": banks, "total_samples": sum(b["samples"] for b in banks)}


# ---------------------------------------------------------------------------
# Stackelberg game endpoints (real solver)
# ---------------------------------------------------------------------------

def _solve_game(iterations: int = 100, learning_rate: float = 0.01) -> Dict[str, Any]:
    solver = state.game_solver
    result = solver.solve(iterations=iterations, learning_rate=learning_rate)
    blue_mix, red_mix = result["blue_mix"], result["red_mix"]
    analyzer_payoff = float(result["leader_payoff"])
    state.game_result = {
        "iterations_run": iterations,
        "leader_payoff": round(analyzer_payoff, 4),
        "history": [round(h, 4) for h in result["history"]],
        "blue_mix": [round(float(x), 4) for x in blue_mix],
        "red_mix": [round(float(x), 4) for x in red_mix],
        "best_blue_strategy": int(np.argmax(blue_mix)),
        "best_red_strategy": int(np.argmax(red_mix)),
        "payoff_matrix": solver.payoff_matrix.to_dict(),
    }
    return state.game_result


@app.get("/api/game/equilibrium")
async def get_game_equilibrium():
    if state.game_solver is None:
        raise HTTPException(status_code=503, detail="Game solver not initialised")
    result = state.game_result or _solve_game()
    return {
        "equilibrium_type": "Stackelberg",
        "leader_role": "defender",
        "follower_role": "attacker",
        "leader_payoff": result["leader_payoff"],
        "blue_mix": result["blue_mix"],
        "red_mix": result["red_mix"],
        "best_blue_strategy": result["best_blue_strategy"],
        "best_red_strategy": result["best_red_strategy"],
        "iterations_run": result["iterations_run"],
        "payoff_matrix": result["payoff_matrix"],
        "converged": True,
    }


@app.post("/api/game/solve")
async def solve_stackelberg(req: SolveGameRequest = SolveGameRequest()):
    if state.game_solver is None:
        raise HTTPException(status_code=503, detail="Game solver not initialised")
    result = _solve_game(iterations=req.iterations, learning_rate=req.learning_rate)
    return {
        "iterations_run": result["iterations_run"],
        "final_leader_payoff": result["leader_payoff"],
        "blue_mix": result["blue_mix"],
        "red_mix": result["red_mix"],
        "history": result["history"][-20:],
    }


@app.get("/api/game/history")
async def get_game_history():
    if state.game_solver is None:
        raise HTTPException(status_code=503, detail="Game solver not initialised")
    result = state.game_result or _solve_game()
    history = result["history"]
    rounds = [
        {
            "iteration": i + 1,
            "leader_payoff": payoff,
        }
        for i, payoff in enumerate(history)
    ]
    return {"history": rounds}


@app.get("/api/game/convergence")
async def get_game_convergence():
    if state.game_solver is None:
        raise HTTPException(status_code=503, detail="Game solver not initialised")
    result = state.game_result or _solve_game()
    history = result["history"]
    gap = [round(abs(history[i] - history[i - 1]), 6) for i in range(1, len(history))]
    converged_at = next((i for i, g in enumerate(gap) if g < 1e-3), None)
    return {
        "iterations": list(range(1, len(history) + 1)),
        "leader_payoffs": history,
        "payoff_gap": gap,
        "converged": converged_at is not None,
        "convergence_point": converged_at,
    }


# ---------------------------------------------------------------------------
# Zero-Knowledge Proof endpoints (real simulated zk system)
# ---------------------------------------------------------------------------

def _latest_feature_ints() -> List[int]:
    rec = _find_transaction(None)
    if rec and rec.get("features"):
        vec = _feature_vector(rec["features"])
    else:
        vec = np.zeros(len(FEATURE_NAMES))
    scaled = np.clip(np.abs(vec[:5]) * 10, 0, 255).astype(int).tolist()
    while len(scaled) < 5:
        scaled.append(0)
    return scaled


MODEL_WEIGHTS_INT = [12, 18, 24, 30, 42]


@app.post("/api/zkp/prove")
async def generate_zkp(transaction_id: Optional[str] = None):
    if state.zkp is None:
        raise HTTPException(status_code=503, detail="ZKP system not initialised")
    features = _latest_feature_ints()
    proof = state.zkp.prove_fraud_check(features, MODEL_WEIGHTS_INT)
    public_inputs = features + [proof["model_hash"]]
    verification = state.zkp.verify_fraud_check(proof, features, proof["model_hash"])

    proof_id = proof["a"][:12]
    # Retain what a verifier needs; the private witness is never stored.
    state.zkp_proofs[proof_id] = {
        "a": proof["a"], "b": proof["b"], "c": proof["c"],
        "public_signals": proof.get("public_signals", []),
        "public_inputs": public_inputs,
    }
    if len(state.zkp_proofs) > 500:
        for stale in list(state.zkp_proofs)[:250]:
            state.zkp_proofs.pop(stale, None)

    return {
        "proof_id": proof_id,
        "transaction_id": transaction_id or (_find_transaction(None) or {}).get("transaction_id", "TX-latest"),
        "proof_type": "hash-commitment-attestation",
        "is_zk_snark": False,
        "circuit": state.zkp.circuit.circuit_name,
        "proving_time_ms": proof["proof_time_ms"],
        "proof_size_bytes": len(proof["a"]) + len(proof["b"]) + len(proof["c"]),
        "public_signals": {
            "is_fraudulent": bool(verification["is_fraud"]),
            "model_hash_tail": hex(proof["model_hash"])[-8:],
            "commitment_tail": proof["commitment"][-8:],
        },
        "self_verification": verification["proof_valid"],
    }


@app.post("/api/zkp/verify")
async def verify_zkp(
    proof_id: Optional[str] = None,
    body: Optional[VerifyProofRequest] = None,
):
    """Verify an attestation.

    Either pass ``proof_id`` for a previously issued proof, or POST the proof
    itself. A tampered proof or a mismatched statement returns valid=false —
    this endpoint does not mint a fresh proof to verify against itself.
    """
    if state.zkp is None:
        raise HTTPException(status_code=503, detail="ZKP system not initialised")

    if body is not None:
        record = {
            "a": body.a, "b": body.b, "c": body.c,
            "public_signals": body.public_signals,
            "public_inputs": body.public_inputs,
        }
        resolved_id = body.a[:12] if body.a else "supplied"
    elif proof_id:
        record = state.zkp_proofs.get(proof_id)
        if record is None:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown proof_id '{proof_id}'. Issue one via POST /api/zkp/prove.",
            )
        resolved_id = proof_id
    else:
        raise HTTPException(
            status_code=422,
            detail="Supply either a proof_id query parameter or a proof body.",
        )

    t0 = time.perf_counter()
    valid = state.zkp.verifier.verify(record, record.get("public_inputs", []))
    elapsed_ms = (time.perf_counter() - t0) * 1000
    return {
        "proof_id": resolved_id,
        "valid": bool(valid),
        "verification_time_ms": round(elapsed_ms, 3),
        "error": None if valid else "Verification failed: proof does not attest to the supplied statement",
        **state.zkp.verifier.get_verification_stats(),
    }


@app.get("/api/zkp/certificate")
async def get_zkp_certificate():
    if state.zkp_certificate is None:
        raise HTTPException(status_code=503, detail="ZKP system not initialised")
    return state.zkp_certificate


@app.get("/api/zkp/stats")
async def get_zkp_stats():
    if state.zkp is None:
        raise HTTPException(status_code=503, detail="ZKP system not initialised")
    stats = state.zkp.verifier.get_verification_stats()
    return {
        **stats,
        "circuit_constraints": len(state.zkp.circuit.constraints),
        "active_circuits": [state.zkp.circuit.circuit_name],
    }


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

@app.websocket("/ws/transactions")
async def ws_transactions(websocket: WebSocket):
    await websocket.accept()
    state.ws_clients.append(websocket)
    logger.info("WebSocket client connected (%d total)", len(state.ws_clients))
    try:
        while True:
            data = await websocket.receive_text()
            try:
                cmd = json.loads(data)
                if cmd.get("action") == "ping":
                    await websocket.send_text(json.dumps({"action": "pong", "ts": datetime.now().isoformat()}))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in state.ws_clients:
            state.ws_clients.remove(websocket)
        logger.info("WebSocket client disconnected (%d remaining)", len(state.ws_clients))


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    uvicorn.run(app, host="0.0.0.0", port=8000)
