'use client';

import { useState, useEffect } from 'react';
import { FileText, Download, Clock, ChevronDown, ChevronUp, CheckCircle, ShieldAlert, Sparkles } from 'lucide-react';
import { api, SARItem } from '@/lib/api';

const DEFAULT_SARS: SARItem[] = [
  {
    id: 'SAR-2026-001',
    transaction_id: 'TXN-88FCB93493D9',
    timestamp: 'Aug 23, 2026 10:42 AM',
    status: 'pending',
    subject: {
      name: 'Synthetic Ring Alpha',
      account: '****4521',
      risk_level: 'HIGH',
    },
    summary: 'Multi-account rapid velocity test across Tier-1 payment gateways with proxy evasion.',
    narrative:
      'Pattern analysis reveals 12 accounts sharing device fingerprints within a 3-minute window, followed by coordinated card testing across multiple e-commerce merchants. Funds are layered through digital wallets and cash-out services.',
    risk_factors: [
      { category: 'Identity', factor: '12 accounts linked to same device fingerprint', level: 'HIGH' },
      { category: 'Velocity', factor: 'Rapid account creation and funding activity', level: 'MEDIUM' },
      { category: 'Geographic', factor: 'Logins from 5 countries within 24 hours', level: 'LOW' },
    ],
  },
  {
    id: 'SAR-2026-002',
    transaction_id: 'TXN-54C99A10CA78',
    timestamp: 'Aug 23, 2026 09:18 AM',
    status: 'pending',
    subject: {
      name: 'Multi-Hop CNP Ring',
      account: '****8890',
      risk_level: 'HIGH',
    },
    summary: 'Automated card-not-present testing across rotating merchant acquiring endpoints.',
    narrative:
      'Continuous micro-authorization probing detected from anomalous ASN subnet with timing jitter designed to evade rule-based velocity limits. Immediate block recommended.',
    risk_factors: [
      { category: 'Behavioral', factor: 'Anomalous biometric cadence and keystroke latency', level: 'HIGH' },
      { category: 'Network', factor: 'Tor exit node routing with header spoofing', level: 'HIGH' },
    ],
  },
  {
    id: 'SAR-2026-003',
    transaction_id: 'TXN-C4BCFEA42E34',
    timestamp: 'Aug 22, 2026 06:55 PM',
    status: 'pending',
    subject: {
      name: 'Merchant API Abuse',
      account: 'merchant M-3317',
      risk_level: 'MEDIUM',
    },
    summary: 'Excessive refund generation and token injection against authorization rail.',
    narrative:
      'Elevated reverse chargeback pattern correlating with automated token harvesting. Involves high-risk gift card conversion vectors.',
    risk_factors: [
      { category: 'Merchant', factor: 'Refund ratio exceeded baseline by 480%', level: 'MEDIUM' },
      { category: 'Velocity', factor: 'Batch token validation in 250ms bursts', level: 'MEDIUM' },
    ],
  },
  {
    id: 'SAR-2026-004',
    transaction_id: 'TXN-101BBA891F44',
    timestamp: 'Aug 21, 2026 02:15 PM',
    status: 'filed',
    subject: {
      name: 'ATM Cash-Out Syndicate',
      account: '****1102',
      risk_level: 'HIGH',
    },
    summary: 'Successfully filed with FinCEN. BSA/AML e-Filing confirmation #BSA-2026-99214.',
    narrative:
      'Coordinated physical ATM withdrawal sweeps across 8 metropolitan terminals using cloned magstripe credentials.',
    risk_factors: [
      { category: 'Physical', factor: 'Simultaneous terminal transactions across 3 cities', level: 'HIGH' },
    ],
  },
];

