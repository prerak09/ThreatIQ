'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bot, RotateCw, TrendingUp, Check, X, Shield, Activity, Cpu } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, Area, AreaChart } from 'recharts';
import { api, MARLAgent } from '@/lib/api';

// Presentation metadata only. Every number displayed in this panel comes from
// the API (/api/marl/agents); nothing here is a placeholder metric. Before the
// first evolution epoch the panel shows an explicit empty state rather than
// inventing a curve.
const AGENT_META: Record<string, { name: string; quote: string; avatarBg: string; iconColor: string }> = {
  'synthetic-id': {
    name: 'Synthetic Identity',
    quote: 'Gradual credit building with distributed KYC.',
    avatarBg: 'bg-[#FFEDE4]', iconColor: 'text-[#CF4500]',
  },
  'card-testing': {
    name: 'Card Testing',
    quote: 'Low-value probing across merchant categories.',
    avatarBg: 'bg-[#FEEAE8]', iconColor: 'text-[#EB001B]',
  },
  'account-takeover': {
    name: 'Account Takeover',
    quote: 'Credential replay with session persistence.',
    avatarBg: 'bg-[#F2EDFD]', iconColor: 'text-[#6366F1]',
  },
  'velocity-abuse': {
    name: 'Velocity Abuse',
    quote: 'Transaction splitting under rate thresholds.',
    avatarBg: 'bg-[#EBF3FE]', iconColor: 'text-[#3860BE]',
  },
  'loyalty-fraud': {
    name: 'Loyalty Fraud',
    quote: 'Points arbitrage across redemption channels.',
    avatarBg: 'bg-[#E8F7EF]', iconColor: 'text-[#0A8150]',
  },
  'credential-stuffing': {
    name: 'Credential Stuffing',
    quote: 'Distributed login attempts with proxy rotation.',
    avatarBg: 'bg-[#FFF4E0]', iconColor: 'text-[#B26B00]',
  },
};

interface UIAgent {
  agent_id: string;
  attack_type: string;
  name: string;
  quote: string;
  avatarBg: string;
  iconColor: string;
  evasion_rate: number;
  delta_this_epoch: number | null;
  episodes_evaluated: number;
  history: number[];
  min_evasion: number | null;
  max_evasion: number | null;
  policyActions: Record<string, number>;
  current_epsilon: number;
}

function toUIAgent(a: any): UIAgent {
  const meta = AGENT_META[a.agent_id] ?? {
    name: String(a.attack_type ?? a.agent_id).replace(/_/g, ' '),
    quote: '',
    avatarBg: 'bg-[#F1F1F1]',
    iconColor: 'text-[#555]',
  };
  return {
    agent_id: a.agent_id,
    attack_type: a.attack_type ?? a.agent_id,
    name: meta.name,
    quote: meta.quote,
    avatarBg: meta.avatarBg,
    iconColor: meta.iconColor,
    evasion_rate: a.evasion_rate ?? 0,
    delta_this_epoch: a.delta_this_epoch ?? null,
    episodes_evaluated: a.episodes_evaluated ?? 0,
    history: Array.isArray(a.history) ? a.history : [],
    min_evasion: a.min_evasion ?? null,
    max_evasion: a.max_evasion ?? null,
    policyActions: a.policy_actions ?? {},
    current_epsilon: a.current_epsilon ?? 1,
  };
}

// Conceptual escalation ladder used to frame what the agents are searching
// over. This is illustrative taxonomy, not a claim about a reached stage —
// the highlighted step is derived from the real epoch count below.
const EVOLUTION_STAGES = [
  { version: 'v1', name: 'Direct Card Testing', desc: 'Single merchant hits' },
  { version: 'v2', name: 'Merchant Rotation', desc: 'Simple path variation' },
  { version: 'v3', name: 'Distributed Chaining', desc: 'Multi-merchant paths' },
  { version: 'v4', name: 'Fallback Networks', desc: 'Redundant pathways' },
  { version: 'v5', name: 'Adaptive Ecosystem', desc: 'Learning & adaptation' },
];

