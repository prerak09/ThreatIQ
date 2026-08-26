"""The MARL loop must actually learn.

An earlier version decayed epsilon, set score = 1 - detection_rate, and never
called a policy update — while the dashboard animated a rising curve from
Math.random(). These tests make that regression impossible to reintroduce
silently.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.red_team.marl_agent import AttackActionSpace, AttackState, MARLOrchestrator


@pytest.fixture()
def orch():
    return MARLOrchestrator()


def test_policy_weights_change_after_evolution(orch):
    """A policy update must move the parameters."""
    agent = next(iter(orch.agents.values()))
    if agent._use_torch:
        before = [p.detach().clone() for p in agent.model.parameters()]
    else:
        before = agent.model.W_actor.copy()

    perf = {at: 0.5 for at in orch.ATTACK_TYPES}
    for _ in range(5):
        orch.evolve_strategies(perf, evaluate_fn=lambda at, a: 0.5, rollout_steps=6)

    if agent._use_torch:
        after = list(agent.model.parameters())
        assert any(not np.allclose(b.numpy(), a.detach().numpy()) for b, a in zip(before, after)), \
            "policy parameters unchanged after evolution — no gradient step ran"
    else:
        assert not np.allclose(before, agent.model.W_actor), \
            "policy parameters unchanged after evolution — no gradient step ran"


def test_history_is_recorded(orch):
    perf = {at: 0.5 for at in orch.ATTACK_TYPES}
    for _ in range(4):
        orch.evolve_strategies(perf, evaluate_fn=lambda at, a: 0.4, rollout_steps=4)

    for at in orch.ATTACK_TYPES:
        assert len(orch.history[at]) == 4, f"{at} history not recorded"
        assert orch.episodes[at] == 16, f"{at} episode count wrong"
    assert orch.epoch == 4


def test_evaluate_fn_actually_drives_the_score(orch):
    """Reported evasion must reflect the supplied detection rate."""
    perf = {at: 0.5 for at in orch.ATTACK_TYPES}
    scores = orch.evolve_strategies(perf, evaluate_fn=lambda at, a: 0.25, rollout_steps=5)
    for at, evasion in scores.items():
        assert abs(evasion - 0.75) < 1e-6, f"{at}: evasion {evasion} does not match 1 - 0.25"


def test_epochs_are_not_a_no_op(orch):
    """Repeated epochs against a varying signal must produce varying history."""
    rng = np.random.default_rng(0)
    perf = {at: 0.5 for at in orch.ATTACK_TYPES}
    for _ in range(10):
        orch.evolve_strategies(
            perf, evaluate_fn=lambda at, a: float(rng.uniform(0.1, 0.9)), rollout_steps=4
        )
    hist = orch.history[orch.ATTACK_TYPES[0]]
    assert len(set(hist)) > 1, "history is constant — epochs are a no-op"


def test_strategy_is_persistent_and_multidimensional(orch):
    """The agent must be able to compound a strategy across dimensions."""
    agent = next(iter(orch.agents.values()))
    defaults = AttackActionSpace()
    for idx in range(7):
        agent._action_from_index(idx)
    current = agent.current_action
    changed = sum(
        1 for f in ("split_count", "velocity_delay_ms", "proxy_rotation",
                    "amount_deviation", "geo_spread", "timing_jitter", "bio_mimicry")
        if getattr(current, f) != getattr(defaults, f)
    )
    assert changed >= 4, (
        f"only {changed} strategy dimensions differ from default — actions are "
        "not accumulating into a compound strategy"
    )


def test_action_snapshot_does_not_alias_agent_state(orch):
    """Returned actions must be snapshots, not references to live state."""
    agent = next(iter(orch.agents.values()))
    snap = agent._action_from_index(6)
    snap.bio_mimicry = 0.999
    assert agent.current_action.bio_mimicry != 0.999


def test_bio_mimicry_is_in_the_action_space():
    """The GenAI-specific evasion lever must exist."""
    action = AttackActionSpace()
    assert hasattr(action, "bio_mimicry")
    assert len(action.to_vector()) == 7


def test_policy_distribution_is_a_valid_simplex(orch):
    perf = {at: 0.5 for at in orch.ATTACK_TYPES}
    orch.evolve_strategies(perf, evaluate_fn=lambda at, a: 0.5, rollout_steps=3)
    dist = orch.policy_distribution(orch.ATTACK_TYPES[0])
    assert len(dist) == 7
    assert abs(sum(dist.values()) - 1.0) < 1e-3
    assert all(v >= 0 for v in dist.values())