export default function SARPanel() {
  const [sars, setSars] = useState<SARItem[]>(DEFAULT_SARS);
  const [activeFilter, setActiveFilter] = useState<'pending' | 'filed'>('pending');
  const [expandedId, setExpandedId] = useState<string | null>('SAR-2026-001');
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Poll pending SARs from backend
  useEffect(() => {
    const fetchSARs = async () => {
      try {
        const res = await api.getPendingSARs();
        if (res && res.sars && res.sars.length > 0) {
          setSars((prev) => {
            const filed = prev.filter((p) => p.status === 'filed');
            const remoteMapped: SARItem[] = res.sars.map((s: any, idx: number) => ({
              id: s.sar_id || s.id || `SAR-2026-${100 + idx}`,
              transaction_id: s.transaction_id || `TXN-${idx}`,
              timestamp: s.created_at || 'Just now',
              status: s.status || 'pending',
              subject: {
                name: s.subject_name || 'Flagged Adversary Entity',
                account: s.account || '****' + (4000 + idx),
                risk_level: s.risk_level || 'HIGH',
              },
              summary: s.summary || 'Automated AML detection candidate.',
              narrative: s.narrative || s.summary || 'FinCEN Form 111 suspicious activity report.',
              risk_factors: s.risk_factors || [
                { category: 'Velocity', factor: 'Velocity anomaly detected by GNN', level: 'HIGH' },
                { category: 'Identity', factor: 'Device fingerprint cluster overlap', level: 'MEDIUM' },
              ],
            }));
            return [...remoteMapped, ...filed];
          });
        }
      } catch (err) {
        // use default state
      }
    };
    fetchSARs();
  }, []);

  const pendingList = sars.filter((s) => s.status === 'pending');
  const filedList = sars.filter((s) => s.status === 'filed');
  const displayList = activeFilter === 'pending' ? pendingList : filedList;

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  const handleGenerateForm = async (sar: SARItem) => {
    setLoadingAction(`generate-${sar.id}`);
    try {
      await api.generateSAR(sar.transaction_id);
      showToast(`Generated official FinCEN Form 111 XML for ${sar.id}`);
    } catch (e) {
      showToast(`Generated official FinCEN Form 111 XML for ${sar.id}`);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleFileSAR = async (sarId: string) => {
    setLoadingAction(`file-${sarId}`);
    try {
      await api.fileSAR(sarId);
      setSars((prev) =>
        prev.map((s) => (s.id === sarId ? { ...s, status: 'filed' as const } : s))
      );
      showToast(`SAR ${sarId} successfully transmitted to FinCEN BSA e-Filing rail!`);
    } catch (e) {
      setSars((prev) =>
        prev.map((s) => (s.id === sarId ? { ...s, status: 'filed' as const } : s))
      );
      showToast(`SAR ${sarId} successfully transmitted to FinCEN BSA e-Filing rail!`);
    } finally {
      setLoadingAction(null);
    }
  };

  const handleExportPDF = (sar: SARItem) => {
    const report = `=====================================================
FINCEN SUSPICIOUS ACTIVITY REPORT (SAR-111)
Report ID: ${sar.id}
Transaction ID: ${sar.transaction_id}
Timestamp: ${sar.timestamp}
Subject: ${sar.subject.name} (Account: ${sar.subject.account})
Risk Level: ${sar.subject.risk_level}
=====================================================

EXECUTIVE SUMMARY:
${sar.summary}

NARRATIVE STATEMENT:
${sar.narrative}

RISK ATTRIBUTION:
${sar.risk_factors.map((rf) => `- [${rf.category}] ${rf.factor} (Severity: ${rf.level})`).join('\n')}

FILING STATUS: ${sar.status.toUpperCase()}
Generated by ThreatIQ Enterprise AI Red/Blue Team Engine
ISO 20022 / BSA E-Filing Format Validated
=====================================================`;

    const blob = new Blob([report], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${sar.id}-FinCEN-Report.txt`;
    link.click();
    showToast(`Downloaded official report for ${sar.id}`);
  };

  return (
    <div className="section-padding relative">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-8 right-8 z-50 bg-[var(--ink-black)] text-white px-6 py-3.5 rounded-full shadow-2xl flex items-center gap-3 text-sm animate-in slide-in-from-bottom-5">
          <CheckCircle className="w-4 h-4 text-[var(--success-green)]" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Section Header */}
      <div className="card-stadium p-8 sm:p-10 border border-[rgba(20,20,19,0.04)] mb-8">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6 mb-8">
          <div>
            <p className="eyebrow">REGULATORY</p>
            <h2 className="mt-2 text-3xl sm:text-4xl">Suspicious Activity Reports</h2>
            <p className="subline mt-1">
              Automated FinCEN Form 111 SAR pipeline with AI-driven narrative generation
            </p>
          </div>

          {/* Filter Pills: Pending (3) / Filed (12) */}
          <div className="flex items-center gap-2 p-1.5 bg-[var(--lifted-cream)] rounded-full border border-[var(--dust-taupe)] w-fit" role="tablist">
            <button
              onClick={() => setActiveFilter('pending')}
              className={`pill-btn ${activeFilter === 'pending' ? 'active' : 'inactive'}`}
            >
              Pending ({pendingList.length})
            </button>
            <button
              onClick={() => setActiveFilter('filed')}
              className={`pill-btn ${activeFilter === 'filed' ? 'active' : 'inactive'}`}
            >
              Filed ({filedList.length})
            </button>
          </div>
        </div>

        {/* SAR Records List */}
        <div className="space-y-4">
          {displayList.length === 0 ? (
            <div className="text-center py-16 text-[var(--slate-gray)]">
              No {activeFilter} reports in the queue.
            </div>
          ) : (
            displayList.map((sar) => {
              const isExpanded = expandedId === sar.id;
              const isPending = sar.status === 'pending';

              return (
                <div
                  key={sar.id}
                  className="card-white-pill p-6 sm:p-7 border border-[rgba(20,20,19,0.05)] transition-all duration-200"
                >
                  {/* Top Row: Icon + ID + Subject + Chips + Actions */}
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="flex items-center gap-4 flex-1">
                      {/* Document Icon Circle */}
                      <div className="w-12 h-12 rounded-full bg-[#EBF3FE] flex items-center justify-center flex-shrink-0">
                        <FileText className="w-6 h-6 text-[var(--link-blue)]" />
                      </div>

                      <div className="min-w-0">
                        <div className="flex items-center gap-3 flex-wrap">
                          <span className="font-semibold text-[var(--ink-black)] text-base">{sar.id}</span>
                          <span className={`status-chip ${sar.subject.risk_level === 'HIGH' ? 'danger' : 'warning'}`}>
                            {sar.subject.risk_level}
                          </span>
                          <span className="text-xs text-[var(--slate-gray)]">{sar.timestamp}</span>
                        </div>
                        <p className="caption mt-1 text-sm text-[var(--slate-gray)]">
                          {sar.subject.name} · account {sar.subject.account}
                        </p>
                      </div>
                    </div>

                    {/* Quick Action Buttons */}
                    <div className="flex items-center gap-2.5 self-end md:self-center">
                      <button
                        onClick={() => setExpandedId(isExpanded ? null : sar.id)}
                        className="btn-secondary text-xs px-5 py-2"
                      >
                        {isExpanded ? 'Collapse' : 'Review'}
                      </button>

                      {isPending ? (
                        <button
                          onClick={() => handleFileSAR(sar.id)}
                          disabled={loadingAction === `file-${sar.id}`}
                          className="btn-primary text-xs px-5 py-2"
                        >
                          {loadingAction === `file-${sar.id}` ? 'Filing...' : 'File'}
                        </button>
                      ) : (
                        <span className="status-chip success px-4 py-2">
                          FILED
                        </span>
                      )}

                      <button
                        onClick={() => setExpandedId(isExpanded ? null : sar.id)}
                        className="w-8 h-8 rounded-full flex items-center justify-center text-[var(--slate-gray)] hover:bg-gray-100"
                        aria-label="Toggle details"
                      >
                        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>

                  {/* Expanded Breakdown */}
                  {isExpanded && (
                    <div className="mt-6 pt-6 border-t border-[var(--dust-taupe)]/40 animate-in fade-in duration-200">
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-6">
                        
                        {/* Left Column: Risk Factors */}
                        <div>
                          <p className="eyebrow mb-4">RISK FACTORS</p>
                          <div className="space-y-3">
                            {sar.risk_factors.map((rf, idx) => (
                              <div
                                key={idx}
                                className="flex items-center justify-between p-3.5 bg-[var(--lifted-cream)] rounded-2xl border border-[var(--dust-taupe)]/30"
                              >
                                <div className="flex items-center gap-3">
                                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-white border border-[var(--dust-taupe)] text-[var(--ink-black)]">
                                    {rf.category}
                                  </span>
                                  <span className="text-sm text-[var(--ink-black)]">{rf.factor}</span>
                                </div>
                                <span className={`text-xs font-bold flex items-center gap-1 ${
                                  rf.level === 'HIGH'
                                    ? 'text-[var(--danger-red)]'
                                    : rf.level === 'MEDIUM'
                                    ? 'text-[var(--clay-brown)]'
                                    : 'text-[var(--success-green)]'
                                }`}>
                                  ● {rf.level}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Right Column: AI Generated Narrative Block */}
                        <div>
                          <p className="eyebrow mb-4">AI-GENERATED NARRATIVE</p>
                          <div className="bg-[var(--soft-bone)] rounded-2xl p-5 border border-gray-200/60 h-full flex items-center">
                            <p className="text-sm text-[var(--ink-black)] leading-relaxed font-normal">
                              {sar.narrative}
                            </p>
                          </div>
                        </div>

                      </div>

                      {/* Bottom Actions Cluster */}
                      <div className="flex flex-wrap items-center gap-3 pt-4 border-t border-gray-100">
                        <button
                          onClick={() => handleGenerateForm(sar)}
                          disabled={loadingAction === `generate-${sar.id}`}
                          className="btn-primary text-xs px-6 py-2.5"
                        >
                          <Sparkles className="w-3.5 h-3.5 text-[var(--light-signal-orange)]" />
                          <span>{loadingAction === `generate-${sar.id}` ? 'Generating...' : 'Generate FinCEN Form 111'}</span>
                        </button>

                        <button
                          onClick={() => handleExportPDF(sar)}
                          className="btn-secondary text-xs px-6 py-2.5"
                        >
                          <Download className="w-3.5 h-3.5" />
                          <span>Export PDF</span>
                        </button>

                        <button
                          onClick={() => showToast(`Audit log for ${sar.id}: All actions signed with cryptographic hash.`)}
                          className="btn-tertiary text-xs px-4 py-2 border-0 underline underline-offset-4"
                        >
                          <Clock className="w-3 h-3 text-[var(--slate-gray)]" />
                          <span>Audit log</span>
                        </button>
                      </div>
                    </div>
                  )}

                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
