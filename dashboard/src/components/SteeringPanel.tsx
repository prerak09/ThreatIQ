'use client';

import { useState, useEffect, useRef } from 'react';
import { Zap, Target, ChevronDown, ChevronUp, Minus, Plus, Circle, Check } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

const CONCEPTS = [
  { id: 'CREDENTIAL_SPOOFING', name: 'CREDENTIAL_SPOOFING', desc: 'Steering vector for credential manipulation patterns', layer: 3, alpha: 0.7, enabled: true },
  { id: 'AUTHORIZATION_BYPASS', name: 'AUTHORIZATION_BYPASS', desc: 'Steering vector for bypassing authorization checks', layer: 5, alpha: 0.9, enabled: true },
  { id: 'COERCIVE_MANIPULATION', name: 'COERCIVE_MANIPULATION', desc: 'Steering vector for social engineering patterns', layer: 7, alpha: 0.6, enabled: false },
  { id: 'VELOCITY_EVASION', name: 'VELOCITY_EVASION', desc: 'Steering vector for avoiding rate limits', layer: 4, alpha: 0.8, enabled: true },
  { id: 'GEO_SPOOFING', name: 'GEO_SPOOFING', desc: 'Steering vector for geographic manipulation', layer: 6, alpha: 0.75, enabled: true },
  { id: 'IDENTITY_FABRICATION', name: 'IDENTITY_FABRICATION', desc: 'Steering vector for synthetic identity generation', layer: 8, alpha: 0.85, enabled: false },
];

const PRESETS = [
  { name: 'Stealth', intensity: 0.2, concepts: ['CREDENTIAL_SPOOFING'], alphas: [0.2] },
  { name: 'Balanced', intensity: 0.5, concepts: ['CREDENTIAL_SPOOFING', 'AUTHORIZATION_BYPASS', 'GEO_SPOOFING'], alphas: [0.5, 0.5, 0.4] },
  { name: 'Aggressive', intensity: 0.8, concepts: ['CREDENTIAL_SPOOFING', 'AUTHORIZATION_BYPASS', 'VELOCITY_EVASION', 'GEO_SPOOFING'], alphas: [0.8, 0.9, 0.7, 0.75] },
  { name: 'Maximum', intensity: 1.0, concepts: ['CREDENTIAL_SPOOFING', 'AUTHORIZATION_BYPASS', 'COERCIVE_MANIPULATION', 'VELOCITY_EVASION', 'GEO_SPOOFING', 'IDENTITY_FABRICATION'], alphas: [1.0, 1.0, 1.0, 1.0, 1.0, 1.0] },
];

const LAYER_EFFECTS = [
  { layer: 'L1', effect: 0.02 },
  { layer: 'L2', effect: 0.04 },
  { layer: 'L3', effect: 0.08 },
  { layer: 'L4', effect: 0.12 },
  { layer: 'L4', effect: 0.15 },
  { layer: 'L5', effect: 0.18 },
  { layer: 'L6', effect: 0.20 },
  { layer: 'L7', effect: 0.18 },
  { layer: 'L8', effect: 0.14 },
  { layer: 'L9', effect: 0.10 },
  { layer: 'L10', effect: 0.06 },
  { layer: 'L11', effect: 0.03 },
  { layer: 'L12', effect: 0.01 },
];

function IOSToggle({ checked, onChange, disabled }: { checked: boolean; onChange: (v: boolean) => void; disabled?: boolean }) {
  return (
    <button
      onClick={() => !disabled && onChange(!checked)}
      disabled={disabled}
      className={`ios-toggle ${checked ? 'on' : ''}`}
      aria-pressed={checked}
      aria-label="Toggle concept"
    />
  );
}