export default function MARLStatus() {
  const [agents, setAgents] = useState<UIAgent[]>([]);
  const [isEvolving, setIsEvolving] = useState(false);
  const [evolutionEpoch, setEvolutionEpoch] = useState(0);
  const [selectedAgentPolicy, setSelectedAgentPolicy] = useState<UIAgent | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  const loadAgents = async () => {
    try {
      const res = await api.getMARLAgents();
      if (res?.agents?.length) {
        setAgents(res.agents.map(toUIAgent));
        setEvolutionEpoch(res.global_step ?? 0);
        setError(null);
      }
    } catch (err) {
      // Surface the failure instead of substituting invented numbers.
      setError('Unable to reach the MARL service. No data shown.');
    } finally {
      setLoaded(true);
    }
  };

  useEffect(() => {
    loadAgents();
  }, []);

  const handleTriggerEvolution = async () => {
    setIsEvolving(true);
    setError(null);
    try {
      await api.evolveMARL(10);
      // Re-read the authoritative state rather than extrapolating locally.
      await loadAgents();
    } catch (err) {
      setError('Evolution request failed. Displayed values are unchanged.');
    } finally {
      setIsEvolving(false);
    }
  };

  const hasData = agents.some((a) => a.history.length > 0);

  return (
    <div className="section-padding relative">
      {/* Ghost Watermark */}
      <div className="ghost-watermark top-10 right-4 text-[140px] pointer-events-none select-none opacity-60">MARL</div>

      {/* Section Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6 mb-10 relative z-10">
        <div>
          <p className="eyebrow">AUTONOMOUS ADVERSARIES</p>
          <h2 className="mt-2 text-3xl sm:text-4xl">MARL Agent Monitor</h2>
          <p className="subline mt-1.5 text-base">
            Multi-agent reinforcement learning attack strategies, live evolution epoch #{evolutionEpoch}
          </p>
        </div>

        <motion.button
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          onClick={handleTriggerEvolution}
          disabled={isEvolving}
          className="btn-primary flex items-center gap-2.5 px-6 py-3 self-start lg:self-auto shadow-level-1"
        >
          <RotateCw className={`w-4 h-4 ${isEvolving ? 'animate-spin' : ''}`} />
          <span>{isEvolving ? 'Evolving Agents...' : 'Trigger Evolution Epoch'}</span>
        </motion.button>
      </div>

      {/* 2x2 Agent Grid with Subtle Smooth Hover */}
      {error && (
        <div className="mb-6 rounded-2xl border border-[#EB001B]/30 bg-[#FEEAE8] px-5 py-3 text-sm text-[#8A0F1B] relative z-10">
          {error}
        </div>
      )}

      {loaded && !hasData && !error && (
        <div className="mb-8 rounded-2xl border border-[var(--dust-taupe)] bg-[var(--soft-bone)] px-6 py-8 text-center relative z-10">
          <p className="text-base font-medium text-[var(--ink-black)]">No evolution epochs recorded yet</p>
          <p className="caption mt-1.5">
            Run an epoch to populate these charts. Every value shown is measured against
            the live detection model — nothing is pre-seeded.
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-7 mb-10 relative z-10">
        {[...agents]
          .sort((a, b) => b.evasion_rate - a.evasion_rate)
          .map((agent, rankIndex) => (
          <motion.div 
            key={agent.agent_id} 
            whileHover={{ y: -3 }}
            transition={{ duration: 0.2 }}
            className="card-stadium p-7 sm:p-8 flex flex-col justify-between border border-[rgba(20,20,19,0.04)] hover:shadow-level-2 transition-shadow duration-300"
          >
            {/* Header row */}
            <div>
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-4">
                  {/* Robot Avatar */}
                  <div className={`w-14 h-14 rounded-full ${agent.avatarBg} flex items-center justify-center shadow-sm`}>
                    <Bot className={`w-7 h-7 ${agent.iconColor}`} />
                  </div>
                  <div>
                    <h3 className="text-xl font-medium text-[var(--ink-black)] tracking-tight">{agent.name}</h3>
                    <p className="caption mt-0.5">{agent.episodes_evaluated.toLocaleString()} episodes evaluated</p>
                  </div>
                </div>

                {/* Rank Badge */}
                <span className="w-8 h-8 rounded-full bg-[var(--ink-black)] text-white text-xs font-bold flex items-center justify-center shadow-sm">
                  #{rankIndex + 1}
                </span>
              </div>

              {/* Stats & Sparkline row */}
              <div className="flex items-end justify-between gap-6 mb-6">
                <div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-medium text-[var(--ink-black)] tracking-tight">
                      {Math.round(agent.evasion_rate * 100)}%
                    </span>
                    {agent.delta_this_epoch !== null && (
                      <span
                        className={`text-sm font-medium flex items-center gap-0.5 ${
                          agent.delta_this_epoch >= 0
                            ? 'text-[var(--success-green)]'
                            : 'text-[#EB001B]'
                        }`}
                      >
                        {agent.delta_this_epoch >= 0 ? '↑ +' : '↓ '}
                        {(agent.delta_this_epoch * 100).toFixed(1)}pp this epoch
                      </span>
                    )}
                  </div>
                  <p className="stat-label mt-1">EVASION RATE</p>
                </div>

                {/* Sparkline with filled gradient */}
                <div className="flex-1 max-w-[200px] flex flex-col items-end">
                  <span className="text-[10px] text-[var(--slate-gray)] font-mono mb-1">
                    {agent.max_evasion !== null ? `max ${agent.max_evasion.toFixed(2)}` : '—'}
                  </span>
                  <div className="w-full h-14">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={agent.history.map((v, i) => ({ i, v }))}>
                        <defs>
                          <linearGradient id={`grad-${agent.agent_id}`} x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#F37338" stopOpacity={0.35} />
                            <stop offset="100%" stopColor="#F37338" stopOpacity={0.0} />
                          </linearGradient>
                        </defs>
                        <YAxis domain={['dataMin', 'dataMax']} hide />
                        <Area
                          type="monotone"
                          dataKey="v"
                          stroke="#CF4500"
                          strokeWidth={2}
                          fill={`url(#grad-${agent.agent_id})`}
                          dot={false}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                  <span className="text-[10px] text-[var(--slate-gray)] font-mono mt-1">
                    {agent.min_evasion !== null ? `min ${agent.min_evasion.toFixed(2)}` : '—'}
                  </span>
                </div>
              </div>

              {/* Quote Block */}
              <div className="bg-[var(--soft-bone)] rounded-2xl p-4 mb-6 border border-gray-100/60">
                <p className="text-sm italic text-[var(--slate-gray)] leading-relaxed">
                  "{agent.quote}"
                </p>
              </div>
            </div>

            {/* Footer row */}
            <div className="flex items-center justify-between pt-4 border-t border-[var(--dust-taupe)]/40">
              <span className="text-xs text-[var(--slate-gray)] font-medium">
                {agent.episodes_evaluated.toLocaleString()} episodes
              </span>

              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setSelectedAgentPolicy(agent)}
                className="btn-secondary text-xs px-5 py-2 hover:bg-[var(--ink-black)] hover:text-white transition-colors"
              >
                View policy
              </motion.button>
            </div>

          </motion.div>
        ))}
      </div>

      {/* Bottom Card: Strategy Evolution Timeline */}
      <div className="card-stadium p-8 border border-[rgba(20,20,19,0.04)] relative z-10">
        <p className="eyebrow mb-8">ADVERSARY ESCALATION LADDER — ILLUSTRATIVE</p>
        <p className="caption -mt-6 mb-8">
          Conceptual framing of the strategy space the agents search. Stage highlighting
          tracks completed evolution epochs ({evolutionEpoch}); it is not a capability claim.
        </p>

        <div className="relative">
          {/* Connecting Orange Orbital Arc Curve */}
          <svg className="hidden md:block absolute top-7 left-12 right-12 w-[calc(100%-6rem)] h-12 pointer-events-none z-0" preserveAspectRatio="none" viewBox="0 0 800 40">
            <path
              d="M 0,20 Q 200,0 400,20 T 800,20"
              fill="none"
              stroke="#F37338"
              strokeWidth="2"
            />
          </svg>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-6 relative z-10">
            {EVOLUTION_STAGES.map((stage, stageIdx) => (
              <motion.div 
                key={stage.version} 
                whileHover={{ y: -3 }}
                className="flex flex-col items-center text-center cursor-default"
              >
                {/* Version badge */}
                <div className={`mb-3 px-3 py-1 rounded-full text-xs font-bold ${
                  (stageIdx < Math.min(EVOLUTION_STAGES.length, Math.floor(evolutionEpoch / 15) + (evolutionEpoch > 0 ? 1 : 0))) ? 'bg-[var(--ink-black)] text-white' : 'bg-[var(--lifted-cream)] text-[var(--slate-gray)] border border-[var(--dust-taupe)]'
                }`}>
                  {stage.version}
                </div>

                {/* Center Circle Node */}
                <div className={`w-16 h-16 rounded-full flex items-center justify-center mb-3.5 transition-all duration-300 ${
                  (stageIdx < Math.min(EVOLUTION_STAGES.length, Math.floor(evolutionEpoch / 15) + (evolutionEpoch > 0 ? 1 : 0)))
                    ? 'bg-[#FFEDE4] border-2 border-[var(--light-signal-orange)] shadow-md scale-105'
                    : 'bg-white border border-[var(--dust-taupe)] shadow-sm'
                }`}>
                  <div className="w-8 h-8 rounded-full bg-[var(--light-signal-orange)]/20 flex items-center justify-center">
                    <Activity className={`w-4 h-4 ${(stageIdx < Math.min(EVOLUTION_STAGES.length, Math.floor(evolutionEpoch / 15) + (evolutionEpoch > 0 ? 1 : 0))) ? 'text-[#CF4500]' : 'text-[var(--slate-gray)]'}`} />
                  </div>
                </div>

                <h4 className="text-sm font-medium text-[var(--ink-black)]">{stage.name}</h4>
                <p className="caption mt-1">{stage.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Policy Modal with Spring Physics */}
      <AnimatePresence>
        {selectedAgentPolicy && (
          <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <motion.div 
              initial={{ scale: 0.92, opacity: 0, y: 15 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.94, opacity: 0, y: 10 }}
              transition={{ type: 'spring', stiffness: 350, damping: 28 }}
              className="bg-white rounded-[32px] max-w-lg w-full p-8 shadow-2xl relative"
            >
              <button
                onClick={() => setSelectedAgentPolicy(null)}
                className="absolute top-6 right-6 w-9 h-9 rounded-full bg-[var(--lifted-cream)] flex items-center justify-center text-[var(--slate-gray)] hover:text-black transition-colors"
              >
                <X className="w-4 h-4" />
              </button>

              <div className="flex items-center gap-3.5 mb-6">
                <div className={`w-12 h-12 rounded-full ${selectedAgentPolicy.avatarBg} flex items-center justify-center`}>
                  <Bot className={`w-6 h-6 ${selectedAgentPolicy.iconColor}`} />
                </div>
                <div>
                  <h3 className="text-xl font-medium">{selectedAgentPolicy.name} Policy</h3>
                  <p className="caption">Reinforcement Learning Action Distribution</p>
                </div>
              </div>

              <div className="space-y-4 mb-6">
                {Object.entries(selectedAgentPolicy.policyActions || {}).map(([action, weight]) => (
                  <div key={action} className="p-4 bg-[var(--lifted-cream)] rounded-2xl">
                    <div className="flex justify-between text-sm font-medium mb-1.5">
                      <span>{action}</span>
                      <span className="font-mono">{Math.round(weight * 100)}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${weight * 100}%` }}
                        transition={{ duration: 0.5, ease: 'easeOut' }}
                        className="bg-[var(--light-signal-orange)] h-2 rounded-full"
                      />
                    </div>
                  </div>
                ))}
              </div>

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setSelectedAgentPolicy(null)}
                className="btn-primary w-full py-3"
              >
                Close Policy View
              </motion.button>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
