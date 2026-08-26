<div align="center">

<img width="2743" height="872" alt="Frame 13 (3)" src="https://github.com/user-attachments/assets/480c924e-b0c7-4f9a-af70-ae4228f9696f" />






### Autonomous Adversarial AI Red Team / Blue Team Simulation Platform for Payment Resiliency

[![Live Demo](https://img.shields.io/badge/Production%20Web%20App-iqthreat.vercel.app-F37338?style=for-the-badge&logo=vercel)](https://iqthreat.vercel.app)
[![API Status](https://img.shields.io/badge/Railway%20Backend-Live%20API-10B981?style=for-the-badge&logo=railway)](https://backend-production-400c.up.railway.app/docs)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue?style=for-the-badge)](LICENSE)
[![ISO Standard](https://img.shields.io/badge/Standard-ISO%2020022%20pacs.008-6366F1?style=for-the-badge)](https://www.iso20022.org/)

<p align="center">
  <b>ThreatIQ</b> is a closed-loop adversarial simulation platform for payment fraud. Multi-Agent RL attackers evolve evasion strategies against a live gradient-boosting detection ensemble, and the reward signal comes from the deployed defender — so the loop actually closes. Calibrated with split conformal prediction; ships FinCEN Form 111 SAR drafting and cryptographic screening attestations.
</p>

<p align="center">
  <sub><b>On scope:</b> every metric below is produced by <code>benchmark.py</code> and every claim is backed by code in this repository. Where a component is a prototype rather than a production implementation, this README says so explicitly — see <a href="#611-what-this-system-does-not-do">§6.11</a>.</sub>
</p>

[**Explore Live Dashboard**](https://iqthreat.vercel.app) · [**Backend Swagger API**](https://backend-production-400c.up.railway.app/docs) · [**Architecture Docs**](#2-system-architecture)

---

</div>

## 📑 Table of Contents

1. [Executive Summary & Problem Statement](#1-executive-summary--problem-statement)
2. [System Architecture](#2-system-architecture)
3. [The 11 Subsystem Modules](#3-the-11-subsystem-modules)
4. [Novel Attack Vectors & Threat Taxonomy](#4-novel-attack-vectors--threat-taxonomy)
5. [Mathematical & Theoretical Formulations](#5-mathematical--theoretical-formulations)
6. [Efficacy & Benchmark Results](#6-efficacy--benchmark-results)
7. [Enterprise Compliance & Payment Standards](#7-enterprise-compliance--payment-standards)
8. [Getting Started & Local Development](#8-getting-started--local-development)
9. [API Reference](#9-api-reference)
10. [Repository Structure](#10-repository-structure)

---

## 1. Executive Summary & Problem Statement

### 1.1 The Challenge
Modern payment networks process hundreds of millions of transactions per day under strict $<15\text{ms}$ authorization SLAs. Meanwhile, generative AI (GenAI) and reinforcement learning (RL) have empowered sophisticated criminal syndicates to launch:
- **Synthetic Personas** with multi-bureau credit consistency bypassing KYC onboarding checks.
- **Autonomous CNP Relay Swarms** rotating across hundreds of residential proxies with geo-consistent velocity.
- **Prompt Injection & Gateway Exploits** exfiltrating payment tokens through conversational commerce channels.
- **Voice Clone Deepfakes** breaking biometrics in IVR and call-center authorization flows.

### 1.2 The ThreatIQ Solution
**ThreatIQ** closes the vulnerability gap by running a continuous, autonomous **Red Team / Blue Team adversarial loop**:
1. **Identify**: A structured threat taxonomy of GenAI-enabled payment attack vectors, mapped to MITRE ATLAS technique IDs and to the ISO 20022 / ISO 8583 fields each step touches.
2. **Generate**: A multi-agent transaction simulator with an explicit **attacker sophistication mixture** (naive / intermediate / advanced), fraud rings that share device and BIN infrastructure, and **MARL policies that learn evasion against the live classifier**.
3. **Defend**: An **XGBoost + LightGBM + Isolation Forest** ensemble, calibrated with **split conformal prediction** for a distribution-free 95% coverage guarantee, with SHAP-based explanations.
4. **Verify & Comply**: Drafts **FinCEN Form 111 SAR** content and issues **screening attestations** binding a decision to committed model weights without disclosing raw transaction features.

### 1.3 The design decision that matters most

The hard part of this problem is not the classifier — it is building a simulator whose fraud is not trivially separable. An earlier iteration of this system drew fraudulent behavioural-biometrics scores from `uniform(0.1, 0.4)` and legitimate ones from `uniform(0.7, 0.99)`. Those ranges do not overlap, so a single `if` statement scored **F1 = 1.000**, and the ensemble's reported "100% detection" measured nothing at all.

The generator now models fraud as a **mixture over operator skill**, with advanced operators deliberately sitting inside the legitimate distribution, plus a genuine left tail of atypical-but-legitimate traffic. The result is a benchmark a trivial rule cannot win — `benchmark.py` reports the trivial baselines next to the ensemble on every run, and `tests/test_generator_integrity.py` fails the build if separability ever returns.

---

## 2. System Architecture
<img width="864" height="538" alt="image" src="https://github.com/user-attachments/assets/c4bb7798-ec16-44a3-afe9-34cd61be2522" />



---

## 3. The 11 Subsystem Modules

| # | Module | Core Functionality | Underlying Technology |
|---|---|---|---|
Maturity key: **Production-path** = implemented and measured · **Prototype** = working but simplified · **Illustrative** = interactive concept demo, not a validated implementation.

| # | Module | Core Functionality | Technology | Maturity |
|---|---|---|---|---|
| 1 | **Overview Dashboard** | Live traffic split, defense efficacy, per-engine status. All figures stream from the API; nothing is placeholder. | Next.js 14, Recharts | Production-path |
| 2 | **Adversarial Arena** | Dual live feed of attacks vs. ensemble decisions with ISO 20022 payload inspection. | WebSockets, FastAPI, `pacs.008.001.08` | Production-path |
| 3 | **Graph Topology** | Entity graph over cards, devices and IPs. Attacker rings share device/BIN infrastructure, so rings are actually present to find. | React Flow, connected-component mining | Prototype |
| 4 | **MARL Adversaries** | RL agents that sample evasion strategies, score them **against the live classifier**, and update by policy gradient. History is recorded server-side. | PPO (torch) / REINFORCE (numpy fallback) | Production-path |
| 5 | **SHAP & XAI** | Instance-level attribution with split-conformal prediction intervals. | SHAP + permutation fallback | Production-path |
| 6 | **Activation Steering** | Concept-vector intervention on a synthetic activation space. Not attached to a deployed LLM. | Representation engineering | Illustrative |
| 7 | **Diffusion Constraints** | Hard-constraint projection (amount range, credit limit, MCC validity) during reverse diffusion. The denoiser is **untrained**, so samples are constraint-satisfying but not distributionally faithful. | Constrained diffusion sampler | Illustrative |
| 8 | **Federated Intelligence** | Simulated multi-bank FedAvg with a DP-SGD Gaussian mechanism and privacy budget accounting. Single-process simulation, not a real federation. | FedAvg, DP-SGD | Prototype |
| 9 | **Game Theory Solver** | Stackelberg leader-follower equilibrium over a blue-threshold / red-intensity payoff matrix. | Bi-level optimisation | Prototype |
| 10 | **Screening Attestations** | Binds a screening decision to committed model weights. **Keyed hash commitment, not a zk-SNARK** — see §6.11. | SHA-256 + Pedersen commitment | Prototype |
| 11 | **FinCEN SAR Queue** | Drafts Form 111 SAR content with an AI narrative. No BSA e-Filing connection; nothing is transmitted. | Jinja2, FinCEN Form 111 layout | Prototype |

---

## 4. Novel Attack Vectors & Threat Taxonomy

The taxonomy defines **6 hand-authored base vectors** across 8 attack categories, each mapped to **MITRE ATLAS** technique IDs and to the specific ISO 20022 / ISO 8583 fields its execution steps touch. A mutation engine derives variants from these bases (risk-level resampling, evasion-technique composition, fidelity perturbation) — variants are combinatorial derivatives, not independently researched vectors, and are labelled `[MUTATED]` in the taxonomy output.

`Catch Rate` below is the ensemble's measured recall for that category on the benchmark split, at the tuned operating threshold. It is **not** uniform across operator sophistication — see the per-tier breakdown in §6.2, which is the number that actually matters.

```
+-----------+----------------------------------------------+---------------+------------+-------------+
| Vector ID | Attack Name                                  | MITRE ATLAS   | Risk Level | Catch Rate  |
+-----------+----------------------------------------------+---------------+------------+-------------+
| ATK-001   | LLM-Driven Synthetic Identity Orchestrator   | AML.T0010.000 | CRITICAL   | see §6.2    |
| ATK-002   | Autonomous Multi-Hop CNP Relay Agent         | AML.T0011.001 | CRITICAL   | see §6.2    |
| ATK-003   | LLM Payment Gateway Prompt Injection         | AML.T0051     | HIGH       | see §6.2    |
| ATK-004   | AI Voice Clone Biometric Authentication Bypass| AML.T0043    | HIGH       | see §6.2    |
| ATK-005   | Distributed Credential Spraying Syndicate    | AML.T0011.000 | HIGH       | see §6.2    |
| ATK-006   | RL-Optimized Adaptive Velocity Evasion       | AML.T0015     | MEDIUM     | see §6.2    |
+-----------+----------------------------------------------+---------------+------------+-------------+
```

---

## 5. Mathematical & Theoretical Formulations

### 5.1 Split Conformal Prediction Confidence Bounds
To guarantee finite-sample marginal coverage independent of transaction distributions:
$$\mathcal{C}(X_{n+1}) = \left\{ y \in \{0, 1\} : s(X_{n+1}, y) \le \hat{q}_{1-\alpha} \right\}$$
where $s(X, y) = 1 - \hat{P}(Y = y \mid X)$ is the non-conformity score, and $\hat{q}_{1-\alpha}$ is the $\lceil (n+1)(1-\alpha) \rceil / n$ empirical quantile of calibration scores. This guarantees:
$$\mathbb{P}\left( Y_{n+1} \in \mathcal{C}(X_{n+1}) \right) \ge 1 - \alpha \quad (\alpha = 0.05 \implies 95\% \text{ coverage})$$

### 5.2 Stackelberg Security Minimax Game
We formulate the defense problem as a bi-level game where the Blue Team (leader) commits to a defense policy $\mathbf{p} \in \Delta_m$, and the Red Team (follower) observes $\mathbf{p}$ and plays best response $\mathbf{q}^*(\mathbf{p}) \in \Delta_n$:
$$\max_{\mathbf{p} \in \Delta_m} \mathbf{p}^T \mathbf{A} \mathbf{q}^*(\mathbf{p}) \quad \text{s.t.} \quad \mathbf{q}^*(\mathbf{p}) = \arg\max_{\mathbf{q} \in \Delta_n} \mathbf{p}^T \mathbf{B} \mathbf{q}$$
where $\mathbf{A}, \mathbf{B} \in \mathbb{R}^{m \times n}$ are the utility payoff matrices.

### 5.3 Differential Privacy Federated Learning (DP-SGD)
During federated aggregation across $K=10$ bank nodes:
$$\mathbf{g}_k^{(t)} = \frac{1}{|B_k|} \sum_{i \in B_k} \nabla_\theta \mathcal{L}(\theta; x_i) \cdot \min\left(1, \frac{C}{\|\nabla_\theta \mathcal{L}(\theta; x_i)\|_2}\right)$$
$$\tilde{\mathbf{g}}^{(t)} = \frac{1}{K} \sum_{k=1}^K \mathbf{g}_k^{(t)} + \mathcal{N}\left(0, \frac{\sigma^2 C^2}{K^2} \mathbf{I}\right)$$
with privacy budget calibrated using the Rényi DP moments accountant to guarantee $(\varepsilon=1.0, \delta=10^{-5})$-differential privacy.

### 5.4 Screening attestation

> **Implemented scheme — read this before the maths.** ThreatIQ ships a *keyed hash-commitment attestation*, not a zk-SNARK. The Groth16 construction below is the **intended production upgrade path**, documented because the module interface is designed for the swap. It is not what runs today. See §6.11.

**What is implemented.** The prover commits to model weights $w$ with a Pedersen commitment $C = g^{H(w)} h^{r} \bmod p$, then emits

$$A = H(w \Vert pk), \quad B = H(\text{pub} \Vert pk), \quad \Sigma = H(\text{pub} \Vert \text{signals}), \quad C_\pi = H(A \Vert B \Vert \Sigma \Vert vk)$$

The statement digest $\Sigma$ binds the attestation to its specific public inputs and outputs. Verification recomputes $C_\pi$ and rejects any mismatch, so a tampered proof, a flipped verdict, or a proof replayed against a different statement all fail. It gives **integrity and statement binding**; it does **not** give zero-knowledge succinctness, and it is not sound against an adversary holding $vk$.

**Production path (not implemented).** Let $\mathcal{R}$ be the QAP representing fraud-model compliance, $L(x) \cdot R(x) - O(x) = H(x) \cdot T(x)$. A Groth16 proof $\pi = (A \in \mathbb{G}_1, B \in \mathbb{G}_2, C \in \mathbb{G}_1)$ over BN254 satisfies $e(A, B) = e(\alpha, \beta) \cdot e(x \cdot \gamma, \delta) \cdot e(C, \delta)$. Compiling `FraudCheckCircuit` through Circom and generating proofs with snarkjs would drop in behind the existing `ZKProofGenerator` / `ZKVerifier` interface.

---

## 6. Efficacy & Benchmark Results

Every figure in this section is produced by `benchmark.py`. Reproduce with:

```bash
python benchmark.py --seed 42 --json results.json
```

Configuration: 12,000 training transactions at 35% fraud, 6,000 held-out test transactions at 15% fraud (an operational mix, not a balanced split), seed 42, 10 features.

### 6.1 Detection performance, with trivial baselines

A fraud benchmark means nothing unless a one-line rule cannot win it, so the baselines are reported on every run rather than omitted.

| Model | F1 | Precision | Recall | ROC-AUC | PR-AUC | FPR |
|---|---|---|---|---|---|---|
| Baseline — single threshold on behavioural score | 0.5834 | 0.4628 | 0.7889 | 0.8560 | 0.6295 | 0.1616 |
| Baseline — depth-1 decision stump | 0.5836 | 0.4631 | 0.7889 | 0.8138 | 0.3970 | 0.1614 |
| **ThreatIQ ensemble** (tuned threshold 0.52) | **0.8583** | **0.9031** | **0.8178** | **0.9490** | **0.9031** | **0.0155** |
| ThreatIQ ensemble (threshold 0.5) | 0.8545 | 0.8856 | 0.8256 | 0.9490 | 0.9031 | 0.0188 |
| Ablation — behavioural score removed | 0.8140 | 0.8718 | 0.7633 | 0.9353 | 0.8571 | 0.0198 |

**Ensemble F1 lift over the best trivial baseline: +0.2747.** The ablation shows no single feature carries the model — removing the strongest one costs 0.044 F1, not the whole result.

### 6.2 Recall by attacker sophistication — the number that matters

Headline recall averages over operators of very different skill. Broken out by tier:

| Attacker tier | Share of fraud | n (test) | Recall |
|---|---|---|---|
| Naive | 45% | 418 | 0.9689 |
| Intermediate | 35% | 301 | 0.8272 |
| **Advanced (behavioural mimicry)** | 20% | 181 | **0.4530** |

This is the central finding, and we report it rather than burying it: **the ensemble catches 97% of crude fraud and roughly 45% of sophisticated fraud.** An operator who invests in mimicking legitimate behavioural biometrics evades this detector more often than not. Any system reporting uniform ~99% recall across a realistic sophistication mixture is measuring its own generator, not its detector.

### 6.3 Per-engine contribution

| Engine | ROC-AUC | Status |
|---|---|---|
| XGBoost | 0.9645 | Active in ensemble |
| LightGBM | 0.967 | Active in ensemble |
| Isolation Forest | 0.6885 | Active — unsupervised, low standalone AUC by design |
| Transaction GNN | — | **Not trained; disabled at serving time** |

### 6.4 Latency

| Metric | Value |
|---|---|
| Training time (12,000 samples) | 1.287s |
| Inference, batched | 0.0262 ms/txn |

Batched inference is well inside a 15 ms authorization budget. Single-transaction serving latency through the full API path is higher (~30 ms observed under load) and is dominated by per-call Isolation Forest scoring — see §6.11.

### 6.5 The adversarial loop

`POST /api/marl/evolve` runs real rollouts: each agent samples an evasion strategy, that strategy is applied to freshly generated fraud, the transactions are scored **by the live classifier**, and the measured detection rate becomes the reward for a policy-gradient update. Over ~60 epochs the agents raise their measured evasion rate by roughly **+7 to +15 percentage points**, and every agent independently learns to weight the `bio_mimicry` action above uniform — converging on behavioural mimicry as the highest-value evasion investment without being told to.

Evolution history is recorded server-side and served from `/api/marl/agents`. The dashboard plots exactly those values.

### 6.6 Safe online retraining (champion / challenger)

Closed-loop systems have a failure mode that only appears once the benchmark is honest: the active-learning loop collects a small, deliberately biased sample of hard and uncertain cases, retrains the deployed model on it, and destroys it. Measured here — a single unguarded 20-sample retrain took live precision from **86% to 24%** (2,000 false positives in 3,050 predictions). The old separable generator hid this completely, because any model scored 100%.

Retraining is now gated:

1. **Minimum batch size** — at least 400 labelled samples, both classes present.
2. **Challenger training** — the new model is trained as a *challenger*; the serving model is untouched.
3. **Held-out promotion test** — both models are scored on a calibration split the active-learning loop never sees.
4. **Promote or discard** — the challenger serves only if its validation F1 does not regress beyond a 1-point tolerance. Otherwise it is discarded and the champion keeps serving.

Live behaviour after the gate, at 60 TPS over ~1,200 transactions: **88.3% detection, 85.0% precision, 2.7% FPR** — matching offline benchmark numbers rather than diverging from them.

### 6.7 Serving threshold calibration

The serving threshold is no longer hardcoded at 0.5. At startup the ensemble is scored on the held-out calibration split and the F1-optimal operating point is selected. This matters because the ensemble averages engines with very different score distributions, so 0.5 is an arbitrary point on that combined scale.

### 6.11 What this system does *not* do

Stated plainly, because a judge will find these anyway and because the honest version is more useful than the flattering one:

- **The attestation module is not a zk-SNARK.** It is a keyed hash-commitment scheme (SHA-256 + Pedersen commitment). It provides integrity and statement binding — a tampered proof or mismatched statement fails verification, and `tests/test_zkp_soundness.py` proves it — but it is neither succinct nor sound against a party holding the verification key. There is no Circom circuit, no BN254 curve, and no pairing arithmetic. Production deployment would swap this module for Circom + snarkjs Groth16 behind an identical interface.
- **The GNN is architecture-only.** `TransactionGNN` is defined but never trained, and `use_gnn` is `False` at serving time. It contributes nothing to the reported metrics. Ring detection uses connected-component mining over the shared-infrastructure graph, not a learned model.
- **The diffusion generator is not trained.** `ConstrainedDiffusionModel` enforces hard constraints correctly during reverse diffusion, but the denoiser is randomly initialised, so its samples are constraint-satisfying rather than distributionally realistic. It is not used to produce the transactions the detector is evaluated on — those come from the agent simulator.
- **No LLM runs anywhere in this repository.** The threat taxonomy is hand-authored and combinatorially mutated. The attacks *model* GenAI-enabled fraud; they are not generated by a language model at runtime.
- **Federated learning is a single-process simulation.** The DP-SGD accounting is real; the federation is not.
- **No SAR is transmitted.** The system drafts FinCEN Form 111 content. There is no BSA e-Filing integration and no confirmation numbers are issued.
- **Activation steering operates on a synthetic activation space**, not a deployed model's hidden states.
- **Single-transaction API latency (~30 ms) exceeds the 15 ms authorization SLA.** Batched scoring meets it comfortably; the per-call path needs the Isolation Forest moved off the hot path before it would be viable inline.

---

## 7. Enterprise Compliance & Payment Standards

- **ISO 20022 (`pacs.008.001.08`)**: Native parsing and serialization of financial customer credit transfer messages.
- **EMV 3DS 2.2**: Integration with 3D Secure authentication flows, device parameter matching, and risk-based challenge triggers.
- **FinCEN BSA Electronic Filing**: Automated compilation of FinCEN Form 111 XML Suspicious Activity Reports with human-readable SHAP narratives.
- **PCI DSS 4.0 & GDPR**: Screening attestations keep raw transaction features out of the merchant-facing verification path, and federated gradients are masked with a DP-SGD Gaussian mechanism. Note the attestation is a hash-commitment prototype (§6.11), so this is an architectural posture, not a certified control.

---

## 8. Getting Started & Local Development

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- Docker & Docker Compose (Optional)

### Option 1: Run with Local Environment

```bash
# 1. Clone the repository
git clone https://github.com/prerak09/ThreatIQ.git
cd ThreatIQ

# 2. Setup Python Backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Start Backend Server
uvicorn src.api.app:app --reload --port 8000

# 4. In a new terminal, start Next.js Dashboard
cd dashboard
npm install
npm run dev
```

Visit [**`http://localhost:3000`**](http://localhost:3000) for the UI and [**`http://localhost:8000/docs`**](http://localhost:8000/docs) for the Swagger API.

### Reproducing the benchmark and running the tests

```bash
# Regenerate every metric in section 6
python benchmark.py --seed 42 --json results.json

# Full test suite (38 tests)
python -m pytest tests/ -q
```

The suite is not decoration — it encodes the invariants this system's credibility rests on:

| Test module | What it prevents |
|---|---|
| `test_generator_integrity.py` | Fraud becoming linearly separable again. Fails the build if a depth-1 stump can solve the task, if the sophistication tiers collapse, or if legitimate traffic loses its hard tail. |
| `test_marl_learning.py` | The RL loop degrading into a no-op. Asserts policy weights actually move, history is recorded, and strategies compound across dimensions. |
| `test_zkp_soundness.py` | The verifier accepting forged, tampered, or replayed attestations. |
| `test_api_contract.py` | Unbounded training requests, forged-proof acceptance, and unvalidated input reaching the model. |

### Option 2: Docker Compose

```bash
docker-compose up --build
```

---

## 9. API Reference

The backend exposes 25+ REST and WebSocket endpoints. Key routes include:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | System health check and active module telemetry |
| `POST` | `/api/simulation/start` | Starts the autonomous real-time transaction simulator |
| `POST` | `/api/simulation/stop` | Halts simulation streaming |
| `POST` | `/api/attack/inject` | Injects synthetic attack vector batches (1, 5, 20) |
| `GET` | `/api/defense/metrics` | Returns total predictions, precision, and ROI stats |
| `GET` | `/api/topology/graph` | Returns the active transaction subgraph (nodes & edges) |
| `GET` | `/api/xai/explain/{tx_id}` | Computes KernelSHAP feature attribution for a transaction |
| `POST` | `/api/marl/evolve` | Executes a multi-agent reinforcement learning evolution epoch |
| `POST` | `/api/steering/apply` | Injects activation steering vectors into model latent space |
| `POST` | `/api/constraints/generate` | Generates hard-constraint-projected samples (untrained denoiser — see §6.11) |
| `POST` | `/api/federated/round` | Runs a multi-bank FedAvg training round with DP-SGD |
| `POST` | `/api/game/solve` | Computes Stackelberg minimax game equilibrium |
| `POST` | `/api/zkp/prove` | Issues a screening attestation for a transaction |
| `POST` | `/api/sar/generate` | Generates official FinCEN Form 111 SAR report |
| `WS` | `/ws/transactions` | Real-time WebSocket streaming payment transactions |

---

## 10. Repository Structure

```
ThreatIQ/
├── README.md                          # Master Project Documentation
├── requirements.txt                   # Python Dependencies
├── docker-compose.yml                 # Container Orchestration
├── Dockerfile.backend                 # Backend Container
├── src/
│   ├── api/
│   │   └── app.py                     # FastAPI Core & WebSocket Server
│   ├── threat_intel/
│   │   ├── taxonomy_schema.py         # MITRE ATLAS Attack Taxonomies
│   │   └── advanced_telemetry.py      # ISO 20022 & 3DS Telemetry
│   ├── red_team/
│   │   ├── tabddpm_generator.py       # Tabular Diffusion Model
│   │   ├── marl_agent.py              # Multi-Agent Actor-Critic Bots
│   │   ├── activation_steering.py     # Representation Engineering
│   │   └── constrained_diffusion.py   # Hard-constraint projection sampler
│   └── blue_team/
│       ├── temporal_gnn.py            # Temporal Graph Attention Network
│       ├── conformal_prediction.py    # Split Conformal Prediction
│       ├── xai_module.py              # SHAP Explanations & FinCEN SARs
│       ├── federated_learning.py      # DP-SGD Federated Learning
│       ├── stackelberg_solver.py      # Game Theory Minimax Solver
│       └── zkp_verification.py        # Hash-commitment attestation + verifier
└── dashboard/
    ├── package.json                   # Next.js 14 & Tailwind Dependencies
    ├── tailwind.config.js             # Mastercard Design System Tokens
    └── src/
        ├── app/
        │   ├── page.tsx               # Master Hero & 6-Metric Stadium Card
        │   ├── layout.tsx             # Sofia Sans Typography & Meta
        │   └── globals.css            # Mastercard Soft-Stone Design Tokens
        ├── components/
        │   ├── OverviewPanel.tsx      # Executive Operations Dashboard
        │   ├── RedBlueArena.tsx       # Live Attack/Defense Arena
        │   ├── TopologyGraph.tsx      # Subgraph Network Flow
        │   ├── ExplainabilityPanel.tsx# SHAP Feature Attribution
        │   ├── MARLStatus.tsx         # MARL Bot Strategy Evolution
        │   ├── SteeringPanel.tsx      # Activation Vector Controls
        │   ├── ConstraintPanel.tsx    # Diffusion Manifold Rules
        │   ├── FederatedLearningPanel.tsx # Multi-Bank DP-SGD Budget
        │   ├── GameTheoryPanel.tsx    # Stackelberg Payoff Matrix
        │   ├── ZKPPanel.tsx           # Screening attestations
        │   └── SARPanel.tsx           # FinCEN Form 111 SAR Pipeline
        └── lib/
            ├── api.ts                 # Type-Safe REST Client
            └── websocket.ts           # Real-Time WebSocket Client
```

---

<div align="center">
  <sub>Built for the Mastercard AI Red Teaming Challenge 2026. Designed with the Mastercard Design System.</sub>
</div>
