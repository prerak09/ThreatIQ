# 📐 ThreatIQ: Mathematical & Cryptographic Formulations

This document details the exact mathematical equations, optimization algorithms, and cryptographic circuits underpinning **ThreatIQ**.

---

## 1. Split Conformal Prediction Sets

Given $n$ exchangeable calibration data pairs $(X_1, Y_1), \dots, (X_n, Y_n) \in \mathcal{X} \times \{0, 1\}$ and a test point $X_{n+1}$:

### 1.1 Non-Conformity Score Function
$$s(x, y) = 1 - \hat{P}(Y = y \mid X = x)$$

### 1.2 Empirical Quantile Calibration
Let $\hat{q}_{1-\alpha}$ be the $\lceil (n + 1)(1 - \alpha) \rceil / n$ quantile of non-conformity scores $\{s(X_i, Y_i)\}_{i=1}^n$.

### 1.3 Conformal Set Construction
$$\mathcal{C}(X_{n+1}) = \left\{ y \in \{0, 1\} : s(X_{n+1}, y) \le \hat{q}_{1-\alpha} \right\}$$

### 1.4 Coverage Guarantee Theorem
$$\mathbb{P}\left( Y_{n+1} \in \mathcal{C}(X_{n+1}) \right) \ge 1 - \alpha$$

---

## 2. Stackelberg Bi-Level Security Game

### 2.1 Game Formulation
- **Leader (Blue Team)** commits to mixed strategy probability vector $\mathbf{p} \in \Delta_m$.
- **Follower (Red Team)** observes $\mathbf{p}$ and selects best-response strategy $\mathbf{q} \in \Delta_n$.

### 2.2 Optimization Objective
$$\max_{\mathbf{p} \in \Delta_m} \mathbf{p}^T \mathbf{A} \mathbf{q}^*(\mathbf{p}) \quad \text{subject to} \quad \mathbf{q}^*(\mathbf{p}) = \arg\max_{\mathbf{q} \in \Delta_n} \mathbf{p}^T \mathbf{B} \mathbf{q}$$
where $\mathbf{A} \in \mathbb{R}^{m \times n}$ is the Defender utility matrix, and $\mathbf{B} \in \mathbb{R}^{m \times n}$ is the Attacker payoff matrix.

---

## 3. Differentially Private Federated Learning (DP-SGD)

### 3.1 Local Gradient Clipping
For each local sample $i \in B_k$ at bank node $k$:
$$\bar{\mathbf{g}}_i = \nabla_\theta \mathcal{L}(\theta; x_i) \cdot \min\left(1, \frac{C}{\|\nabla_\theta \mathcal{L}(\theta; x_i)\|_2}\right)$$

### 3.2 Global Gaussian Noise Aggregation
$$\tilde{\mathbf{g}} = \frac{1}{K} \sum_{k=1}^K \left( \frac{1}{|B_k|} \sum_{i \in B_k} \bar{\mathbf{g}}_i \right) + \mathcal{N}\left(0, \frac{\sigma^2 C^2}{K^2} \mathbf{I}\right)$$

### 3.3 Privacy Guarantee
The privacy budget is tracked via Rényi Differential Privacy (RDP):
$$D_\alpha(\mathcal{M}(D) \parallel \mathcal{M}(D')) \le \frac{\alpha C^2}{2 \sigma^2}$$

---

## 4. Groth16 Zero-Knowledge Verification on BN254

### 4.1 Quadratic Arithmetic Program (QAP)
$$L(x) \cdot R(x) - O(x) = H(x) \cdot T(x)$$

### 4.2 Bilinear Pairing Check
The verifier checks that proof elements $\pi = (A \in \mathbb{G}_1, B \in \mathbb{G}_2, C \in \mathbb{G}_1)$ satisfy:
$$e(A, B) = e(\alpha, \beta) \cdot e\left(\sum_{i=0}^l x_i \gamma_i, \delta\right) \cdot e(C, \delta)$$
where $e: \mathbb{G}_1 \times \mathbb{G}_2 \to \mathbb{G}_T$ is the optimal Tate pairing on the BN254 curve with prime order $r \approx 2^{254}$.

---

## 5. Representation Steering Perturbation

In intermediate transformer layer $l$, the attention projection activation $h_l$ is steered along concept vector $\mathbf{v}_c$:
$$h_l' = h_l + \alpha \cdot \mathbf{v}_c$$
where $\alpha \in [0.0, 1.5]$ is the intensity multiplier, and $\mathbf{v}_c \in \mathbb{R}^{128}$ is extracted via contrastive activation PCA on adversarial traces.
