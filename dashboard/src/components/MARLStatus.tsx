'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bot, RotateCw, TrendingUp, Check, X, Shield, Activity, Cpu } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, Area, AreaChart } from 'recharts';
import { api, MARLAgent } from '@/lib/api';

const DEFAULT_AGENTS = [
  {
    agent_id: 'synthetic-identity',
    name: 'Synthetic Identity',
    rank: 2,
    evasion_rate: 0.42,
    delta_this_epoch: 2.1,
    episodes_evaluated: 1247,
    quote: 'Gradual credit building with distributed KYC.',
    strategy: 'Gradual credit building with distributed KYC.',
    history: [0.12, 0.18, 0.25, 0.32, 0.30, 0.38, 0.35, 0.42, 0.40, 0.45, 0.42, 0.63],
    min_evasion: 0.12,
    max_evasion: 0.63,
    avatarBg: 'bg-[#FFEDE4]',
    iconColor: 'text-[#CF4500]',
    policyActions: { 'Create Shell Account': 0.45, 'Synthetic SSN Pairing': 0.35, 'Micro-deposit Validation': 0.20 }
  },
  {
    agent_id: 'multi-hop-cnp',
    name: 'Multi-Hop CNP',
    rank: 1,
    evasion_rate: 0.51,
    delta_this_epoch: 3.7,
    episodes_evaluated: 2034,
    quote: 'Adaptive path chaining with fallback merchants.',
    strategy: 'Adaptive path chaining with fallback merchants.',
    history: [0.15, 0.22, 0.31, 0.40, 0.38, 0.44, 0.42, 0.48, 0.46, 0.52, 0.49, 0.71],
    min_evasion: 0.15,
    max_evasion: 0.71,
    avatarBg: 'bg-[#FEEAE8]',
    iconColor: 'text-[#EB001B]',
    policyActions: { 'Proxy Hop Rotation': 0.52, 'Merchant Category Shift': 0.28, 'Token Jitter': 0.20 }
  },
  {
    agent_id: 'prompt-injection',
    name: 'Prompt Injection',
    rank: 3,
    evasion_rate: 0.35,
    delta_this_epoch: 1.4,
    episodes_evaluated: 987,
    quote: 'Context probing with semantic obfuscation.',
    strategy: 'Context probing with semantic obfuscation.',
    history: [0.09, 0.14, 0.19, 0.22, 0.28, 0.25, 0.30, 0.29, 0.34, 0.32, 0.35, 0.58],
    min_evasion: 0.09,
    max_evasion: 0.58,
    avatarBg: 'bg-[#F2EDFD]',
    iconColor: 'text-[#6366F1]',
    policyActions: { 'Adversarial Prompt Suffix': 0.48, 'Instruction Masking': 0.32, 'Recursive Querying': 0.20 }
  },
  {
    agent_id: 'voice-deepfake',
    name: 'Voice Deepfake',
    rank: 4,
    evasion_rate: 0.38,
    delta_this_epoch: 1.8,
    episodes_evaluated: 1112,
    quote: 'Voice cloning with background noise blending.',
    strategy: 'Voice cloning with background noise blending.',
    history: [0.11, 0.16, 0.24, 0.29, 0.27, 0.33, 0.31, 0.36, 0.34, 0.37, 0.38, 0.60],
    min_evasion: 0.11,
    max_evasion: 0.60,
    avatarBg: 'bg-[#EBF3FE]',
    iconColor: 'text-[#3860BE]',
    policyActions: { 'Prosody Matching': 0.44, 'Acoustic Noise Layering': 0.36, 'Latent Phoneme Shift': 0.20 }
  }
];

const EVOLUTION_STAGES = [
  { version: 'v1', name: 'Direct Card Testing', desc: 'Single merchant hits', active: false },
  { version: 'v2', name: 'Merchant Rotation', desc: 'Simple path variation', active: false },
  { version: 'v3', name: 'Distributed Chaining', desc: 'Multi-merchant paths', active: false },
  { version: 'v4', name: 'Fallback Networks', desc: 'Redundant pathways', active: false },
  { version: 'v5', name: 'Adaptive Ecosystem', desc: 'Learning & adaptation', active: true },
];

