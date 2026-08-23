# AGENTS.md - Mastercard AI Red Team Arena

## Project Purpose

Autonomous closed-loop Red Team / Blue Team AI simulation for payment security. Identifies GenAI-powered fraud attack vectors, generates adversarial transactions to stress-test defenses, and iteratively improves detection through active learning and game-theoretic optimization.

---

## Architecture Overview

Three-pillar adversarial loop:

    [Threat Intel] --> [Red Team Attacks] --> [Blue Team Detection] --> [Feedback Loop]
           ^                                                           |
           +-- Steering + MARL Evolution + Active Learning <------------+

Data flow:
1. ThreatIntelGenerator produces MITRE ATLAS-aligned attack vectors
2. AttackerAgent and VictimAgent generate mixed transaction streams
3. MerchantEngine processes through mock payment gateway
4. FraudDetectionModel (IsolationForest + XGBoost) classifies each transaction
5. ActiveLearningLoop tracks false negatives, triggers retraining
6. MARLOrchestrator evolves attacker strategies based on defender performance
7. StackelbergSolver computes game-theoretic equilibrium
8. WebSocket streaming pushes live transactions to React dashboard

---

## Tech Stack

**Backend (Python 3.11):** FastAPI, Uvicorn, XGBoost, scikit-learn, NumPy, PyTorch (optional), SHAP (optional), lxml, dicttoxml

**Frontend (TypeScript / React 18):** Next.js 14, Tailwind CSS, Recharts, React Flow (@xyflow/react), Lucide React

---

## Directory Structure

    Mastercard/
      AGENTS.md
      requirements.txt
      Dockerfile.backend
      docker-compose.yml
      models/
      src/
        __init__.py
        threat_intel/
          __init__.py
          taxonomy_schema.py        # AttackVector, ThreatTaxonomy, enums (205 lines)
          generator.py              # ThreatIntelGenerator, 6 base vectors (503 lines)
          advanced_telemetry.py     # 3DS2, TLS, Browser, Behavioral telemetry (481 lines)
        red_team/
          __init__.py
          agents.py                 # AttackerAgent, VictimAgent, MerchantEngine (494 lines)
          simulation_runner.py      # SimulationRunner orchestrator (388 lines)
          ISO20022_formatter.py     # pacs.008 message formatting (315 lines)
          tabddpm_generator.py      # TabDDPM diffusion model (176 lines)
          marl_agent.py             # MARLAgent, MARLOrchestrator, ActorCritic (250 lines)
          activation_steering.py    # Steering vectors, concepts, intensity (354 lines)
          constrained_diffusion.py  # Hard constraints, gradient-guided diffusion (405 lines)
        blue_team/
          __init__.py
          gnn_model.py              # FraudDetectionModel, TransactionGNN (605 lines)
          feature_pipeline.py       # FeaturePipeline (391 lines)
          active_learning_loop.py   # ActiveLearningLoop, replay buffer (557 lines)
          temporal_gnn.py           # TemporalGNN, FraudRingDetector (224 lines)
          conformal_prediction.py   # ConformalPredictor, ONNX export (191 lines)
          federated_learning.py     # FedAvg, DP-SGD, privacy budget (349 lines)
          stackelberg_solver.py     # Bi-level game solver (272 lines)
          xai_module.py             # SHAPExplainer, SARGenerator (400 lines)
          zkp_verification.py       # Groth16 proofs, Pedersen commitments (248 lines)
        api/
          __init__.py
          app.py                    # FastAPI app, 50+ endpoints, WebSocket (1058 lines)
      dashboard/
        package.json
        tailwind.config.js
        tsconfig.json
        Dockerfile
        src/
          app/
            layout.tsx
            page.tsx
            globals.css
          components/
            ArenaDashboard.tsx      # Main container, 9 tabs (629 lines)
            RedBlueArena.tsx
            AttackMatrix.tsx
            DefenseMetrics.tsx
            AttackInjection.tsx
            TopologyGraph.tsx
            SARPanel.tsx
            ExplainabilityPanel.tsx
            MARLStatus.tsx
            SteeringPanel.tsx
            ConstraintPanel.tsx
            FederatedLearningPanel.tsx
            GameTheoryPanel.tsx
            ZKPPanel.tsx
            StatusBadge.tsx
            MetricCard.tsx

