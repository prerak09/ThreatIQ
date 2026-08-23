# 🏛️ ThreatIQ: Enterprise Architecture Deep-Dive

This document provides a comprehensive technical breakdown of the **ThreatIQ** architecture, covering each of its three foundational pillars, inter-module communication pipelines, and real-time streaming topologies.

---

## 1. High-Level Architectural Topology

ThreatIQ is structured around a **Closed-Loop Adversarial Ecosystem**:

```
 [ RAW PAYMENT INGESTION ] 
 (ISO 20022 pacs.008, EMV 3DS 2.2, JA3/JA4 TLS)
            │
            ▼
┌───────────────────────────────────────────────────────────┐
│           PILLAR 1: ADVERSARIAL THREAT INTELLIGENCE       │
│  - MITRE ATLAS Attack Taxonomy Mapping                    │
│  - Behavioral Biometric Profiler                          │
│  - Fraud Ring Community Detection                         │
└───────────────────────────┬───────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────┐
│           PILLAR 2: GENERATIVE RED TEAM ENGINE            │
│  - TabDDPM (Tabular Denoising Diffusion)                  │
│  - Frank-Wolfe Manifold Invariant Projection              │
│  - MARL Actor-Critic Multi-Agent Evolutionary Bots        │
│  - Representation Steering Vectors (Attention Wo)         │
└───────────────────────────┬───────────────────────────────┘
                            │
                            ▼ (Adversarial Transaction Stream)
┌───────────────────────────────────────────────────────────┐
│           PILLAR 3: BLUE TEAM DEFENSE ENSEMBLE            │
│  - Temporal Graph Attention Network (TGAT + Time2Vec)     │
│  - Gradient Boosted Trees (XGBoost + LightGBM)            │
│  - Unsupervised Outlier Mining (Isolation Forest)         │
│  - Split Conformal Prediction Coverage Guarantee (95%)    │
└───────────────────────────┬───────────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────────┐
│           PILLAR 4: COMPLIANCE & CRYPTOGRAPHIC ASSURANCE   │
│  - Groth16 zk-SNARK Verifier (BN254 Pairing Curve)        │
│  - DP-SGD Federated Multi-Bank Aggregation (FedAvg)       │
│  - KernelSHAP Feature Attribution Engine                  │
│  - Automated FinCEN Form 111 XML SAR Generator            │
└───────────────────────────────────────────────────────────┘
```

---

## 2. Pillar 1: Adversarial Threat Intelligence

### 2.1 ISO 20022 `pacs.008.001.08` Ingestion Engine
- Implements full XSD schema validation for SEPA and SWIFT cross-border customer credit transfer messages.
- Extracts `FIToFICstmrCdtTrf` group headers, debtor/creditor agent BICs, settlement methods (`CLRG`), and unstructured remittance information (`RmtInf`).
- Invariant integrity verification ensures transaction currency complies with ISO 4217 and IBAN checksums adhere to ISO 13616 Mod-97 standards.

### 2.2 Behavioral Biometrics & Network Fingerprinting
- **JA3 / JA4+ TLS Handshake Fingerprinting**: Identifies automated bot scrapers and head-less client libraries directly from TLS `ClientHello` cipher suites and extension orders.
- **Keystroke & Mouse Trajectory Dynamics**: Calculates flight time, dwell time, and curvature entropy to identify synthetic autonomous purchasing agents.

---

## 3. Pillar 2: Generative Red Team Engine

### 3.1 Tabular Denoising Diffusion Probabilistic Models (TabDDPM)
- Operates in mixed continuous/categorical feature space using Noise Conditioned Score Networks (NCSN).
- Forward Gaussian diffusion corrupts genuine transaction vectors; reverse parameterized neural network $\epsilon_\theta(x_t, t)$ reconstructs high-fidelity fraud distributions.

### 3.2 Frank-Wolfe Manifold Constraints
To prevent generative AI from hallucinating invalid payment data, reverse diffusion steps are projected onto hard banking invariant manifolds:
$$\hat{x}_0 = x_t - \sigma_t \left( \epsilon_\theta(x_t, t) + \gamma \nabla_x \mathcal{C}(x_t) \right)$$
Enforces strictly bounded amounts, credit line limits, valid merchant category codes (MCCs), and Benford's Law first-digit distribution.

### 3.3 Multi-Agent Reinforcement Learning (MARL)
- **Architecture**: Centralized Training with Decentralized Execution (CTDE).
- 4 autonomous adversary bots (`Multi-Hop CNP`, `Synthetic Identity`, `Prompt Injection`, `Voice Deepfake`) evolve policies over sequential epochs to bypass changing Blue Team thresholds.

---

## 4. Pillar 3: Blue Team Defense Ensemble

### 4.1 Temporal Graph Attention Networks (TGAT)
- Constructs dynamic entity subgraphs linking Cardholder accounts, Mobile Device Fingerprints, Residential IP subnets, and Acquirer Merchant IDs.
- **Time2Vec** maps continuous transaction timestamps into harmonic periodic embeddings, allowing multi-head self-attention to detect multi-merchant velocity bursts.

### 4.2 Split Conformal Prediction Calibration
- Provides distribution-free finite sample guarantees:
$$\mathbb{P}(Y \in \mathcal{C}(X)) \ge 1 - \alpha \quad (\alpha = 0.05 \implies 95\% \text{ guaranteed coverage})$$
- Generates rigorous prediction sets: `{ Fraudulent, High Risk }` or `{ Legitimate, Low Risk }`.

---

## 5. Pillar 4: Cryptographic Compliance & Assurance

### 5.1 Groth16 zk-SNARK Verification
- Proves model screening compliance on the **BN254 elliptic curve**.
- Merchants receive a $192\text{-byte}$ zero-knowledge proof verifying that transaction fraud probability $< 0.15$ without exposing cardholder PAN or private bank feature weights.

### 5.2 Differential Privacy Multi-Bank Federated Learning
- Implements FedAvg across 10 institutional banking nodes with DP-SGD Gaussian perturbation ($\varepsilon=1.0, \delta=10^{-5}$), preserving customer privacy under global model updates.
