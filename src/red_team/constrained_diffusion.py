"""
Constraint-Guided Tabular Diffusion for Synthetic Transaction Generation.

Extends TabDDPM with hard constraint enforcement during reverse diffusion.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np


class HardConstraint(ABC):
    """Base class for hard constraints on synthetic data."""

    @abstractmethod
    def check(self, x: Any) -> bool:
        """Check if constraint is satisfied."""

    @abstractmethod
    def penalty(self, x: Any) -> float:
        """Compute penalty magnitude (0 if satisfied)."""

    def gradient(self, x: Any) -> np.ndarray:
        """Compute gradient of constraint for guidance. Default returns zeros."""
        return np.zeros_like(np.asarray(x, dtype=np.float64))


class AmountConstraint(HardConstraint):
    """Ensures transaction amount is within valid bounds."""

    def __init__(self, min_amount: float = 0.01, max_amount: float = 1_000_000.0):
        self.min_amount = min_amount
        self.max_amount = max_amount

    def check(self, x: Any) -> bool:
        val = float(x)
        return self.min_amount <= val <= self.max_amount

    def penalty(self, x: Any) -> float:
        val = float(x)
        low = max(0.0, self.min_amount - val)
        high = max(0.0, val - self.max_amount)
        return low ** 2 + high ** 2

    def gradient(self, x: Any) -> np.ndarray:
        val = np.asarray(x, dtype=np.float64)
        grad = np.zeros_like(val)
        lo = val < self.min_amount
        hi = val > self.max_amount
        grad[lo] = -2.0 * (self.min_amount - val[lo])
        grad[hi] = 2.0 * (val[hi] - self.max_amount)
        return grad


class IBANConstraint(HardConstraint):
    """Validates IBAN mod-97 checksum (ISO 13616)."""

    def check(self, x: Any) -> bool:
        return self.validate_checksum(str(x))

    def penalty(self, x: Any) -> float:
        return 0.0 if self.check(x) else 1.0

    @staticmethod
    def validate_checksum(iban: str) -> bool:
        cleaned = re.sub(r'[\s\-]', '', str(iban)).upper()
        if len(cleaned) < 15 or not re.match(r'^[A-Z0-9]+$', cleaned):
            return False
        rearranged = cleaned[4:] + cleaned[:4]
        numeric = ''
        for ch in rearranged:
            if ch.isdigit():
                numeric += ch
            else:
                numeric += str(ord(ch) - ord('A') + 10)
        try:
            return int(numeric) % 97 == 1
        except (ValueError, OverflowError):
            return False


class CurrencyCodeConstraint(HardConstraint):
    """Validates ISO 4217 currency codes."""

    VALID_CODES = frozenset({
        'USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD', 'SEK', 'NOK',
        'DKK', 'SGD', 'HKD', 'KRW', 'INR', 'BRL', 'MXN', 'ZAR', 'RUB', 'CNY',
        'TRY', 'PLN', 'THB', 'IDR', 'MYR', 'PHP', 'CZK', 'HUF', 'ILS', 'CLP',
        'TWD', 'ARS', 'COP', 'PEN', 'EGP', 'NGN', 'KES', 'GHS', 'AED', 'SAR',
        'QAR', 'KWD', 'BHD', 'OMR', 'JOD', 'LBP', 'PKR', 'BDT', 'LKR', 'VND',
    })

    def check(self, x: Any) -> bool:
        return str(x).upper() in self.VALID_CODES

    def penalty(self, x: Any) -> float:
        return 0.0 if self.check(x) else 1.0


class TimeSequenceConstraint(HardConstraint):
    """Ensures transaction timestamps are monotonically increasing."""

    def __init__(self, min_gap_seconds: float = 0.0):
        self.min_gap_seconds = min_gap_seconds

    def check(self, x: Any) -> bool:
        ts = np.asarray(x, dtype=np.float64).ravel()
        if len(ts) < 2:
            return True
        diffs = np.diff(ts)
        return bool(np.all(diffs >= self.min_gap_seconds))

    def penalty(self, x: Any) -> float:
        ts = np.asarray(x, dtype=np.float64).ravel()
        if len(ts) < 2:
            return 0.0
        diffs = np.diff(ts)
        violations = np.maximum(0.0, self.min_gap_seconds - diffs)
        return float(np.sum(violations ** 2))

    def gradient(self, x: Any) -> np.ndarray:
        ts = np.asarray(x, dtype=np.float64).ravel()
        if len(ts) < 2:
            return np.zeros_like(ts)
        grad = np.zeros_like(ts)
        diffs = np.diff(ts)
        viol = (diffs < self.min_gap_seconds).astype(np.float64)
        grad[:-1] -= 2.0 * viol * (self.min_gap_seconds - diffs)
        grad[1:] += 2.0 * viol * (self.min_gap_seconds - diffs)
        return grad


class CreditLimitConstraint(HardConstraint):
    """Ensures transaction amount does not exceed credit limit."""

    def __init__(self, default_limit: float = 5_000.0):
        self.default_limit = default_limit

    def check(self, x: Any, credit_limit: Any = None) -> bool:
        limit = self.default_limit if credit_limit is None else float(credit_limit)
        return float(x) <= limit

    def penalty(self, x: Any, credit_limit: Any = None) -> float:
        limit = self.default_limit if credit_limit is None else float(credit_limit)
        over = max(0.0, float(x) - limit)
        return over ** 2

    def gradient(self, x: Any, credit_limit: Any = None) -> np.ndarray:
        val = np.asarray(x, dtype=np.float64)
        limit = self.default_limit if credit_limit is None else float(credit_limit)
        grad = np.zeros_like(val)
        viol = val > limit
        grad[viol] = 2.0 * (val[viol] - limit)
        return grad


class MerchantCategoryConstraint(HardConstraint):
    """Validates Merchant Category Code against allowed set."""

    VALID_MCCS = frozenset({
        5411, 5412, 5812, 5814, 5999, 4121, 4131, 6011, 6012, 7995,
    })

    def check(self, x: Any) -> bool:
        return int(x) in self.VALID_MCCS

    def penalty(self, x: Any) -> float:
        return 0.0 if self.check(x) else 1.0


class ConstraintRegistry:
    """Manages a collection of named constraints."""

    def __init__(self) -> None:
        self._constraints: Dict[str, HardConstraint] = {}

    def register(self, name: str, constraint: HardConstraint) -> None:
        self._constraints[name] = constraint

    def get_all(self) -> List[HardConstraint]:
        return list(self._constraints.values())

    def names(self) -> List[str]:
        return list(self._constraints.keys())

    def check_all(self, x: Dict[str, Any]) -> Dict[str, bool]:
        results: Dict[str, bool] = {}
        for name, constraint in self._constraints.items():
            if name in x:
                try:
                    results[name] = constraint.check(x[name])
                except Exception:
                    results[name] = False
            else:
                results[name] = True
        return results

    def total_penalty(self, x: Dict[str, Any]) -> float:
        total = 0.0
        for name, constraint in self._constraints.items():
            if name in x:
                try:
                    total += constraint.penalty(x[name])
                except Exception:
                    total += 1.0
        return total

    def constraint_gradient(self, x: Dict[str, Any]) -> Dict[str, np.ndarray]:
        grads: Dict[str, np.ndarray] = {}
        for name, constraint in self._constraints.items():
            if name in x:
                try:
                    grads[name] = constraint.gradient(x[name])
                except Exception:
                    grads[name] = np.zeros(1)
        return grads


class ConstrainedDiffusionModel:
    """Diffusion model with constraint-guided reverse process."""

    def __init__(
        self,
        constraint_registry: ConstraintRegistry,
        gamma: float = 1.0,
        guidance_scale: float = 2.0,
        n_timesteps: int = 1000,
        beta_start: float = 1e-4,
        beta_end: float = 0.02,
    ):
        self.registry = constraint_registry
        self.gamma = gamma
        self.guidance_scale = guidance_scale
        self.n_timesteps = n_timesteps
        self.betas = np.linspace(beta_start, beta_end, n_timesteps)
        self.alphas = 1.0 - self.betas
        self.alpha_bars = np.cumprod(self.alphas)

    def _compute_constraint_grad(
        self, x_t: np.ndarray, feature_names: List[str]
    ) -> np.ndarray:
        grad = np.zeros_like(x_t)
        for col_idx, fname in enumerate(feature_names):
            col_vals = x_t[:, col_idx]
            for constraint in self.registry.get_all():
                try:
                    cgrad = constraint.gradient(col_vals)
                    grad[:, col_idx] += self.guidance_scale * cgrad
                except Exception:
                    pass
        return grad

    def constrained_score(
        self,
        x_t: np.ndarray,
        t: int,
        epsilon_theta: np.ndarray,
        feature_names: List[str],
    ) -> np.ndarray:
        alpha_bar_t = self.alpha_bars[t]
        sqrt_one_minus_alpha_bar = np.sqrt(1.0 - alpha_bar_t)
        score = -epsilon_theta / sqrt_one_minus_alpha_bar
        c_grad = self._compute_constraint_grad(x_t, feature_names)
        return score + self.gamma * c_grad

    def guided_reverse_step(
        self,
        x_t: np.ndarray,
        t: int,
        t_next: int,
        epsilon_theta: np.ndarray,
        feature_names: List[str],
    ) -> np.ndarray:
        alpha_t = self.alphas[t]
        alpha_bar_next = self.alpha_bars[t_next] if t_next >= 0 else 1.0
        beta_t = self.betas[t]
        sqrt_beta_t = np.sqrt(beta_t)
        c_grad = self._compute_constraint_grad(x_t, feature_names)
        eps_guided = epsilon_theta + self.gamma * c_grad
        x0_hat = (x_t - sqrt_beta_t * eps_guided) / np.sqrt(alpha_t)
        x0_hat = np.clip(x0_hat, -5.0, 5.0)
        if t_next >= 0:
            coeff = np.sqrt(alpha_bar_next)
            noise_coeff = np.sqrt(1.0 - alpha_bar_next)
            x_prev = coeff * x0_hat + noise_coeff * np.random.randn(*x_t.shape)
        else:
            x_prev = x0_hat
        return x_prev

    def sample(
        self,
        n_samples: int,
        feature_names: List[str],
        initial_noise: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        dim = len(feature_names)
        if initial_noise is not None:
            x = initial_noise.copy()
        else:
            x = np.random.randn(n_samples, dim)
        for t in range(self.n_timesteps - 1, -1, -1):
            dummy_eps = np.random.randn(*x.shape)
            t_next = t - 1
            x = self.guided_reverse_step(x, t, t_next, dummy_eps, feature_names)
        return x

    def validate_samples(
        self, samples: np.ndarray, feature_names: List[str]
    ) -> Dict[str, float]:
        """Per-column constraint satisfaction rate across ALL samples."""
        n = samples.shape[0]
        report: Dict[str, float] = {}
        for col_idx, fname in enumerate(feature_names):
            col_vals = samples[:, col_idx]
            satisfied = 0
            checked = 0
            for constraint in self.registry.get_all():
                for val in col_vals:
                    try:
                        if constraint.check(val):
                            satisfied += 1
                    except Exception:
                        pass
                    checked += 1
            report[fname] = satisfied / checked if checked > 0 else 1.0
        return report

    @staticmethod
    def enforce_benford_law(amounts: np.ndarray) -> np.ndarray:
        benford_dist = np.log10(1.0 + 1.0 / np.arange(1, 10))
        abs_amounts = np.abs(amounts) + 1e-10
        first_digits = (
            abs_amounts / np.power(10, np.floor(np.log10(abs_amounts)))
        ).astype(int)
        first_digits = np.clip(first_digits, 1, 9)
        adjusted = amounts.copy()
        for d in range(1, 10):
            mask = first_digits == d
            count = np.sum(mask)
            expected = int(benford_dist[d - 1] * len(amounts))
            if count > expected + 10:
                excess = count - expected
                indices = np.where(mask)[0]
                remove_idx = np.random.choice(
                    indices, size=min(excess, count), replace=False
                )
                adjusted[remove_idx] = -9999.0
        return adjusted[adjusted > 0]


class ConstraintViolationReporter:
    """Generates detailed constraint violation reports."""

    def report(
        self,
        samples: np.ndarray,
        registry: ConstraintRegistry,
        feature_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        n_samples = samples.shape[0]
        result: Dict[str, Any] = {
            "total_samples": n_samples,
            "violations": {},
            "summary": {},
        }
        if feature_names is None:
            feature_names = [f"col_{i}" for i in range(samples.shape[1])]
        for col_idx, fname in enumerate(feature_names):
            col_vals = samples[:, col_idx]
            violation_count = 0
            checked = 0
            for constraint in registry.get_all():
                for val in col_vals:
                    try:
                        if not constraint.check(val):
                            violation_count += 1
                    except Exception:
                        violation_count += 1
                    checked += 1
            rate = violation_count / checked if checked > 0 else 0.0
            result["violations"][fname] = {
                "count": violation_count,
                "rate": rate,
                "satisfaction_rate": 1.0 - rate,
            }
        total_violations = sum(
            v["count"] for v in result["violations"].values()
        )
        result["summary"] = {
            "total_violations": total_violations,
            "avg_violation_rate": total_violations
            / (n_samples * max(1, len(feature_names))),
        }
        return result

    def plot_violation_rates(self) -> Dict[str, Any]:
        """Return data structure for visualization (bar chart data)."""
        return {
            "type": "bar",
            "title": "Constraint Violation Rates",
            "xlabel": "Feature",
            "ylabel": "Violation Rate",
        }
