"""Guards against the failure mode that invalidates the whole submission.

If the attacker and victim generators drift back into producing linearly
separable traffic, every detection metric becomes meaningless. These tests
fail loudly when that happens.
"""

from __future__ import annotations

import numpy as np
import pytest
from sklearn.metrics import f1_score
from sklearn.tree import DecisionTreeClassifier

from src.red_team.simulation_runner import FEATURE_NAMES, SimulationRunner, extract_features


@pytest.fixture(scope="module")
def sim():
    return SimulationRunner(num_victims=200, fraud_ratio=0.15, transaction_rate_tps=10.0)


def _dataset(sim, n_fraud=450, n_legit=2550):
    """Roughly 15% fraud — an operational mix, not a balanced one.

    A 50/50 split inflates F1 for any majority-ish rule and would make this
    guard pass on a generator that is in fact separable.
    """
    txs = [sim.attacker.generate_transaction() for _ in range(n_fraud)]
    txs += [sim.victim.generate_transaction() for _ in range(n_legit)]
    X = np.stack([
        np.array([extract_features(t)[k] for k in FEATURE_NAMES]) for t in txs
    ])
    y = np.array([1 if t.is_fraud else 0 for t in txs])
    return X, y, txs


def test_behavioural_score_ranges_overlap(sim):
    """Fraud and legitimate biometric scores must genuinely overlap."""
    fraud = np.array([
        sim.attacker.generate_transaction().behavioral_biometrics_score
        for _ in range(1500)
    ])
    legit = np.array([
        sim.victim.generate_transaction().behavioral_biometrics_score
        for _ in range(1500)
    ])

    lo, hi = max(fraud.min(), legit.min()), min(fraud.max(), legit.max())
    assert hi > lo, "fraud and legitimate biometric ranges are disjoint"

    in_overlap_fraud = ((fraud >= lo) & (fraud <= hi)).mean()
    in_overlap_legit = ((legit >= lo) & (legit <= hi)).mean()
    assert in_overlap_fraud > 0.5, f"only {in_overlap_fraud:.1%} of fraud lies in the overlap"
    assert in_overlap_legit > 0.5, f"only {in_overlap_legit:.1%} of legit lies in the overlap"


def test_no_single_feature_separates_classes(sim):
    """A depth-1 stump must not solve the task."""
    X, y, _ = _dataset(sim)
    stump = DecisionTreeClassifier(max_depth=1, random_state=0).fit(X, y)
    f1 = f1_score(y, stump.predict(X))
    assert f1 < 0.70, (
        f"a depth-1 decision stump reaches F1={f1:.3f}. The generator is separable "
        "and every downstream detection metric is meaningless."
    )


def test_all_sophistication_tiers_are_produced(sim):
    """The attacker mixture must actually emit every tier."""
    tiers = [
        sim.attacker.generate_transaction().raw_payload_logs.get("sophistication_tier")
        for _ in range(2000)
    ]
    counts = {t: tiers.count(t) for t in set(tiers)}
    for tier in ("naive", "intermediate", "advanced"):
        assert counts.get(tier, 0) > 50, f"tier '{tier}' underrepresented: {counts}"


def test_advanced_tier_is_actually_stealthy(sim):
    """Advanced operators must sit inside the legitimate biometric band."""
    advanced = [
        t.behavioral_biometrics_score
        for t in (sim.attacker.generate_transaction() for _ in range(4000))
        if t.raw_payload_logs.get("sophistication_tier") == "advanced"
    ]
    assert advanced, "no advanced-tier transactions generated"
    assert np.mean(advanced) > 0.55, "advanced tier is not mimicking legitimate behaviour"


def test_fraud_rings_share_infrastructure(sim):
    """Ring activity must reuse devices, or ring detection can never fire."""
    txs = [sim.attacker.generate_transaction() for _ in range(1200)]
    ring_txs = [t for t in txs if t.raw_payload_logs.get("ring_id")]
    assert len(ring_txs) > 200, "almost no ring-attributed transactions"

    devices = [t.device_fingerprint for t in ring_txs]
    assert len(set(devices)) < len(devices) * 0.5, "ring transactions do not reuse devices"


def test_legitimate_traffic_has_a_hard_tail(sim):
    """Some legitimate traffic must look atypical, or FPR is unrealistically 0."""
    legit = [sim.victim.generate_transaction() for _ in range(2000)]
    low_bio = [t for t in legit if t.behavioral_biometrics_score < 0.7]
    assert len(low_bio) > 100, "no atypical-but-legitimate sessions in the population"


def test_amount_distributions_overlap(sim):
    """Amount alone must not separate the classes."""
    fraud = np.array([sim.attacker.generate_transaction().amount for _ in range(1500)])
    legit = np.array([sim.victim.generate_transaction().amount for _ in range(1500)])
    overlap_lo, overlap_hi = max(fraud.min(), legit.min()), min(fraud.max(), legit.max())
    assert overlap_hi > overlap_lo
    assert ((fraud >= overlap_lo) & (fraud <= overlap_hi)).mean() > 0.8


def test_features_are_finite(sim):
    X, _, _ = _dataset(sim, 300, 300)
    assert np.isfinite(X).all(), "non-finite values in the feature matrix"
