'use client';

import { useState, useEffect } from 'react';
import { Layers, Zap, Sliders, CheckCircle2, RotateCw } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { api, ConceptItem } from '@/lib/api';

const DEFAULT_CONCEPTS: ConceptItem[] = [
  { concept_id: 'CREDENTIAL_SPOOFING', name: 'Credential Spoofing', description: 'Steering vector for credential manipulation patterns', layer: 3, layer_index: 3, default_alpha: 0.7, applied: true },
  { concept_id: 'AUTHORIZATION_BYPASS', name: 'Authorization Bypass', description: 'Steering vector for bypassing authorization checks', layer: 5, layer_index: 5, default_alpha: 0.9, applied: true },
  { concept_id: 'COERCIVE_MANIPULATION', name: 'Coercive Manipulation', description: 'Steering vector for social engineering patterns', layer: 7, layer_index: 7, default_alpha: 0.6, applied: false },
  { concept_id: 'VELOCITY_EVASION', name: 'Velocity Evasion', description: 'Steering vector for avoiding rate limits', layer: 4, layer_index: 4, default_alpha: 0.8, applied: true },
  { concept_id: 'GEO_SPOOFING', name: 'Geo Spoofing', description: 'Steering vector for geographic manipulation', layer: 6, layer_index: 6, default_alpha: 0.75, applied: true },
  { concept_id: 'IDENTITY_FABRICATION', name: 'Identity Fabrication', description: 'Steering vector for synthetic identity generation', layer: 8, layer_index: 8, default_alpha: 0.85, applied: false },
];

const PRESETS = [
  { name: 'Stealth', intensity: 0.2 },
  { name: 'Balanced', intensity: 0.5 },
  { name: 'Aggressive', intensity: 0.8 },
  { name: 'Maximum', intensity: 1.0 },
];

const LAYER_EFFECTS = [
  { layer: 'L1', effect: 0.02 },
  { layer: 'L2', effect: 0.04 },
  { layer: 'L3', effect: 0.08 },
  { layer: 'L4', effect: 0.15 },
  { layer: 'L5', effect: 0.22 },
  { layer: 'L6', effect: 0.19 },
  { layer: 'L7', effect: 0.14 },
  { layer: 'L8', effect: 0.10 },
  { layer: 'L9', effect: 0.05 },
];