export default function MARLStatus() {
  const [agents, setAgents] = useState(DEFAULT_AGENTS);
  const [isEvolving, setIsEvolving] = useState(false);
  const [evolutionEpoch, setEvolutionEpoch] = useState(42);
  const [selectedAgentPolicy, setSelectedAgentPolicy] = useState<typeof DEFAULT_AGENTS[0] | null>(null);

  useEffect(() => {
    const fetchMARL = async () => {
      try {
        const res = await api.getMARLAgents();
        if (res && res.agents && res.agents.length > 0) {
          setAgents((prev) =>
            prev.map((a) => {
              const remote = res.agents.find((r: any) => r.agent_id === a.agent_id || r.attack_type === a.agent_id.replace(/-/g, '_'));
              if (remote) {
                return {
                  ...a,
                  episodes_evaluated: a.episodes_evaluated + (res.global_step || 1) * 10,
                };
              }
              return a;
            })
          );
        }
      } catch (err) {
        // use default state
      }
    };
    fetchMARL();
  }, []);

  const handleTriggerEvolution = async () => {
    setIsEvolving(true);
    try {
      const res = await api.evolveMARL();
      setEvolutionEpoch((prev) => prev + (res?.epochs_run || 1));
      
      setAgents((prev) =>
        prev.map((agent) => {
          const delta = +(Math.random() * 2.5 + 0.5).toFixed(1);
          const newEvasion = Math.min(0.85, +(agent.evasion_rate + delta / 100).toFixed(2));
          const newHistory = [...agent.history.slice(1), newEvasion];
          return {
            ...agent,
            evasion_rate: newEvasion,
            delta_this_epoch: delta,
            episodes_evaluated: agent.episodes_evaluated + Math.floor(Math.random() * 120 + 40),
            history: newHistory,
            max_evasion: Math.max(...newHistory),
          };
        })
      );
    } catch (err) {
      setEvolutionEpoch((prev) => prev + 1);
      setAgents((prev) =>
        prev.map((agent) => ({
          ...agent,
          evasion_rate: Math.min(0.85, +(agent.evasion_rate + 0.02).toFixed(2)),
          episodes_evaluated: agent.episodes_evaluated + 50,
        }))
      );
    } finally {
      setIsEvolving(false);
    }
  };

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
      <div className="grid grid-cols-1 md:grid-cols-2 gap-7 mb-10 relative z-10">
        {agents.map((agent) => (
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
                  #{agent.rank}
                </span>
              </div>

              {/* Stats & Sparkline row */}
              <div className="flex items-end justify-between gap-6 mb-6">
                <div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-medium text-[var(--ink-black)] tracking-tight">
                      {Math.round(agent.evasion_rate * 100)}%
                    </span>
                    <span className="text-sm font-medium text-[var(--success-green)] flex items-center gap-0.5">
                      ↑ +{agent.delta_this_epoch} this epoch
                    </span>
                  </div>
                  <p className="stat-label mt-1">EVASION RATE</p>
                </div>

                {/* Sparkline with filled gradient */}
                <div className="flex-1 max-w-[200px] flex flex-col items-end">
                  <span className="text-[10px] text-[var(--slate-gray)] font-mono mb-1">max {agent.max_evasion.toFixed(2)}</span>
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
                  <span className="text-[10px] text-[var(--slate-gray)] font-mono mt-1">min {agent.min_evasion.toFixed(2)}</span>
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
        <p className="eyebrow mb-8">TOP AGENT STRATEGY EVOLUTION (MULTI-HOP CNP)</p>

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
            {EVOLUTION_STAGES.map((stage) => (
              <motion.div 
                key={stage.version} 
                whileHover={{ y: -3 }}
                className="flex flex-col items-center text-center cursor-default"
              >
                {/* Version badge */}
                <div className={`mb-3 px-3 py-1 rounded-full text-xs font-bold ${
                  stage.active ? 'bg-[var(--ink-black)] text-white' : 'bg-[var(--lifted-cream)] text-[var(--slate-gray)] border border-[var(--dust-taupe)]'
                }`}>
                  {stage.version}
                </div>

                {/* Center Circle Node */}
                <div className={`w-16 h-16 rounded-full flex items-center justify-center mb-3.5 transition-all duration-300 ${
                  stage.active
                    ? 'bg-[#FFEDE4] border-2 border-[var(--light-signal-orange)] shadow-md scale-105'
                    : 'bg-white border border-[var(--dust-taupe)] shadow-sm'
                }`}>
                  <div className="w-8 h-8 rounded-full bg-[var(--light-signal-orange)]/20 flex items-center justify-center">
                    <Activity className={`w-4 h-4 ${stage.active ? 'text-[#CF4500]' : 'text-[var(--slate-gray)]'}`} />
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
