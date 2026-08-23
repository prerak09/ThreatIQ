'use client';

import { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { ChevronDown, ChevronUp, Download, FileText, AlertTriangle, Shield, TrendingUp, Target } from 'lucide-react';

const SHAP_DATA = [
  { name: 'behavioral_score', value: 0.35, direction: 'positive' },
  { name: 'velocity_1h', value: 0.28, direction: 'positive' },
  { name: 'geo_distance_km', value: 0.22, direction: 'positive' },
  { name: 'device_fingerprint_entropy', value: 0.18, direction: 'positive' },
  { name: 'amount_log', value: 0.15, direction: 'positive' },
  { name: 'time_since_last_txn', value: -0.12, direction: 'negative' },
  { name: 'ip_reputation_score', value: 0.11, direction: 'positive' },
];

const RISK_FACTORS = [
  { category: 'Behavioral', factor: 'Abnormally low biometric consistency', level: 'HIGH' as const },
  { category: 'Velocity', factor: 'Exceeds 99th percentile transaction frequency', level: 'HIGH' as const },
  { category: 'Geographic', factor: 'Cross-continental transaction within 2 hours', level: 'MEDIUM' as const },
];

function RiskChip({ level }: { level: 'HIGH' | 'MEDIUM' | 'LOW' }) {
  const configs = {
    HIGH: { className: 'status-chip danger' },
    MEDIUM: { className: 'status-chip warning' },
    LOW: { className: 'status-chip success' },
  };
  const config = configs[level];
  return <span className={config.className}>{level}</span>;
}

export default function ExplainabilityPanel() {
  return (
    <div className="section-padding">
      <div className="mb-8">
        <p className="eyebrow">MODEL TRANSPARENCY</p>
        <h2 className="mt-1">Why Was This Flagged?</h2>
        <p className="subline mt-2">Transaction TXN-DEMO-001 · SHAP attribution with conformal confidence</p>
      </div>

      <div className="grid-2 gap-8 mb-12">
        {/* Left Card - Feature Attribution */}
        <div className="card-stadium p-8 relative overflow-hidden">
          <div className="ghost-watermark" style={{ bottom: '-20%', right: '-10%', fontSize: '96px' }}>WHY</div>
          
          <div className="relative z-10">
            <div className="mb-6 flex items-center gap-3">
              <span className="status-chip danger">DECLINE</span>
              <span className="stat-value text-[var(--danger-red)]">94% confidence</span>
            </div>

            <div className="h-[320px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={SHAP_DATA} layout="vertical" margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--dust-taupe)" vertical={false} horizontal={false} />
                  <XAxis 
                    type="number" 
                    domain={[-0.4, 0.4]} 
                    tickLine={false} 
                    axisLine={false} 
                    tick={{ fill: 'var(--slate-gray)', fontSize: 11 }}
                    tickFormatter={(v) => v > 0 ? `+${v.toFixed(2)}` : v.toFixed(2)}
                  />
                  <YAxis 
                    dataKey="name" 
                    type="category" 
                    width={160} 
                    tickLine={false} 
                    axisLine={false} 
                    tick={{ fill: 'var(--ink-black)', fontSize: 12, fontWeight: 450 }}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'var(--lifted-cream)', 
                      border: '1px solid var(--dust-taupe)', 
                      borderRadius: '12px',
                      boxShadow: '0 8px 24px rgba(0,0,0,0.08)'
                    }}
                    labelStyle={{ color: 'var(--ink-black)', fontWeight: 500 }}
                    formatter={(v: number) => [`${v > 0 ? '+' : ''}${v.toFixed(2)}`, 'SHAP Value']}
                  />
                  <Bar 
                    dataKey="value" 
                    radius={[0, 999, 999, 0]} 
                    barSize={18}
                  >
                    {SHAP_DATA.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={entry.direction === 'positive' ? 'var(--light-signal-orange)' : 'var(--link-blue)'} 
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <p className="caption mt-4 text-center">Red = increases fraud score · Blue = decreases</p>

            {/* Orange arc connecting verdict to chart */}
            <div className="absolute left-8 top-20 bottom-20 w-1.5 bg-gradient-to-b from-[var(--light-signal-orange)] to-transparent pointer-events-none" />
          </div>
        </div>

        {/* Right Card - Risk Narrative */}
        <div className="card-stadium p-8">
          <p className="eyebrow mb-6">RISK FACTORS</p>
          <div className="space-y-4 mb-8">
            {RISK_FACTORS.map((rf, i) => (
              <div key={i} className="flex items-start gap-3 p-4 bg-[var(--lifted-cream)] rounded-[20px]">
                <span className="pill-btn inactive text-xs capitalize mt-0.5">{rf.category.toLowerCase()}</span>
                <span className="text-[var(--ink-black)] text-sm flex-1">{rf.factor}</span>
                <div className="flex items-center gap-2">
                  <RiskChip level={rf.level} />
                </div>
              </div>
            ))}
          </div>

          {/* Conformal Gauge */}
          <div className="relative w-32 h-32 mx-auto mb-6">
            <svg viewBox="0 0 100 100" className="w-full h-full">
              <circle 
                cx="50" cy="50" r="40" 
                stroke="#E8E2DA" strokeWidth="8" fill="none" 
              />
              <circle 
                cx="50" cy="50" r="40" 
                stroke="var(--link-blue)" 
                strokeWidth="8" 
                fill="none" 
                strokeDasharray={`${0.912 * 251.2} 251.2`}
                strokeLinecap="round"
                transform="rotate(-90 50 50)"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="stat-value text-[var(--link-blue)]">91%</span>
              <span className="caption text-center">Coverage</span>
            </div>
          </div>
          <p className="caption text-center">Conformal guarantee 91.2%</p>

          {/* Narrative */}
          <div className="bg-[var(--soft-bone)] rounded-[20px] p-6 mb-6">
            <p className="text-[var(--ink-black)] text-sm leading-relaxed">
              This transaction exhibits strong indicators of automated fraud. The behavioral biometrics score of 0.12 is significantly below the legitimate baseline (mean: 0.82). Combined with 47 transactions in the last hour and a 4,200km geographic displacement, this is classified as a multi-hop CNP relay attack.
            </p>
          </div>

          {/* Actions */}
          <div className="flex flex-wrap gap-3">
            <button className="btn-primary">
              <FileText className="w-4 h-4" /> Generate SAR
            </button>
            <button className="btn-secondary">
              <Target className="w-4 h-4" /> Counterfactual: what would change this?
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}