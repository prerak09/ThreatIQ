"""Game-Theoretic Stackelberg Equilibrium Solver for AI Red Team Challenge."""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum


class AttackType(Enum):
    EVASION = "evasion"
    POISONING = "poisoning"
    MODEL_STEALING = "model_stealing"
    ADVERSARIAL = "adversarial"


class DefenseFeature(Enum):
    ANOMALY_DETECTION = "anomaly_detection"
    INPUT_VALIDATION = "input_validation"
    MODEL_HARDENING = "model_hardening"
    RATE_LIMITING = "rate_limiting"


@dataclass
class PayoffMatrix:
    blue_payoffs: np.ndarray
    red_payoffs: np.ndarray
    
    def __post_init__(self):
        if self.blue_payoffs.shape != self.red_payoffs.shape:
            raise ValueError("Payoff matrices must have same dimensions")
    
    def set_payoff(self, blue_row: int, red_col: int, blue_val: float, red_val: float):
        self.blue_payoffs[blue_row, red_col] = blue_val
        self.red_payoffs[blue_row, red_col] = red_val
    
    def get_blue_payoffs(self) -> np.ndarray:
        return self.blue_payoffs.copy()
    
    def get_red_payoffs(self) -> np.ndarray:
        return self.red_payoffs.copy()
    
    def to_dict(self) -> Dict:
        return {
            "blue_payoffs": self.blue_payoffs.tolist(),
            "red_payoffs": self.red_payoffs.tolist(),
            "shape": self.blue_payoffs.shape
        }


@dataclass
class BlueTeamStrategy:
    threshold: float = 0.5
    features_used: List[DefenseFeature] = field(default_factory=lambda: list(DefenseFeature))
    _mut_rate: float = 0.1
    
    def compute_payoff(self, attack_dist: np.ndarray, intensity: float) -> float:
        defense_strength = self.threshold * len(self.features_used) / 4
        detection_prob = min(1.0, defense_strength * 1.5)
        payoff = detection_prob * 10 - (1 - detection_prob) * intensity * 5
        return float(np.clip(payoff, -10, 10))
    
    def mutate(self) -> 'BlueTeamStrategy':
        new_threshold = np.clip(self.threshold + np.random.normal(0, self._mut_rate), 0.1, 0.9)
        new_features = self.features_used.copy()
        if np.random.random() < 0.3:
            if len(new_features) > 1 and np.random.random() < 0.5:
                new_features.pop(np.random.randint(len(new_features)))
            else:
                available = [f for f in DefenseFeature if f not in new_features]
                if available:
                    new_features.append(np.random.choice(available))
        return BlueTeamStrategy(threshold=new_threshold, features_used=new_features)


@dataclass
class RedTeamStrategy:
    attack_type: AttackType = AttackType.EVASION
    intensity: float = 0.5
    evasion_budget: float = 1.0
    _mut_rate: float = 0.15
    
    def compute_payoff(self, defense_threshold: float) -> float:
        effectiveness = {
            AttackType.EVASION: 1.0 - defense_threshold * 0.8,
            AttackType.POISONING: 0.7 - defense_threshold * 0.5,
            AttackType.MODEL_STEALING: 0.9 - defense_threshold * 0.6,
            AttackType.ADVERSARIAL: 0.8 - defense_threshold * 0.7
        }
        base = effectiveness.get(self.attack_type, 0.5)
        cost = (self.intensity * self.evasion_budget) * 0.3
        return float(np.clip(base * self.intensity * 10 - cost, -10, 10))
    
    def mutate(self) -> 'RedTeamStrategy':
        new_intensity = np.clip(self.intensity + np.random.normal(0, self._mut_rate), 0.1, 1.0)
        new_budget = np.clip(self.evasion_budget + np.random.normal(0, self._mut_rate * 2), 0.5, 3.0)
        new_type = self.attack_type
        if np.random.random() < 0.2:
            new_type = np.random.choice(list(AttackType))
        return RedTeamStrategy(attack_type=new_type, intensity=new_intensity, evasion_budget=new_budget)