---

## Detailed Module Specifications

### Threat Intelligence (src/threat_intel/)

#### taxonomy_schema.py (205 lines)
MITRE ATLAS-aligned attack vector definitions for payment security.

Enums:
- AttackCategory(Enum): 8 MITRE-aligned categories for payment systems
- RiskLevel(Enum): LOW=1, MEDIUM=2, HIGH=3, CRITICAL=4
- PaymentChannel(Enum): ECOMMERCE, POS, MOBILE_WALLET, CNP, P2P, B2B

Dataclasses:
- AttackPrecondition: description, required_access, target_component, estimated_difficulty (1-10)
- AttackStep: step_id, description, iso20022_fields, iso8583_fields, evasion_technique
- AttackVector: vector_id, name, category, risk_level, description, preconditions, execution_steps, target_channels, fidelity_score (0-1), bypass_probability (0-1), mitre_atlas_mapping
- ThreatTaxonomy: vectors, version, last_updated

Methods on ThreatTaxonomy:
- add_vector(vector) -> None
- get_by_category(category) -> List[AttackVector]
- get_by_risk_level(level) -> List[AttackVector]
- get_high_risk_vectors() -> List[AttackVector]
- get_by_channel(channel) -> List[AttackVector]
- calculate_overall_risk_score() -> float
- to_json() -> str / from_json(json_str) -> ThreatTaxonomy

#### generator.py (503 lines)
Automated attack vector synthesis and MITRE ATLAS mapping.

class ThreatIntelGenerator(seed=None):
  - _initialize_base_vectors(): Creates 6 base vectors:
    - ATK-001: LLM-Driven Synthetic Identity Orchestrator (CRITICAL, fidelity=0.92, bypass=0.45)
    - ATK-002: Autonomous CNP Relay Agent (CRITICAL, fidelity=0.88, bypass=0.52)
    - ATK-003: LLM Payment Gateway Injection (HIGH, fidelity=0.78, bypass=0.38)
    - ATK-004: AI Voice Clone Authentication Bypass (HIGH, fidelity=0.85, bypass=0.42)
    - ATK-005: Aggressive Bot Checkout Exploitation (HIGH, fidelity=0.82, bypass=0.35)
    - ATK-006: Adaptive Velocity Control Evasion (MEDIUM, fidelity=0.75, bypass=0.48)
  - synthesize_novel_variant(base_vector_id, mutation_rate=0.3) -> AttackVector
  - generate_batch(count, categories=None) -> List[AttackVector]
  - export_taxonomy(output_path) -> None
  - get_statistics() -> Dict

#### advanced_telemetry.py (481 lines)
Advanced payment telemetry schema for transaction analysis and ML feature engineering.

Dataclasses:
- ThreeDS2Context: 3-D Secure 2.2 fields
- TLSFingerprint: JA3/JA4 TLS fingerprinting
- BrowserFingerprint: canvas_hash, webgl_hash, audio_hash, platform, language
- BehavioralBiometrics: 20 fields (mouse dynamics, keyboard dynamics, touch, device motion)
- AdvancedPaymentTelemetry: Combines all + ISO 20022 + geo/IP; to_ml_features()

MITREATLASMapper:
- AML_TACTICS: Dict mapping 7 tactic IDs
- map_attack(attack_category) -> List[Dict]
- get_tactic_details(tactic_id) -> Optional[Dict]

### Red Team (src/red_team/)

#### agents.py (494 lines)
Multi-Agent Simulation Engine for payment fraud.

Transaction dataclass fields:
- transaction_id: str, timestamp: str, amount: float, currency: str
- merchant_category_code: str, card_number_last4: str, device_fingerprint: str
- ip_address: str, geo_lat: float, geo_long: float, auth_channel: str
- behavioral_biometrics_score: float, is_fraud: bool, attack_vector_id: Optional[str]
- iso20022_payload: Optional[str], raw_payload_logs: Dict[str, Any]

