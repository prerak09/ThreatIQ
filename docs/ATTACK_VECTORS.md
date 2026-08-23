# 🎯 ThreatIQ: Attack Vectors & MITRE ATLAS Taxonomy

This reference details the 6 GenAI-powered payment fraud attack vectors simulated within **ThreatIQ**, their technical mechanisms, and their corresponding defensive mitigations.

---

## 1. ATK-001: LLM-Driven Synthetic Identity Orchestrator

- **MITRE ATLAS ID**: `AML.T0010.001`
- **Severity**: CRITICAL
- **Mechanism**:
  1. Multi-LLM pipeline generates coherent identities (Name, SSN, DOB, Address, Employer).
  2. Coordinated micro-deposit transactions build artificial credit histories across multiple financial institutions over 30–90 days.
  3. Orchestrates synchronized credit line draw-downs across multiple issuers.
- **Defensive Countermeasures**:
  - Device entropy clustering across newly established accounts.
  - Subgraph community mining in the Temporal GNN to detect shared merchant tokenization hubs.

---

## 2. ATK-002: Autonomous Multi-Hop CNP Relay Agent

- **MITRE ATLAS ID**: `AML.T0020.002`
- **Severity**: CRITICAL
- **Mechanism**:
  1. Autonomous purchasing agent routes card-not-present (CNP) authorizations through rotating residential proxy pools.
  2. Jitters inter-arrival times ($50\text{ms} - 400\text{ms}$) to defeat deterministic velocity counters.
  3. Dynamically shifts merchant category codes (MCCs) from low-risk utilities to high-risk digital gift cards.
- **Defensive Countermeasures**:
  - JA4+ TLS fingerprint anomaly analysis.
  - Behavioral cadence modeling across multi-hop authorization flows.

---

## 3. ATK-003: LLM Payment Gateway Prompt Injection

- **MITRE ATLAS ID**: `AML.T0043.001`
- **Severity**: HIGH
- **Mechanism**:
  1. Injects adversarial prompt suffixes (e.g., recursive instruction overrides) into conversational commerce assistant chatbots.
  2. Manipulates the natural-language response to extract tokenized PANs and authorization cryptograms.
- **Defensive Countermeasures**:
  - Input/output sanitization with perplexity threshold filters.
  - Intermediate activation steering ($W_o$) monitoring semantic token shifts.

---

## 4. ATK-004: AI Voice Clone Biometric Authentication Bypass

- **MITRE ATLAS ID**: `AML.T0027.001`
- **Severity**: HIGH
- **Mechanism**:
  1. Few-shot neural voice cloning synthesizes cardholder voiceprints from public audio samples.
  2. Layers synthetic background acoustic noise to mask spectral distortion during IVR phone-banking challenge verifications.
- **Defensive Countermeasures**:
  - Prosody consistency analysis and acoustic phase spectrum verification.
  - Multi-factor out-of-band push confirmation on registered hardware.

---

## 5. ATK-005: Distributed Credential Spraying Syndicate

- **MITRE ATLAS ID**: `AML.T0011.001`
- **Severity**: HIGH
- **Mechanism**:
  1. Distributed bot network attempts low-frequency credential validation against digital wallets and checkout gateways.
  2. Distributes attempts across thousands of IP subnets to stay below rate-limiting thresholds.
- **Defensive Countermeasures**:
  - Subnet-level entropy profiling and graph connectivity density scoring.

---

## 6. ATK-006: RL-Optimized Adaptive Velocity Evasion

- **MITRE ATLAS ID**: `AML.T0019.001`
- **Severity**: MEDIUM
- **Mechanism**:
  1. Reinforcement learning agent probes merchant authorization limits by observing decline response codes.
  2. Adapts transaction burst frequencies and split amounts in real time to operate just beneath automated alert thresholds.
- **Defensive Countermeasures**:
  - Cumulative balance manifold bounds enforced via Frank-Wolfe optimization.
  - Split Conformal Prediction non-conformity tracking.
