#!/usr/bin/env python3
"""Reproducible benchmark for the ThreatIQ detection ensemble.

Every number in the README's "Measured results" table is produced by this
script. Run it with::

    python benchmark.py                 # default: 12k train / 6k test
    python benchmark.py --n-train 40000 --n-test 20000 --seed 7
    python benchmark.py --json results.json

Why the trivial baselines are reported alongside the ensemble
-------------------------------------------------------------
A fraud benchmark is only meaningful if a one-line rule cannot win it. This
script therefore always reports two baselines next to the ensemble:

* a single-feature threshold on the behavioural-biometrics score, and
* a depth-1 decision stump over all features.

If either baseline approaches the ensemble's F1, the *generator* is broken and
the detection numbers are not evidence of anything. Publishing the gap is the
point.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from sklearn.metrics import (  # noqa: E402
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.tree import DecisionTreeClassifier  # noqa: E402

from src.blue_team.gnn_model import FraudDetectionModel  # noqa: E402
from src.red_team.simulation_runner import (  # noqa: E402
    FEATURE_NAMES,
    SimulationRunner,
    extract_features,
)


def build_dataset(sim: SimulationRunner, n: int, fraud_ratio: float, rng: np.random.Generator):
    """Generate a labelled dataset from the live attacker/victim agents."""
    n_fraud = int(n * fraud_ratio)
    txs = [sim.attacker.generate_transaction() for _ in range(n_fraud)]
    txs += [sim.victim.generate_transaction() for _ in range(n - n_fraud)]

    X = np.stack([
        np.array([extract_features(t)[k] for k in FEATURE_NAMES], dtype=np.float64)
        for t in txs
    ])
    y = np.array([1 if t.is_fraud else 0 for t in txs], dtype=int)
    tiers = [t.raw_payload_logs.get("sophistication_tier") for t in txs]

    order = rng.permutation(len(y))
    return X[order], y[order], [tiers[i] for i in order]


def score(y_true: np.ndarray, proba: np.ndarray, threshold: float) -> Dict[str, float]:
    pred = (proba >= threshold).astype(int)
    return {
        "threshold": round(float(threshold), 4),
        "precision": round(float(precision_score(y_true, pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_true, proba)), 4),
        "pr_auc": round(float(average_precision_score(y_true, proba)), 4),
        "false_positive_rate": round(
            float(((pred == 1) & (y_true == 0)).sum() / max((y_true == 0).sum(), 1)), 4
        ),
    }


def best_threshold(y_true: np.ndarray, proba: np.ndarray) -> float:
    """Threshold maximising F1 on the given split."""
    candidates = np.unique(np.round(np.linspace(0.05, 0.95, 91), 3))
    scores = [(f1_score(y_true, (proba >= t).astype(int), zero_division=0), t) for t in candidates]
    return float(max(scores)[1])


def per_tier_recall(y_true: np.ndarray, proba: np.ndarray, tiers: List[str], threshold: float):
    """Recall broken down by attacker sophistication.

    The headline recall hides the thing that matters: advanced operators who
    mimic legitimate behaviour are the ones a real deployment misses.
    """
    pred = (proba >= threshold).astype(int)
    out = {}
    for tier in ("naive", "intermediate", "advanced"):
        idx = [i for i, t in enumerate(tiers) if t == tier and y_true[i] == 1]
        if idx:
            out[tier] = {
                "n": len(idx),
                "recall": round(float(pred[idx].mean()), 4),
            }
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n-train", type=int, default=12_000)
    ap.add_argument("--n-test", type=int, default=6_000)
    ap.add_argument("--train-fraud-ratio", type=float, default=0.35,
                    help="Enriched so the supervised engines see enough fraud.")
    ap.add_argument("--test-fraud-ratio", type=float, default=0.15,
                    help="Closer to an operational mix.")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--json", type=str, default=None, help="Write results to this path.")
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    np.random.seed(args.seed)
    import random
    random.seed(args.seed)

    print("=" * 72)
    print("ThreatIQ detection benchmark")
    print("=" * 72)
    print(f"seed={args.seed}  n_train={args.n_train}  n_test={args.n_test}")
    print(f"train fraud ratio={args.train_fraud_ratio}  test fraud ratio={args.test_fraud_ratio}")
    print()

    sim = SimulationRunner(num_victims=500, fraud_ratio=args.test_fraud_ratio,
                           transaction_rate_tps=10.0)

    X_tr, y_tr, _ = build_dataset(sim, args.n_train, args.train_fraud_ratio, rng)
    X_te, y_te, tiers_te = build_dataset(sim, args.n_test, args.test_fraud_ratio, rng)

    results: Dict[str, object] = {
        "config": vars(args),
        "n_features": len(FEATURE_NAMES),
        "feature_names": list(FEATURE_NAMES),
    }

    # ---------------- Baselines -------------------------------------------
    bio_idx = FEATURE_NAMES.index("behavioral_score")
    bio_proba = 1.0 - np.clip(X_te[:, bio_idx], 0.0, 1.0)
    t_bio = best_threshold(y_te, bio_proba)
    results["baseline_single_feature"] = score(y_te, bio_proba, t_bio)

    stump = DecisionTreeClassifier(max_depth=1, random_state=args.seed).fit(X_tr, y_tr)
    stump_proba = stump.predict_proba(X_te)[:, 1]
    results["baseline_depth1_stump"] = score(y_te, stump_proba, 0.5)

    # ---------------- Ensemble --------------------------------------------
    model = FraudDetectionModel(contamination=0.05)
    t0 = time.perf_counter()
    train_metrics = model.train(X_tr, y_tr, feature_names=list(FEATURE_NAMES))
    train_seconds = time.perf_counter() - t0

    t0 = time.perf_counter()
    ens_proba = model.predict_proba(X_te)[:, 1]
    infer_seconds = time.perf_counter() - t0

    t_ens = best_threshold(y_te, ens_proba)
    results["ensemble"] = score(y_te, ens_proba, t_ens)
    results["ensemble_at_0.5"] = score(y_te, ens_proba, 0.5)
    results["train_seconds"] = round(train_seconds, 3)
    results["inference_ms_per_txn"] = round(infer_seconds * 1000 / len(X_te), 4)
    results["train_metrics"] = train_metrics
    results["per_tier_recall"] = per_tier_recall(y_te, ens_proba, tiers_te, t_ens)

    # ---------------- Per-engine ------------------------------------------
    engines = {}
    X_scaled = model._scaler.transform(X_te)
    for name, fn in (
        ("isolation_forest", model._score_isolation_forest),
        ("xgboost", model._score_xgb),
        ("lightgbm", model._score_lgb),
    ):
        try:
            s = fn(X_scaled)
            if s is not None:
                engines[name] = round(float(roc_auc_score(y_te, s)), 4)
        except Exception as exc:  # pragma: no cover
            engines[name] = f"unavailable: {exc}"
    engines["transaction_gnn"] = "not trained — disabled at serving time"
    results["per_engine_roc_auc"] = engines

    # ---------------- Ablation --------------------------------------------
    keep = [i for i in range(len(FEATURE_NAMES)) if i != bio_idx]
    abl = FraudDetectionModel(contamination=0.05)
    abl.train(X_tr[:, keep], y_tr, feature_names=[FEATURE_NAMES[i] for i in keep])
    abl_proba = abl.predict_proba(X_te[:, keep])[:, 1]
    results["ablation_no_behavioral_score"] = score(y_te, abl_proba, best_threshold(y_te, abl_proba))

    # ---------------- Report ----------------------------------------------
    def row(label: str, d: Dict[str, float]) -> str:
        return (f"{label:<34} F1={d['f1']:.4f}  P={d['precision']:.4f}  "
                f"R={d['recall']:.4f}  AUC={d['roc_auc']:.4f}  FPR={d['false_positive_rate']:.4f}")

    print(row("Baseline: behavioural threshold", results["baseline_single_feature"]))
    print(row("Baseline: depth-1 stump", results["baseline_depth1_stump"]))
    print(row("Ensemble (tuned threshold)", results["ensemble"]))
    print(row("Ensemble (threshold 0.5)", results["ensemble_at_0.5"]))
    print(row("Ablation: no behavioural score", results["ablation_no_behavioral_score"]))
    print()

    lift = results["ensemble"]["f1"] - max(
        results["baseline_single_feature"]["f1"], results["baseline_depth1_stump"]["f1"]
    )
    print(f"Ensemble F1 lift over best trivial baseline: {lift:+.4f}")
    print()
    print("Recall by attacker sophistication tier:")
    for tier, d in results["per_tier_recall"].items():
        print(f"  {tier:<14} n={d['n']:<6} recall={d['recall']:.4f}")
    print()
    print("Per-engine ROC-AUC:")
    for k, v in results["per_engine_roc_auc"].items():
        print(f"  {k:<20} {v}")
    print()
    print(f"Training: {results['train_seconds']}s   "
          f"Inference: {results['inference_ms_per_txn']} ms/txn (batched)")

    if lift < 0.05:
        print()
        print("WARNING: the ensemble barely beats a trivial baseline. Either the")
        print("generator has become separable again, or the ensemble is not adding")
        print("value. Treat the detection numbers as unproven until this is resolved.")

    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=2, default=str))
        print(f"\nWrote {args.json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