class AttackerAgent(attack_vectors, proxy_pool_size=100, fraud_amount_range=(5.0, 500.0)):
  - _generate_ip_pool() -> List[str]
  - _generate_device_fingerprint() -> str
  - _generate_card_number() -> str: Luhn-valid with BIN [4111, 5555, 3782, 6011]
  - _select_attack_vector() -> AttackVector: Weighted by risk_level * fidelity_score
  - _generate_fraud_amount(vector) -> float
  - generate_transaction(timestamp) -> Transaction

class VictimAgent(num_users=1000, user_base_region="US"):
  - _generate_user_profiles() -> List[Dict]
  - _generate_benford_amount() -> float: P(d) = log10(1 + 1/d)
  - generate_transaction(user_id, timestamp) -> Transaction

class MerchantEngine(merchant_id="MERCH-001", fraud_detection_enabled=True, processing_latency_ms=50.0):
  - _validate_transaction(transaction) -> Dict: INVALID_AMOUNT, HIGH_AMOUNT, VELOCITY_EXCEEDED, IMPOSSIBLE_TRAVEL
  - _calculate_distance(lat1, lon1, lat2, lon2) -> float: Haversine km
  - process_transaction(transaction) -> Dict: status, response_code, authorization_code
  - get_statistics() -> Dict

#### simulation_runner.py (388 lines)
class SimulationRunner(num_victims=500, fraud_ratio=0.15, transaction_rate_tps=10.0, enable_active_learning=True):
  - set_blue_team_classifier(classifier_fn) -> None
  - start() / stop(): Thread-based simulation loop
  - inject_custom_attack(attack_type, count=10) -> List[Dict]
  - get_current_metrics() -> Dict
  - get_transaction_history(limit=100, fraud_only=False) -> List[Dict]
  - reset() -> None

#### ISO20022_formatter.py (315 lines)
class ISO20022Formatter(bank_bic="MASTCRDMC"):
  - format_credit_transfer(transaction, ...) -> Dict: pacs.008.001.08
  - format_payment_status(original_message_id, status, reason_code) -> Dict
  - to_xml_string(message) -> str
  - extract_features_for_ml(message) -> Dict[str, float]

#### tabddpm_generator.py (176 lines)
class TabDDPM (PyTorch nn.Module):
  - forward_diffusion(x_0, t) -> (x_t, noise)
  - sample(n_samples) -> np.ndarray: Full reverse diffusion from noise
  - fit(X, y=None, epochs=100, batch_size=256)
  - generate_fraud_samples(n_samples, attack_type) -> np.ndarray

#### marl_agent.py (250 lines)
class MARLAgent(state_dim=5, action_dim=6, lr=3e-4, gamma=0.99, epsilon=1.0):
  - select_action(state, explore=True) -> (action_idx, log_prob, value)
  - compute_reward(bypass_success, detection_prob, anomaly_score) -> float
  - update(states, actions, rewards, next_states): PPO-style
  - train_episode(simulator_fn, blue_team_fn, steps=50) -> float

class MARLOrchestrator:
  ATTACK_TYPES = ["account_takeover", "card_testing", "synthetic_id", "velocity_abuse", "loyalty_fraud", "credential_stuffing"]
  - evolve_strategies(blue_team_performance) -> None
  - get_best_attacks(n=3) -> List[Dict]

#### activation_steering.py (354 lines)
class SteeringConceptLibrary(dim=128):
  6 concepts: CREDENTIAL_SPOOFING, AUTHORIZATION_BYPASS, COERCIVE_MANIPULATION, VELOCITY_EVASION, GEO_SPOOFING, IDENTITY_FABRICATION
  - get_concept(name) -> SteeringVector
  - list_concepts() -> List[str]

class ActivationSteeringEngine(model_dim=128, num_layers=12):
  - apply_steering(hidden_states, concept_name, alpha=1.0): h_l' = h_l + alpha * v_steering
  - measure_steering_effect(original, steered) -> dict

class AttackIntensityController:
  PRESETS = {stealth (0.2), balanced (0.4-0.5), aggressive (0.7-0.9), maximum (1.0)}
  - intensity_to_config(intensity) -> dict

#### constrained_diffusion.py (405 lines)
6 HardConstraint subclasses: AmountConstraint, IBANConstraint, CurrencyCodeConstraint, TimeSequenceConstraint, CreditLimitConstraint, MerchantCategoryConstraint

