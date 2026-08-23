'use client';

import { useState } from 'react';
import { Shield, CheckCircle, Clock, ExternalLink, Download, Hash, Circle, Check } from 'lucide-react';

const MOCK_PROOFS = [
  { id: 'proof-1a2b3c', txId: 'TX-8a3f', time: '145ms', size: '256B', valid: true },
  { id: 'proof-4d5e6f', txId: 'TX-7c1e', time: '132ms', size: '256B', valid: true },
  { id: 'proof-7g8h9i', txId: 'TX-2d9a', time: '158ms', size: '256B', valid: false },
  { id: 'proof-0j1k2l', txId: 'TX-5b4c', time: '141ms', size: '256B', valid: true },
];

function ZKPPanel() {
  const [activeTab, setActiveTab] = useState<'verify' | 'certificate' | 'stats'>('verify');
  const [selectedProof, setSelectedProof] = useState(MOCK_PROOFS[0]);

  return (
    <div className="section-padding">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-8">
        <div>
          <p className="eyebrow">ZERO-KNOWLEDGE COMPLIANCE</p>
          <h2 className="mt-1">Proof Verification</h2>
          <p className="subline mt-2">Groth16-style zk-SNARKs · merchants verify fraud screening without seeing private data</p>
        </div>
        <button className="btn-primary ml-auto lg:ml-0">
          <Hash className="w-5 h-5" /> Generate Proof
        </button>
      </div>

      <div className="grid-3 gap-8 mb-8">
        {/* Card 1: Proof Status */}
        <div className="card-stadium p-8 lg:col-span-2 relative">
          <div className="ghost-watermark" style={{ bottom: '-10%', right: '-5%', fontSize: '120px' }}>PROOF</div>
          
          <div className="relative z-10 flex flex-col items-center">
            <div className="relative mb-8">
              <div className="w-40 h-40 rounded-full border-2 border-[var(--ink-black)] flex items-center justify-center relative mx-auto">
                <CheckCircle className="w-20 h-20 text-[var(--success-green)]" />
                <div className="absolute inset-0 rounded-full border-2 border-[var(--light-signal-orange)] animate-ping" style={{ animationDuration: '3s' }} />
              </div>
            </div>
            <div className="status-chip success text-lg px-6 py-3 mb-4">VERIFIED</div>
            <p className="text-[var(--slate-gray)] text-sm mb-6">Last verified: 2 minutes ago</p>
            <div className="flex flex-wrap gap-3 justify-center">
              <button className="btn-secondary">
                <Shield className="w-4 h-4" /> Verify Proof
              </button>
              <button className="btn-primary">
                <Download className="w-4 h-4" /> Download Certificate
              </button>
            </div>
          </div>
        </div>

        {/* Card 2: Proof Statistics */}
        <div className="card-stadium p-8">
          <div className="grid-2 gap-4">
            <div className="card-white-pill p-6 text-center">
              <p className="stat-value-lg">145 ms</p>
              <p className="stat-label">Generation</p>
            </div>
            <div className="card-white-pill p-6 text-center">
              <p className="stat-value-lg">23 ms</p>
              <p className="stat-label">Verification</p>
            </div>
            <div className="card-white-pill p-6 text-center">
              <p className="stat-value-lg">128 B</p>
              <p className="stat-label">Proof Size</p>
            </div>
            <div className="card-white-pill p-6 text-center">
              <p className="stat-value-lg">99.7%</p>
              <p className="stat-label">Success Rate</p>
            </div>
          </div>
        </div>
      </div>

      {/* Card 3: Merchant Certificate */}
      <div className="card-stadium p-8 relative">
        <div className="flex items-start gap-4 mb-6">
          <div className="flex items-center gap-2">
            <div className="relative w-10 h-10 rounded-full">
              <div className="absolute left-0 top-0 w-10 h-10 rounded-full bg-[#EB001B]" />
              <div className="absolute left-[30%] top-0 w-10 h-10 rounded-full bg-[#F79E1B]" />
            </div>
            <div>
              <p className="stat-label">MERCHANT CERTIFICATE</p>
              <p className="font-medium text-[var(--ink-black)] text-sm">CERT-2026-001</p>
            </div>
            <span className="status-chip success ml-auto">VALID</span>
          </div>

          <div className="grid-3 gap-4 mb-6">
            <div className="p-4 bg-[var(--lifted-cream)] rounded-[20px] border border-[var(--dust-taupe)]">
              <p className="stat-label">Circuit</p>
              <p className="font-mono text-sm">FraudCheck-128</p>
            </div>
            <div className="p-4 bg-[var(--lifted-cream)] rounded-[20px] border border-[var(--dust-taupe)]">
              <p className="stat-label">Commitment Hash</p>
              <p className="font-mono text-xs">0x7f8a3b4c5d6e...</p>
            </div>
            <div className="p-4 bg-[var(--lifted-cream)] rounded-[20px] border border-[var(--dust-taupe)]">
              <p className="stat-label">Issued</p>
              <p className="text-[var(--ink-black)] text-sm font-medium">2026-08-22 14:32 UTC</p>
            </div>
          </div>

          <div className="bg-[var(--soft-bone)] rounded-[20px] p-5 mb-6 relative">
            <p className="caption mb-3">What this proves:</p>
            <p className="text-[var(--ink-black)] text-sm leading-relaxed">
              This Zero-Knowledge Proof proves that: (1) The fraud detection model was applied correctly to your transaction features, (2) The model weights match the committed hash, ensuring no tampering, (3) The fraud score determination (fraud/not-fraud) is accurate. All without revealing the proprietary model weights or intermediate computations.
            </p>
            <div className="absolute -right-6 -bottom-6 w-20 h-20 rounded-full bg-white border-2 border-[var(--ink-black)] flex items-center justify-center shadow-level-2">
              <Shield className="w-10 h-10 text-[var(--ink-black)]" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}