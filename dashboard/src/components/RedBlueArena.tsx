'use client';

import { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  ShieldCheck, 
  Zap, 
  CheckCircle, 
  XCircle, 
  Eye, 
  Sliders, 
  RefreshCw,
  Send,
  Code
} from 'lucide-react';
import { api, Transaction } from '@/lib/api';
import { streamClient } from '@/lib/websocket';

const ATTACK_VECTORS = [
  { id: 'multi_hop_cnp', name: 'Multi-Hop CNP' },
  { id: 'synthetic_identity', name: 'Synthetic Identity' },
  { id: 'prompt_injection', name: 'Prompt Injection' },
  { id: 'voice_deepfake', name: 'Voice Deepfake' },
  { id: 'credential_stuffing', name: 'Credential Stuffing' },
  { id: 'velocity_abuse', name: 'Velocity Abuse' },
];

const INITIAL_TRANSACTIONS: Transaction[] = [
  {
    id: 'TXN-88FCB93493D9',
    amount: 14500.0,
    currency: 'USD',
    channel: 'tokenized',
    attack_type: 'Multi-Hop CNP',
    status: 'detected',
    timestamp: Date.now() - 2000,
    card_last4: '4521',
    blue_team_confidence: 0.94,
    blue_team_result: {
      is_fraud: true,
      confidence: 0.94,
      latency_ms: 11.8,
      engine_scores: { xgboost: 0.96, lightgbm: 0.93, iforest: 0.88 },
    },
  },
  {
    id: 'TXN-54C99A10CA78',
    amount: 3200.0,
    currency: 'EUR',
    channel: 'e-commerce',
    attack_type: 'Synthetic Identity',
    status: 'detected',
    timestamp: Date.now() - 7000,
    card_last4: '8890',
    blue_team_confidence: 0.89,
    blue_team_result: {
      is_fraud: true,
      confidence: 0.89,
      latency_ms: 9.4,
      engine_scores: { xgboost: 0.91, lightgbm: 0.88, iforest: 0.74 },
    },
  },
  {
    id: 'TXN-C4BCFEA42E34',
    amount: 85.5,
    currency: 'USD',
    channel: 'pos_contactless',
    attack_type: 'Normal Payment',
    status: 'approved',
    timestamp: Date.now() - 15000,
    card_last4: '1102',
    blue_team_confidence: 0.08,
    blue_team_result: {
      is_fraud: false,
      confidence: 0.08,
      latency_ms: 6.2,
      engine_scores: { xgboost: 0.06, lightgbm: 0.07, iforest: 0.12 },
    },
  },
];

export interface RedBlueArenaProps {
  isRunning?: boolean;
  isConnected?: boolean;
  onStart?: () => void;
  onStop?: () => void;
  onAttackInjected?: (injectedCount: number, detected: number, addedRoi: number) => void;
}

