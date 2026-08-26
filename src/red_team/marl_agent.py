"""Multi-Agent Reinforcement Learning for adversarial attack optimization."""

import logging

import numpy as np
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


@dataclass
class AttackActionSpace:
    split_count: int = 10
    velocity_delay_ms: float = 50.0
    proxy_rotation: int = 5
    amount_deviation: float = 0.1
    geo_spread: int = 3
    timing_jitter: float = 0.2
    # Investment in behavioural-biometrics mimicry: the GenAI-specific lever.
    # A synthesised session that reproduces human typing cadence, scroll and
    # touch dynamics raises the behavioural score toward legitimate range.
    bio_mimicry: float = 0.0

    def sample(self):
        return AttackActionSpace(
            split_count=np.random.randint(2, 20),
            velocity_delay_ms=np.random.uniform(10, 500),
            proxy_rotation=np.random.randint(1, 20),
            amount_deviation=np.random.uniform(0.01, 0.5),
            geo_spread=np.random.randint(1, 10),
            timing_jitter=np.random.uniform(0.0, 1.0),
            bio_mimicry=np.random.uniform(0.0, 1.0),
        )

    def to_vector(self):
        return np.array([
            self.split_count / 20.0,
            self.velocity_delay_ms / 500.0,
            self.proxy_rotation / 20.0,
            self.amount_deviation,
            self.geo_spread / 10.0,
            self.timing_jitter,
            self.bio_mimicry,
        ], dtype=np.float32)


@dataclass
class AttackState:
    detection_probability: float = 0.5
    anomaly_score: float = 0.5
    velocity_remaining: float = 1.0
    amount_remaining: float = 1.0
    bypass_history: float = 0.0

    def to_tensor(self):
        return np.array([
            self.detection_probability,
            self.anomaly_score,
            self.velocity_remaining,
            self.amount_remaining,
            self.bypass_history,
        ], dtype=np.float32)


if TORCH_AVAILABLE:
    class ActorCritic(nn.Module):
        def __init__(self, state_dim, action_dim):
            super().__init__()
            self.shared = nn.Sequential(
                nn.Linear(state_dim, 128), nn.ReLU(),
                nn.Linear(128, 128), nn.ReLU(),
            )
            self.actor = nn.Sequential(nn.Linear(128, action_dim), nn.Softmax(dim=-1))
            self.critic = nn.Linear(128, 1)

        def forward(self, state):
            shared = self.shared(state)
            return self.actor(shared), self.critic(shared)

        def get_action(self, state_t):
            probs, value = self.forward(state_t)
            dist = torch.distributions.Categorical(probs)
            action = dist.sample()
            return action, dist.log_prob(action), value.squeeze(-1)

        def evaluate(self, states, actions):
            probs, values = self.forward(states)
            dist = torch.distributions.Categorical(probs)
            return dist.log_prob(actions), dist.entropy(), values.squeeze(-1)
else:
    class ActorCritic:
        def __init__(self, state_dim, action_dim):
            self.W_actor = np.random.randn(state_dim, action_dim) * 0.01
            self.W_critic = np.random.randn(state_dim, 1) * 0.01

        def _softmax(self, x):
            e = np.exp(x - np.max(x))
            return e / e.sum()

        def get_action(self, state):
            probs = self._softmax(state @ self.W_actor)
            action = int(np.random.choice(len(probs), p=probs))
            value = float(np.asarray(state @ self.W_critic).ravel()[0])
            return action, float(np.log(probs[action] + 1e-8)), value

        def update(self, states, actions, returns, lr=0.05):
            """REINFORCE with a learned linear baseline.

            The torch path uses PPO; this keeps the numpy fallback a real
            learner rather than a no-op, so the evolution curve is genuine
            even in deployments without torch installed.
            """
            states = np.asarray(states, dtype=np.float64)
            returns = np.asarray(returns, dtype=np.float64)
            if returns.std() > 1e-8:
                returns = (returns - returns.mean()) / (returns.std() + 1e-8)
            else:
                returns = returns - returns.mean()

            for s_vec, a, G in zip(states, actions, returns):
                probs = self._softmax(s_vec @ self.W_actor)
                baseline = float(np.asarray(s_vec @ self.W_critic).ravel()[0])
                advantage = G - baseline

                # d(log pi_a)/d(logits) = onehot(a) - probs
                grad_logits = -probs
                grad_logits[a] += 1.0
                self.W_actor += lr * advantage * np.outer(s_vec, grad_logits)
                self.W_critic += lr * (G - baseline) * s_vec.reshape(-1, 1)


