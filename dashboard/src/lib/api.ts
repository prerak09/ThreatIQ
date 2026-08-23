/**
 * ThreatIQ Centralized API Client
 * Connects to Railway FastAPI Backend
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'https://backend-production-400c.up.railway.app';

export const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_URL ||
  API_BASE_URL.replace(/^http/, 'ws');

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers || {}),
      },
    });

    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(`API error ${res.status}: ${errorText || res.statusText}`);
    }

    return (await res.json()) as T;
  } catch (error) {
    console.warn(`Fetch error for ${endpoint}:`, error);
    throw error;
  }
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface HealthResponse {
  status: string;
  simulation_running: boolean;
  model_trained: boolean;
  marl_orchestrator: boolean;
  sar_queue_size: number;
  active_learning_active: boolean;
  threat_intel_active: boolean;
  conformal_detector: boolean;
  conformal_calibrated: boolean;
  steering_engine: boolean;
  constraints_active: boolean;
  federated_learning: boolean;
  game_solver: boolean;
  zkp_system: boolean;
  temporal_gnn: boolean;
  timestamp: string;
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
  timestamp: number | string;
  is_fraud?: boolean;
  card_last4?: string;
  merchant_id?: string;
  blue_team_confidence?: number;
  blue_team_result?: {
    is_fraud: boolean;
    confidence: number;
    latency_ms: number;
    engine_scores?: Record<string, number>;
  };
  merchant_result?: {
    status: string;
    response_code?: string;
  };
}

export interface MARLAgent {
  agent_id: string;
  name: string;
  rank: number;
  evasion_rate: number;
  delta_this_epoch: number;
  episodes_evaluated: number;
  quote: string;
  strategy: string;
  history: number[];
  min_evasion: number;
  max_evasion: number;
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
  name: string;
  description: string;
  layer: number;
  default_alpha: number;
  applied: boolean;
}

export interface PresetItem {
  name: string;
  intensity: number;
  concepts: string[];
  alphas: number[];
}

export interface BankStatus {
  bank_id: string;
  name: string;
  status: string;
  data_points: number;
  local_accuracy: number;
  contribution_weight: number;
  latency_ms: number;
  is_training?: boolean;
}

export interface ZKPProveResponse {
  proof_id: string;
  tx_id: string;
  verification_key_hash: string;
  generation_time_ms: number;
  is_valid: boolean;
  proof_size_bytes: number;
}

export interface GameEquilibriumResponse {
  blue_strategy: string;
  red_strategy: string;
  blue_payoff: number;
  red_payoff: number;
  iterations: number;
  converged: boolean;
}

// ---------------------------------------------------------------------------
// API Object
// ---------------------------------------------------------------------------

export const api = {
  // Health
  getHealth: () => fetchJson<HealthResponse>('/api/health'),

  // Simulation Lifecycle
  startSimulation: (req?: SimulationStartRequest) =>
    fetchJson<{ message: string; tps: number; fraud_ratio: number }>('/api/simulation/start', {
      method: 'POST',
      body: JSON.stringify(req || { num_victims: 500, fraud_ratio: 0.18, transaction_rate_tps: 12.0 }),
    }),

  stopSimulation: () =>
    fetchJson<{ message: string }>('/api/simulation/stop', {
      method: 'POST',
    }),

  getMetrics: () => fetchJson<any>('/api/metrics'),
  getDefenseMetrics: () => fetchJson<DefenseMetrics>('/api/defense/metrics'),

  // Attack Injection & Taxonomy
  injectAttack: (attack_type: string, count: number = 5) =>
    fetchJson<{ injected_count: number; attack_type: string; results: any[] }>('/api/attack/inject', {
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
  getTopologyGraph: () => fetchJson<any>('/api/topology/graph'),
  getFraudRings: () => fetchJson<any>('/api/topology/rings'),

  // MARL Multi-Agent Reinforcement Learning
  getMARLAgents: () => fetchJson<{ total_agents: number; agents: any[] }>('/api/marl/agents'),
  evolveMARL: () =>
    fetchJson<{ message: string; active_attacks: string[]; total_agents: number; iteration: number }>('/api/marl/evolve', {
      method: 'POST',
    }),
  getMARLHistory: () => fetchJson<any>('/api/marl/history'),

  // Steering
  getSteeringConcepts: () => fetchJson<{ concepts: ConceptItem[] }>('/api/steering/concepts'),
  applySteering: (concept_id: string, intensity: number = 0.5) =>
    fetchJson<{ message: string; concept_id: string; intensity: number; is_active: boolean }>('/api/steering/apply', {
      method: 'POST',
      body: JSON.stringify({ concept_id, intensity }),
    }),
  getSteeringPresets: () => fetchJson<{ presets: Record<string, PresetItem> }>('/api/steering/presets'),

  // Constraints
  getConstraintsList: () => fetchJson<{ total_constraints: number; constraints: any[] }>('/api/constraints/list'),
  validateConstraints: (transaction: Record<string, any>) =>
    fetchJson<{ is_valid: boolean; violations: string[]; count: number }>('/api/constraints/validate', {
      method: 'POST',
      body: JSON.stringify(transaction),
    }),
  generateConstrainedSample: (attack_type: string = 'multi_hop_cnp') =>
    fetchJson<{ is_valid: boolean; violations: string[]; sample: any }>('/api/constraints/generate', {
      method: 'POST',
      body: JSON.stringify({ attack_type }),
    }),

  // Federated Learning
  getFederatedStatus: () => fetchJson<any>('/api/federated/status'),
  runFederatedRound: () =>
    fetchJson<{ round: number; global_accuracy: number; participating_banks: number; epsilon_used: number }>('/api/federated/round', {
      method: 'POST',
    }),
  getFederatedPrivacy: () => fetchJson<any>('/api/federated/privacy'),
  getFederatedBanks: () => fetchJson<{ total_banks: number; banks: BankStatus[] }>('/api/federated/banks'),

  // Game Theory
  getGameEquilibrium: () => fetchJson<GameEquilibriumResponse>('/api/game/equilibrium'),
  solveGame: (iterations: number = 100, learning_rate: number = 0.01) =>
    fetchJson<{ message: string; iterations: number; blue_strategy: string; red_strategy: string; blue_payoff: number; red_payoff: number; converged: boolean }>('/api/game/solve', {
      method: 'POST',
      body: JSON.stringify({ iterations, learning_rate }),
    }),
  getGameConvergence: () => fetchJson<{ iterations: number; history: any[] }>('/api/game/convergence'),

  // ZKP Verification
  generateZKPProof: (tx_id: string, risk_score: number = 0.15) =>
    fetchJson<ZKPProveResponse>('/api/zkp/prove', {
      method: 'POST',
      body: JSON.stringify({ tx_id, risk_score }),
    }),
  verifyZKPProof: (proof_id: string) =>
    fetchJson<{ is_valid: boolean; verified_at: string }>('/api/zkp/verify', {
      method: 'POST',
      body: JSON.stringify({ proof_id }),
    }),
  getZKPCertificate: () => fetchJson<any>('/api/zkp/certificate'),
  getZKPStats: () => fetchJson<any>('/api/zkp/stats'),

  // SAR (Suspicious Activity Reports)
  getPendingSARs: () => fetchJson<{ total_pending: number; sars: any[] }>('/api/sar/pending'),
  generateSAR: (transaction_id?: string) =>
    fetchJson<{ message: string; sar: any }>('/api/sar/generate', {
      method: 'POST',
      body: JSON.stringify({ transaction_id: transaction_id || `TXN-SAR-${Date.now()}` }),
    }),
  fileSAR: (sar_id: string) =>
    fetchJson<{ message: string; sar_id: string; filed_at: string }>(`/api/sar/${encodeURIComponent(sar_id)}/file`, {
      method: 'POST',
    }),
};
