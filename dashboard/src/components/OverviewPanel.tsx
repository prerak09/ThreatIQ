'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { 
  ShieldCheck, 
  ShieldAlert, 
  Bot, 
  Activity, 
  TrendingUp, 
  Zap, 
  Network, 
  Key, 
  Share2, 
  FileText, 
  Layers, 
  CheckCircle2, 
  ArrowUpRight,
  Sparkles,
  Server
} from 'lucide-react';
import { ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';
import { TabId } from './ArenaDashboard';
import { Transaction } from '@/lib/api';

interface OverviewPanelProps {
  onSelectTab: (tab: TabId) => void;
  isRunning: boolean;
  isConnected: boolean;
  totalProcessed: number;
  totalAttacks: number;
  detectedCount: number;
  detectionRate: number;
  roiAmount: number;
  transactions: Transaction[];
  onStartSimulation: () => void;
  onStopSimulation: () => void;
}

const ATTACK_DISTRIBUTION = [
  { name: 'Multi-Hop CNP', value: 38, color: '#F37338' },
  { name: 'Synthetic Identity', value: 27, color: '#EB001B' },
  { name: 'Prompt Injection', value: 18, color: '#6366F1' },
  { name: 'Voice Deepfake', value: 12, color: '#3860BE' },
  { name: 'Credential Stuffing', value: 5, color: '#10B981' },
];

const ENSEMBLE_ENGINES = [
  { name: 'XGBoost GBDT', role: 'Feature Scoring', accuracy: '98.2%', latency: '2.4ms', status: 'ONLINE', color: 'text-[var(--link-blue)]' },
  { name: 'LightGBM Ensemble', role: 'Gradient Boosting', accuracy: '97.9%', latency: '2.1ms', status: 'ONLINE', color: 'text-[var(--link-blue)]' },
  { name: 'Isolation Forest', role: 'Unsupervised Outlier', accuracy: '94.6%', latency: '1.8ms', status: 'ONLINE', color: 'text-[var(--light-signal-orange)]' },
  { name: 'Temporal Graph Neural Net', role: 'Ring & Flow Detection', accuracy: '99.1%', latency: '5.5ms', status: 'ONLINE', color: 'text-[var(--success-green)]' },
];

export default function OverviewPanel({
  onSelectTab,
  isRunning,
  isConnected,
  totalProcessed,
  totalAttacks,
  detectedCount,
  detectionRate,
  roiAmount,
  transactions,
  onStartSimulation,
  onStopSimulation,
}: OverviewPanelProps) {
  const legitimateCount = Math.max(0, totalProcessed - totalAttacks);
  const legitimateRatio = totalProcessed > 0 ? ((legitimateCount / totalProcessed) * 100).toFixed(1) : '82.0';
  const fraudRatio = totalProcessed > 0 ? ((totalAttacks / totalProcessed) * 100).toFixed(1) : '18.0';

  return (
    <div className="section-padding relative">
      {/* Ghost Watermark */}
      <div className="ghost-watermark top-10 right-4 text-[140px] pointer-events-none select-none opacity-60">PULSE</div>

      {/* Overview Executive Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6 mb-10 relative z-10">
        <div>
          <p className="eyebrow">EXECUTIVE INTELLIGENCE DASHBOARD</p>
          <h2 className="mt-2 text-3xl sm:text-4xl">Platform Operations Overview</h2>
          <p className="subline mt-1.5 text-base">
            Holistic situational awareness across AI red team mutations, defense ensembles, and regulatory compliance
          </p>
        </div>

        {/* Quick Launch Action Bar */}
        <div className="flex items-center gap-3 flex-wrap">
          <motion.button
            whileHover={{ scale: 1.04 }}
            whileTap={{ scale: 0.96 }}
            onClick={() => onSelectTab('arena')}
            className="btn-primary flex items-center gap-2 px-5 py-2.5 text-sm shadow-sm"
          >
            <Zap className="w-4 h-4 text-[var(--light-signal-orange)]" />
            <span>Launch Attack in Arena</span>
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.04 }}
            whileTap={{ scale: 0.96 }}
            onClick={() => onSelectTab('topology')}
            className="btn-secondary flex items-center gap-2 px-5 py-2.5 text-sm"
          >
            <Network className="w-4 h-4 text-[var(--ink-black)]" />
            <span>Inspect Graph Topology</span>
          </motion.button>
        </div>
      </div>

      {/* Top 3 High-Impact Macro Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-7 mb-10 relative z-10">
        
        {/* Card 1: Traffic Composition & Volume */}
        <motion.div 
          whileHover={{ y: -3 }}
          className="card-stadium p-7 border border-[rgba(20,20,19,0.04)] shadow-level-1 flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="eyebrow">NETWORK TRAFFIC SPLIT</span>
              <span className="status-chip success text-[11px]">82/18 RATIO</span>
            </div>
            <h3 className="text-xl font-medium mb-2">Live Payment Volume</h3>
            <p className="caption text-xs mb-6">Real-time ISO 20022 clearing stream throughput</p>

            {/* Split Progress Bar */}
            <div className="w-full bg-gray-100 rounded-full h-3.5 mb-3 flex overflow-hidden p-0.5">
              <div 
                style={{ width: `${legitimateRatio}%` }} 
                className="bg-[var(--success-green)] h-full rounded-full transition-all duration-500" 
                title={`Legitimate: ${legitimateRatio}%`}
              />
              <div 
                style={{ width: `${fraudRatio}%` }} 
                className="bg-[var(--danger-red)] h-full rounded-full transition-all duration-500 ml-1" 
                title={`Fraud Attacks: ${fraudRatio}%`}
              />
            </div>

            <div className="flex justify-between text-xs font-semibold font-mono">
              <span className="text-[var(--success-green)] flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[var(--success-green)]" />
                {legitimateCount.toLocaleString()} Legitimate ({legitimateRatio}%)
              </span>
              <span className="text-[var(--danger-red)] flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-[var(--danger-red)]" />
                {totalAttacks.toLocaleString()} Fraud ({fraudRatio}%)
              </span>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-[var(--dust-taupe)]/40 flex justify-between items-center text-xs">
            <span className="text-[var(--slate-gray)]">Total Stream Volume:</span>
            <span className="font-bold text-sm text-[var(--ink-black)]">{totalProcessed.toLocaleString()} txns</span>
          </div>
        </motion.div>

        {/* Card 2: AI Defense Posture & Catch Rate */}
        <motion.div 
          whileHover={{ y: -3 }}
          className="card-stadium p-7 border border-[rgba(20,20,19,0.04)] shadow-level-1 flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="eyebrow">DEFENSE EFFICACY</span>
              <span className="status-chip success text-[11px]">ACTIVE ENSEMBLE</span>
            </div>
            <h3 className="text-xl font-medium mb-2">Block Accuracy</h3>
            <p className="caption text-xs mb-4">Percentage of malicious vectors intercepted</p>

            <div className="flex items-baseline gap-3 mb-4">
              <span className="text-5xl font-bold text-[var(--link-blue)] tracking-tight">
                {totalAttacks > 0 ? `${detectionRate}%` : '96.4%'}
              </span>
              <span className="text-xs font-semibold text-[var(--success-green)]">
                ↑ {detectedCount} of {totalAttacks || 1} caught
              </span>
            </div>

            <div className="p-3.5 bg-[var(--lifted-cream)] rounded-2xl border border-[var(--dust-taupe)]/30 text-xs flex justify-between">
              <span className="text-[var(--slate-gray)]">Average Decision Latency:</span>
              <span className="font-bold text-[var(--ink-black)] font-mono">11.8 ms</span>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-[var(--dust-taupe)]/40 flex justify-between items-center text-xs">
            <span className="text-[var(--slate-gray)]">Estimated ROI Prevented:</span>
            <span className="font-bold text-sm text-[var(--success-green)] font-mono">${roiAmount.toLocaleString()}</span>
          </div>
        </motion.div>

        {/* Card 3: Attack Vector Composition Donut */}
        <motion.div 
          whileHover={{ y: -3 }}
          className="card-stadium p-7 border border-[rgba(20,20,19,0.04)] shadow-level-1 flex flex-col justify-between"
        >
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="eyebrow">ATTACK VECTOR MIX</span>
              <span className="status-chip warning text-[11px]">5 VECTORS</span>
            </div>
            <h3 className="text-xl font-medium mb-1">Threat Distribution</h3>
            <p className="caption text-xs mb-3">Live adversarial generation mix</p>

            <div className="h-28 w-full flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={ATTACK_DISTRIBUTION}
                    cx="50%"
                    cy="50%"
                    innerRadius={30}
                    outerRadius={48}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {ATTACK_DISTRIBUTION.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v: any) => [`${v}%`, 'Share']} />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="grid grid-cols-2 gap-2 text-[11px] font-medium mt-2">
              <div className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-[#F37338]" /> Multi-Hop CNP (38%)</div>
              <div className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-[#EB001B]" /> Synthetic ID (27%)</div>
              <div className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-[#6366F1]" /> Prompt Injection (18%)</div>
              <div className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-[#3860BE]" /> Voice Deepfake (12%)</div>
            </div>
          </div>
        </motion.div>

      </div>

      {/* Middle Row: AI Defense Ensemble Engine Table + Interactive Subsystem Tiles */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-10 relative z-10">
        
        {/* Left 2 Cols: AI Defense Models Status */}
        <div className="lg:col-span-2 card-stadium p-8 border border-[rgba(20,20,19,0.04)] shadow-level-1">
          <div className="flex items-center justify-between mb-6 pb-4 border-b border-[var(--dust-taupe)]/40">
            <div>
              <p className="eyebrow">BLUE TEAM ARCHITECTURE</p>
              <h3 className="text-xl font-medium mt-1">Multi-Model Defense Ensemble</h3>
            </div>
            <button onClick={() => onSelectTab('xai')} className="text-xs font-semibold text-[var(--link-blue)] hover:underline flex items-center gap-1">
              Explain Models (SHAP) <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-3.5">
            {ENSEMBLE_ENGINES.map((eng) => (
              <div
                key={eng.name}
                className="p-4 bg-[var(--lifted-cream)] rounded-2xl border border-[var(--dust-taupe)]/30 flex items-center justify-between gap-4"
              >
                <div className="flex items-center gap-3.5">
                  <div className="w-9 h-9 rounded-full bg-white border border-[var(--dust-taupe)] flex items-center justify-center">
                    <Server className="w-4 h-4 text-[var(--ink-black)]" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-sm text-[var(--ink-black)]">{eng.name}</h4>
                    <p className="caption text-xs">{eng.role}</p>
                  </div>
                </div>

                <div className="flex items-center gap-6 text-xs">
                  <div className="text-right">
                    <span className="stat-label">Accuracy</span>
                    <p className={`font-bold ${eng.color}`}>{eng.accuracy}</p>
                  </div>
                  <div className="text-right">
                    <span className="stat-label">Latency</span>
                    <p className="font-mono text-[var(--slate-gray)]">{eng.latency}</p>
                  </div>
                  <span className="status-chip success text-[10px]">
                    {eng.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Col: Subsystem Shortcuts & Status */}
        <div className="card-stadium p-8 border border-[rgba(20,20,19,0.04)] shadow-level-1 flex flex-col justify-between">
          <div>
            <p className="eyebrow mb-4">PLATFORM MODULES</p>
            
            <div className="space-y-3">
              <button
                onClick={() => onSelectTab('marl')}
                className="w-full p-3.5 bg-[var(--lifted-cream)] hover:bg-white transition-all rounded-2xl border border-[var(--dust-taupe)]/30 flex items-center justify-between text-left group"
              >
                <div className="flex items-center gap-3">
                  <Bot className="w-5 h-5 text-[var(--light-signal-orange)]" />
                  <div>
                    <p className="font-semibold text-xs text-[var(--ink-black)]">MARL Adversaries</p>
                    <p className="caption text-[11px]">Epoch #42 · 4 Bots Evolving</p>
                  </div>
                </div>
                <ArrowUpRight className="w-4 h-4 text-[var(--slate-gray)] group-hover:text-black transition-colors" />
              </button>

              <button
                onClick={() => onSelectTab('federated')}
                className="w-full p-3.5 bg-[var(--lifted-cream)] hover:bg-white transition-all rounded-2xl border border-[var(--dust-taupe)]/30 flex items-center justify-between text-left group"
              >
                <div className="flex items-center gap-3">
                  <Share2 className="w-5 h-5 text-[var(--link-blue)]" />
                  <div>
                    <p className="font-semibold text-xs text-[var(--ink-black)]">Federated Intelligence</p>
                    <p className="caption text-[11px]">10 Bank Nodes · DP ε=9.5</p>
                  </div>
                </div>
                <ArrowUpRight className="w-4 h-4 text-[var(--slate-gray)] group-hover:text-black transition-colors" />
              </button>

              <button
                onClick={() => onSelectTab('zkp')}
                className="w-full p-3.5 bg-[var(--lifted-cream)] hover:bg-white transition-all rounded-2xl border border-[var(--dust-taupe)]/30 flex items-center justify-between text-left group"
              >
                <div className="flex items-center gap-3">
                  <Key className="w-5 h-5 text-[var(--success-green)]" />
                  <div>
                    <p className="font-semibold text-xs text-[var(--ink-black)]">ZKP Verification</p>
                    <p className="caption text-[11px]">Groth16 BN254 · 192B Proofs</p>
                  </div>
                </div>
                <ArrowUpRight className="w-4 h-4 text-[var(--slate-gray)] group-hover:text-black transition-colors" />
              </button>

              <button
                onClick={() => onSelectTab('sar')}
                className="w-full p-3.5 bg-[var(--lifted-cream)] hover:bg-white transition-all rounded-2xl border border-[var(--dust-taupe)]/30 flex items-center justify-between text-left group"
              >
                <div className="flex items-center gap-3">
                  <FileText className="w-5 h-5 text-[#8B5CF6]" />
                  <div>
                    <p className="font-semibold text-xs text-[var(--ink-black)]">FinCEN SAR Queue</p>
                    <p className="caption text-[11px]">Automated Form 111 AML</p>
                  </div>
                </div>
                <ArrowUpRight className="w-4 h-4 text-[var(--slate-gray)] group-hover:text-black transition-colors" />
              </button>
            </div>
          </div>

          <p className="caption text-center mt-6">
            ISO 20022 pacs.008 · Dual-Engine Real-Time ML Screening Rail
          </p>
        </div>

      </div>

      {/* Bottom Live Transaction Activity Feed Strip */}
      <div className="card-stadium p-8 border border-[rgba(20,20,19,0.04)] shadow-level-1">
        <div className="flex items-center justify-between mb-4">
          <p className="eyebrow">RECENT NETWORK ACTIVITY ({transactions.length} RECENT)</p>
          <button onClick={() => onSelectTab('arena')} className="text-xs font-semibold text-[var(--link-blue)] hover:underline">
            View Live Stream in Arena →
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3.5">
          {transactions.slice(0, 8).map((tx) => {
            const isAttack = tx.is_fraud || tx.status === 'detected' || tx.status === 'blocked';
            return (
              <div 
                key={tx.id}
                onClick={() => onSelectTab('arena')}
                className="p-3.5 bg-[var(--lifted-cream)] rounded-2xl border border-[var(--dust-taupe)]/30 cursor-pointer hover:bg-white transition-all"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-xs text-[var(--ink-black)]">{tx.id}</span>
                  <span className={`status-chip text-[9px] ${isAttack ? 'danger' : 'success'}`}>
                    {isAttack ? 'BLOCKED' : 'APPROVED'}
                  </span>
                </div>
                <p className="caption text-[11px] truncate">
                  {tx.attack_type || (isAttack ? 'Fraud Vector' : 'Normal Payment')} · {tx.currency || 'USD'} {tx.amount?.toFixed(0)}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
