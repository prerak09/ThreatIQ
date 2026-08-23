'use client';

import { useState, useEffect } from 'react';
import { CheckCircle, AlertCircle, Zap, BarChart2, Download, RotateCcw } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const CONSTRAINTS = [
  { id: 'AmountRange', name: 'Amount Range', type: 'Range', spec: '1.00 – 10,000.00', satisfied: true, rate: 99.8 },
  { id: 'IBANChecksum', name: 'IBAN Checksum', type: 'Mod-97', spec: 'ISO 13616', satisfied: true, rate: 100.0 },
  { id: 'CurrencyCode', name: 'Currency Code', type: 'ISO 4217', spec: '50 valid codes', satisfied: true, rate: 100.0 },
  { id: 'TimeSequence', name: 'Time Sequence', type: 'Monotonic', spec: 'Strictly increasing', satisfied: false, rate: 98.2 },
  { id: 'CreditLimit', name: 'Credit Limit', type: 'Cap', spec: 'Per-card limit', satisfied: false, rate: 98.5 },
  { id: 'MerchantCategory', name: 'Merchant Category', type: 'MCC', spec: '10 valid MCCs', satisfied: true, rate: 100.0 },
];

const VIOLATIONS = [
  { type: 'Credit Limit', count: 12, color: 'rgba(179,38,30,0.6)' },
  { type: 'Time Sequence', count: 7, color: 'rgba(154,58,10,0.6)' },
  { type: 'Amount Range', count: 3, color: 'rgba(207,69,0,0.4)' },
];

export default function ConstraintPanel() {
  const [satisfactionRate, setSatisfactionRate] = useState(99.6);

  useEffect(() => {
    const interval = setInterval(() => {
      setSatisfactionRate(prev => Math.max(95, Math.min(100, prev + (Math.random() - 0.5) * 0.2)));
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="section-padding">
      <div className="mb-8">
        <p className="eyebrow">SYNTHETIC DATA INTEGRITY</p>
        <h2 className="mt-1">Constraint Compliance</h2>
        <p className="subline mt-2">Six hard invariants validated on every generated transaction batch</p>
      </div>

      <div className="grid-2 gap-8 mb-8">
        {/* Card 1: Overall Gauge */}
        <div className="card-stadium p-8 relative">
          <div className="relative w-48 h-48 mx-auto mb-6">
            <svg viewBox="0 0 100 100" className="w-full h-full">
              <circle cx="50" cy="50" r="40" stroke="#E8E2DA" strokeWidth="8" fill="none" />
              <circle 
                cx="50" cy="50" r="40" 
                stroke="#2E7D32" 
                strokeWidth="8" 
                fill="none" 
                strokeDasharray={`${satisfactionRate / 100 * 251.2} 251.2`}
                strokeLinecap="round"
                transform="rotate(-90 50 50)"
                className="transition-all duration-500"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="stat-value-xxl">{satisfactionRate.toFixed(1)}%</span>
              <p className="stat-label">SATISFACTION RATE</p>
            </div>
          </div>
          <div className="flex flex-col sm:flex-row gap-3">
            <button className="btn-secondary flex-1">
              <Zap className="w-4 h-4" /> Generate Constrained Batch
            </button>
            <button className="btn-primary flex-1">
              <BarChart2 className="w-4 h-4" /> Validate Samples
            </button>
          </div>
        </div>

        {/* Card 2: Constraint List */}
        <div className="card-stadium p-8">
          <div className="space-y-3">
            {CONSTRAINTS.map((constraint) => (
              <div key={constraint.id} className="card-white-pill p-4 flex items-center gap-4">
                <div className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
                  style={{ backgroundColor: constraint.satisfied ? 'rgba(46,125,50,0.1)' : 'rgba(154,58,10,0.1)' }}>
                  {constraint.satisfied ? (
                    <CheckCircle className="w-5 h-5 text-[var(--success-green)]" />
                  ) : (
                    <AlertCircle className="w-5 h-5 text-[var(--warning-clay)]" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-[var(--ink-black)]">{constraint.name}</p>
                  <p className="text-[var(--slate-gray)] text-xs mt-0.5">{constraint.spec}</p>
                </div>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <span className={`font-mono text-sm font-medium ${constraint.satisfied ? 'text-[var(--success-green)]' : 'text-[var(--warning-clay)]'}`}>
                    {constraint.rate.toFixed(1)}%
                  </span>
                  <span className="px-2 py-0.5 rounded-full border border-[var(--dust-taupe)] text-[var(--slate-gray)] text-xs uppercase">{constraint.type}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Card 3: Violations Breakdown */}
      <div className="card-stadium p-8">
        <p className="eyebrow mb-6">VIOLATIONS BY TYPE</p>
        <div className="space-y-4 mb-6">
          {VIOLATIONS.map((v, i) => (
            <div key={i} className="flex items-center gap-4">
              <div className="flex-1">
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-[var(--ink-black)] font-medium">{v.type}</span>
                  <span className="font-medium text-[var(--ink-black)]">{v.count}</span>
                </div>
                <div className="h-3.5 bg-[var(--soft-bone)] rounded-full overflow-hidden">
                  <div 
                    className="h-full rounded-full transition-all duration-500" 
                    style={{ backgroundColor: v.color, width: `${v.count / 12 * 100}%` }}
                  />
                </div>
              </div>
            </div>
          ))}
          
          <div className="card-white-pill p-3 flex items-center gap-3">
            <div className="w-6 h-6 rounded-full bg-[var(--success-tint)] flex items-center justify-center">
              <CheckCircle className="w-4 h-4 text-[var(--success-green)]" />
            </div>
            <span className="text-[var(--ink-black)] font-medium text-sm">BENFORD COMPLIANT · χ² = 2.41</span>
          </div>
        </div>
      </div>
    </div>
  );
}