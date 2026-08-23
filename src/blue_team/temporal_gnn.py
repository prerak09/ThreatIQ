"""Temporal Graph Attention Network for payment fraud detection."""

import math
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

import time
import uuid


@dataclass
class TemporalEdge:
    source_id: str
    target_id: str
    timestamp: float
    edge_type: str  # transaction/shared_device/shared_ip/shared_card
    features: Dict[str, float] = field(default_factory=dict)


class TemporalGraph:
    def __init__(self):
        self.nodes: Dict[str, Dict] = {}
        self.edges: List[TemporalEdge] = []

    def add_node(self, node_id: str, node_type: str, features: Optional[Dict] = None, timestamp: float = 0.0):
        self.nodes[node_id] = {"type": node_type, "features": features or {}, "timestamp": timestamp}

    def add_edge(self, source_id: str, target_id: str, timestamp: float, edge_type: str, features: Optional[Dict] = None):
        self.edges.append(TemporalEdge(source_id, target_id, timestamp, edge_type, features or {}))

    def get_neighbors(self, node_id: str) -> List[str]:
        neighbors = set()
        for e in self.edges:
            if e.source_id == node_id:
                neighbors.add(e.target_id)
            elif e.target_id == node_id:
                neighbors.add(e.source_id)
        return list(neighbors)

    def get_temporal_neighbors(self, node_id: str, reference_ts: float,
                               time_window: float) -> List[TemporalEdge]:
        """Edges touching ``node_id`` within [reference_ts - time_window, reference_ts]."""
        cutoff = float(reference_ts) - float(time_window)
        return [
            e for e in self.edges
            if (e.source_id == node_id or e.target_id == node_id)
            and cutoff <= e.timestamp <= float(reference_ts)
        ]

    def to_adjacency_matrix(self) -> Tuple[np.ndarray, List[str]]:
        node_ids = sorted(self.nodes.keys())
        idx = {n: i for i, n in enumerate(node_ids)}
        n = len(node_ids)
        adj = np.zeros((n, n), dtype=np.float32)
        for e in self.edges:
            if e.source_id in idx and e.target_id in idx:
                adj[idx[e.source_id], idx[e.target_id]] = 1.0
                adj[idx[e.target_id], idx[e.source_id]] = 1.0
        return adj, node_ids

    def get_node_features(self) -> Tuple[np.ndarray, List[str]]:
        node_ids = sorted(self.nodes.keys())
        dim = max(len(self.nodes[n]["features"]) for n in node_ids) if node_ids else 0
        features = np.zeros((len(node_ids), max(dim, 1)), dtype=np.float32)
        for i, nid in enumerate(node_ids):
            vals = list(self.nodes[nid]["features"].values())
            features[i, :len(vals)] = vals
        return features, node_ids


if TORCH_AVAILABLE:
    class TemporalAttentionLayer(nn.Module):
        def __init__(self, node_dim: int, edge_dim: int, num_heads: int = 4):
            super().__init__()
            self.num_heads = num_heads
            self.head_dim = node_dim // num_heads
            self.scale = self.head_dim ** -0.5
            self.q_proj = nn.Linear(node_dim, node_dim)
            self.k_proj = nn.Linear(node_dim, node_dim)
            self.v_proj = nn.Linear(node_dim, node_dim)
            self.time_proj = nn.Linear(1, num_heads)
            self.out_proj = nn.Linear(node_dim, node_dim)

        @staticmethod
        def sinusoidal_encoding(timestamps: torch.Tensor, dim: int) -> torch.Tensor:
            freqs = torch.exp(-math.log(10000.0) * torch.arange(0, dim, 2, device=timestamps.device).float() / dim)
            args = timestamps.unsqueeze(-1) * freqs.unsqueeze(0)
            return torch.cat([torch.sin(args), torch.cos(args)], dim=-1)

        def forward(self, node_features: torch.Tensor, neighbor_features: torch.Tensor, timestamps: torch.Tensor) -> torch.Tensor:
            B, N, D = node_features.shape
            time_enc = self.sinusoidal_encoding(timestamps.view(-1), D).view(B, N, -1)[:, :, :D]
            q = self.q_proj(node_features).view(B, N, self.num_heads, self.head_dim).transpose(1, 2)
            k = self.k_proj(neighbor_features + time_enc).view(B, N, self.num_heads, self.head_dim).transpose(1, 2)
            v = self.v_proj(neighbor_features + time_enc).view(B, N, self.num_heads, self.head_dim).transpose(1, 2)
            attn = (q @ k.transpose(-2, -1)) * self.scale
            time_bias = self.time_proj(timestamps.unsqueeze(-1)).permute(0, 2, 1).expand_as(attn)
            attn = F.softmax(attn + time_bias, dim=-1)
            out = (attn @ v).transpose(1, 2).reshape(B, N, D)
            return self.out_proj(out)

    class TemporalGNN(nn.Module):
        def __init__(self, node_dim: int, edge_dim: int, hidden_dim: int = 64, num_heads: int = 4, num_layers: int = 2):
            super().__init__()
            self.input_proj = nn.Linear(node_dim, hidden_dim)
            self.layers = nn.ModuleList([TemporalAttentionLayer(hidden_dim, edge_dim, num_heads) for _ in range(num_layers)])
            self.classifier = nn.Sequential(nn.Linear(hidden_dim * 2, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, 1))
            self.norms = nn.ModuleList([nn.LayerNorm(hidden_dim) for _ in range(num_layers)])

        def forward(self, graph_batch: Dict[str, torch.Tensor]) -> torch.Tensor:
            x = self.input_proj(graph_batch["node_features"])
            timestamps = graph_batch["timestamps"]
            for layer, norm in zip(self.layers, self.norms):
                x = norm(x + layer(x, x, timestamps))
            mean_pool = x.mean(dim=1)
            max_pool = x.max(dim=1).values
            readout = torch.cat([mean_pool, max_pool], dim=-1)
            return self.classifier(readout)

        @torch.no_grad()
        def predict(self, graph: TemporalGraph) -> float:
            adj, node_ids = graph.to_adjacency_matrix()
            feats, _ = graph.get_node_features()
            x = torch.tensor(feats, dtype=torch.float32).unsqueeze(0)
            ts = torch.zeros(1, len(node_ids), dtype=torch.float32)
            batch = {"node_features": x, "timestamps": ts}
            return torch.sigmoid(self.forward(batch)).item()
