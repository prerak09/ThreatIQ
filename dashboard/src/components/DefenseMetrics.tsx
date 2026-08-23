'use client';

import { useMemo } from 'react';
import { TrendingUp, TrendingDown, DollarSign, AlertTriangle } from 'lucide-react';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const KPIS = [
  { label: 'Precision', value: '96.2%', trend: 'up', delta: '+0.4' },
  { label: 'Recall', value: '94.8%', trend: 'up', delta: '+0.3' },
  { label: 'ROC-AUC', value: '0.987', trend: 'up', delta: '+0.002' },
  { label: 'Latency', value: '12.3ms', trend: 'down', delta: '-0.8' },
];

const DETECTION_DATA = [
  { time: '00:00', rate: 88 },
  { time: '02:00', rate: 90 },
  { time: '04:00', rate: 87 },
  { time: '06:00', rate: 92 },
  { time: '08:00', rate: 95 },
  { time: '10:00', rate: 93 },
  { time: '12:00', rate: 96 },
  { time: '14:00', rate: 94 },
  { time: '16:00', rate: 97 },
  { time: '18:00', rate: 95 },
  { time: '20:00', rate: 93 },
  { time: '22:00', rate: 91 },
];

const FINANCIAL_STATS = [
  { label: 'LOSS MITIGATED', value: '$2,847,500', color: 'var(--success-green)', icon: TrendingUp },
  { label: 'FALSE-ALARM COST', value: '$124,300', color: 'var(--warning-clay)', icon: AlertTriangle },
];

function KPICard({ label, value, trend, delta }: { label: string; value: string; trend: 'up' | 'down'; delta: string }) {
  return (
    <div className="card-white-pill p-6">
      <p className="stat-label">{label}</p>
      <div className="flex items-baseline gap-2 mt-2">
        <span className="stat-value-lg">{value}</span>
        <span className={`flex items-center gap-0.5 text-sm font-medium ${trend === 'up' ? 'text-[var(--success-green)]' : 'text-[var(--danger-red)]'}`}>
          {trend === 'up' ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
          <span>{delta}</span>
        </div>
      </div>
    </div>
  );
}

function DetectionRateChart() {
  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={DETECTION_DATA} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="detectionGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--light-signal-orange)" stopOpacity={0.15} />
              <stop offset="100%" stopColor="var(--light-signal-orange)" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--dust-taupe)" vertical={false} horizontal={true} />
          <XAxis dataKey="time" stroke="var(--slate-gray)" fontSize={11} tickLine={false} axisLine={false} />
          <YAxis 
            domain={[80, 100]} 
            stroke="var(--slate-gray)" 
            fontSize={11} 
            tickLine={false} 
            axisLine={false} 
            tickFormatter={(v) => `${v}%`}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'var(--lifted-cream)', 
              border: '1px solid var(--dust-taupe)', 
              borderRadius: '12px',
              boxShadow: '0 8px 24px rgba(0,0,0,0.08)'
            }}
            labelStyle={{ color: 'var(--ink-black)', fontWeight: 500 }}
            formatter={(v: number) => [`${v}%`, 'Detection Rate']}
          />
          <Area 
            type="monotone" 
            dataKey="rate" 
            stroke="var(--ink-black)" 
            strokeWidth={2.5} 
            fillOpacity={1} 
            fill="url(#detectionGradient)" 
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

function FinancialStat({ label, value, color, icon: Icon }: { label: string; value: string; color: string; icon: React.ComponentType<{ className?: string }> }) {
  return (
    <div className="flex-1 flex flex-col items-center">
      <p className="stat-label text-center">{label}</p>
      <div className="flex items-center justify-center gap-2 mt-2">
        <Icon className="w-5 h-5" style={{ color }} />
        <span className="stat-value" style={{ color }}>{value}</span>
      </div>
    </div>
  );
}

export default function DefenseMetrics() {
  return (
    <div className="card-stadium p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <p className="eyebrow">BLUE TEAM PERFORMANCE</p>
          <h3 className="mt-1">Detection Quality</h3>
        </div>
      </div>

      {/* Row 1: KPI Tiles */}
      <div className="grid-4 mb-8">
        {KPIS.map((kpi) => (
          <KPICard key={kpi.label} {...kpi} />
        ))}
      </div>

      {/* Row 2: Detection Rate Chart */}
      <div className="mb-8">
        <p className="eyebrow mb-4">DETECTION RATE — LIVE</p>
        <DetectionRateChart />
      </div>

      {/* Row 3: Financial Stats */}
      <div className="flex items-center justify-between gap-8">
        <div className="w-px h-16 bg-[var(--dust-taupe)]" />
        {FINANCIAL_STATS.map((stat, i) => (
          <FinancialStat key={i} {...stat} />
        ))}
        <div className="w-px h-16 bg-[var(--dust-taupe)]" />
      </div>

      {/* Drill-down satellite button */}
      <div className="mt-8 flex justify-end">
        <div className="satellite-btn" aria-label="Drill down into full reports">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
        </div>
      </div>
    </div>
  );
}