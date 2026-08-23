'use client';

import { useState, useEffect } from 'react';
import { Shield, TrendingUp, BarChart2, Target, Circle, Dot } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, Legend } from 'recharts';

const BANKS = [
  { id: 'bank-001', name: 'Alpha National Bank', samples: 12500, accuracy: 0.9312, latency: 42.3, training: true },
  { id: 'bank-002', name: 'Meridian Financial', samples: 9800, accuracy: 0.9187, latency: 38.1, training: false },
  { id: 'bank-003', name: 'Pacific Coast CU', samples: 7200, accuracy: 0.9054, latency: 55.8, training: true },
  { id: 'bank-004', name: 'Heartland Bank Corp', samples: 11000, accuracy: 0.9276, latency: 41.5, training: false },
  { id: 'bank-005', name: 'Summit Digital Bank', samples: 8400, accuracy: 0.9103, latency: 47.2, training: false },
  { id: 'bank-006', name: 'Metro Payments Inc', samples: 6100, accuracy: 0.8989, latency: 62.4, training: false },
  { id: 'bank-007', name: 'Valley Trust Co', samples: 5400, accuracy: 0.8892, latency: 58.7, training: false },
  { id: 'bank-008', name: 'Horizon Commerce', samples: 4800, accuracy: 0.8821, latency: 65.3, training: false },
  { id: 'bank-009', name: 'Apex Savings Bank', samples: 4200, accuracy: 0.8765, latency: 71.2, training: false },
  { id: 'bank-010', name: 'Sterling Federal', samples: 3800, accuracy: 0.8698, latency: 78.4, training: false },
];

const DP_DATA = [
  { round: 1, no_dp: 0.75, dp: 0.70 },
  { round: 2, no_dp: 0.78, dp: 0.72 },
  { round: 3, no_dp: 0.81, dp: 0.74 },
  { round: 4, no_dp: 0.83, dp: 0.76 },
  { round: 5, no_dp: 0.85, dp: 0.78 },
  { round: 6, no_dp: 0.87, dp: 0.80 },
  { round: 7, no_dp: 0.88, dp: 0.81 },
  { round: 8, no_dp: 0.90, dp: 0.82 },
  { round: 9, no_dp: 0.91, dp: 0.83 },
  { round: 10, no_dp: 0.92, dp: 0.84 },
  { round: 11, no_dp: 0.93, dp: 0.85 },
  { round: 12, no_dp: 0.93, dp: 0.86 },
  { round: 13, no_dp: 0.94, dp: 0.87 },
  { round: 14, no_dp: 0.94, dp: 0.88 },
  { round: 15, no_dp: 0.95, dp: 0.88 },
];