class ConstraintRegistry: register(), check_all(), total_penalty(), constraint_gradient()
class ConstrainedDiffusionModel(registry, gamma=1.0, guidance_scale=2.0, n_timesteps=1000):
  - guided_reverse_step(x_t, t, t_next, epsilon_theta, feature_names): DDIM with constraint guidance
  - sample(n_samples, feature_names, initial_noise=None): Full constrained reverse process
  - enforce_benford_law(amounts) -> np.ndarray: Static method

class ConstraintViolationReporter: report(samples, registry, feature_names)


### Blue Team (src/blue_team/)

#### gnn_model.py (605 lines)
class FraudDetectionModel(contamination=0.01, xgb_params=None, lgb_params=None, use_gnn=False, gnn_in_channels=16, model_dir="models"):
  Engine 1: Isolation Forest (200 estimators)
  Engine 2: XGBoost (300 estimators, max_depth=6, lr=0.05, scale_pos_weight=10)
  Engine 3 (optional): LightGBM (300 estimators)
  Engine 4 (optional): TransactionGNN (GCNConv + Linear classifier)
  - train(X, y=None, feature_names=None) -> Dict: precision/recall/f1/auc
  - predict(features, threshold=0.5) -> PredictionResult
  - predict_batch(features, threshold=0.5) -> List[PredictionResult]
  - save_model(path) / load_model(path)

#### feature_pipeline.py (391 lines)
class FeaturePipeline(windows=None, geo_lookup=None):
  - compute_velocity_features(timestamp, card_id, ip_address, device_id) -> Dict
  - compute_geo_features(transaction, card_id) -> Dict
  - compute_temporal_features(timestamp, card_id) -> Dict
  - extract_features(transaction) -> Tuple[np.ndarray, List[str]]
  - _haversine(lat1, lon1, lat2, lon2) -> float: great-circle km

#### active_learning_loop.py (557 lines)
class ActiveLearningLoop(detection_threshold=0.85, replay_buffer_size=10000, avg_fraud_cost=500.0):
  - evaluate_batch(y_true, y_pred, y_proba, transactions, timestamps) -> PerformanceMetrics
  - flag_missed_detections(y_true, y_pred, y_proba, transactions) -> List[Dict]
  - generate_retraining_data(min_fraud_ratio=0.3) -> Tuple[np.ndarray, np.ndarray]
  - estimate_financial_loss(y_true, y_pred, transaction_amounts) -> FinancialLossEstimate
  - trigger_retrain(current_metrics=None) -> bool

#### temporal_gnn.py (224 lines)
class TemporalGNN(node_dim, edge_dim, hidden_dim=64, num_heads=4, num_layers=2):
  - TemporalAttentionLayer: multi-head attention + sinusoidal time encoding
  - forward(graph_batch) -> Tensor

class FraudRingDetector(model):
  - detect_rings(graph, min_ring_size=3) -> List[List[str]]: DFS cycle detection
  - analyze_topology(graph) -> Dict[str, float]

#### conformal_prediction.py (191 lines)
class ConformalPredictor(base_model, alpha=0.05):
  - fit_calibration(cal_X, cal_y)
  - predict(x) -> List[int]: prediction set
  - coverage_guarantee() -> Dict

class ConformalFraudDetector(fraud_model, alpha=0.05):
  - detect(transaction_features) -> Dict: prediction_set, confidence, recommended_action

class ONNXExporter:
  - export_to_onnx(model, input_shape, output_path) -> bool
  - benchmark_latency(onnx_path, n_runs=1000) -> Dict

#### federated_learning.py (349 lines)
class FederatedLearningCoordinator(n_banks=10):
  - initialize_banks(bank_data_list)
  - run_round() -> Dict: FedAvg with gradient aggregation
  - run_training(n_rounds=10) -> List[Dict]

class DPAggregator(epsilon=1.0, delta=1e-5, max_norm=1.0):
  - aggregate(gradients, sample_counts) -> Tuple[np.ndarray, Dict]

class PrivacyBudgetTracker(total_epsilon=10.0):
  - consume(epsilon, delta) -> bool
  - is_exhausted() -> bool

class FederatedSimulation(n_banks=10, fraud_ratio=0.15):
  - simulate_attack_injection(round_num) -> Dict
  - run_full_simulation(n_rounds=20) -> Dict

