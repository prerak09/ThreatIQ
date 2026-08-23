'use client';

import { useState, useEffect, useCallback } from 'react';
import { Play, Square, RotateCcw, Activity } from 'lucide-react';
import ArenaDashboard, { TabId } from '@/components/ArenaDashboard';
import { api, DefenseMetrics, Transaction } from '@/lib/api';
import { streamClient } from '@/lib/websocket';

const NAV_TABS: Array<{ id: TabId; label: string }> = [
  { id: 'arena', label: 'Arena' },
  { id: 'topology', label: 'Topology' },
  { id: 'xai', label: 'XAI' },
  { id: 'marl', label: 'MARL' },
  { id: 'steering', label: 'Steering' },
  { id: 'constraints', label: 'Constraints' },
  { id: 'federated', label: 'Federated' },
  { id: 'game', label: 'Game Theory' },
  { id: 'zkp', label: 'ZKP' },
  { id: 'sar', label: 'SAR' },
];

export default function Page() {
  const [activeTab, setActiveTab] = useState<TabId>('arena');
  const [isRunning, setIsRunning] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [loadingAction, setLoadingAction] = useState(false);
  
  // Real-time live metrics
  const [totalAttacks, setTotalAttacks] = useState(128);
  const [detectedCount, setDetectedCount] = useState(89);
  const [detectionRate, setDetectionRate] = useState(69.5);
  const [latencyMs, setLatencyMs] = useState(12.3);
  const [roiAmount, setRoiAmount] = useState(2723200);

  // Initialize WebSocket and poll defense metrics
  useEffect(() => {
    streamClient.connect();

    const unsubStatus = streamClient.onStatus((status) => {
      setIsConnected(status);
    });

    const unsubTx = streamClient.onTransaction((tx: Transaction) => {
      setTotalAttacks((prev) => prev + 1);
      if (tx.status === 'detected' || tx.status === 'blocked' || tx.blue_team_result?.is_fraud) {
        setDetectedCount((prev) => {
          const next = prev + 1;
          setTotalAttacks((tot) => {
            if (tot > 0) setDetectionRate(Number(((next / tot) * 100).toFixed(1)));
            return tot;
          });
          return next;
        });
        setRoiAmount((prev) => prev + (tx.amount > 0 ? Math.round(tx.amount * 120) : 450));
      }
      if (tx.blue_team_result?.latency_ms) {
        setLatencyMs(Number(tx.blue_team_result.latency_ms.toFixed(1)));
      }
    });

    // Check initial health and metrics from backend
    const fetchInitialData = async () => {
      try {
        const health = await api.getHealth();
        if (health) {
          setIsConnected(true);
          setIsRunning(health.simulation_running);
        }
        const defense = await api.getDefenseMetrics();
        if (defense && defense.total_predictions > 0) {
          setTotalAttacks(defense.total_predictions);
          const detected = defense.total_predictions - defense.total_false_negatives;
          setDetectedCount(Math.max(0, detected));
          setDetectionRate(Number((defense.roi?.detection_rate || (detected / defense.total_predictions) * 100).toFixed(1)));
          if (defense.roi?.cost_avoidance > 0) {
            setRoiAmount(Math.round(defense.roi.cost_avoidance));
          }
        }
      } catch (err) {
        console.log('Backend polling initial state:', err);
      }
    };

    fetchInitialData();
    const interval = setInterval(fetchInitialData, 8000);

    return () => {
      unsubStatus();
      unsubTx();
      clearInterval(interval);
      streamClient.disconnect();
    };
  }, []);

  const handleToggleSimulation = async () => {
    setLoadingAction(true);
    try {
      if (isRunning) {
        await api.stopSimulation();
        setIsRunning(false);
      } else {
        await api.startSimulation({ num_victims: 500, fraud_ratio: 0.18, transaction_rate_tps: 12 });
        setIsRunning(true);
      }
    } catch (err) {
      console.warn('Simulation toggle fallback to local simulation:', err);
      setIsRunning(!isRunning);
    } finally {
      setLoadingAction(false);
    }
  };

  const handleReset = async () => {
    setLoadingAction(true);
    try {
      await api.startSimulation({ num_victims: 500, fraud_ratio: 0.15, transaction_rate_tps: 10 });
      setTotalAttacks(0);
      setDetectedCount(0);
      setDetectionRate(0);
      setRoiAmount(0);
      setIsRunning(true);
    } catch (e) {
      setTotalAttacks(0);
      setDetectedCount(0);
      setDetectionRate(0);
    } finally {
      setLoadingAction(false);
    }
  };

  return (
    <div className="min-h-screen relative overflow-x-hidden">
      {/* Ghost Watermark */}
      <div className="ghost-watermark top-24 -right-16 text-[180px] select-none">ARENA</div>

      {/* Decorative SVG Orbital Arcs */}
      <svg className="fixed inset-0 w-full h-full pointer-events-none z-0" xmlns="http://www.w3.org/2000/svg">
        <path
          d="M -100,80 Q 200,30 500,160 T 1200,100 T 1800,240"
          fill="none"
          stroke="var(--light-signal-orange)"
          strokeWidth="1.2"
          strokeDasharray="4 6"
          opacity="0.35"
        />
        <path
          d="M 50,600 Q 400,750 900,550 T 1700,700"
          fill="none"
          stroke="var(--light-signal-orange)"
          strokeWidth="1"
          opacity="0.25"
        />
      </svg>

      {/* Floating Nav Pill (Mastercard Design) */}
      <header className="fixed top-6 left-1/2 -translate-x-1/2 z-50 w-full max-w-[1280px] px-4 sm:px-8">
        <div className="bg-white/95 backdrop-blur-md rounded-full shadow-[0_4px_24px_rgba(0,0,0,0.06)] border border-[rgba(20,20,19,0.06)] px-6 sm:px-8 py-3.5 flex items-center justify-between gap-4">
          
          {/* ThreatIQ Proprietary Inspired Logo Mark */}
          <div className="flex items-center gap-3.5 flex-shrink-0 cursor-pointer" onClick={() => setActiveTab('arena')}>
            <div className="relative w-9 h-7 flex items-center justify-center">
              <svg width="34" height="26" viewBox="0 0 34 26" fill="none" xmlns="http://www.w3.org/2000/svg">
                {/* Left Stadium / Lens (Red Team Signal Rust) */}
                <rect x="1" y="3" width="18" height="20" rx="9" fill="#CF4500" />
                {/* Right Interlocking Lens (Blue Team / Gold Intelligence Core) */}
                <rect x="13" y="3" width="18" height="20" rx="9" fill="#F79E1B" opacity="0.9" style={{ mixBlendMode: 'multiply' }} />
                {/* Satellite Micro Orbit Dot */}
                <circle cx="28" cy="6" r="3" fill="#FFFFFF" stroke="#141413" strokeWidth="1" />
              </svg>
            </div>
            <span className="text-[var(--ink-black)] font-medium text-lg tracking-tight">ThreatIQ</span>
          </div>

          {/* Center Nav Tab Links */}
          <nav className="hidden lg:flex items-center gap-1.5 flex-1 justify-center" aria-label="Module Navigation">
            {NAV_TABS.map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-3.5 py-1.5 rounded-full font-medium text-sm transition-all duration-200 ${
                    isActive
                      ? 'bg-[var(--ink-black)] text-white shadow-sm'
                      : 'text-[var(--ink-black)] hover:bg-[var(--lifted-cream)] hover:text-black'
                  }`}
                  aria-current={isActive ? 'page' : undefined}
                >
                  {tab.label}
                </button>
              );
            })}
          </nav>

          {/* Right Status Indicator + Reset */}
          <div className="flex items-center gap-3 flex-shrink-0">
            <div className={`flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider transition-colors ${
              isConnected ? 'bg-[var(--success-tint)] text-[var(--success-green)]' : 'bg-gray-100 text-gray-500'
            }`}>
              <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-[var(--success-green)] animate-pulse' : 'bg-gray-400'}`} />
              {isConnected ? 'LIVE' : 'OFFLINE'}
            </div>

            <button
              onClick={handleReset}
              disabled={loadingAction}
              className="w-10 h-10 rounded-full border border-[var(--dust-taupe)] bg-white flex items-center justify-center hover:bg-[var(--canvas-cream)] transition-all active:scale-95 disabled:opacity-50"
              title="Reset simulation"
              aria-label="Reset simulation"
            >
              <RotateCcw className={`w-4 h-4 text-[var(--ink-black)] ${loadingAction ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="pt-28 pb-20 relative z-10">
        <div className="container-main">
          
          {/* Hero Section */}
          <section className="mb-10 relative pt-6">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-8">
              <div>
                <p className="eyebrow">AUTONOMOUS ADVERSARIAL SIMULATION</p>
                <h1 className="mt-2.5">ThreatIQ Arena</h1>
                <p className="subline mt-2.5 max-w-2xl text-[17px]">
                  Enterprise AI Red Team / Blue Team Payment Fraud Simulation
                </p>
              </div>

              {/* Action Cluster (Start Button + Running Pulse Widget) */}
              <div className="flex items-center gap-5 flex-wrap">
                <button
                  onClick={handleToggleSimulation}
                  disabled={loadingAction}
                  className={`${isRunning ? 'btn-stop' : 'btn-primary'} text-lg px-8 py-3.5 shadow-level-1`}
                >
                  {isRunning ? (
                    <>
                      <Square className="w-5 h-5 fill-current" /> Stop
                    </>
                  ) : (
                    <>
                      <Play className="w-5 h-5 fill-current" /> Start Simulation
                    </>
                  )}
                </button>

                {/* Animated Status Circle Satellite Widget */}
                <div className="card-white-pill px-5 py-2.5 flex items-center gap-3 border border-[rgba(20,20,19,0.06)]">
                  <div className="relative w-8 h-8 flex items-center justify-center">
                    <div className={`w-3.5 h-3.5 rounded-full ${isRunning ? 'bg-[var(--success-green)] animate-ping absolute' : ''}`} />
                    <div className={`w-3.5 h-3.5 rounded-full ${isRunning ? 'bg-[var(--success-green)]' : 'bg-[var(--dust-taupe)]'}`} />
                  </div>
                  <div className="text-left">
                    <p className="text-xs font-bold tracking-wider uppercase text-[var(--slate-gray)]">STATUS</p>
                    <p className="text-sm font-medium text-[var(--ink-black)]">{isRunning ? 'Running' : 'Standby'}</p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* 5-Column Stats Stadium Card */}
          <div className="card-stadium p-6 sm:p-8 mb-12 border border-[rgba(20,20,19,0.04)]" role="region" aria-label="Live Simulation Statistics">
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-6 sm:gap-8 items-center text-center">
              
              {/* Total Attacks */}
              <div className="flex flex-col items-center">
                <span className="stat-label">TOTAL ATTACKS</span>
                <span className="stat-value-xl text-[var(--danger-red)] mt-1.5">{totalAttacks.toLocaleString()}</span>
              </div>

              {/* Detected */}
              <div className="flex flex-col items-center border-l sm:border-l border-[var(--dust-taupe)]/40 pl-4 sm:pl-8">
                <span className="stat-label">DETECTED</span>
                <span className="stat-value-xl text-[var(--success-green)] mt-1.5">{detectedCount.toLocaleString()}</span>
              </div>

              {/* Detection Rate */}
              <div className="flex flex-col items-center border-l sm:border-l border-[var(--dust-taupe)]/40 pl-4 sm:pl-8">
                <span className="stat-label">DETECTION RATE</span>
                <span className="stat-value-xl text-[var(--link-blue)] mt-1.5">{detectionRate}%</span>
              </div>

              {/* Latency */}
              <div className="flex flex-col items-center border-l sm:border-l border-[var(--dust-taupe)]/40 pl-4 sm:pl-8">
                <span className="stat-label">LATENCY</span>
                <span className="stat-value-xl mt-1.5">{latencyMs}ms</span>
              </div>

              {/* ROI */}
              <div className="col-span-2 sm:col-span-1 flex flex-col items-center border-l-0 lg:border-l border-[var(--dust-taupe)]/40 lg:pl-8">
                <span className="stat-label">ROI</span>
                <span className="stat-value-xl text-[var(--success-green)] mt-1.5">${roiAmount.toLocaleString()}</span>
              </div>

            </div>
          </div>

          {/* Module Tabs and Arena Dashboard Views */}
          <ArenaDashboard 
            activeTab={activeTab} 
            onSelectTab={setActiveTab}
            isRunning={isRunning}
            isConnected={isConnected}
            onStart={() => setIsRunning(true)}
            onStop={() => setIsRunning(false)}
          />

        </div>
      </main>

      {/* Mastercard Warm Editorial Dark Footer */}
      <footer className="bg-[var(--ink-black)] text-white pt-16 pb-24 border-t border-black">
        <div className="container-main">
          <div className="flex flex-col md:flex-row md:items-start justify-between gap-12 mb-14">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="relative w-8 h-6 flex items-center justify-center">
                  <svg width="30" height="22" viewBox="0 0 34 26" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="1" y="3" width="18" height="20" rx="9" fill="#CF4500" />
                    <rect x="13" y="3" width="18" height="20" rx="9" fill="#F79E1B" opacity="0.9" style={{ mixBlendMode: 'screen' }} />
                    <circle cx="28" cy="6" r="3" fill="#FFFFFF" />
                  </svg>
                </div>
                <span className="text-xl font-medium tracking-tight">ThreatIQ</span>
              </div>
              <h2 className="text-white text-2xl font-medium max-w-md leading-snug">
                Autonomous Adversarial Intelligence for Resilient Global Payments.
              </h2>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-10 text-sm">
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-[var(--slate-gray)] mb-4">PLATFORM</p>
                <ul className="space-y-2.5 text-gray-300">
                  <li><button onClick={() => setActiveTab('arena')} className="hover:text-white transition-colors">Adversarial Arena</button></li>
                  <li><button onClick={() => setActiveTab('topology')} className="hover:text-white transition-colors">Graph Topology</button></li>
                  <li><button onClick={() => setActiveTab('marl')} className="hover:text-white transition-colors">MARL Evasion</button></li>
                  <li><button onClick={() => setActiveTab('xai')} className="hover:text-white transition-colors">SHAP & XAI</button></li>
                </ul>
              </div>
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-[var(--slate-gray)] mb-4">DEFENSE</p>
                <ul className="space-y-2.5 text-gray-300">
                  <li><button onClick={() => setActiveTab('steering')} className="hover:text-white transition-colors">Activation Steering</button></li>
                  <li><button onClick={() => setActiveTab('federated')} className="hover:text-white transition-colors">Federated DP-SGD</button></li>
                  <li><button onClick={() => setActiveTab('game')} className="hover:text-white transition-colors">Stackelberg Solver</button></li>
                  <li><button onClick={() => setActiveTab('zkp')} className="hover:text-white transition-colors">ZKP Verification</button></li>
                </ul>
              </div>
              <div>
                <p className="text-xs font-bold uppercase tracking-wider text-[var(--slate-gray)] mb-4">COMPLIANCE</p>
                <ul className="space-y-2.5 text-gray-300">
                  <li><button onClick={() => setActiveTab('sar')} className="hover:text-white transition-colors">FinCEN SAR Filing</button></li>
                  <li><a href="https://backend-production-400c.up.railway.app/docs" target="_blank" rel="noreferrer" className="hover:text-white transition-colors">API Docs (Swagger) ↗</a></li>
                  <li><a href="https://github.com/prerak09/ThreatIQ" target="_blank" rel="noreferrer" className="hover:text-white transition-colors">GitHub Repository ↗</a></li>
                </ul>
              </div>
            </div>
          </div>

          <div className="pt-8 border-t border-gray-800 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[var(--slate-gray)]">
            <p>© 2026 ThreatIQ Platform. Inspired by Mastercard Design System.</p>
            <div className="flex items-center gap-6">
              <span className="pill-btn inactive text-xs text-gray-400 bg-gray-900 border-gray-700">ISO 20022 Compliant</span>
              <span>FastAPI + Next.js + Railway + Vercel</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