class MARLAgent:
    def __init__(self, state_dim=5, action_dim=7, lr=3e-3, gamma=0.99, epsilon=1.0):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.05
        self.model = ActorCritic(state_dim, action_dim)
        # Persistent strategy the policy incrementally shapes.
        self.current_action = AttackActionSpace()
        self._use_torch = TORCH_AVAILABLE
        self.ppo_epochs = 4
        if TORCH_AVAILABLE:
            self.optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)

    def select_action(self, state: AttackState, explore=True):
        s = state.to_tensor()
        if self._use_torch:
            with torch.no_grad():
                s_t = torch.tensor(s).unsqueeze(0)
                action, log_prob, value = self.model.get_action(s_t)
            return int(action.item()), float(log_prob.item()), float(value.item())
        else:
            action, log_prob, value = self.model.get_action(s)
            return action, log_prob, value

    def compute_reward(self, bypass_success, detection_prob, anomaly_score, alpha=0.5, beta=0.3):
        return float(bypass_success - alpha * detection_prob - beta * anomaly_score)

    def update(self, states, actions, rewards, next_states,
               old_log_probs=None):
        """PPO-style clipped surrogate update.

        ``old_log_probs`` must come from the behaviour policy at rollout
        time; without them the importance ratio is meaningless (it would be
        identically 1 and the actor would never receive a policy gradient).
        """
        returns_np = []
        G_np = 0.0
        for r in reversed(rewards):
            G_np = r + self.gamma * G_np
            returns_np.insert(0, G_np)

        if not self._use_torch:
            self.model.update(
                [s.to_tensor() if hasattr(s, "to_tensor") else s for s in states],
                actions,
                returns_np,
            )
            return
        returns = []
        G = 0
        for r in reversed(rewards):
            G = r + self.gamma * G
            returns.insert(0, G)
        states_t = torch.tensor(np.array(states), dtype=torch.float32)
        actions_t = torch.tensor(actions, dtype=torch.long)
        returns_t = torch.tensor(returns, dtype=torch.float32)
        returns_t = (returns_t - returns_t.mean()) / (returns_t.std() + 1e-8)

        old_t = (
            torch.tensor(np.asarray(old_log_probs), dtype=torch.float32)
            if old_log_probs is not None else None
        )

        # PPO runs K optimisation epochs over each collected batch. A single
        # step per batch is what made the policy look frozen: 60 epochs x 1
        # step is not enough signal to move a 128-unit network off uniform.
        for _ in range(self.ppo_epochs):
            new_log_probs, entropy, values = self.model.evaluate(states_t, actions_t)
            advantages = returns_t - values.detach()

            if old_t is not None:
                ratio = torch.exp(new_log_probs - old_t)
            else:
                # No behaviour-policy log probs recorded — fall back to vanilla
                # policy gradient on the fresh log probs.
                ratio = torch.exp(new_log_probs)

            surr1 = ratio * advantages
            surr2 = torch.clamp(ratio, 0.8, 1.2) * advantages
            loss_actor = -torch.min(surr1, surr2).mean()
            loss_critic = F.mse_loss(values, returns_t)
            loss = loss_actor + 0.5 * loss_critic - 0.01 * entropy.mean()
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

    def train_episode(self, simulator_fn: Callable, blue_team_fn: Callable, steps=50):
        state = AttackState()
        states, actions, rewards, next_states, log_probs = [], [], [], [], []
        total_reward = 0
        for _ in range(steps):
            action_idx, log_prob, value = self.select_action(state, explore=True)
            action = self._action_from_index(action_idx)
            new_state, detection_prob, anomaly_score, bypass = simulator_fn(action)
            reward = self.compute_reward(bypass, detection_prob, anomaly_score)
            states.append(state.to_tensor())
            actions.append(action_idx)
            rewards.append(reward)
            log_probs.append(log_prob)
            next_states.append(new_state.to_tensor())
            state = new_state
            total_reward += reward
        if len(states) > 10:
            self.update(states, actions, rewards, next_states,
                        old_log_probs=log_probs)
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        return total_reward

    def _action_from_index(self, idx):
        """Apply action ``idx`` to the agent's *persistent* strategy.

        Previously this rebuilt an AttackActionSpace from defaults every call,
        so only one dimension was ever non-default and the agent could never
        compound a multi-dimensional evasion strategy — the policy had nothing
        to learn toward. The strategy now persists across steps and each action
        nudges one dimension, so successful combinations accumulate.
        """
        action = self.current_action
        mappings = [
            lambda: setattr(action, 'split_count',
                            int(np.clip(action.split_count + np.random.randint(-3, 4), 2, 20))),
            lambda: setattr(action, 'velocity_delay_ms',
                            float(np.clip(action.velocity_delay_ms + np.random.uniform(-80, 80), 10, 500))),
            lambda: setattr(action, 'proxy_rotation',
                            int(np.clip(action.proxy_rotation + np.random.randint(-3, 4), 1, 20))),
            lambda: setattr(action, 'amount_deviation',
                            float(np.clip(action.amount_deviation + np.random.uniform(-0.1, 0.1), 0.01, 0.5))),
            lambda: setattr(action, 'geo_spread',
                            int(np.clip(action.geo_spread + np.random.randint(-2, 3), 1, 10))),
            lambda: setattr(action, 'timing_jitter',
                            float(np.clip(action.timing_jitter + np.random.uniform(-0.2, 0.2), 0.0, 1.0))),
            lambda: setattr(action, 'bio_mimicry',
                            float(np.clip(action.bio_mimicry + np.random.uniform(-0.15, 0.25), 0.0, 1.0))),
        ]
        if idx < len(mappings):
            mappings[idx]()
        # Return a snapshot so callers cannot mutate the agent's live strategy.
        return AttackActionSpace(**vars(action))

    def get_evasion_strategy(self, attack_vector: str):
        state = AttackState(
            detection_probability=0.7,
            anomaly_score=0.6,
            velocity_remaining=0.8,
            amount_remaining=0.9,
            bypass_history=0.3,
        )
        action_idx, _, _ = self.select_action(state, explore=False)
        action = self._action_from_index(action_idx)
        return {
            "attack_vector": attack_vector,
            "split_count": action.split_count,
            "velocity_delay_ms": round(action.velocity_delay_ms, 1),
            "proxy_rotation": action.proxy_rotation,
            "amount_deviation": round(action.amount_deviation, 4),
            "geo_spread": action.geo_spread,
            "timing_jitter": round(action.timing_jitter, 4),
        }