#### stackelberg_solver.py (272 lines)
class StackelbergSolver(blue_strategies, red_strategies):
  - solve(iterations=100, learning_rate=0.01) -> Dict
  - compute_equilibrium_mixed() -> Dict

class SecurityGameSimulator(solver):
  - simulate_game(n_rounds=100) -> Dict
  - compute_nash_fallback() -> Dict

class EquilibriumAnalyzer(solver):
  - convergence_rate(history) -> float
  - stability_score(blue_mix, red_mix) -> float

#### xai_module.py (400 lines)
class SHAPExplainer(model, background_data=None):
  - explain_prediction(features, feature_names) -> np.ndarray
  - get_top_features(shap_values, feature_names, n=10) -> List[Tuple[str, float]]

class ExplanationEngine(shap_explainer, feature_names):
  - explain_transaction(transaction_features, transaction_id) -> FraudExplanation
  - explain_fraud_ring(ring_transactions, graph_metrics) -> Dict
  - generate_risk_factors(features) -> List[Dict]

class SARGenerator(explanation_engine):
  - generate_sar(transaction_data, explanation, graph_context) -> Dict
  - to_xml(sar_data) -> str: FinCEN-format XML

class SARQueue(max_queue_size=1000):
  - add_sar(sar_data) -> str
  - get_pending_sars() -> List[Dict]
  - mark_filed(sar_id) -> bool
  - get_statistics() -> Dict

#### zkp_verification.py (248 lines)
class ZKPFraudSystem(threshold=128):
  - prove_fraud_check(features, model_weights) -> Dict: commitment + proof
  - verify_fraud_check(proof, features, expected_hash) -> Dict

class FraudCheckCircuit(threshold=128) extends ZKCircuit:
  - evaluate(private_inputs, public_inputs) -> List[int]

class ZKProofGenerator(circuit):
  - generate_proof(private_inputs, public_inputs) -> Dict

class ZKVerifier(verification_key=None):
  - verify(proof, public_inputs) -> bool
  - batch_verify(proofs) -> List[bool]

class CircomExporter:
  - export_circuit(circuit, output_path) -> str
  - generate_r1cs_constraints(circuit) -> List[Dict]
  - generate_witness(circuit, private_inputs, public_inputs) -> List[int]


### API (src/api/)

#### app.py (1058 lines)
FastAPI application with 50+ endpoints, WebSocket, lifespan initialization.

Core endpoints:
- GET /api/health: Health check with component status
- POST /api/simulation/start: Start simulation (num_victims, fraud_ratio, tps)
- POST /api/simulation/stop: Stop simulation
- GET /api/metrics: Current simulation metrics
- GET /api/transactions: Transaction history (limit, fraud_only)

Threat Intelligence:
- GET /api/threats/taxonomy: Full threat taxonomy JSON
- GET /api/threats/statistics: Vector statistics by category/risk

Attack:
- POST /api/attack/inject: Inject custom attack (attack_type, count)
- GET /api/attack/matrix: Attack category vs risk level heatmap

Model:
- POST /api/model/train: Retrain model (n_samples)
- GET /api/model/metrics: Model version, fitted status, training time
- POST /api/model/threshold: Update fraud threshold

Defense:
- GET /api/defense/metrics: Active learning summary, financial loss, ROI

XAI:
- GET /api/xai/explain/{transaction_id}: SHAP explanation for transaction
- GET /api/xai/ring-explanation: Fraud ring topology explanation

SAR:
- GET /api/sar/pending: Pending SARs queue
- POST /api/sar/generate: Generate SAR for transaction
- POST /api/sar/{sar_id}/file: File a SAR

Topology:
- GET /api/topology/graph: Merchant network graph (nodes, edges, metrics)
- GET /api/topology/rings: Payment network ring analysis

MARL:
- GET /api/marl/agents: Agent status (id, role, strategy, reward, epsilon)
- POST /api/marl/evolve: Run evolution epochs
- GET /api/marl/history: Evolution history

Conformal Prediction:
- GET /api/conformal/stats: Coverage, error bound, set sizes

Activation Steering:
- GET /api/steering/concepts: Available steering concepts
- POST /api/steering/apply: Apply steering (concept_id, intensity)
- GET /api/steering/presets: Intensity presets

