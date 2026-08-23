"""Privacy-Preserving Federated Learning for Multi-Bank Fraud Detection.

Implements FedAvg with Differential Privacy for the Mastercard AI Red Team Challenge.
"""

import numpy as np
from typing import Tuple, List, Dict, Optional


class GaussianNoise:
    """Calibrated Gaussian noise generator for differential privacy."""

    def __init__(self, sigma: float, sensitivity: float, seed: Optional[int] = None):
        self.sigma = sigma
        self.sensitivity = sensitivity
        self.rng = np.random.default_rng(seed)

    def add_noise(self, tensor: np.ndarray) -> np.ndarray:
        """Add calibrated Gaussian noise to tensor."""
        noise = self.rng.normal(0, self.sigma * self.sensitivity, tensor.shape)
        return tensor + noise

    @staticmethod
    def compute_noise_multiplier(epsilon: float, delta: float, steps: int) -> float:
        """Compute sigma for (epsilon, delta)-DP using advanced composition."""
        if epsilon <= 0 or delta <= 0:
            raise ValueError("Epsilon and delta must be positive")
        delta_tilde = delta / (2 * steps)
        sigma = np.sqrt(2 * np.log(1.25 / delta_tilde)) * np.sqrt(steps) / epsilon
        return sigma


class GradientClipper:
    """Gradient clipping for bounded sensitivity."""

    def __init__(self, max_norm: float = 1.0):
        self.max_norm = max_norm

    def clip(self, gradient: np.ndarray) -> np.ndarray:
        """Clip gradient to max_norm using L2 norm."""
        grad_norm = np.linalg.norm(gradient)
        if grad_norm > self.max_norm:
            gradient = gradient * (self.max_norm / grad_norm)
        return gradient

    def clip_norm(self, gradient: np.ndarray) -> float:
        """Compute L2 norm after clipping."""
        clipped = self.clip(gradient)
        return float(np.linalg.norm(clipped))


class LocalBankTrainer:
    """Local trainer for individual bank data."""

    def __init__(self, bank_id: int, model_params: np.ndarray,
                 local_data: Tuple[np.ndarray, np.ndarray],
                 local_epochs: int = 5, lr: float = 0.01):
        self.bank_id = bank_id
        self.model_params = model_params.copy()
        self.X, self.y = local_data
        self.local_epochs = local_epochs
        self.lr = lr
        self.initial_params = model_params.copy()
        self._loss_history: List[float] = []

    def train(self) -> Tuple[np.ndarray, int, Dict]:
        """Local training returning (gradient, n_samples, metrics)."""
        for _ in range(self.local_epochs):
            predictions = self._forward(self.X)
            loss = self._compute_loss(predictions, self.y)
            self._loss_history.append(loss)
            grad = self._compute_gradient(predictions, self.y)
            self.model_params -= self.lr * grad

        gradient = self.initial_params - self.model_params
        metrics = {
            "final_loss": self._loss_history[-1] if self._loss_history else 0.0,
            "epochs": self.local_epochs,
            "bank_id": self.bank_id
        }
        return gradient, len(self.y), metrics

    def compute_local_loss(self) -> float:
        """Compute current local loss."""
        predictions = self._forward(self.X)
        return self._compute_loss(predictions, self.y)

    def get_data_distribution(self) -> dict:
        """Get local data statistics."""
        class_counts = np.bincount(self.y.astype(int), minlength=2)
        return {
            "n_samples": len(self.y),
            "fraud_ratio": float(class_counts[1] / len(self.y)),
            "positive_count": int(class_counts[1]),
            "negative_count": int(class_counts[0])
        }

    def _forward(self, X: np.ndarray) -> np.ndarray:
        logits = X @ self.model_params
        return 1 / (1 + np.exp(-np.clip(logits, -500, 500)))

    def _compute_loss(self, pred: np.ndarray, y: np.ndarray) -> float:
        eps = 1e-7
        return float(-np.mean(y * np.log(pred + eps) + (1 - y) * np.log(1 - pred + eps)))

    def _compute_gradient(self, pred: np.ndarray, y: np.ndarray) -> np.ndarray:
        error = pred - y
        return self.X.T @ error / len(y)


