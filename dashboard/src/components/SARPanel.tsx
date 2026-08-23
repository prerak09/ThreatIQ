'use client';

import { useState } from 'react';
import { FileText, AlertCircle, CheckCircle, Clock, ArrowRight, Download, ChevronDown, ChevronUp, Shield } from 'lucide-react';

interface SAR {
  id: string;
  status: 'pending' | 'filed';
  timestamp: string;
  subject: {
    name: string;
    account: string;
    risk_level: 'HIGH' | 'MEDIUM' | 'LOW';
  };
  summary: string;
  risk_factors: Array<{
    category: string;
    factor: string;
    level: 'HIGH' | 'MEDIUM' | 'LOW';
  }>;
  narrative: string;
}

const MOCK_SARS: SAR[] = [
  {
    id: 'SAR-2026-001',
    status: 'pending',
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    subject: { name: 'Synthetic Ring Alpha', account: '****4521', risk_level: 'HIGH' },
    summary: 'Coordinated synthetic identity fraud ring detected across 12 accounts',
    risk_factors: [
      { category: 'Identity', factor: 'Synthetic ID patterns', level: 'HIGH' },
      { category: 'Velocity', factor: '142 txns in 3 hours', level: 'HIGH' },
      { category: 'Geographic', factor: 'Impossible travel', level: 'MEDIUM' },
    ],
    narrative: 'Pattern analysis reveals 12 accounts sharing device fingerprints and IP addresses within a 3-minute window. Transaction amounts follow Benford-distributed pattern suggesting algorithmic generation.',
  },
  {
    id: 'SAR-2026-002',
    status: 'pending',
    timestamp: new Date(Date.now() - 7200000).toISOString(),
    subject: { name: 'CNP Relay Network', account: '****7890', risk_level: 'HIGH' },
    summary: 'Distributed card-not-present relay attack across 47 merchant endpoints',
    risk_factors: [
      { category: 'Velocity', factor: '234 txns in 1 hour', level: 'HIGH' },
      { category: 'Geographic', factor: 'Multi-country proxy chain', level: 'HIGH' },
      { category: 'Device', factor: 'Shared device fingerprint cluster', level: 'MEDIUM' },
    ],
    narrative: 'Attack orchestrated through distributed proxy network with geo-consistent rotation. Card credentials sourced from multiple breach databases.',
  },
  {
    id: 'SAR-2026-003',
    status: 'filed',
    timestamp: new Date(Date.now() - 86400000).toISOString(),
    subject: { name: 'Prompt Injection Campaign', account: '****1122', risk_level: 'MEDIUM' },
    summary: 'LLM payment assistant manipulated via encoded payload injection',
    risk_factors: [
      { category: 'Injection', factor: 'Encoded payload in description field', level: 'HIGH' },
      { category: 'Data Exfil', factor: 'Card data leaked via LLM response', level: 'MEDIUM' },
    ],
    narrative: 'Adversary embedded prompt override in transaction description. Merchant LLM extracted and returned sanitized card data in natural language response.',
  },
];

function formatTime(ts: string) {
  return new Date(ts).toLocaleString('en-US', { 
    month: 'short', 
    day: 'numeric', 
    hour: '2-digit', 
    minute: '2-digit' 
  });
}

function RiskChip({ level }: { level: 'HIGH' | 'MEDIUM' | 'LOW' }) {
  const configs = {
    HIGH: { className: 'status-chip danger', label: 'HIGH' },
    MEDIUM: { className: 'status-chip warning', label: 'MEDIUM' },
    LOW: { className: 'status-chip success', label: 'LOW' },
  };
  const config = configs[level];
  return <span className={config.className}>{config.label}</span>;
}