Constrained Diffusion:
- GET /api/constraints/list: List all constraints
- POST /api/constraints/validate: Validate samples against constraints
- POST /api/constraints/generate: Generate constrained samples

Federated Learning:
- GET /api/federated/status: Training status, round, accuracy
- POST /api/federated/round: Trigger a federated round
- GET /api/federated/privacy: Privacy budget (epsilon/delta)
- GET /api/federated/banks: Per-bank status and accuracy

Stackelberg Game Theory:
- GET /api/game/equilibrium: Current equilibrium state
- POST /api/game/solve: Run Stackelberg solver
- GET /api/game/history: Game history rounds
- GET /api/game/convergence: Convergence data over iterations

Zero-Knowledge Proofs:
- POST /api/zkp/prove: Generate ZKP for transaction
- POST /api/zkp/verify: Verify a ZKP proof
- GET /api/zkp/certificate: ZKP system certificate
- GET /api/zkp/stats: Proof generation statistics

WebSocket:
- ws://localhost:8000/ws/transactions: Real-time transaction streaming

---

## Dashboard (dashboard/)

- ArenaDashboard.tsx: Main container, 9 tabs, state management
- RedBlueArena.tsx: Split-view transaction feeds (red=fraud, blue=legitimate)
- AttackMatrix.tsx: Heatmap visualization of attack categories vs risk levels
- DefenseMetrics.tsx: Precision/Recall/ROC-AUC charts, historical trends
- AttackInjection.tsx: Judge attack injection panel for A/B testing
- TopologyGraph.tsx: React Flow network graph of merchant relationships
- SARPanel.tsx: SAR management (pending, filed, generate)
- ExplainabilityPanel.tsx: SHAP feature importance visualization
- MARLStatus.tsx: MARL agent performance and evolution status
- SteeringPanel.tsx: Activation steering controls and concept library
- ConstraintPanel.tsx: Constraint satisfaction monitoring
- FederatedLearningPanel.tsx: Privacy budget tracking, per-bank status
- GameTheoryPanel.tsx: Payoff matrix, Stackelberg convergence
- ZKPPanel.tsx: ZK proof verification status
- StatusBadge.tsx: Reusable status indicator component
- MetricCard.tsx: Reusable metric display card

---

## Key Algorithms

- **Benford's Law** for amount distributions: P(d) = log10(1 + 1/d) for first digit
- **Luhn Algorithm** for card validation: checksum verification
- **Haversine Distance** for geo-velocity: great-circle km between coordinates
- **Mod-97** for IBAN validation: ISO 13616 checksum
- **Gradient-Guided Constrained Diffusion**: score + gamma * constraint_gradient
- **Actor-Critic RL** for attack optimization: PPO-style clipped surrogate updates
- **Federated Averaging with DP-SGD**: FedAvg aggregation + Gaussian noise
- **Stackelberg Equilibrium** solving: gradient ascent on leader payoff, best-response follower
- **Conformal Prediction** with guaranteed bounds: nonconformity scores, quantile threshold
- **Groth16-style ZK Proofs**: commitment + verification
- **Pedersen Commitments**: cryptographically binding hash commitments
- **SHAP TreeExplainer** with permutation fallback: feature importance
- **ISO 20022 pacs.008** formatting: structured payment messages

---

## How to Run

    # Backend
    pip install -r requirements.txt
    uvicorn src.api.app:app --host 0.0.0.0 --port 8000

    # Dashboard
    cd dashboard
    npm install
    npm run dev

    # Docker
    docker-compose up --build

---

## How to Extend

- Add new attack vector: edit generator.py _initialize_base_vectors(), add to AttackCategory enum in taxonomy_schema.py
- Add new constraint: extend HardConstraint in constrained_diffusion.py, register in ConstraintRegistry
- Add new dashboard tab: create component in dashboard/src/components/, add tab to ArenaDashboard.tsx
- Add new API endpoint: add to src/api/app.py
- Add new MARL attack type: add to MARLOrchestrator.ATTACK_TYPES in marl_agent.py
- Add new steering concept: add to SteeringConceptLibrary.CONCEPTS in activation_steering.py
- Add new federated bank: extend FederatedSimulation.generate_bank_data() in federated_learning.py
