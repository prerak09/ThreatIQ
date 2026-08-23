'use client';

import { useState } from 'react';
import { Zap, Plus, Minus, Play, X } from 'lucide-react';

const ATTACK_OPTIONS = [
  'Synthetic Identity',
  'Multi-Hop CNP',
  'Prompt Injection',
  'Voice Deepfake',
  'Merchant API Abuse',
  'Velocity Evasion',
];

export interface AttackInjectionProps {
  isRunning?: boolean;
  onInject?: (attackType: string, count: number) => void;
}

export default function AttackInjection({ isRunning = false, onInject }: AttackInjectionProps) {
  const [attackType, setAttackType] = useState(ATTACK_OPTIONS[0]);
  const [count, setCount] = useState(10);
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);

  const handleLaunch = () => {
    if (!isRunning) return;
    onInject?.(attackType, count);
    const detected = Math.floor(count * 0.7);
    const missed = count - detected;
    setResult({ success: true, message: `Injected ${count} × ${attackType} — ${detected} detected, ${missed} missed` });
    setTimeout(() => setResult(null), 5000);
  };

  const handleFlood = () => {
    if (!isRunning) return;
    onInject?.(attackType, count * 5);
    const detected = Math.floor(count * 5 * 0.5);
    const missed = count * 5 - detected;
    setResult({ success: true, message: `FLOOD: Injected ${count * 5} × ${attackType} — ${detected} detected, ${missed} missed` });
    setTimeout(() => setResult(null), 5000);
  };

  return (
    <div className="card-stadium p-8">
      <div className="mb-8">
        <p className="eyebrow">RED TEAM CONSOLE</p>
        <h3 className="mt-1">Inject Custom Attack</h3>
      </div>

      <div className="flex flex-col lg:flex-row lg:items-end gap-6">
        {/* Attack Type Select */}
        <div className="flex-1 lg:w-64">
          <label className="stat-label block mb-2">ATTACK VECTOR</label>
          <div className="relative">
            <select
              value={attackType}
              onChange={(e) => setAttackType(e.target.value)}
              className="select-pill w-full"
              aria-label="Attack vector type"
            >
              {ATTACK_OPTIONS.map(opt => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Count Input with Stepper */}
        <div className="flex items-center gap-3 lg:w-48">
          <label className="stat-label block mb-2">VOLUME</label>
          <div className="flex items-center gap-2 w-full">
            <button
              onClick={() => setCount(c => Math.max(1, c - 1))}
              className="stepper-btn flex-shrink-0"
              aria-label="Decrease count"
            >
              <Minus className="w-4 h-4" />
            </button>
            <input
              type="number"
              value={count}
              onChange={(e) => setCount(Math.max(1, parseInt(e.target.value) || 1))}
              className="number-pill"
              min={1}
              max={1000}
              aria-label="Attack count"
            />
            <button
              onClick={() => setCount(c => Math.min(1000, c + 1))}
              className="stepper-btn flex-shrink-0"
              aria-label="Increase count"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Launch Attack Button */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleLaunch}
            disabled={!isRunning}
            className={`btn-primary w-full lg:w-auto ${isRunning ? '' : 'opacity-50 cursor-not-allowed'}`}
            aria-disabled={!isRunning}
          >
            <Play className="w-5 h-5" /> Launch Attack
          </button>

          {/* Flood Button - Destructive */}
          <button
            onClick={handleFlood}
            disabled={!isRunning}
            className={`btn-destructive w-full lg:w-auto ${isRunning ? '' : 'opacity-50 cursor-not-allowed'}`}
            aria-disabled={!isRunning}
          >
            <Zap className="w-5 h-5" /> Flood ×50
          </button>
        </div>
      </div>

      {/* Result Strip */}
      {result && (
        <div className="mt-6 card-white-pill p-4 flex items-center gap-3 animate-slide-in">
          <div className="w-8 h-8 rounded-full bg-[var(--success-tint)] flex items-center justify-center flex-shrink-0">
            <svg className="w-5 h-5 text-[var(--success-green)]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
          </div>
          <span className="text-[var(--ink-black)] font-medium text-sm">{result.message}</span>
          <span className="text-[var(--slate-gray)] text-sm ml-auto">{new Date().toLocaleTimeString()}</span>
        </div>
      )}
    </div>
  );
}