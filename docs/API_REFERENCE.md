# 📡 ThreatIQ: REST & WebSocket API Specification

Base URL: `https://backend-production-400c.up.railway.app`  
WebSocket URL: `wss://backend-production-400c.up.railway.app/ws/transactions`  
Swagger Interactive Docs: `https://backend-production-400c.up.railway.app/docs`

---

## 1. Simulation & Lifecycle Endpoints

### `POST /api/simulation/start`
Starts the autonomous real-time transaction simulator.

**Request Body**:
```json
{
  "num_victims": 500,
  "fraud_ratio": 0.18,
  "transaction_rate_tps": 8.0
}
```

**Response** (`200 OK`):
```json
{
  "message": "Simulation started",
  "tps": 8.0,
  "fraud_ratio": 0.18
}
```

### `POST /api/simulation/stop`
Stops the live simulation stream.

**Response** (`200 OK`):
```json
{
  "message": "Simulation stopped"
}
```

---

## 2. Attack Injection & Threat Endpoints

### `POST /api/attack/inject`
Injects an adversarial attack batch directly into the model screening pipeline.

**Request Body**:
```json
{
  "attack_type": "multi_hop_cnp",
  "count": 5
}
```

**Response** (`200 OK`):
```json
{
  "injected": 5,
  "attack_type": "multi_hop_cnp",
  "results": [
    {
      "id": "TXN-88FCB93493D9",
      "amount": 14500.0,
      "currency": "USD",
      "status": "detected",
      "blue_team_confidence": 0.94,
      "blue_team_result": {
        "is_fraud": true,
        "confidence": 0.94,
        "latency_ms": 11.8,
        "engine_scores": {
          "xgboost": 0.96,
          "lightgbm": 0.93,
          "iforest": 0.88
        }
      }
    }
  ]
}
```

---

## 3. Explainability & Graph Endpoints

### `GET /api/xai/explain/{transaction_id}`
Computes KernelSHAP feature attributions for a given transaction ID.

**Response** (`200 OK`):
```json
{
  "transaction_id": "TXN-88FCB93493D9",
  "confidence": 0.94,
  "shap_values": {
    "behavioral_score": 0.38,
    "velocity_1h": 0.31,
    "geo_distance_km": 0.26,
    "device_fingerprint_entropy": 0.21
  },
  "conformal_set": ["Fraudulent", "High Risk"]
}
```

### `GET /api/topology/graph`
Returns the active transaction graph topology.

**Response** (`200 OK`):
```json
{
  "nodes": [
    { "id": "card-4521", "type": "card", "risk_score": 0.94, "degree": 4 },
    { "id": "dev-a854988e", "type": "device", "risk_score": 0.89, "degree": 6 }
  ],
  "edges": [
    { "source": "card-4521", "target": "dev-a854988e", "weight": 14500.0, "is_fraud": true }
  ]
}
```

---

## 4. Advanced Subsystem Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/marl/evolve` | `POST` | Triggers a reinforcement learning evolution epoch across all 4 adversary agents |
| `/api/steering/apply` | `POST` | Applies attention steering vector perturbations: `{"concept_id": "CREDENTIAL_SPOOFING", "alpha": 0.7}` |
| `/api/constraints/generate` | `POST` | Synthesizes Frank-Wolfe manifold-constrained transaction samples |
| `/api/federated/round` | `POST` | Executes a multi-bank FedAvg training step with DP-SGD privacy aggregation |
| `/api/game/solve` | `POST` | Solves the Stackelberg minimax game: `{"iterations": 100, "lr": 0.01}` |
| `/api/zkp/prove` | `POST` | Generates a Groth16 zk-SNARK fraud compliance proof on curve BN254 |
| `/api/sar/generate` | `POST` | Compiles FinCEN Form 111 XML Suspicious Activity Report with SHAP narrative |

---

## 5. WebSocket Streaming

### `WS /ws/transactions`
Connect to receive real-time streaming transactions formatted in ISO 20022 `pacs.008` structure.

**Payload Structure**:
```json
{
  "type": "attack",
  "id": "TXN-88FCB93493D9",
  "amount": 14500.0,
  "attack_type": "Multi-Hop CNP",
  "status": "detected",
  "channel": "tokenized",
  "confidence": 0.94
}
```
