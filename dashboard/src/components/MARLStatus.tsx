'use client';

import { useState } from 'react';
import { TrendingUp, Target, ExternalLink, Clock, BarChart2 } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const AGENTS = [
  { 
    id: 'synthetic-identity', 
    name: 'Synthetic Identity', 
    evasion: 0.42, 
    episodes: 1247, 
    strategy: 'Gradual credit building with distributed KYC', 
    history: [0.30, 0.35, 0.42, 0.38, 0.45, 0.42, 0.44, 0.41, 0.43, 0.42],
    rank: 2 
  },
  { 
    id: 'multi-hop-cnp', 
    name: 'Multi-Hop CNP', 
    evasion: 0.51, 
    episodes: 2103, 
    strategy: 'Geo-consistent proxy rotation with timing jitter', 
    history: [0.40, 0.45, 0.48, 0.52, 0.51, 0.53, 0.50, 0.52, 0.51, 0.51],
    rank: 1 
  },
  { 
    id: 'prompt-injection', 
    name: 'Prompt Injection', 
    evasion: 0.35, 
    episodes: 892, 
    strategy: 'Context-aware payload encoding', 
    history: [0.20, 0.25, 0.30, 0.32, 0.35, 0.33, 0.34, 0.36, 0.35, 0.35],
    rank: 3 
  },
  { 
    id: 'voice-deepfake', 
    name: 'Voice Deepfake', 
    evasion: 0.38, 
    episodes: 654, 
    strategy: 'Emotional context matching with prosody transfer', 
    history: [0.25, 0.30, 0.33, 0.36, 0.38, 0.37, 0.39, 0.38, 0.38, 0.38],
    rank: 4 
  },
];

function Sparkline({ data }: { data: number[] }) {
  return (
    <ResponsiveContainer width="100%" height={60}>
      <LineChart data={data.map((v, i) => ({ i, v }))} margin={{ top: 5, right: 5, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="sparkGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--light-signal-orange)" stopOpacity={0.15} />
            <stop offset="100%" stopColor="var(--light-signal-orange)" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="transparent" />
        <XAxis dataKey="i" stroke="transparent" tickLine={false} axisLine={false} />
        <YAxis domain={[0, 1]} stroke="transparent" tickLine={false} axisLine={false} />
        <Tooltip contentStyle={{ backgroundColor: 'var(--lifted-cream)', border: '1px solid var(--dust-taupe)', borderRadius: '8px' }} formatter={(v: number) => [`${Math.round(v * 100)}%`, 'Evasion']} />
        <Line type="monotone" dataKey="v" stroke="var(--ink-black)" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}

function AgentCard({ agent, rank }: { agent: typeof AGENTS[0]; rank: number }) {
  return (
    <div className="card-stadium p-7 relative">
      <div className="flex items-start gap-4 mb-5">
        <div className="w-12 h-12 rounded-full bg-[var(--danger-tint)] flex items-center justify-center flex-shrink-0">
          <BarChart2 className="w-6 h-6 text-[var(--danger-red)]" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h4 className="text-[var(--ink-black)] font-medium text-lg">{agent.name}</h4>
            <span className="pill-btn active text-xs">#{rank}</span>
          </div>
          <div className="flex items-center gap-2 text-[var(--slate-gray)] text-sm">
            <span>{agent.episodes.toLocaleString()} episodes</span>
          </div>
        </div>
        <div className="text-right">
          <p className="stat-value text-[var(--danger-red)]">{Math.round(agent.evasion * 100)}%</p>
          <p className="stat-label">Evasion Rate</p>
        </div>
      </div>

      <div className="mb-5">
        <Sparkline data={agent.history} />
        <div className="flex justify-between text-[var(--dust-taupe)] text-xs mt-1">
          <span>Min</span>
          <span>Max</span>
        </div>
      </div>

      <div className="bg-[var(--soft-bone)] rounded-[20px] p-4 mb-5">
        <p className="text-[var(--slate-gray)] text-sm italic leading-relaxed">"{agent.strategy}"</p>
      </div>

      <div className="flex items-center justify-between">
        <span className="text-[var(--slate-gray)] text-sm">{agent.episodes.toLocaleString()} episodes</span>
        <button className="pill-btn inactive text-xs">
          <ExternalLink className="w-3 h-3" /> View policy
        </button>
      </div>
    </div>
  );
}

function StrategyTimeline() {
  const versions = ['v1', 'v2', 'v3', 'v4', 'v5'];
  return (
    <div className="card-stadium p-6 mt-8">
      <p className="eyebrow mb-4">STRATEGY EVOLUTION</p>
      <div className="flex items-center gap-4 overflow-x-auto pb-4">
        {versions.map((v, i) => (
          <div key={v} className="flex flex-col items-center flex-shrink-0">
            <div className={`w-16 h-16 rounded-full border-3 flex items-center justify-center bg-white ${i === versions.length - 1 ? 'border-[var(--ink-black)]' : 'border-[var(--dust-taupe)]'} relative`}>
              <span className="text-[var(--ink-black)] font-medium text-sm">{v}</span>
              {i < versions.length - 1 && (
                <div className="absolute top-1/2 right-[-14px] w-12 h-1.5 bg-gradient-to-r from-transparent to-[var(--light-signal-orange)]" />
              )}
            </div>
            <span className="text-[var(--slate-gray)] text-xs mt-2">{i === versions.length - 1 ? 'Current' : `Gen ${i + 1}`}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function MARLStatus() {
  return (
    <div className="section-padding">
      <div className="mb-8">
        <p className="eyebrow">AUTONOMOUS ADVERSARIES</p>
        <h2 className="mt-1">MARL Agent Monitor</h2>
        <p className="subline mt-2">Multi-agent reinforcement learning attack strategies, live evolution</p>
      </div>

      <div className="grid-2 gap-6 mb-8">
        {AGENTS.map((agent, i) => (
          <AgentCard key={agent.id} agent={agent} rank={i + 1} />
        ))}
      </div>

      <StrategyTimeline />
    </div>
  );
}