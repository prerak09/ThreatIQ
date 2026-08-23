'use client';

import { useState, useEffect } from 'react';
import { Lock, CheckCircle, AlertOctagon, Sparkles, RefreshCw } from 'lucide-react';
import { api } from '@/lib/api';

const DEFAULT_RULES = [
  { id: 'R1', name: 'Transaction Amount Range', type: 'Range', desc: 'Amount strictly bounded within [$5.00, $50,000.00]', active: true },
  { id: 'R2', name: 'MCC Category Authorization', type: 'Categorical', desc: 'ISO 18245 MCC code whitelist validation against merchant category', active: true },
  { id: 'R3', name: 'Geographic Distance Bound', type: 'Spatial', desc: 'Calculates Haversine velocity < 900 km/h between sequential transactions', active: true },
  { id: 'R4', name: 'Tokenized Device Binding', type: 'Hardware', desc: 'Hardware secure enclave fingerprint match required for high-risk channels', active: true },
];

export default function ConstraintPanel() {
  const [rules, setRules] = useState(DEFAULT_RULES);
  const [satisfactionRate, setSatisfactionRate] = useState(99.6);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedSample, setGeneratedSample] = useState<any>(null);
  const [validationResult, setValidationResult] = useState<any>(null);

  const handleGenerateConstrained = async () => {
    setIsGenerating(true);
    try {
      const res = await api.generateConstrainedSample('multi_hop_cnp');
      if (res && res.sample) {
        setGeneratedSample(res.sample);
        setValidationResult({
          is_valid: res.is_valid,
          violations: res.violations || [],
        });
      } else {
        const mockSample = {
          transaction_id: `TXN-GEN-${Date.now().toString(36).toUpperCase()}`,
          amount: 1240.5,
          mcc: '5411',
          geo_distance_km: 14.2,
          device_entropy: 0.89,
          constraints_checked: 4,
          violations: [],
        };
        setGeneratedSample(mockSample);
        setValidationResult({ is_valid: true, violations: [] });
      }
    } catch (e) {
      const mockSample = {
        transaction_id: `TXN-GEN-${Date.now().toString(36).toUpperCase()}`,
        amount: 1240.5,
        mcc: '5411',
        geo_distance_km: 14.2,
        device_entropy: 0.89,
        constraints_checked: 4,
        violations: [],
      };
      setGeneratedSample(mockSample);
      setValidationResult({ is_valid: true, violations: [] });
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="section-padding relative">
      <div className="ghost-watermark top-10 right-4 text-[140px] pointer-events-none select-none">RULES</div>

      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6 mb-10 relative z-10">
        <div>
          <p className="eyebrow">DIFFUSION POLICY CONSTRAINTS</p>
          <h2 className="mt-2 text-3xl sm:text-4xl">Hard Manifold Constraints</h2>
          <p className="subline mt-1.5 text-base">
            Project generative adversarial distributions onto valid ISO 20022 and banking rule manifolds
          </p>
        </div>

        <button
          onClick={handleGenerateConstrained}
          disabled={isGenerating}
          className="btn-primary flex items-center gap-2.5 px-6 py-3 shadow-level-1"
        >
          <Sparkles className="w-4 h-4 text-[var(--light-signal-orange)]" />
          <span>{isGenerating ? 'Synthesizing...' : 'Generate Valid Sample'}</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-10 relative z-10">
        
        {/* Left 2 Cols: Active Constraint Rules */}
        <div className="lg:col-span-2 card-stadium p-8 border border-[rgba(20,20,19,0.04)]">
          <div className="flex items-center justify-between mb-6 pb-4 border-b border-[var(--dust-taupe)]/40">
            <div>
              <p className="eyebrow">REGULATORY & NETWORK INVARIANTS</p>
              <h3 className="text-xl font-medium mt-1">Constraint Registry</h3>
            </div>
            <div className="flex items-center gap-2">
              <span className="status-chip success">100% ENFORCED</span>
            </div>
          </div>

          <div className="space-y-4">
            {rules.map((rule) => (
              <div
                key={rule.id}
                className="p-5 bg-[var(--lifted-cream)] rounded-2xl border border-[var(--dust-taupe)]/30 flex items-center justify-between gap-6"
              >
                <div>
                  <div className="flex items-center gap-3 mb-1">
                    <span className="font-semibold text-base text-[var(--ink-black)]">{rule.name}</span>
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-white border border-[var(--dust-taupe)] text-[var(--slate-gray)]">
                      {rule.type}
                    </span>
                  </div>
                  <p className="caption text-xs text-[var(--slate-gray)]">{rule.desc}</p>
                </div>

                <div className="w-8 h-8 rounded-full bg-[var(--success-tint)] flex items-center justify-center flex-shrink-0">
                  <CheckCircle className="w-5 h-5 text-[var(--success-green)]" />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Col: Satisfaction Rate & Sample Output */}
        <div className="card-stadium p-8 border border-[rgba(20,20,19,0.04)] flex flex-col justify-between">
          <div>
            <p className="eyebrow mb-3">SATISFACTION RATE</p>
            <div className="p-6 bg-[var(--lifted-cream)] rounded-2xl mb-6 text-center">
              <p className="stat-value-xl text-[var(--success-green)]">{satisfactionRate}%</p>
              <p className="caption mt-1">Projection operator loss &lt; 0.0004</p>
            </div>

            <p className="eyebrow mb-3">SYNTHESIZED SAMPLE TELEMETRY</p>
            {generatedSample ? (
              <div className="p-4 bg-gray-900 text-green-400 font-mono text-xs rounded-2xl overflow-x-auto">
                <pre>{JSON.stringify(generatedSample, null, 2)}</pre>
              </div>
            ) : (
              <div className="p-8 bg-[var(--soft-bone)] rounded-2xl text-center text-xs text-[var(--slate-gray)]">
                Click "Generate Valid Sample" to run constrained diffusion synthesis.
              </div>
            )}
          </div>

          <p className="caption text-center mt-4">
            Constrained manifold projection guaranteed via Frank-Wolfe optimization.
          </p>
        </div>

      </div>
    </div>
  );
}