else:
    class TemporalAttentionLayer:
        def __init__(self, node_dim, edge_dim, num_heads=4):
            self.w = np.random.randn(node_dim, node_dim) * 0.01

        def forward(self, node_features, neighbor_features, timestamps):
            return node_features @ self.w

    class TemporalGNN:
        def __init__(self, node_dim, edge_dim, hidden_dim=64, num_heads=4, num_layers=2):
            self.w = np.random.randn(node_dim, hidden_dim) * 0.01
            self.head_w = np.random.randn(hidden_dim, 1) * 0.01

        def forward(self, graph_batch):
            x = graph_batch["node_features"] @ self.w
            return x.mean(axis=1) @ self.head_w

        def predict(self, graph):
            feats, _ = graph.get_node_features()
            batch = {"node_features": feats}
            return float(1.0 / (1.0 + np.exp(-self.forward(batch).item())))


class FraudRingDetector:
    """Detects fraud rings as strongly connected components in the graph."""

    def __init__(self, model: TemporalGNN):
        self.model = model

    def detect_rings(self, graph: TemporalGraph, min_ring_size: int = 3) -> List[List[str]]:
        """Return strongly connected components with >= min_ring_size nodes.

        Uses the *directed* edge structure — every node of an SCC can reach
        every other node, i.e. the component contains a genuine cycle.
        (The undirected projection would misreport simple chains as rings.)
        Tarjan's algorithm, iterative.
        """
        node_ids = sorted(graph.nodes.keys())
        n = len(node_ids)
        if n == 0:
            return []
        idx = {nid: i for i, nid in enumerate(node_ids)}

        neighbors: List[List[int]] = [[] for _ in range(n)]
        for e in graph.edges:
            if e.source_id in idx and e.target_id in idx:
                neighbors[idx[e.source_id]].append(idx[e.target_id])

        index_counter = [0]
        stack: List[int] = []
        on_stack = [False] * n
        indices = [-1] * n
        lowlink = [0] * n
        rings: List[List[str]] = []

        def strongconnect(v: int) -> None:
            # Iterative Tarjan to avoid recursion limits on large graphs.
            work = [(v, 0)]
            while work:
                node, pi = work[-1]
                if pi == 0:
                    indices[node] = lowlink[node] = index_counter[0]
                    index_counter[0] += 1
                    stack.append(node)
                    on_stack[node] = True
                recurse = False
                while pi < len(neighbors[node]):
                    w = neighbors[node][pi]
                    pi += 1
                    if indices[w] == -1:
                        work[-1] = (node, pi)
                        work.append((w, 0))
                        recurse = True
                        break
                    elif on_stack[w]:
                        lowlink[node] = min(lowlink[node], indices[w])
                if recurse:
                    continue
                if pi >= len(neighbors[node]):
                    work.pop()
                    if lowlink[node] == indices[node]:
                        component: List[int] = []
                        while True:
                            w = stack.pop()
                            on_stack[w] = False
                            component.append(w)
                            if w == node:
                                break
                        if len(component) >= min_ring_size:
                            rings.append([node_ids[i] for i in component])
                    if work:
                        parent = work[-1][0]
                        lowlink[parent] = min(lowlink[parent], lowlink[node])

        for v in range(n):
            if indices[v] == -1:
                strongconnect(v)
        return rings

    def analyze_topology(self, graph: TemporalGraph) -> Dict[str, float]:
        adj, node_ids = graph.to_adjacency_matrix()
        n = len(node_ids)
        if n == 0:
            return {"density": 0, "clustering": 0, "avg_degree": 0}
        edge_count = adj.sum() / 2
        density = (2 * edge_count) / (n * (n - 1)) if n > 1 else 0
        degrees = adj.sum(axis=1)
        triangles = np.trace(adj @ adj @ adj) / 6
        clustering = 0
        for i in range(n):
            neighbors = np.where(adj[i] > 0)[0]
            k = len(neighbors)
            if k >= 2:
                sub = adj[np.ix_(neighbors, neighbors)]
                clustering += sub.sum() / (k * (k - 1))
        clustering /= n
        return {"density": float(density), "clustering": float(clustering), "avg_degree": float(degrees.mean())}

    def get_suspicious_clusters(self, graph: TemporalGraph, threshold: float = 0.7) -> List[List[str]]:
        adj, node_ids = graph.to_adjacency_matrix()
        visited = [False] * len(node_ids)
        clusters = []
        for i in range(len(node_ids)):
            if visited[i]:
                continue
            component, queue = [], [i]
            while queue:
                node = queue.pop(0)
                if visited[node]:
                    continue
                visited[node] = True
                component.append(node)
                for neighbor in np.where(adj[node] > 0)[0]:
                    if not visited[neighbor]:
                        queue.append(neighbor)
            density = 0
            sz = len(component)
            if sz > 1:
                sub = adj[np.ix_(component, component)]
                density = sub.sum() / (sz * (sz - 1))
            if density >= threshold:
                clusters.append([node_ids[c] for c in component])
        return clusters