export default function RedBlueArena({ 
  isRunning = false, 
  isConnected = false, 
  onStart, 
  onStop,
  onAttackInjected,
}: RedBlueArenaProps) {
  const [transactions, setTransactions] = useState<Transaction[]>(INITIAL_TRANSACTIONS);
  const [selectedAttack, setSelectedAttack] = useState('multi_hop_cnp');
  const [injectCount, setInjectCount] = useState(5);
  const [isInjecting, setIsInjecting] = useState(false);
  const [selectedTxPayload, setSelectedTxPayload] = useState<Transaction | null>(null);
  const [threshold, setThreshold] = useState(0.75);

  // Subscribe to live transactions
  useEffect(() => {
    const unsub = streamClient.onTransaction((tx) => {
      if (isRunning) {
        setTransactions((prev) => [tx, ...prev.slice(0, 30)]);
      }
    });
    return () => unsub();
  }, [isRunning]);

  const handleInjectAttack = async () => {
    setIsInjecting(true);
    try {
      const res = await api.injectAttack(selectedAttack, injectCount);
      if (res && res.results && res.results.length > 0) {
        const mapped: Transaction[] = res.results.map((r: any) => ({
          id: r.id || r.transaction_id || `TXN-${Math.random().toString(36).substr(2, 6)}`,
          amount: r.amount || 2500,
          currency: r.currency || 'USD',
          channel: r.channel || r.auth_channel || 'tokenized',
          attack_type: r.attack_vector_id || r.attack_vector || selectedAttack,
          status: r.status || (r.blue_team_flagged ? 'detected' : 'missed'),
          timestamp: Date.now(),
          is_fraud: true,
          card_last4: r.card_last4 || '9901',
          blue_team_confidence: r.blue_team_confidence || 0.88,
          blue_team_result: r.blue_team_result,
        }));

        let detected = 0;
        let addedRoi = 0;
        mapped.forEach((m) => {
          if (m.status === 'detected' || m.status === 'blocked' || m.blue_team_result?.is_fraud) {
            detected++;
            addedRoi += Math.round(m.amount * 120);
          }
        });

        if (onAttackInjected) {
          onAttackInjected(mapped.length, detected, addedRoi);
        }

        setTransactions((prev) => [...mapped, ...prev.slice(0, 30)]);
      }
    } catch (err) {
      console.warn('Attack injection fallback:', err);
      // Fallback local injection
      const mock: Transaction = {
        id: `TXN-${Date.now().toString(36).toUpperCase()}`,
        amount: Math.round(Math.random() * 8000 + 500),
        currency: 'USD',
        channel: 'e-commerce',
        attack_type: selectedAttack.replace(/_/g, ' ').toUpperCase(),
        status: Math.random() > 0.3 ? 'detected' : 'missed',
        timestamp: Date.now(),
        is_fraud: true,
        card_last4: '7721',
        blue_team_confidence: 0.87,
      };
      if (onAttackInjected) {
        onAttackInjected(1, mock.status === 'detected' ? 1 : 0, 1500);
      }
      setTransactions((prev) => [mock, ...prev.slice(0, 30)]);
    } finally {
      setIsInjecting(false);
    }
  };

  const handleUpdateThreshold = async (newVal: number) => {
    setThreshold(newVal);
    try {
      await api.updateThreshold(newVal);
    } catch (e) {
      // ignore
    }
  };

  const redAttacks = transactions.filter((t) => t.is_fraud || t.attack_type !== 'Normal Payment');
  const blueDefenses = transactions;

  return (
    <div className="section-padding relative">
      {/* Quick Attack Injector Control Bar */}
      <div className="card-stadium p-6 sm:p-8 mb-10 border border-[rgba(20,20,19,0.04)]">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div>
            <p className="eyebrow">RED TEAM ADVERSARIAL INJECTOR</p>
            <h3 className="mt-1 text-2xl font-medium">Inject Synthetic Attack Payload</h3>
          </div>

          <div className="flex items-center gap-3.5 flex-wrap">
            <select
              value={selectedAttack}
              onChange={(e) => setSelectedAttack(e.target.value)}
              className="px-4 py-2.5 rounded-full bg-[var(--lifted-cream)] border border-[var(--dust-taupe)] text-sm font-medium text-[var(--ink-black)] focus:outline-none"
            >
              {ATTACK_VECTORS.map((atk) => (
                <option key={atk.id} value={atk.id}>{atk.name}</option>
              ))}
            </select>

            <select
              value={injectCount}
              onChange={(e) => setInjectCount(Number(e.target.value))}
              className="px-4 py-2.5 rounded-full bg-[var(--lifted-cream)] border border-[var(--dust-taupe)] text-sm font-medium text-[var(--ink-black)] focus:outline-none"
            >
              <option value={1}>1 Vector</option>
              <option value={5}>5 Vectors (Burst)</option>
              <option value={20}>20 Vectors (Swarm)</option>
            </select>

            <button
              onClick={handleInjectAttack}
              disabled={isInjecting}
              className="btn-primary text-sm px-6 py-2.5 shadow-sm"
            >
              <Zap className="w-4 h-4 text-[var(--light-signal-orange)]" />
              <span>{isInjecting ? 'Injecting...' : 'Launch Attack'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Dual Column: Red Team (Attacks) vs Blue Team (Detection) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-10">
        
        {/* Red Team Column */}
        <div className="card-stadium p-7 sm:p-8 border border-[rgba(20,20,19,0.04)]">
          <div className="flex items-center justify-between mb-6 pb-4 border-b border-[var(--dust-taupe)]/40">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-[#FEEAE8] flex items-center justify-center">
                <ShieldAlert className="w-5 h-5 text-[var(--danger-red)]" />
              </div>
              <div>
                <p className="eyebrow">RED TEAM SIMULATION</p>
                <h3 className="text-xl font-medium">Adversarial Probing Stream</h3>
              </div>
            </div>
            <span className="pill-btn inactive text-xs">
              {redAttacks.length} Active
            </span>
          </div>

          <div className="space-y-3.5 max-h-[500px] overflow-y-auto pr-2">
            {redAttacks.length === 0 ? (
              <p className="text-center py-16 text-[var(--slate-gray)]">No active attacks in stream. Launch an attack above.</p>
            ) : (
              redAttacks.map((tx) => (
                <div key={tx.id} className="p-4 bg-[var(--lifted-cream)] rounded-2xl border border-[rgba(20,20,19,0.04)] flex items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-sm text-[var(--ink-black)]">{tx.id}</span>
                      <span className="status-chip danger text-[10px]">ATTACK</span>
                    </div>
                    <p className="caption text-xs">
                      {tx.attack_type} · {tx.currency || 'USD'} {tx.amount.toLocaleString()} · card ****{tx.card_last4 || '4521'}
                    </p>
                  </div>

                  <button
                    onClick={() => setSelectedTxPayload(tx)}
                    className="satellite-btn !w-9 !h-9"
                    title="Inspect ISO20022 message payload"
                  >
                    <Code className="w-4 h-4 text-[var(--slate-gray)]" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Blue Team Column */}
        <div className="card-stadium p-7 sm:p-8 border border-[rgba(20,20,19,0.04)]">
          <div className="flex items-center justify-between mb-6 pb-4 border-b border-[var(--dust-taupe)]/40">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-[#EBF3FE] flex items-center justify-center">
                <ShieldCheck className="w-5 h-5 text-[var(--link-blue)]" />
              </div>
              <div>
                <p className="eyebrow">BLUE TEAM DEFENSE</p>
                <h3 className="text-xl font-medium">GNN Ensemble Decision Stream</h3>
              </div>
            </div>
            <span className="pill-btn active text-xs bg-[var(--link-blue)]">
              Real-time
            </span>
          </div>

          <div className="space-y-3.5 max-h-[500px] overflow-y-auto pr-2">
            {blueDefenses.length === 0 ? (
              <p className="text-center py-16 text-[var(--slate-gray)]">No decisions yet.</p>
            ) : (
              blueDefenses.map((tx) => {
                const isDetected = tx.status === 'detected' || tx.status === 'blocked';
                return (
                  <div key={tx.id} className="p-4 bg-[var(--lifted-cream)] rounded-2xl border border-[rgba(20,20,19,0.04)] flex items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-semibold text-sm text-[var(--ink-black)]">{tx.id}</span>
                        <span className={`status-chip text-[10px] ${isDetected ? 'danger' : 'success'}`}>
                          {isDetected ? 'BLOCKED' : 'CLEARED'}
                        </span>
                        <span className="caption font-mono text-[11px]">
                          {Math.round((tx.blue_team_confidence || 0.85) * 100)}% conf
                        </span>
                      </div>
                      <p className="caption text-xs">
                        Channel: {tx.channel || 'tokenized'} · Latency {tx.blue_team_result?.latency_ms || 11.2}ms
                      </p>
                    </div>

                    <button
                      onClick={() => setSelectedTxPayload(tx)}
                      className="satellite-btn !w-9 !h-9"
                      title="View Decision & SHAP"
                    >
                      <Eye className="w-4 h-4 text-[var(--slate-gray)]" />
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </div>

      </div>

      {/* Transaction ISO 20022 & Decision Inspector Modal */}
      {selectedTxPayload && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-[32px] max-w-xl w-full p-8 shadow-2xl relative animate-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between mb-6">
              <div>
                <span className="eyebrow">ISO 20022 TELEMETRY</span>
                <h3 className="text-xl font-medium mt-1">{selectedTxPayload.id}</h3>
              </div>
              <button
                onClick={() => setSelectedTxPayload(null)}
                className="w-9 h-9 rounded-full bg-[var(--lifted-cream)] flex items-center justify-center text-[var(--slate-gray)] hover:text-black"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4 mb-6 text-sm">
              <div className="p-4 bg-[var(--lifted-cream)] rounded-2xl space-y-2">
                <div className="flex justify-between"><span className="text-[var(--slate-gray)]">Amount:</span> <span className="font-semibold">{selectedTxPayload.currency || 'USD'} {selectedTxPayload.amount.toFixed(2)}</span></div>
                <div className="flex justify-between"><span className="text-[var(--slate-gray)]">Attack Vector:</span> <span className="font-semibold text-[var(--danger-red)]">{selectedTxPayload.attack_type}</span></div>
                <div className="flex justify-between"><span className="text-[var(--slate-gray)]">Ensemble Confidence:</span> <span className="font-semibold text-[var(--link-blue)]">{Math.round((selectedTxPayload.blue_team_confidence || 0.88) * 100)}%</span></div>
                <div className="flex justify-between"><span className="text-[var(--slate-gray)]">ISO Standard:</span> <span className="font-mono">pacs.008.001.08 (Mastercard SEPA)</span></div>
              </div>

              <div className="p-4 bg-gray-900 text-green-400 font-mono text-xs rounded-2xl overflow-x-auto">
                <pre>{JSON.stringify(selectedTxPayload.blue_team_result || selectedTxPayload, null, 2)}</pre>
              </div>
            </div>

            <button
              onClick={() => setSelectedTxPayload(null)}
              className="btn-primary w-full py-3"
            >
              Close Inspector
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
