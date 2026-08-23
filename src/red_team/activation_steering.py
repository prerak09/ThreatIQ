"""
Activation Steering & Representation Engineering Module

Implements steering vectors to manipulate LLM internal activations
for generating more realistic adversarial attacks.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class SteeringVector:
    """Steering vector for a single adversarial concept."""

    name: str
    vector: np.ndarray
    layer_index: int
    alpha: float
    description: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "vector": self.vector.tolist(),
            "layer_index": self.layer_index,
            "alpha": self.alpha,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SteeringVector":
        return cls(
            name=d["name"],
            vector=np.array(d["vector"], dtype=np.float32),
            layer_index=d["layer_index"],
            alpha=d["alpha"],
            description=d["description"],
        )


class SteeringConceptLibrary:
    """Pre-defined steering concepts for payment fraud adversarial attacks."""

    CONCEPTS: Dict[str, dict] = {
        "CREDENTIAL_SPOOFING": {
            "layer_index": 3,
            "alpha": 0.7,
            "description": "Steering vector for credential manipulation patterns",
            "seed": 42,
        },
        "AUTHORIZATION_BYPASS": {
            "layer_index": 5,
            "alpha": 0.9,
            "description": "Steering vector for bypassing authorization checks",
            "seed": 137,
        },
        "COERCIVE_MANIPULATION": {
            "layer_index": 7,
            "alpha": 0.6,
            "description": "Steering vector for social engineering patterns",
            "seed": 256,
        },
        "VELOCITY_EVASION": {
            "layer_index": 4,
            "alpha": 0.8,
            "description": "Steering vector for avoiding rate limits",
            "seed": 512,
        },
        "GEO_SPOOFING": {
            "layer_index": 6,
            "alpha": 0.75,
            "description": "Steering vector for geographic manipulation",
            "seed": 1024,
        },
        "IDENTITY_FABRICATION": {
            "layer_index": 8,
            "alpha": 0.85,
            "description": "Steering vector for synthetic identity generation",
            "seed": 2048,
        },
    }

    def __init__(self, dim: int = 128):
        self._dim = dim
        self._vectors: Dict[str, SteeringVector] = {}
        self._build_library()

    def _build_library(self) -> None:
        for name, meta in self.CONCEPTS.items():
            rng = np.random.RandomState(meta["seed"])
            raw = rng.randn(self._dim).astype(np.float32)
            mean_profile = {
                "CREDENTIAL_SPOOFING": (0.12, 0.05),
                "AUTHORIZATION_BYPASS": (0.20, 0.08),
                "COERCIVE_MANIPULATION": (0.08, 0.03),
                "VELOCITY_EVASION": (0.15, 0.06),
                "GEO_SPOOFING": (0.10, 0.04),
                "IDENTITY_FABRICATION": (0.18, 0.07),
            }
            mu, sigma = mean_profile[name]
            vector = (raw * sigma + mu).astype(np.float32)
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
            self._vectors[name] = SteeringVector(
                name=name,
                vector=vector,
                layer_index=meta["layer_index"],
                alpha=meta["alpha"],
                description=meta["description"],
            )

    def get_concept(self, name: str) -> SteeringVector:
        if name not in self._vectors:
            raise KeyError(f"Unknown concept: {name}")
        return self._vectors[name]

    def list_concepts(self) -> List[str]:
        return list(self._vectors.keys())


class ActivationSteeringEngine:
    """Core engine for applying and composing steering vectors on hidden states."""

    def __init__(self, model_dim: int = 128, num_layers: int = 12):
        self._model_dim = model_dim
        self._num_layers = num_layers
        self._library = SteeringConceptLibrary(dim=model_dim)
        self._cache: Dict[str, np.ndarray] = {}

    def _generate_steering_vector(self, concept_name: str) -> np.ndarray:
        if concept_name in self._cache:
            return self._cache[concept_name]
        vec = self._library.get_concept(concept_name).vector
        self._cache[concept_name] = vec
        return vec

    def apply_steering(
        self,
        hidden_states: np.ndarray,
        concept_name: str,
        alpha: float = 1.0,
    ) -> np.ndarray:
        v = self._generate_steering_vector(concept_name)
        scaled = (alpha * v).astype(hidden_states.dtype)
        return hidden_states + scaled

    def remove_steering(
        self,
        hidden_states: np.ndarray,
        concept_name: str,
    ) -> np.ndarray:
        v = self._generate_steering_vector(concept_name)
        return hidden_states - v.astype(hidden_states.dtype)

    def batch_steering(
        self,
        hidden_states_batch: np.ndarray,
        concepts: List[str],
        alphas: List[float],
    ) -> np.ndarray:
        result = hidden_states_batch.copy()
        for concept, alpha in zip(concepts, alphas):
            vec = self._generate_steering_vector(concept)
            result = result + (alpha * vec).astype(result.dtype)
        return result

    def compose_steering(
        self,
        concepts: List[str],
        weights: List[float],
    ) -> np.ndarray:
        composed = np.zeros(self._model_dim, dtype=np.float32)
        for concept, w in zip(concepts, weights):
            composed += w * self._generate_steering_vector(concept)
        norm = np.linalg.norm(composed)
        if norm > 0:
            composed = composed / norm
        return composed

    def measure_steering_effect(
        self,
        original: np.ndarray,
        steered: np.ndarray,
    ) -> dict:
        diff = steered - original
        cos_sim = (
            float(np.dot(original, steered) / (np.linalg.norm(original) * np.linalg.norm(steered) + 1e-8))
        )
        l2 = float(np.linalg.norm(diff))
        orig_norm = float(np.linalg.norm(original))
        dir_align = float(np.dot(original, diff) / (orig_norm * l2 + 1e-8))
        return {
            "cosine_similarity": round(cos_sim, 6),
            "l2_norm": round(l2, 6),
            "direction_alignment": round(dir_align, 6),
            "magnitude_ratio": round(l2 / (orig_norm + 1e-8), 6),
        }

    def hook_registration_demo(self) -> dict:
        layers = [0, 3, 5, 7]
        hooks = []
        for li in layers:
            vec = self._library.get_concept(
                list(SteeringConceptLibrary.CONCEPTS.keys())[li % 6]
            )
            hooks.append({
                "layer_index": li,
                "hook_type": "forward",
                "concept": vec.name,
                "pre_forward": f"store h[{li}]",
                "post_forward": f"h[{li}] += alpha * v_{vec.name}",
            })
        return {
            "num_hooks": len(hooks),
            "hooks": hooks,
            "note": "Demo mode — in production these would be registered via PyTorch forward hooks.",
        }


class AttackIntensityController:
    """Maps UI slider values [0.0, 1.0] to steering configurations."""

    PRESETS: Dict[str, dict] = {
        "stealth": {
            "concepts": ["CREDENTIAL_SPOOFING"],
            "alphas": [0.2],
            "layers": [3],
        },
        "balanced": {
            "concepts": ["CREDENTIAL_SPOOFING", "AUTHORIZATION_BYPASS", "GEO_SPOOFING"],
            "alphas": [0.5, 0.5, 0.4],
            "layers": [3, 5, 6],
        },
        "aggressive": {
            "concepts": [
                "CREDENTIAL_SPOOFING", "AUTHORIZATION_BYPASS",
                "VELOCITY_EVASION", "GEO_SPOOFING",
            ],
            "alphas": [0.8, 0.9, 0.7, 0.75],
            "layers": [3, 4, 5, 6],
        },
        "maximum": {
            "concepts": [
                "CREDENTIAL_SPOOFING", "AUTHORIZATION_BYPASS",
                "COERCIVE_MANIPULATION", "VELOCITY_EVASION",
                "GEO_SPOOFING", "IDENTITY_FABRICATION",
            ],
            "alphas": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
            "layers": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        },
    }

    def intensity_to_config(self, intensity: float) -> dict:
        intensity = max(0.0, min(1.0, intensity))
        all_concepts = list(SteeringConceptLibrary.CONCEPTS.keys())

        if intensity <= 0.3:
            n = max(1, int(np.ceil(intensity / 0.3 * 2)))
            alphas = [round(0.1 + intensity * 0.5, 4) for _ in range(n)]
            layers = sorted(
                [SteeringConceptLibrary.CONCEPTS[c]["layer_index"] for c in all_concepts[:n]]
            )
        elif intensity <= 0.7:
            n = max(2, int(np.ceil((intensity - 0.3) / 0.4 * 4)))
            alphas = [round(0.4 + (intensity - 0.3) * 1.0, 4) for _ in range(n)]
            layers = sorted(
                [SteeringConceptLibrary.CONCEPTS[c]["layer_index"] for c in all_concepts[:n]]
            )
        else:
            n = len(all_concepts)
            alphas = [round(0.7 + (intensity - 0.7) * 1.0, 4) for _ in range(n)]
            layers = list(range(12))

        return {
            "concepts": all_concepts[:n],
            "alphas": alphas,
            "layers": layers,
            "intensity": round(intensity, 4),
        }

    def get_preset(self, preset_name: str) -> dict:
        if preset_name not in self.PRESETS:
            raise KeyError(f"Unknown preset: {preset_name}. Choose from {list(self.PRESETS)}")
        return dict(self.PRESETS[preset_name])


class SteeringEffectVisualizer:
    """Visualization helpers for steering effects."""

    def compute_tsne_projection(self, steered_vectors: Dict[str, np.ndarray]) -> dict:
        coords = {}
        names = list(steered_vectors.keys())
        if len(names) < 2:
            return {"coordinates": coords, "method": "t-SNE", "perplexity": 5}

        vectors = np.stack([steered_vectors[n] for n in names])
        n = len(names)
        sim = vectors @ vectors.T
        dist = np.clip(1.0 - sim, 0, None)
        np.fill_diagonal(dist, 0)

        rng = np.random.RandomState(42)
        embed = rng.randn(n, 2).astype(np.float32) * 0.01
        lr = 200.0
        perplexity = min(5.0, float(n - 1))

        for _ in range(200):
            p = np.exp(-dist ** 2 / (2 * perplexity))
            np.fill_diagonal(p, 0)
            p = p / (p.sum(axis=1, keepdims=True) + 1e-8)
            q_num = 1.0 / (1.0 + np.sum((embed[:, None] - embed[None]) ** 2, axis=2))
            np.fill_diagonal(q_num, 0)
            q = q_num / (q_num.sum() + 1e-8)
            pq = p - q
            grad = np.zeros_like(embed)
            for i in range(n):
                diff = embed[i] - embed
                grad[i] = 4 * (pq[i] * diff).sum(axis=0)
            embed -= lr * grad
            lr *= 0.99

        for i, name in enumerate(names):
            coords[name] = {"x": round(float(embed[i, 0]), 4), "y": round(float(embed[i, 1]), 4)}

        return {"coordinates": coords, "method": "t-SNE (numpy)", "perplexity": perplexity}

    def compute_similarity_matrix(self, concepts: List[str]) -> dict:
        lib = SteeringConceptLibrary()
        vecs = np.stack([lib.get_concept(c).vector for c in concepts])
        sim = vecs @ vecs.T
        matrix = {}
        for i, c1 in enumerate(concepts):
            matrix[c1] = {}
            for j, c2 in enumerate(concepts):
                matrix[c1][c2] = round(float(sim[i, j]), 4)
        return {"concepts": concepts, "matrix": matrix}

    def generate_radar_chart_data(self, concept_name: str) -> dict:
        lib = SteeringConceptLibrary()
        vec = lib.get_concept(concept_name).vector
        axes = ["credential_depth", "auth_complexity", "social_weight", "velocity_resistance", "geo_variance", "identity_density"]
        step = len(vec) // len(axes)
        values = []
        for i in range(len(axes)):
            start = i * step
            end = start + step
            values.append(round(float(np.mean(np.abs(vec[start:end]))), 4))
        mag = np.linalg.norm(values)
        if mag > 0:
            values = [round(v / mag, 4) for v in values]
        return {"concept": concept_name, "axes": axes, "values": values}