export default function FederatedLearningPanel() {
  const [epsilonUsed, setEpsilonUsed] = useState(6.75);
  const [currentRound, setCurrentRound] = useState(12);
  const [globalAccuracy, setGlobalAccuracy] = useState(0.9234);
  const [isTraining, setIsTraining] = useState(false);
  const [bankStatuses, setBankStatuses] = useState(BANKS.map(b => ({ ...b, training: false })));

  useEffect(() => {
    const interval = setInterval(() => {
      setEpsilonUsed((prev) => Math.min(10, prev + 0.01));
      setGlobalAccuracy((prev) => Math.min(0.95, prev + Math.random() * 0.001));
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleRunRound = () => {
    setIsTraining(true);
    setCurrentRound((c) => c + 1);
    setGlobalAccuracy((c) => Math.min(0.95, c + 0.005));
    setEpsilonUsed((c) => c + 0.25);
    
    // Simulate training
    const trainingBanks = BANKS.slice(0, 4).map((b) => b.id);
    setBankStatuses((prev) => prev.map((b) => ({ ...b, training: trainingBanks.includes(b.id) })));
    
    setTimeout(() => {
      setIsTraining(false);
      setBankStatuses((prev) => prev.map((b) => ({ ...b, training: false })));
    }, 3000);
  };

  return (
    <div className="section-padding">
      <div className="mb-8">
        <p className="eyebrow">PRIVACY-PRESERVING TRAINING</p>
        <h2 className="mt-1">Federated Intelligence</h2>
        <p className="subline mt-2">FedAvg across 10 institutions · DP-SGD noise ε=1.0, δ=1e-5</p>
      </div>

      <div className="grid-2 gap-8 mb-8">
        {/* Card 1: Privacy Budget */}
        <div className="card-stadium p-8 relative">
          <div className="relative w-48 h-48 mx-auto mb-6">
            <svg viewBox="0 0 100 100" className="w-full h-full">
              <circle cx="50" cy="50" r="40" stroke="#E8E2DA" strokeWidth="12" fill="none" />
              <circle 
                cx="50" cy="50" r="40" 
                stroke="var(--link-blue)" 
                strokeWidth="12" 
                fill="none" 
                strokeDasharray={`${(epsilonUsed / 10) * 251.2} 251.2`}
                strokeLinecap="round"
                transform="rotate(-90 50 50)"
                className="transition-all duration-500"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <p className="stat-value-xl text-[var(--link-blue)]">ε {epsilonUsed.toFixed(1)} / 10.0</p>
              <p className="stat-label">PRIVACY BUDGET</p>
            </div>
          </div>
          <div className="grid-2 gap-4 text-center">
            <div className="p-4 bg-[var(--lifted-cream)] rounded-[20px]">
              <p className="stat-label">Delta</p>
              <p className="stat-value font-mono">1e-5</p>
            </div>
            <div className="p-4 bg-[var(--lifted-cream)] rounded-[20px]">
              <p className="stat-label">Noise Multiplier</p>
              <p className="stat-value font-mono">σ = 1.1</p>
            </div>
            <div className="p-4 bg-[var(--lifted-cream)] rounded-[20px] sm:col-span-2">
              <p className="stat-label">Clipping Norm</p>
              <p className="stat-value font-mono">C = 1.0</p>
            </div>
          </div>
        </div>

        {/* Card 2: Bank Network */}
        <div className="card-stadium p-8 relative">
          <div className="relative h-80 w-full">
            {/* Central coordinator */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
              <div className="w-18 h-18 rounded-full bg-[var(--ink-black)] flex items-center justify-center shadow-level-2 z-10">
                <Shield className="w-8 h-8 text-white" />
              </div>
            </div>
            
            {/* Banks in constellation */}
            {BANKS.map((bank, i) => {
              const angle = (i / BANKS.length) * Math.PI * 2 - Math.PI / 2;
              const radius = 160;
              const x = 50 + Math.cos(angle) * radius / 100;
              const y = 50 + Math.sin(angle) / 100;
              
              return (
                <div 
                  key={bank.id} 
                  className="absolute w-24 transition-all duration-500"
                  style={{ 
                    left: `calc(${x}% - 48px)`, 
                    top: `calc(${y}% - 48px)`,
                    zIndex: bank.training ? 10 : 1
                  }}
                >
                  <div className="relative">
                    <div className={`w-16 h-16 rounded-full bg-white border-2 flex items-center justify-center shadow-level-1 ${bank.training ? 'border-[var(--light-signal-orange)] animate-pulse' : 'border-[var(--dust-taupe)]'}`}>
                      <Circle className="w-8 h-8 text-[var(--ink-black)]" />
                    </div>
                    {bank.training && (
                      <div className="absolute inset-0 rounded-full border-2 border-[var(--light-signal-orange)] animate-ring" />
                    )}
                  </div>
                  <p className="text-center text-[var(--slate-gray)] text-xs mt-1 max-w-[100px]">{bank.name}</p>
                  <span className={`block text-center mt-1 ${bank.accuracy > 0.92 ? 'text-[var(--success-green)]' : 'text-[var(--ink-black)]'} font-medium text-xs`}>
                    {Math.round(bank.accuracy * 100)}%
                  </span>
                </div>
              );
            })}
            
            {/* Connecting arcs - using SVG */}
            <svg className="absolute inset-0 pointer-events-none" style={{ opacity: 0.3 }}>
              {BANKS.map((_, i) => {
                const angle = (i / BANKS.length) * Math.PI * 2 - Math.PI / 2;
                const radius = 160;
                const x = 50 + Math.cos(angle) * radius / 100;
                const y = 50 + Math.sin(angle) / 100;
                return (
                  <line 
                    key={i} 
                    x1="50%" y1="50%" 
                    x2={`${x}%`} y2={`${y}%`} 
                    stroke="var(--light-signal-orange)" 
                    strokeWidth="1" 
                  />
                );
              })}
            </svg>
          </div>
        </div>
      </div>

      {/* Card 3: DP vs No-DP Chart */}
      <div className="card-stadium p-8">
        <p className="eyebrow mb-4">UTILITY TRADE-OFF</p>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={DP_DATA} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="noDPGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--ink-black)" stopOpacity={0.1} />
                  <stop offset="100%" stopColor="var(--ink-black)" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="dpGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--link-blue)" stopOpacity={0.1} />
                  <stop offset="100%" stopColor="var(--link-blue)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--dust-taupe)" vertical={false} />
              <XAxis dataKey="round" stroke="var(--slate-gray)" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis domain={[0.65, 1]} stroke="var(--slate-gray)" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(v) => `${Math.round(v * 100)}%`} />
              <Tooltip contentStyle={{ backgroundColor: 'var(--lifted-cream)', border: '1px solid var(--dust-taupe)', borderRadius: '12px' }} labelStyle={{ color: 'var(--ink-black)', fontWeight: 500 }} />
              <Legend />
              <Area type="monotone" dataKey="no_dp" stroke="var(--ink-black)" strokeWidth={2} fillOpacity={1} fill="url(#noDPGradient)" name="No-DP" />
              <Area type="monotone" dataKey="dp" stroke="var(--link-blue)" strokeWidth={2} fillOpacity={1} fill="url(#dpGradient)" name="DP (ε=1.0)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        <p className="caption mt-4 text-center">Privacy cost ≈ 2–3 points of accuracy — acceptable for cross-institution sharing.</p>
      </div>

      {/* Bank Status Cards */}
      <div className="grid-4 gap-4">
        {BANKS.map((bank) => (
          <div key={bank.id} className="card-white-pill p-4 flex flex-col items-center gap-2">
            <p className="font-medium text-[var(--ink-black)] text-sm">{bank.name}</p>
            <p className="stat-value text-[var(--ink-black)]">{Math.round(bank.accuracy * 100)}%</p>
            <p className="caption">{bank.samples.toLocaleString()} samples · {bank.latency.toFixed(1)}ms</p>
          </div>
        ))}
      </div>
    </div>
  );
}