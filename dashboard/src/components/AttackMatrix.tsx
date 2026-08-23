'use client';

import { useState, useMemo } from 'react';
import { ChevronDown } from 'lucide-react';

const ATTACK_ROWS = [
  'Synthetic Identity',
  'Multi-Hop CNP',
  'Prompt Injection',
  'Voice Deepfake',
  'Merchant API Abuse',
  'Velocity Evasion',
];

const CHANNEL_COLS = ['Ecommerce', 'POS', 'Mobile Wallet', 'CNP', 'P2P'];

const HEATMAP_DATA = [
  [0.23, 0.12, 0.45, 0.91, 0.08],  // Synthetic Identity
  [0.34, 0.18, 0.22, 0.67, 0.15],  // Multi-Hop CNP
  [0.56, 0.23, 0.31, 0.42, 0.19],  // Prompt Injection
  [0.18, 0.12, 0.28, 0.35, 0.09],  // Voice Deepfake
  [0.41, 0.29, 0.38, 0.52, 0.24],  // Merchant API Abuse
  [0.67, 0.34, 0.45, 0.78, 0.31],  // Velocity Evasion
];

function getCellColor(value: number) {
  if (value < 0.2) return { bg: 'bg-[var(--soft-bone)]', text: 'text-[var(--ink-black)]' };
  if (value < 0.5) return { bg: 'bg-[rgba(154,58,10,0.3)]', text: 'text-[var(--ink-black)]' };
  if (value < 0.7) return { bg: 'bg-[rgba(207,69,0,0.5)]', text: 'text-white' };
  return { bg: 'bg-[rgba(207,69,0,0.8)]', text: 'text-white' };
}

function HeatmapCell({ value, isMax }: { value: number; isMax: boolean }) {
  const { bg, text } = getCellColor(value);
  return (
    <div className={`relative ${bg} ${text} rounded-[20px] h-[56px] w-full flex items-center justify-center font-medium text-sm ${isMax ? 'ring-1.5 ring-[var(--ink-black)]' : ''}`}>
      {(value * 100).toFixed(0)}%
      {isMax && (
        <div className="absolute -top-3 -right-3 w-7 h-7 rounded-full bg-white border-2 border-[var(--ink-black)] flex items-center justify-center shadow-level-1">
          <svg className="w-4 h-4 text-[var(--ink-black)] mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" /></svg>
        </div>
      )}
    </div>
  );
}

function Legend() {
  const items = [
    { label: 'LOW', color: 'var(--soft-bone)' },
    { label: 'MED', color: 'rgba(154,58,10,0.12)' },
    { label: 'HIGH', color: 'rgba(207,69,0,0.15)' },
  ];
  return (
    <div className="flex items-center gap-3" aria-label="Heatmap legend">
      {items.map((item, i) => (
        <span key={i} className="flex items-center gap-1.5">
          <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: item.color }} />
          <span className="text-xs font-bold text-[var(--slate-gray)] uppercase">{item.label}</span>
        </span>
      ))}
    </div>
  );
}

export default function AttackMatrix() {
  return (
    <div className="card-stadium p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <p className="eyebrow">THREAT COVERAGE</p>
          <h3 className="mt-1">Attack × Channel Matrix</h3>
        </div>
        <Legend />
      </div>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse" role="table" aria-label="Attack vector success probability by channel">
          <thead>
            <tr>
              <th className="w-48 text-left py-2 px-0" aria-hidden="true"></th>
              {CHANNEL_COLS.map((col, ci) => (
                <th key={ci} className="text-center py-3 px-2 stat-label uppercase tracking-wider">{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {HEATMAP_DATA.map((row, ri) => (
              <tr key={ri}>
                <td className="text-left py-3 px-0 font-medium text-[var(--ink-black)] text-sm pr-6 w-48">{ATTACK_ROWS[ri]}</td>
                {row.map((value, ci) => {
                  const isMax = value === 0.91 && ri === 1 && ci === 3;
                  return (
                    <td key={ci} className="relative">
                      <HeatmapCell value={value} isMax={isMax} />
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="caption mt-4">Probability of attack success per vector-channel pair, updated live during simulation.</p>
    </div>
  );
}