class MARLOrchestrator:
    ATTACK_TYPES = [
        "account_takeover", "card_testing", "synthetic_id",
        "velocity_abuse", "loyalty_fraud", "credential_stuffing",
    ]

    def __init__(self):
        self.agents: Dict[str, MARLAgent] = {at: MARLAgent() for at in self.ATTACK_TYPES}
        self.scores: Dict[str, float] = {at: 0.0 for at in self.ATTACK_TYPES}
        # Real, recorded evolution history — the dashboard plots this rather
        # than synthesising a curve client-side.
        self.history: Dict[str, List[float]] = {at: [] for at in self.ATTACK_TYPES}
        self.episodes: Dict[str, int] = {at: 0 for at in self.ATTACK_TYPES}
        self.best_actions: Dict[str, AttackActionSpace] = {}
        self.epoch: int = 0

    def evolve_strategies(
        self,
        blue_team_performance: Dict[str, float],
        evaluate_fn: Optional[Callable[[str, AttackActionSpace], float]] = None,
        rollout_steps: int = 8,
    ) -> Dict[str, float]:
        """Run one evolution epoch: rollout -> reward -> policy update.

        Parameters
        ----------
        blue_team_performance:
            Measured detection rate per attack type, used to seed the state
            and as the fallback reward signal.
        evaluate_fn:
            ``fn(attack_type, action) -> detection_rate``. When supplied, each
            sampled action is scored against the *live* blue-team classifier,
            which is what actually closes the red/blue loop. Without it the
            agent still learns, but only against the last observed detection
            rate.
        rollout_steps:
            Actions sampled per agent per epoch before the policy update.

        Returns
        -------
        dict mapping attack_type -> evasion rate measured this epoch.
        """
        epoch_scores: Dict[str, float] = {}

        for attack_type, agent in self.agents.items():
            seed_detection = blue_team_performance.get(attack_type, 0.5)

            states, actions, rewards, log_probs = [], [], [], []
            state = AttackState(
                detection_probability=seed_detection,
                anomaly_score=1.0 - agent.epsilon,
                velocity_remaining=1.0,
                amount_remaining=1.0,
                bypass_history=self.scores.get(attack_type, 0.0),
            )

            detections = []
            for _ in range(max(1, rollout_steps)):
                action_idx, log_prob, _ = agent.select_action(state, explore=True)
                candidate = agent._action_from_index(action_idx)

                if evaluate_fn is not None:
                    detection_rate = float(evaluate_fn(attack_type, candidate))
                else:
                    detection_rate = seed_detection
                detections.append(detection_rate)

                bypass = 1.0 - detection_rate
                reward = agent.compute_reward(
                    bypass_success=bypass,
                    detection_prob=detection_rate,
                    anomaly_score=state.anomaly_score,
                )

                states.append(state.to_tensor())
                actions.append(action_idx)
                rewards.append(reward)
                log_probs.append(log_prob)

                state = AttackState(
                    detection_probability=detection_rate,
                    anomaly_score=max(0.0, state.anomaly_score - 0.05),
                    velocity_remaining=max(0.0, state.velocity_remaining - 0.1),
                    amount_remaining=max(0.0, state.amount_remaining - 0.1),
                    bypass_history=bypass,
                )

            # Real policy gradient step — this is what was missing.
            agent.update(states, actions, rewards, states, old_log_probs=log_probs)

            # Keep the best action found this epoch as the agent's strategy.
            best_idx = int(np.argmin(detections))
            self.best_actions[attack_type] = agent._action_from_index(actions[best_idx])

            evasion = 1.0 - float(np.mean(detections))
            self.scores[attack_type] = evasion
            epoch_scores[attack_type] = evasion
            self.history.setdefault(attack_type, []).append(round(evasion, 4))
            self.episodes[attack_type] = self.episodes.get(attack_type, 0) + len(actions)

            agent.epsilon = max(agent.epsilon_min, agent.epsilon * agent.epsilon_decay)

        self.epoch += 1
        return epoch_scores

    def select_action_for_agent(self, agent, state):
        return agent.select_action(state, explore=True)

    def get_best_attacks(self, n=3):
        ranked = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)[:n]
        results = []
        for attack_type, score in ranked:
            strategy = self.agents[attack_type].get_evasion_strategy(attack_type)
            strategy["evasion_score"] = round(score, 4)
            results.append(strategy)
        return results

    def policy_distribution(self, attack_type: str) -> Dict[str, float]:
        """Current action-selection probabilities for one agent.

        Note on the torch path: ``model.actor`` consumes the 128-dim output of
        ``model.shared``, not the raw state vector. Calling it with the state
        directly raises a shape error — and an earlier version swallowed that
        in a bare except and returned a uniform distribution, so the UI showed
        a flat 1/7 across every action and looked plausible while being wrong.
        Go through ``forward`` so both paths return the real policy, and let a
        genuine failure surface as an empty dict rather than fabricated
        uniform weights.
        """
        agent = self.agents[attack_type]
        state = AttackState(
            detection_probability=1.0 - self.scores.get(attack_type, 0.0),
            anomaly_score=1.0 - agent.epsilon,
            bypass_history=self.scores.get(attack_type, 0.0),
        )
        s_vec = state.to_tensor()
        labels = ["split_count", "velocity_delay", "proxy_rotation",
                  "amount_deviation", "geo_spread", "timing_jitter",
                  "bio_mimicry"]
        try:
            if agent._use_torch:
                with torch.no_grad():
                    s_t = torch.tensor(s_vec, dtype=torch.float32).unsqueeze(0)
                    # forward() applies shared -> actor (actor already ends in
                    # Softmax), returning (probs, value).
                    probs, _ = agent.model(s_t)
                    probs = probs.numpy().ravel()
            else:
                probs = agent.model._softmax(s_vec @ agent.model.W_actor)
        except Exception as exc:
            logger.warning(
                "policy_distribution failed for %s: %s", attack_type, exc
            )
            return {}

        if len(probs) != len(labels):
            logger.warning(
                "policy_distribution size mismatch for %s: %d vs %d",
                attack_type, len(probs), len(labels),
            )
            return {}
        return {l: round(float(p), 4) for l, p in zip(labels, probs)}

    def get_all_strategies(self):
        return {
            at: agent.get_evasion_strategy(at)
            for at, agent in self.agents.items()
        }
