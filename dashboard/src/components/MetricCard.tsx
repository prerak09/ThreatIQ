'use client';

import { TrendingUp, TrendingDown } from 'lucide-react';

interface MetricCardProps {
  label: string;
  value: string;
  trend?: 'up' | 'down';
  delta?: string;
  color?: string;
  icon?: React.ReactNode;
}

export function MetricCard({ label, value, trend, delta, color, icon }: MetricCardProps) {
  return (
    <div className="card-white-pill p-6">
      <p className="stat-label">{label}</p>
      <div className="flex items-baseline gap-2 mt-2">
        <span className="stat-value-lg" style={{ color: color || 'var(--ink-black)' }}>{value}</span>
        {trend && delta && (
          <span className={`flex items-center gap-0.5 text-sm font-medium ${trend === 'up' ? 'text-[var(--success-green)]' : 'text-[var(--danger-red)]'}`}>
            {trend === 'up' ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
            <span>{delta}</span>
          </span>
        )}
        {icon && <span className="ml-auto">{icon}</span>}
      </div>
    </div>
  );
}