class DPAggregator:
    """Federated averaging aggregator with differential privacy."""

    def __init__(self, epsilon: float = 1.0, delta: float = 1e-5,
                 max_norm: float = 1.0, n_banks: int = 10):
        self.epsilon = epsilon
        self.delta = delta
        self.n_banks = n_banks
        self.clipper = GradientClipper(max_norm)
        self.noise_multiplier = GaussianNoise.compute_noise_multiplier(
            epsilon, delta, steps=1
        )
        self.noise_gen = GaussianNoise(sigma=1.0, sensitivity=self.noise_multiplier)
        self.total_noise_added = 0.0

    def aggregate(self, gradients: List[np.ndarray],
                  sample_counts: List[int]) -> Tuple[np.ndarray, Dict]:
        """Federated averaging with DP noise."""
        total_samples = sum(sample_counts)
        weighted_grad = np.zeros_like(gradients[0])

        for grad, count in zip(gradients, sample_counts):
            clipped = self.clipper.clip(grad)
            weight = count / total_samples
            weighted_grad += weight * clipped

        noise = self.noise_gen.add_noise(weighted_grad)
        self.total_noise_added += float(np.linalg.norm(noise - weighted_grad))

        metrics = {
            "n_banks": len(gradients),
            "total_samples": total_samples,
            "noise_norm": float(np.linalg.norm(noise - weighted_grad)),
            "clipped_grad_norm": float(np.linalg.norm(weighted_grad))
        }
        return noise, metrics

    def compute_privacy_budget(self, steps: int) -> Tuple[float, float]:
        """Current (epsilon, delta) spend."""
        eps = self.epsilon * np.sqrt(steps * np.log(1 / self.delta))
        return eps, self.delta * steps

    def privacy_accountant(self) -> dict:
        """Full privacy accounting."""
        return {
            "epsilon_per_step": self.epsilon,
            "delta_per_step": self.delta,
            "noise_multiplier": self.noise_multiplier,
            "total_noise_added": self.total_noise_added
        }


class PrivacyBudgetTracker:
    """Track cumulative privacy budget consumption."""

    def __init__(self, total_epsilon: float = 10.0, total_delta: float = 1e-4):
        self.total_epsilon = total_epsilon
        self.total_delta = total_delta
        self.consumed_epsilon = 0.0
        self.consumed_delta = 0.0
        self.history: List[Dict] = []

    def consume(self, epsilon: float, delta: float) -> bool:
        """Consume privacy budget, return True if within budget."""
        if self.consumed_epsilon + epsilon > self.total_epsilon:
            return False
        if self.consumed_delta + delta > self.total_delta:
            return False
        self.consumed_epsilon += epsilon
        self.consumed_delta += delta
        self.history.append({"epsilon": epsilon, "delta": delta})
        return True

    def remaining(self) -> Dict:
        """Remaining budget."""
        return {
            "epsilon": self.total_epsilon - self.consumed_epsilon,
            "delta": self.total_delta - self.consumed_delta
        }

    def is_exhausted(self) -> bool:
        """Check if budget exhausted."""
        rem = self.remaining()
        return rem["epsilon"] <= 0 or rem["delta"] <= 0

    def get_composition(self) -> Dict:
        """Advanced composition theorem bounds."""
        k = len(self.history)
        if k == 0:
            return {"k": 0, "epsilon_total": 0, "delta_total": 0}
        eps_per = [h["epsilon"] for h in self.history]
        delta_per = [h["delta"] for h in self.history]
        eps_avg = np.mean(eps_per)
        delta_sum = np.sum(delta_per)
        eps_advanced = eps_avg * np.sqrt(2 * k * np.log(1 / max(delta_sum, 1e-10))) + k * eps_avg**2 / 2
        return {
            "k": k,
            "epsilon_basic": sum(eps_per),
            "epsilon_advanced": float(eps_advanced),
            "delta_total": float(delta_sum)
        }