function SARRow({ sar, onExpand, isExpanded, onAction }: { 
  sar: SAR; 
  onExpand: () => void; 
  isExpanded: boolean; 
  onAction: (action: 'review' | 'file', id: string) => void;
}) {
  const isFiled = sar.status === 'filed';
  
  return (
    <div className="card-white-pill p-5 relative overflow-hidden transition-all">
      <div className="flex items-start gap-4">
        <div className="w-12 h-12 rounded-full bg-[var(--info-tint)] flex items-center justify-center flex-shrink-0">
          <FileText className="w-6 h-6 text-[var(--link-blue)]" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 flex-wrap">
            <span className="font-medium text-[var(--ink-black)]">{sar.id}</span>
            <span className="text-[var(--slate-gray)] text-sm">{sar.subject.name} · {sar.subject.account}</span>
            <RiskChip level={sar.subject.risk_level} />
            <span className="text-[var(--slate-gray)] text-sm ml-auto">{formatTime(sar.timestamp)}</span>
          </div>
          <p className="text-[var(--slate-gray)] text-sm mt-1 line-clamp-2">{sar.summary}</p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {isExpanded ? (
            <button onClick={onExpand} className="pill-btn inactive text-xs" aria-label="Collapse">
              <ChevronUp className="w-4 h-4" /> Collapse
            </button>
          ) : (
            <button onClick={onExpand} className="pill-btn inactive text-xs" aria-label="Expand">
              <ChevronDown className="w-4 h-4" /> Expand
            </button>
          )}
          {!isFiled && (
            <>
              <button onClick={() => onAction('review', sar.id)} className="pill-btn inactive text-xs">
                Review
              </button>
              <button onClick={() => onAction('file', sar.id)} className="pill-btn active text-xs">
                <FileText className="w-3 h-3" /> File
              </button>
            </>
          )}
          {isFiled && (
            <span className="status-chip success">FILED</span>
          )}
        </div>
      </div>

      {isExpanded && (
        <div className="mt-5 pt-5 border-t border-[var(--dust-taupe)] animate-slide-down">
          <p className="eyebrow mb-3">RISK FACTORS</p>
          <div className="space-y-3 mb-5">
            {sar.risk_factors.map((rf, i) => (
              <div key={i} className="flex items-center gap-3 p-3 bg-[var(--lifted-cream)] rounded-[20px]">
                <span className="pill-btn inactive text-xs capitalize">{rf.category.toLowerCase()}</span>
                <span className="text-[var(--ink-black)] text-sm flex-1">{rf.factor}</span>
                <RiskChip level={rf.level} />
              </div>
            ))}
          </div>
          
          <div className="bg-[var(--soft-bone)] rounded-[20px] p-5 mb-5">
            <p className="text-[var(--ink-black)] text-sm leading-relaxed">{sar.narrative}</p>
          </div>

          <div className="flex flex-wrap gap-3">
            <button className="btn-primary">
              <FileText className="w-4 h-4" /> Generate FinCEN Form 111
            </button>
            <button className="btn-secondary">
              <Download className="w-4 h-4" /> Export PDF
            </button>
            <a href="#" className="pill-btn inactive text-xs">
              <Clock className="w-3 h-3" /> Audit log
            </a>
          </div>
        </div>
      )}
    </div>
  );
}

export default function SARPanel() {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'pending' | 'filed'>('pending');

  const pendingSars = MOCK_SARS.filter(s => s.status === 'pending');
  const filedSars = MOCK_SARS.filter(s => s.status === 'filed');

  const handleAction = (action: 'review' | 'file', id: string) => {
    console.log(action, id);
  };

  return (
    <div className="card-stadium p-8">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-8">
        <div>
          <p className="eyebrow">REGULATORY</p>
          <h3 className="mt-1">Suspicious Activity Reports</h3>
        </div>
        <div className="flex items-center gap-2" role="tablist" aria-label="SAR status">
          <button
            role="tab"
            aria-selected={activeTab === 'pending'}
            onClick={() => setActiveTab('pending')}
            className={`pill-btn ${activeTab === 'pending' ? 'active' : 'inactive'}`}
          >
            Pending ({pendingSars.length})
          </button>
          <button
            role="tab"
            aria-selected={activeTab === 'filed'}
            onClick={() => setActiveTab('filed')}
            className={`pill-btn ${activeTab === 'filed' ? 'active' : 'inactive'}`}
          >
            Filed ({filedSars.length})
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {(activeTab === 'pending' ? pendingSars : filedSars).map((sar) => (
          <SARRow
            key={sar.id}
            sar={sar}
            isExpanded={expandedId === sar.id}
            onExpand={() => setExpandedId(expandedId === sar.id ? null : sar.id)}
            onAction={(action, id) => console.log(action, id)}
          />
        ))}
      </div>
    </div>
  );
}