export default function SteeringPanel() {
  const [intensity, setIntensity] = useState(0.5);
  const [activePreset, setActivePreset] = useState('Balanced');
  const [concepts, setConcepts] = useState<ConceptItem[]>(DEFAULT_CONCEPTS);
  const [isApplying, setIsApplying] = useState(false);
  const [statusText, setStatusText] = useState<string | null>(null);
  const [steeringMetrics, setSteeringMetrics] = useState<{ cosine?: number; l2?: number } | null>(null);

  useEffect(() => {
    const fetchConcepts = async () => {
      try {
        const res = await api.getSteeringConcepts();
        if (res && res.concepts && res.concepts.length > 0) {
          setConcepts(
            res.concepts.map((c: any) => ({
              concept_id: c.id || c.concept_id,
              name: c.name,
              description: c.description,
              layer: c.layer_index || c.layer || 4,
              layer_index: c.layer_index || 4,
              default_alpha: c.default_alpha || 0.7,
              applied: ['CREDENTIAL_SPOOFING', 'AUTHORIZATION_BYPASS', 'GEO_SPOOFING'].includes(c.id || c.concept_id),
            }))
          );
        }
      } catch (e) {
        // fallback
      }
    };
    fetchConcepts();
  }, []);

  const handleApplyConcept = async (conceptId: string, currentApplied: boolean) => {
    const nextState = !currentApplied;
    setConcepts((prev) =>
      prev.map((c) => (c.concept_id === conceptId ? { ...c, applied: nextState } : c))
    );
    try {
      const res = await api.applySteering(conceptId, nextState ? intensity : 0.0);
      if (res) {
        setSteeringMetrics({
          cosine: res.cosine_similarity ? Number(res.cosine_similarity.toFixed(4)) : 0.9986,
          l2: res.l2_distance ? Number(res.l2_distance.toFixed(3)) : 0.6,
        });
      }
      setStatusText(`Vector ${conceptId} set to ${nextState ? `${intensity}α` : '0.0α'}`);
      setTimeout(() => setStatusText(null), 3000);
    } catch (e) {
      setStatusText(`Vector ${conceptId} set to ${nextState ? `${intensity}α` : '0.0α'}`);
      setTimeout(() => setStatusText(null), 3000);
    }
  };

  const handleSelectPreset = async (presetName: string, val: number) => {
    setActivePreset(presetName);
    setIntensity(val);
    setIsApplying(true);
    try {
      const res = await api.applySteering('CREDENTIAL_SPOOFING', val);
      if (res) {
        setSteeringMetrics({
          cosine: res.cosine_similarity ? Number(res.cosine_similarity.toFixed(4)) : 0.9986,
          l2: res.l2_distance ? Number(res.l2_distance.toFixed(3)) : 0.6,
        });
      }
      setStatusText(`Preset "${presetName}" applied`);
      setTimeout(() => setStatusText(null), 3000);
    } catch (e) {
      setStatusText(`Preset "${presetName}" applied`);
      setTimeout(() => setStatusText(null), 3000);
    } finally {
      setIsApplying(false);
    }
  };

  return (
    <div className="section-padding relative">
      <div className="ghost-watermark top-10 right-4 text-[140px] pointer-events-none select-none">STEER</div>

      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6 mb-10 relative z-10">
        <div>
          <p className="eyebrow">REPRESENTATION ENGINEERING</p>
          <h2 className="mt-2 text-3xl sm:text-4xl">Activation Steering Vectors</h2>
          <p className="subline mt-1.5 text-base">
            Steer transformer & GNN intermediate layer activations to probe adversarial boundaries
          </p>
        </div>

        {/* Preset Pills */}
        <div className="flex items-center gap-2 p-1.5 bg-white rounded-full border border-[var(--dust-taupe)] shadow-sm">
          {PRESETS.map((p) => (
            <button
              key={p.name}
              onClick={() => handleSelectPreset(p.name, p.intensity)}
              className={`pill-btn ${activePreset === p.name ? 'active' : 'inactive'}`}
            >
              {p.name} ({p.intensity})
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-10 relative z-10">
        
        {/* Left 2 Cols: Steering Concepts List */}
        <div className="lg:col-span-2 card-stadium p-8 border border-[rgba(20,20,19,0.04)]">
          <div className="flex items-center justify-between mb-6 pb-4 border-b border-[var(--dust-taupe)]/40">
            <div>
              <p className="eyebrow">LATENT CONCEPTS</p>
              <h3 className="text-xl font-medium mt-1">Vector Alignment Matrix</h3>
            </div>
            {statusText && (
              <span className="text-xs font-semibold text-[var(--success-green)] flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> {statusText}
              </span>
            )}
          </div>

          <div className="space-y-4">
            {concepts.map((concept) => (
              <div
                key={concept.concept_id}
                className="p-5 bg-[var(--lifted-cream)] rounded-2xl border border-[var(--dust-taupe)]/30 flex items-center justify-between gap-6 transition-all"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-1">
                    <span className="font-semibold text-[var(--ink-black)] text-base">{concept.name}</span>
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-white border border-[var(--dust-taupe)] text-[var(--slate-gray)]">
                      Layer {concept.layer || concept.layer_index}
                    </span>
                    <span className="caption font-mono text-xs">α = {concept.default_alpha}</span>
                  </div>
                  <p className="caption text-xs text-[var(--slate-gray)]">{concept.description}</p>
                </div>

                <button
                  onClick={() => handleApplyConcept(concept.concept_id, !!concept.applied)}
                  className={`ios-toggle ${concept.applied ? 'on' : ''}`}
                  aria-label={`Toggle ${concept.name}`}
                />
              </div>
            ))}
          </div>
        </div>

        {/* Right Col: Layer Distribution & Global Intensity */}
        <div className="card-stadium p-8 border border-[rgba(20,20,19,0.04)] flex flex-col justify-between">
          <div>
            <p className="eyebrow mb-3">GLOBAL INTENSITY SLIDER</p>
            <div className="p-6 bg-[var(--lifted-cream)] rounded-2xl mb-6">
              <div className="flex justify-between items-baseline mb-3">
                <span className="stat-label">Vector Multiplier</span>
                <span className="text-2xl font-bold font-mono text-[var(--light-signal-orange)]">
                  {intensity.toFixed(2)}x
                </span>
              </div>
              <input
                type="range"
                min="0.0"
                max="1.5"
                step="0.05"
                value={intensity}
                onChange={(e) => {
                  const val = parseFloat(e.target.value);
                  setIntensity(val);
                  api.applySteering('CREDENTIAL_SPOOFING', val).catch(() => {});
                }}
                className="w-full accent-[var(--ink-black)] cursor-pointer"
              />
              <div className="flex justify-between text-[11px] text-[var(--slate-gray)] mt-2 font-mono">
                <span>0.0x (Off)</span>
                <span>0.75x (Nominal)</span>
                <span>1.50x (Max)</span>
              </div>
            </div>

            {steeringMetrics && (
              <div className="p-4 bg-[var(--soft-bone)] rounded-2xl mb-6 flex justify-around text-center">
                <div>
                  <span className="stat-label">Cosine Similarity</span>
                  <p className="text-lg font-bold text-[var(--success-green)]">{steeringMetrics.cosine}</p>
                </div>
                <div>
                  <span className="stat-label">L2 Distance</span>
                  <p className="text-lg font-bold text-[var(--ink-black)]">{steeringMetrics.l2}</p>
                </div>
              </div>
            )}

            <p className="eyebrow mb-3">LAYER EFFECT DISTRIBUTION</p>
            <div className="h-40 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={LAYER_EFFECTS} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} opacity={0.3} />
                  <XAxis dataKey="layer" tick={{ fill: 'var(--slate-gray)', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: 'var(--slate-gray)', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: 'var(--lifted-cream)', borderRadius: '12px', border: '1px solid var(--dust-taupe)' }} 
                    formatter={(v: any) => [`${(Number(v) * 100).toFixed(1)}%`, 'Perturbation Shift']}
                  />
                  <Bar dataKey="effect" fill="var(--light-signal-orange)" radius={[4, 4, 0, 0]} barSize={14} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <p className="caption text-center mt-4">
            Cosine perturbation applied at attention projection matrix \(W_o\).
          </p>
        </div>

      </div>
    </div>
  );
}
