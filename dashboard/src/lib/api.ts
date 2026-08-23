/**
 * ThreatIQ Centralized API Client
 * Connects Frontend directly to Railway FastAPI Backend
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'https://backend-production-400c.up.railway.app';

export const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_URL ||
  (API_BASE_URL.startsWith('https://')
    ? API_BASE_URL.replace('https://', 'wss://')
    : API_BASE_URL.replace('http://', 'ws://'));

async function fetchJson<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const defaultHeaders = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  };

  const response = await fetch(url, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status} ${response.statusText}`;
    try {
      const err = await response.json();
      errorDetail = err.detail || err.message || errorDetail;
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }

  return response.json() as Promise<T>;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  components: Record<string, boolean>;
}

export interface SimulationStartRequest {
  num_victims?: number;
  fraud_ratio?: number;
  transaction_rate_tps?: number;
}

export interface DefenseMetrics {
  total_predictions: number;
  total_false_negatives: number;
  total_false_positives: number;
  replay_buffer_size: number;
  retraining_samples: number;
  batches_evaluated: number;
  last_retrain_time: number;
  detection_threshold: number;
  financial_loss: {
    false_negative_cost: number;
    false_positive_cost: number;
    total_cost: number;
  };
  roi: {
    detection_rate: number;
    cost_avoidance: number;
  };
  detection_rate_trend: number[];
}

export interface AttackInjectRequest {
  attack_type: string;
  count: number;
}

export interface Transaction {
  id: string;
  transaction_id?: string;
  amount: number;
  currency?: string;
  channel?: string;
  auth_channel?: string;
  attack_type?: string;
  attack_vector?: string;
  status: 'detected' | 'blocked' | 'missed' | 'approved' | 'flagged';
  timestamp?: string | number;
  is_fraud?: boolean;
  card_last4?: string;
  merchant_id?: string;
  blue_team_confidence?: number;
  blue_team_result?: {
    is_fraud: boolean;
    confidence: number;
    latency_ms: number;
    engine_scores?: {
      xgboost?: number;
      lightgbm?: number;
      iforest?: number;
      xgb?: number;
      lgb?: number;
    };
  };
  merchant_result?: any;
}

export interface MARLAgent {
  agent_id: string;
  name?: string;
  role?: string;
  attack_type?: string;
  reward?: number;
  current_epsilon?: number;
  strategy?: any;
  rank?: number;
  evasion_rate?: number;
  episodes_evaluated?: number;
  quote?: string;
  history?: number[];
  min_evasion?: number;
  max_evasion?: number;
  action_distribution?: Record<string, number>;
}

export interface SARItem {
  id: string;
  transaction_id: string;
  timestamp: string;
  status: 'pending' | 'filed';
  subject: {
    name: string;
    account: string;
    risk_level: 'HIGH' | 'MEDIUM' | 'LOW';
  };
  summary: string;
  narrative: string;
  risk_factors: Array<{
    category: string;
    factor: string;
    level: 'HIGH' | 'MEDIUM' | 'LOW';
  }>;
}

export interface ConceptItem {
  concept_id: string;
  id?: string;
  name: string;
  description: string;
  layer?: number;
  layer_index?: number;
  default_alpha: number;
  applied?: boolean;
}

export interface PresetItem {
  name: string;
  concepts: string[];
  alphas: number[];
  layers?: number[];
}

export interface BankStatus {
  bank_id: string;
  name: string;
  status: string;
  data_points: number;
  local_accuracy: number;
  contribution_weight: number;
  latency_ms: number;
}

export interface GameEquilibriumResponse {
  equilibrium_type: string;
  leader_role: string;
  follower_role: string;
  leader_payoff: number;
  blue_mix: number[];
  red_mix?: number[];
  best_blue_strategy?: number;
  best_red_strategy?: number;
  payoff_matrix?: {
    blue_payoffs: number[][];
    red_payoffs: number[][];
    shape?: number[];
  };
  iterations_run?: number;
  converged?: boolean;
}

export interface ZKPProveResponse {
  proof_id: string;
  tx_id?: string;
  transaction_id?: string;
  proof_type?: string;
  circuit?: string;
  proving_time_ms?: number;
  generation_time_ms?: number;
  proof_size_bytes?: number;
  verification_key_hash?: string;
  is_valid?: boolean;
  public_signals?: any;
  self_verification?: boolean;
}

export const api = {
  // Health
  getHealth: () => fetchJson<HealthResponse>('/api/health'),

  // Simulation Lifecycle
  startSimulation: (req?: SimulationStartRequest) =>
    fetchJson<{ message: string; tps: number; fraud_ratio: number }>('/api/simulation/start', {
      method: 'POST',
      body: JSON.stringify(req || { num_victims: 500, fraud_ratio: 0.18, transaction_rate_tps: 8.0 }),
    }),

  stopSimulation: () =>
    fetchJson<{ message: string }>('/api/simulation/stop', {
      method: 'POST',
    }),

  getMetrics: () => fetchJson<any>('/api/metrics'),
  getDefenseMetrics: () => fetchJson<DefenseMetrics>('/api/defense/metrics'),

  // Attack Injection & Taxonomy
  injectAttack: (attack_type: string, count: number = 5) =>
    fetchJson<{ injected: number; attack_type: string; results: any[] }>('/api/attack/inject', {
      method: 'POST',
      body: JSON.stringify({ attack_type, count }),
    }),

  getAttackMatrix: () => fetchJson<any>('/api/attack/matrix'),
  getThreatTaxonomy: () => fetchJson<any>('/api/threats/taxonomy'),
  getThreatStatistics: () => fetchJson<any>('/api/threats/statistics'),

  // Model & Defense
  trainModel: (n_samples: number = 1000) =>
    fetchJson<{ message: string; train_metrics: any; test_metrics: any }>('/api/model/train', {
      method: 'POST',
      body: JSON.stringify({ n_samples }),
    }),

  updateThreshold: (threshold: number) =>
    fetchJson<{ message: string; new_threshold: number }>('/api/model/threshold', {
      method: 'POST',
      body: JSON.stringify({ threshold }),
    }),

  // Explainability & Conformal
  getExplanation: (transaction_id: string) =>
    fetchJson<any>(`/api/xai/explain/${encodeURIComponent(transaction_id)}`),

  getRingExplanation: () => fetchJson<any>('/api/xai/ring-explanation'),
  getConformalStats: () => fetchJson<any>('/api/conformal/stats'),

  // Topology & Graph
  getTopologyGraph: () => fetchJson<{ nodes: any[]; edges: any[]; metrics: any }>('/api/topology/graph'),
  getFraudRings: () => fetchJson<{ rings: any[]; total_rings: number; total_nodes: number }>('/api/topology/rings'),

  // MARL Multi-Agent Reinforcement Learning
  getMARLAgents: () => fetchJson<{ agents: any[]; global_step: number }>('/api/marl/agents'),
  evolveMARL: () =>
    fetchJson<{ evolved: boolean; epochs_run: number; history: any[] }>('/api/marl/evolve', {
      method: 'POST',
    }),

  // Activation Steering
  getSteeringConcepts: () => fetchJson<{ concepts: any[]; total: number }>('/api/steering/concepts'),
  getSteeringPresets: () => fetchJson<{ presets: PresetItem[] }>('/api/steering/presets'),
  applySteering: (concept_id: string, alpha: number = 0.7) =>
    fetchJson<any>('/api/steering/apply', {
      method: 'POST',
      body: JSON.stringify({ concept_id, alpha }),
    }),

  // Constrained Diffusion
  getConstraints: () => fetchJson<{ constraints: any[]; total: number }>('/api/constraints/list'),
  validateConstraints: (features: Record<string, any>) =>
    fetchJson<any>('/api/constraints/validate', {
      method: 'POST',
      body: JSON.stringify({ features }),
    }),
  generateConstrainedSample: (attack_type: string = 'multi_hop_cnp') =>
    fetchJson<{ n_generated: number; samples: any[]; benford_first_digits: any }>('/api/constraints/generate', {
      method: 'POST',
      body: JSON.stringify({ attack_type }),
    }),

  // Federated Learning
  getFederatedStatus: () => fetchJson<any>('/api/federated/status'),
  getFederatedBanks: () => fetchJson<{ banks: any[]; total_samples: number }>('/api/federated/banks'),
  runFederatedRound: () =>
    fetchJson<any>('/api/federated/round', {
      method: 'POST',
    }),

  // Game Theory
  getGameEquilibrium: () => fetchJson<GameEquilibriumResponse>('/api/game/equilibrium'),
  solveGame: (iterations: number = 100, lr: number = 0.01) =>
    fetchJson<any>('/api/game/solve', {
      method: 'POST',
      body: JSON.stringify({ iterations, lr }),
    }),

  // Zero-Knowledge Proofs
  generateZKPProof: (tx_id: string = 'TXN-001', amount: number = 150.0, score: number = 0.12) =>
    fetchJson<ZKPProveResponse>('/api/zkp/prove', {
      method: 'POST',
      body: JSON.stringify({ tx_id, amount, score }),
    }),
  verifyZKPProof: (proof_id: string) =>
    fetchJson<any>(`/api/zkp/verify?proof_id=${encodeURIComponent(proof_id)}`, {
      method: 'POST',
    }),
  getZKPCertificate: () => fetchJson<any>('/api/zkp/certificate'),

  // Suspicious Activity Reports
  getPendingSARs: () => fetchJson<any>('/api/sar/pending'),
  generateSAR: (transaction_id?: string) =>
    fetchJson<any>(`/api/sar/generate${transaction_id ? `?transaction_id=${encodeURIComponent(transaction_id)}` : ''}`, {
      method: 'POST',
    }),
  fileSAR: (sar_id: string) =>
    fetchJson<any>(`/api/sar/${encodeURIComponent(sar_id)}/file`, {
      method: 'POST',
    }),
};