export default function SteeringPanel() {
  const [intensity, setIntensity] = useState(0.5);
  const [activePreset, setActivePreset] = useState(1); // Balanced
  const [concepts, setConcepts] = useState(CONCEPTS.map(c => ({ ...c })));
  const [effect, setEffect] = useState({ cosine: 0.85, l2: 0.12 });

  const sliderRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const preset = PRESETS[activePreset];
    setIntensity(preset.intensity);
    setConcepts(prev => prev.map(c => ({
      ...c,
      enabled: preset.concepts.includes(c.id)
    })));
  }, [activePreset]);

  useEffect(() => {
    const enabled = concepts.filter(c => c.enabled);
    const cosine = 1 - intensity * 0.3 + Math.random() * 0.05;
    const l2 = intensity * 0.2 + Math.random() * 0.05;
    setEffect({ cosine: Math.min(1, Math.max(0, cosine)), l2: Math.min(0.5, Math.max(0, l2)) });
  }, [intensity, concepts]);

  const handlePresetClick = (idx: number) => {
    setActivePreset(idx);
  };

  const handleConceptToggle = (id: string) => {
    setConcepts(prev => prev.map(c => c.id === id ? { ...c, enabled: !c.enabled } : c));
    setActivePreset(-1);
  };

  const intensityToConfig = (intensity: number) => {
    if (intensity <= 0.3) {
      const n = Math.max(1, Math.ceil(intensity / 0.3 * 2));
      return { concepts: CONCEPTS.slice(0, n).map(c => c.id), alphas: Array(n).fill(0).map((_, i) => 0.1 + intensity * 0.5) };
    } else if (intensity <= 0.7) {
      const n = Math.max(2, Math.ceil((intensity - 0.3) / 0.4 * 4));
      return { concepts: CONCEPTS.slice(0, n).map(c => c.id), alphas: Array(n).fill(0).map((_, i) => 0.4 + (intensity - 0.3) * 1.0) };
    } else {
      return { concepts: CONCEPTS.map(c => c.id), alphas: CONCEPTS.map(() => 0.7 + (intensity - 0.7) * 1.0) };
    }
  };

  return (
    <div className="section-padding">
      <div className="mb-8">
        <p className="eyebrow">REPRESENTATION ENGINEERING</p>
        <h2 className="mt-1">Activation Steering</h2>
        <p className="subline mt-2">h' = h + α·v — bend the model's latent space toward attack concepts</p>
      </div>

      {/* Card 1: Attack Intensity */}
      <div className="card-stadium p-8 mb-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <p className="eyebrow">ATTACK INTENSITY</p>
            <h3 className="mt-1">Intensity Controller</h3>
          </div>
          <div className="w-24 text-right">
            <span className="stat-value-xl">α = {intensity.toFixed(2)}</span>
          </div>
        </div>

        <div className="relative mb-8">
          <input
            ref={sliderRef}
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={intensity}
            onChange={(e) => {
              setIntensity(parseFloat(e.target.value));
              setActivePreset(-1);
            }}
            className="custom-slider w-full"
            aria-label="Attack intensity"
          />
          <div className="flex justify-between text-[var(--slate-gray)] text-xs mt-3">
            <span>0</span>
            <span>0.25</span>
            <span>0.5</span>
            <span>0.75</span>
            <span>1.0</span>
          </div>
        </div>

        <div className="flex flex-wrap gap-3">
          {PRESETS.map((preset, idx) => (
            <button
              key={preset.name}
              onClick={() => handlePresetClick(idx)}
              className={`pill-btn ${activePreset === idx ? 'active' : idx === 3 ? 'destructive inactive' : 'inactive'}`}
              aria-pressed={activePreset === idx}
            >
              {preset.name}
              {preset.name === 'Maximum' && <span className="ml-1">({intensity.toFixed(1)})</span>}
            </button>
          ))}
        </div>
      </div>

      <div className="grid-2 gap-8 mb-8">
        {/* Card 2: Concept Library */}
        <div className="card-stadium p-8">
          <p className="eyebrow mb-6">CONCEPT LIBRARY</p>
          <div className="space-y-3">
            {concepts.map((concept) => (
              <div key={concept.id} className="card-white-pill p-4 flex items-center gap-4">
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-[var(--ink-black)] text-sm">{concept.name}</p>
                  <p className="text-[var(--slate-gray)] text-xs mt-0.5">{concept.desc}</p>
                </div>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <span className="text-[var(--slate-gray)] text-xs">L{concept.layer}</span>
                  <IOSToggle checked={concept.enabled} onChange={() => handleConceptToggle(concept.id)} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Card 3: Steering Effect */}
        <div className="card-stadium p-8">
          <p className="eyebrow mb-6">STEERING EFFECT</p>
          
          <div className="grid-2 gap-6 mb-8">
            <div className="relative w-40 h-40 mx-auto">
              <svg viewBox="0 0 100 100" className="w-full h-full">
                <circle cx="50" cy="50" r="40" stroke="#E8E2DA" strokeWidth="8" fill="none" />
                <circle 
                  cx="50" cy="50" r="40" 
                  stroke="var(--link-blue)" 
                  strokeWidth="8" 
                  fill="none" 
                  strokeDasharray={`${effect.cosine * 251.2} 251.2`}
                  strokeLinecap="round"
                  transform="rotate(-90 50 50)"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="stat-value text-[var(--link-blue)]">{Math.round(effect.cosine * 100)}%</span>
                <span className="caption">Cosine Similarity</span>
              </div>
            </div>
            <div className="flex flex-col items-center justify-center">
              <p className="stat-value">{effect.l2.toFixed(2)}</p>
              <p className="stat-label">L² Norm</p>
            </div>
          </div>

          <div>
            <p className="stat-label mb-3">Layer Effect Distribution</p>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={LAYER_EFFECTS} layout="vertical" margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--dust-taupe)" vertical={false} horizontal={false} />
                  <XAxis type="number" domain={[0, 0.25]} tickLine={false} axisLine={false} tick={{ fill: 'var(--slate-gray)', fontSize: 10 }} />
                  <YAxis dataKey="layer" type="category" width={40} tickLine={false} axisLine={false} tick={{ fill: 'var(--ink-black)', fontSize: 11 }} />
                  <Tooltip contentStyle={{ backgroundColor: 'var(--lifted-cream)', border: '1px solid var(--dust-taupe)', borderRadius: '8px' }} formatter={(v: number) => [`${v.toFixed(2)}`, 'Effect']} />
                  <Bar dataKey="effect" radius={[0, 999, 999, 0]} barSize={12} fill="var(--light-signal-orange)" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>

      {/* Ghost watermark */}
      <div className="ghost-watermark" style={{ bottom: '20%', right: '-10%', fontSize: '96px' }}>STEER</div>
    </div>
  );
}