class StackelbergSolver:
    def __init__(self, blue_strategies: List[BlueTeamStrategy], red_strategies: List[RedTeamStrategy]):
        self.blue_strategies = blue_strategies
        self.red_strategies = red_strategies
        n_blue = len(blue_strategies)
        n_red = len(red_strategies)
        self.payoff_matrix = PayoffMatrix(
            blue_payoffs=np.zeros((n_blue, n_red)),
            red_payoffs=np.zeros((n_blue, n_red))
        )
        self._compute_payoffs()
    
    def _compute_payoffs(self):
        for i, blue in enumerate(self.blue_strategies):
            for j, red in enumerate(self.red_strategies):
                blue_pay = blue.compute_payoff(np.array([red.intensity]), red.intensity)
                red_pay = red.compute_payoff(blue.threshold)
                self.payoff_matrix.set_payoff(i, j, blue_pay, red_pay)
    
    def _best_response_red(self, blue_idx: int) -> int:
        red_payoffs = self.payoff_matrix.get_red_payoffs()[blue_idx, :]
        return int(np.argmax(red_payoffs))
    
    def _leader_payoff(self, blue_idx: int, blue_mix: np.ndarray) -> float:
        red_best = self._best_response_red(blue_idx)
        return float(np.sum(blue_mix * self.payoff_matrix.get_blue_payoffs()[:, red_best]))
    
    def solve(self, iterations: int = 100, learning_rate: float = 0.01) -> Dict:
        n_blue = len(self.blue_strategies)
        n_red = len(self.red_strategies)
        blue_mix = np.ones(n_blue) / n_blue
        red_mix = np.ones(n_red) / n_red
        
        history = []
        for _ in range(iterations):
            for i in range(n_blue):
                best_red = self._best_response_red(i)
                current_pay = np.dot(blue_mix, self.payoff_matrix.get_blue_payoffs()[:, best_red])
                gradient = self.payoff_matrix.get_blue_payoffs()[i, best_red] - current_pay
                blue_mix[i] += learning_rate * gradient
            
            blue_mix = np.clip(blue_mix, 0.01, 1.0)
            blue_mix /= blue_mix.sum()
            
            red_payoffs = red_mix @ self.payoff_matrix.get_red_payoffs().T
            best_responses = np.argmax(self.payoff_matrix.get_red_payoffs(), axis=1)
            red_mix_new = np.zeros(n_red)
            for i in range(n_blue):
                red_mix_new[best_responses[i]] += blue_mix[i]
            red_mix = red_mix_new
            red_mix = np.clip(red_mix, 0.01, 1.0)
            red_mix /= red_mix.sum()
            
            leader_pay = sum(blue_mix[i] * self.payoff_matrix.get_blue_payoffs()[i, self._best_response_red(i)] for i in range(n_blue))
            history.append(leader_pay)
        
        return {"blue_mix": blue_mix, "red_mix": red_mix, "leader_payoff": history[-1], "history": history}
    
    def compute_equilibrium_mixed(self) -> Dict:
        result = self.solve(iterations=200)
        return {"mixed_strategy": result["blue_mix"], "opponent_mix": result["red_mix"], "value": result["leader_payoff"]}
    
    def verify_equilibrium(self, blue_mix: np.ndarray, red_mix: np.ndarray, tol: float = 0.01) -> bool:
        n_blue = len(self.blue_strategies)
        blue_expected = blue_mix @ self.payoff_matrix.get_blue_payoffs() @ red_mix
        for i in range(n_blue):
            deviation_payoff = np.dot(blue_mix, self.payoff_matrix.get_blue_payoffs()[:, np.argmax(self.payoff_matrix.get_red_payoffs()[i, :])])
            if deviation_payoff - blue_expected > tol:
                return False
        return True