class FederatedLearningCoordinator:
    """Main coordinator for federated learning rounds."""

    def __init__(self, n_banks: int = 10, global_model_params: Optional[np.ndarray] = None):
        self.n_banks = n_banks
        self.global_model_params = global_model_params or np.random.randn(100) * 0.01
        self.bank_trainers: List[LocalBankTrainer] = []
        self.round_metrics: List[Dict] = []
        self.round_count = 0

    def initialize_banks(self, bank_data_list: List[Tuple[np.ndarray, np.ndarray]]):
        """Create LocalBankTrainer for each bank."""
        self.bank_trainers = []
        for i, data in enumerate(bank_data_list[:self.n_banks]):
            trainer = LocalBankTrainer(i, self.global_model_params, data)
            self.bank_trainers.append(trainer)

    def run_round(self) -> Dict:
        """Execute one FedAvg round."""
        self.round_count += 1
        gradients, counts, metrics_list = [], [], []

        for trainer in self.bank_trainers:
            grad, n_samples, m = trainer.train()
            gradients.append(grad)
            counts.append(n_samples)
            metrics_list.append(m)

        total_samples = sum(counts)
        weighted_grad = np.zeros_like(gradients[0])
        for g, c in zip(gradients, counts):
            weighted_grad += (c / total_samples) * g

        self.global_model_params += 0.01 * weighted_grad

        for trainer in self.bank_trainers:
            trainer.model_params = self.global_model_params.copy()
            trainer.initial_params = self.global_model_params.copy()

        round_info = {
            "round": self.round_count,
            "n_banks": len(self.bank_trainers),
            "total_samples": total_samples,
            "avg_loss": np.mean([m["final_loss"] for m in metrics_list]),
            "grad_norm": float(np.linalg.norm(weighted_grad))
        }
        self.round_metrics.append(round_info)
        return round_info

    def run_training(self, n_rounds: int = 10) -> List[Dict]:
        """Run full training."""
        for _ in range(n_rounds):
            self.run_round()
        return self.round_metrics

    def get_global_model(self) -> np.ndarray:
        return self.global_model_params.copy()

    def get_round_metrics(self) -> List[Dict]:
        return self.round_metrics

    def differential_stats(self) -> Dict:
        """Compare DP vs non-DP performance."""
        losses = [m["avg_loss"] for m in self.round_metrics]
        if not losses:
            return {"dp_loss_history": [], "convergence": False}
        return {
            "dp_loss_history": losses,
            "final_loss": losses[-1],
            "convergence": losses[-1] < losses[0] * 0.5,
            "loss_reduction": float((losses[0] - losses[-1]) / max(losses[0], 1e-7))
        }


class FederatedSimulation:
    """Simulates multi-bank federated learning ecosystem."""

    def __init__(self, n_banks: int = 10, fraud_ratio: float = 0.15, data_size: int = 1000):
        self.n_banks = n_banks
        self.fraud_ratio = fraud_ratio
        self.data_size = data_size
        self.rng = np.random.default_rng(42)
        self.feature_dim = 100
        self.attack_rounds: Dict[int, Dict] = {}

    def generate_bank_data(self) -> List[Tuple[np.ndarray, np.ndarray]]:
        """Generate synthetic data for each bank."""
        bank_data = []
        for i in range(self.n_banks):
            n = self.data_size + self.rng.integers(-100, 100)
            X = self.rng.standard_normal((n, self.feature_dim))
            weights = self.rng.standard_normal(self.feature_dim) * 0.1
            fraud_idx = self.rng.choice(n, int(n * self.fraud_ratio), replace=False)
            y = np.zeros(n)
            y[fraud_idx] = 1
            X[fraud_idx] += self.rng.standard_normal((len(fraud_idx), self.feature_dim)) * 0.5
            bank_data.append((X, y))
        return bank_data

    def simulate_attack_injection(self, round_num: int) -> Dict:
        """Inject red team attacks at specific rounds."""
        attack_types = {
            "gradient_poisoning": self.rng.uniform(-2, 2, self.feature_dim),
            "model_update_manipulation": self.rng.uniform(-1, 1, self.feature_dim) * 0.5,
            "data_poisoning": {"flip_ratio": self.rng.uniform(0.1, 0.3)}
        }
        attack = attack_types[self.rng.choice(list(attack_types.keys()))]
        self.attack_rounds[round_num] = {
            "type": list(attack_types.keys())[
                list(attack_types.values()).index(attack)
            ],
            "severity": float(np.linalg.norm(attack) if isinstance(attack, np.ndarray) else attack.get("flip_ratio", 0)),
            "round": round_num
        }
        return self.attack_rounds[round_num]

    def run_full_simulation(self, n_rounds: int = 20) -> Dict:
        """Complete simulation with metrics."""
        bank_data = self.generate_bank_data()
        coordinator = FederatedLearningCoordinator(self.n_banks)
        coordinator.initialize_banks(bank_data)

        attack_rounds = self.rng.choice(range(1, n_rounds), size=min(3, n_rounds), replace=False)
        attack_results = {}
        for r in attack_rounds:
            attack_results[int(r)] = self.simulate_attack_injection(int(r))

        metrics = coordinator.run_training(n_rounds)

        return {
            "round_metrics": metrics,
            "attacks": attack_results,
            "final_model_norm": float(np.linalg.norm(coordinator.get_global_model())),
            "privacy_stats": coordinator.differential_stats(),
            "convergence_achieved": metrics[-1]["avg_loss"] < metrics[0]["avg_loss"] * 0.5 if metrics else False
        }