class SecurityGameSimulator:
    def __init__(self, solver: StackelbergSolver):
        self.solver = solver
        self.round_results: List[Dict] = []
    
    def play_round(self, blue_strategy: BlueTeamStrategy, red_strategy: RedTeamStrategy) -> Dict:
        blue_pay = blue_strategy.compute_payoff(np.array([red_strategy.intensity]), red_strategy.intensity)
        red_pay = red_strategy.compute_payoff(blue_strategy.threshold)
        detected = blue_strategy.threshold > red_strategy.intensity * 0.8
        result = {
            "blue_payoff": blue_pay, "red_payoff": red_pay,
            "detected": detected, "blue_threshold": blue_strategy.threshold,
            "attack_intensity": red_strategy.intensity
        }
        self.round_results.append(result)
        return result
    
    def simulate_game(self, n_rounds: int = 100) -> Dict:
        equilibrium = self.solver.solve(iterations=50)
        blue_mix, red_mix = equilibrium["blue_mix"], equilibrium["red_mix"]
        results = {"blue_wins": 0, "red_wins": 0, "draws": 0, "payoffs": []}
        
        for _ in range(n_rounds):
            blue_idx = np.random.choice(len(self.solver.blue_strategies), p=blue_mix)
            red_idx = np.random.choice(len(self.solver.red_strategies), p=red_mix)
            round_result = self.play_round(self.solver.blue_strategies[blue_idx], self.solver.red_strategies[red_idx])
            results["payoffs"].append(round_result)
            if round_result["blue_payoff"] > round_result["red_payoff"]:
                results["blue_wins"] += 1
            elif round_result["red_payoff"] > round_result["blue_payoff"]:
                results["red_wins"] += 1
            else:
                results["draws"] += 1
        
        results["blue_win_rate"] = results["blue_wins"] / n_rounds
        results["red_win_rate"] = results["red_wins"] / n_rounds
        return results
    
    def compute_nash_fallback(self) -> Dict:
        n_blue = len(self.solver.blue_strategies)
        n_red = len(self.solver.red_strategies)
        blue_pay = self.solver.payoff_matrix.get_blue_payoffs()
        
        row_mins = np.min(blue_pay, axis=1)
        maximin_idx = np.argmax(row_mins)
        security_level = float(row_mins[maximin_idx])
        
        col_maxs = np.max(blue_pay, axis=0)
        minimax_idx = np.argmin(col_maxs)
        minimax_value = float(col_maxs[minimax_idx])
        
        return {
            "maximin_strategy": maximin_idx, "security_level": security_level,
            "minimax_strategy": minimax_idx, "minimax_value": minimax_value,
            "value_gap": abs(security_level - minimax_value),
            "has_saddle_point": np.isclose(security_level, minimax_value, atol=0.01)
        }


class EquilibriumAnalyzer:
    def __init__(self, solver: StackelbergSolver):
        self.solver = solver
    
    def convergence_rate(self, history: List[float], window: int = 10) -> float:
        if len(history) < window + 1:
            return 0.0
        recent = np.array(history[-window:])
        changes = np.abs(np.diff(recent))
        avg_change = np.mean(changes)
        return float(1.0 / (1.0 + avg_change))
    
    def stability_score(self, blue_mix: np.ndarray, red_mix: np.ndarray, n_sims: int = 50) -> float:
        payoffs = []
        for _ in range(n_sims):
            bi = np.random.choice(len(self.solver.blue_strategies), p=blue_mix)
            ri = np.random.choice(len(self.solver.red_strategies), p=red_mix)
            payoffs.append(self.solver.payoff_matrix.get_blue_payoffs()[bi, ri])
        
        std_dev = np.std(payoffs)
        mean_pay = np.mean(payoffs)
        cv = std_dev / abs(mean_pay) if abs(mean_pay) > 1e-6 else float('inf')
        return float(1.0 / (1.0 + cv))
    
    def payoff_trend(self, history: List[float], window: int = 20) -> Dict:
        if len(history) < 2:
            return {"trend": "insufficient_data", "slope": 0.0, "direction": "flat"}
        
        arr = np.array(history[-window:])
        x = np.arange(len(arr))
        slope = float(np.polyfit(x, arr, 1)[0])
        
        if slope > 0.01:
            direction = "improving"
        elif slope < -0.01:
            direction = "declining"
        else:
            direction = "stable"
        
        return {"trend": direction, "slope": slope, "direction": direction, "mean": float(np.mean(arr)), "std": float(np.std(arr))}
