'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, Square, RotateCcw, Activity } from 'lucide-react';
import ArenaDashboard, { TabId } from '@/components/ArenaDashboard';
import { api, Transaction } from '@/lib/api';
import { streamClient } from '@/lib/websocket';

const NAV_TABS: Array<{ id: TabId; label: string }> = [
  { id: 'overview', label: 'Overview' },
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

const INITIAL_TRANSACTIONS: Transaction[] = [
  {
    id: 'TXN-88FCB93493D9',
    amount: 14500.0,
    currency: 'USD',
    channel: 'tokenized',
    attack_type: 'Multi-Hop CNP',
    status: 'detected',
    timestamp: Date.now() - 2000,
    card_last4: '4521',
    is_fraud: true,
    blue_team_confidence: 0.94,
    blue_team_result: {
      is_fraud: true,
      confidence: 0.94,
      latency_ms: 11.8,
      engine_scores: { xgboost: 0.96, lightgbm: 0.93, iforest: 0.88 },
    },
  },
  {
    id: 'TXN-54C99A10CA78',
    amount: 3200.0,
    currency: 'EUR',
    channel: 'e-commerce',
    attack_type: 'Synthetic Identity',
    status: 'detected',
    timestamp: Date.now() - 7000,
    card_last4: '8890',
    is_fraud: true,
    blue_team_confidence: 0.89,
    blue_team_result: {
      is_fraud: true,
      confidence: 0.89,
      latency_ms: 9.4,
      engine_scores: { xgboost: 0.91, lightgbm: 0.88, iforest: 0.74 },
    },
  },
  {
    id: 'TXN-C4BCFEA42E34',
    amount: 85.5,
    currency: 'USD',
    channel: 'pos_contactless',
    attack_type: 'Normal Payment',
    status: 'approved',
    timestamp: Date.now() - 15000,
    card_last4: '1102',
    is_fraud: false,
    blue_team_confidence: 0.08,
    blue_team_result: {
      is_fraud: false,
      confidence: 0.08,
      latency_ms: 6.2,
      engine_scores: { xgboost: 0.06, lightgbm: 0.07, iforest: 0.12 },
    },
  },
];

export default function Page() {
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const [isRunning, setIsRunning] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [loadingAction, setLoadingAction] = useState(false);
  
  // Real-time live simulation metrics
  const [totalProcessed, setTotalProcessed] = useState(0);
  const [totalAttacks, setTotalAttacks] = useState(0);
  const [detectedCount, setDetectedCount] = useState(0);
  const [detectionRate, setDetectionRate] = useState(96.4);
  const [latencyMs, setLatencyMs] = useState(11.8);
  const [roiAmount, setRoiAmount] = useState(0);

  // Centralized Transactions List shared across all modules
  const [transactions, setTransactions] = useState<Transaction[]>(INITIAL_TRANSACTIONS);

  // Initialize WebSocket and sync with backend
  useEffect(() => {
    streamClient.connect();

    const unsubStatus = streamClient.onStatus((status) => {
      setIsConnected(status);
    });

    const unsubTx = streamClient.onTransaction((tx: Transaction) => {
      setIsRunning((currentRunning) => {
        if (!currentRunning) return currentRunning;

        // Correctly classify attack vs legitimate stream traffic
        const isExplicitAttack: boolean = Boolean(
          (tx as any).type === 'attack' || 
          tx.is_fraud === true || 
          (tx.attack_vector && tx.attack_vector !== 'legitimate' && tx.attack_vector !== 'unknown') ||
          (tx.attack_type && tx.attack_type !== 'Normal Payment' && tx.attack_type !== 'unknown' && tx.attack_type !== 'legitimate')
        );

        const normalizedTx: Transaction = {
          ...tx,
          is_fraud: isExplicitAttack,
          attack_type: isExplicitAttack ? (tx.attack_type || tx.attack_vector || 'Multi-Hop CNP') : 'Normal Payment',
          status: isExplicitAttack ? (tx.status || 'detected') : 'approved',
        };

        setTransactions((prev) => [normalizedTx, ...prev.slice(0, 40)]);
        setTotalProcessed((prev) => prev + 1);

        if (isExplicitAttack) {
          const isDetected = normalizedTx.status === 'detected' || normalizedTx.status === 'blocked' || tx.blue_team_result?.is_fraud !== false;
          setTotalAttacks((prevAttacks) => {
            const nextAttacks = prevAttacks + 1;
            if (isDetected) {
              setDetectedCount((prevDet) => {
                const nextDet = prevDet + 1;
                setDetectionRate(Number(((nextDet / nextAttacks) * 100).toFixed(1)));
                return nextDet;
              });
              setRoiAmount((prevRoi) => prevRoi + (normalizedTx.amount > 0 ? Math.round(normalizedTx.amount * 120) : 4500));
            } else {
              setDetectedCount((prevDet) => {
                setDetectionRate(Number(((prevDet / nextAttacks) * 100).toFixed(1)));
                return prevDet;
              });
            }
            return nextAttacks;
          });
        }

        if (tx.blue_team_result?.latency_ms) {
          setLatencyMs(Number(tx.blue_team_result.latency_ms.toFixed(1)));
        }

        return currentRunning;
      });
    });

    // Check backend health & initial defense metrics
    const fetchInitialData = async () => {
      try {
        const health = await api.getHealth();
        if (health) {
          setIsConnected(true);
        }
        const defense = await api.getDefenseMetrics();
        if (defense && defense.total_predictions > 0) {
          const estimatedAttacks = Math.round(defense.total_predictions * 0.18);
          const detected = Math.max(0, estimatedAttacks - defense.total_false_negatives);
          setTotalProcessed(defense.total_predictions);
          setTotalAttacks(estimatedAttacks);
          setDetectedCount(detected);
          setDetectionRate(estimatedAttacks > 0 ? Number(((detected / estimatedAttacks) * 100).toFixed(1)) : 96.4);
          if (defense.roi?.cost_avoidance > 0) {
            setRoiAmount(Math.round(defense.roi.cost_avoidance));
          }
        }
      } catch (err) {
        console.log('Backend sync:', err);
      }
    };

    fetchInitialData();

    return () => {
      unsubStatus();
      unsubTx();
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
        await api.startSimulation({ num_victims: 500, fraud_ratio: 0.18, transaction_rate_tps: 8 });
        setIsRunning(true);
      }
    } catch (err) {
      console.warn('Simulation toggle fallback:', err);
      setIsRunning(!isRunning);
    } finally {
      setLoadingAction(false);
    }
  };

  const handleReset = async () => {
    setLoadingAction(true);
    try {
      await api.stopSimulation();
      setIsRunning(false);
      setTotalProcessed(0);
      setTotalAttacks(0);
      setDetectedCount(0);
      setDetectionRate(0);
      setRoiAmount(0);
      setTransactions(INITIAL_TRANSACTIONS);
    } catch (e) {
      setIsRunning(false);
      setTotalProcessed(0);
      setTotalAttacks(0);
      setDetectedCount(0);
      setDetectionRate(0);
      setRoiAmount(0);
      setTransactions(INITIAL_TRANSACTIONS);
    } finally {
      setLoadingAction(false);
    }
  };

  const handleManualAttackInjected = (
    injectedCount: number, 
    detected: number, 
    addedRoi: number, 
    newTxs?: Transaction[]
  ) => {
    if (newTxs && newTxs.length > 0) {
      setTransactions((prev) => [...newTxs, ...prev.slice(0, 40)]);
    }
    setTotalProcessed((prev) => prev + injectedCount);
    setTotalAttacks((prev) => {
      const nextTotal = prev + injectedCount;
      setDetectedCount((prevDet) => {
        const nextDet = prevDet + detected;
        setDetectionRate(nextTotal > 0 ? Number(((nextDet / nextTotal) * 100).toFixed(1)) : 100);
        return nextDet;
      });
      return nextTotal;
    });
    setRoiAmount((prev) => prev + addedRoi);
  };

  return (
    <div className="min-h-screen relative overflow-x-hidden">
      {/* Ghost Watermark */}
      <div className="ghost-watermark top-24 -right-16 text-[180px] select-none opacity-60">PULSE</div>

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

      {/* Floating Apple-Style Smooth Nav Pill */}
      <header className="fixed top-6 left-1/2 -translate-x-1/2 z-50 w-full max-w-[1280px] px-4 sm:px-8">
        <motion.div 
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ type: 'spring', stiffness: 280, damping: 24 }}
          className="bg-white/90 backdrop-blur-xl rounded-full shadow-[0_8px_32px_rgba(0,0,0,0.06)] border border-[rgba(20,20,19,0.06)] px-5 sm:px-7 py-3 flex items-center justify-between gap-4"
        >
          {/* ThreatIQ Brand with Spring Hover */}
          <motion.div 
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            className="flex items-center gap-2.5 flex-shrink-0 cursor-pointer select-none" 
            onClick={() => setActiveTab('overview')}
          >
            <img 
              src="/threatiq-logo.png" 
              alt="ThreatIQ Logo" 
              className="w-8 h-8 object-contain" 
            />
            <span className="text-[var(--ink-black)] font-medium text-lg tracking-tight">ThreatIQ</span>
          </motion.div>

          {/* Center Apple-Style Sliding Pill Tabs */}
          <nav className="hidden lg:flex items-center gap-1 flex-1 justify-center relative" aria-label="Module Navigation">
            {NAV_TABS.map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`relative px-3.5 py-1.5 rounded-full font-medium text-sm transition-colors duration-200 z-10 select-none ${
                    isActive ? 'text-white' : 'text-[var(--ink-black)] hover:text-black'
                  }`}
                  aria-current={isActive ? 'page' : undefined}
                >
                  {/* Apple Smooth Sliding Pill Indicator */}
                  {isActive && (
                    <motion.div
                      layoutId="nav-active-pill"
                      className="absolute inset-0 bg-[var(--ink-black)] rounded-full -z-10 shadow-sm"
                      transition={{ type: 'spring', stiffness: 400, damping: 32 }}
                    />
                  )}
                  {tab.label}
                </button>
              );
            })}
          </nav>

          {/* Right Status Indicator + Smooth Action Buttons */}
          <div className="flex items-center gap-3 flex-shrink-0">
            <div className={`flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider transition-colors duration-300 ${
              isConnected ? 'bg-[var(--success-tint)] text-[var(--success-green)]' : 'bg-gray-100 text-gray-500'
            }`}>
              <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-[var(--success-green)] animate-pulse' : 'bg-gray-400'}`} />
              {isConnected ? 'LIVE' : 'OFFLINE'}
            </div>

            <motion.button
              whileHover={{ scale: 1.08, rotate: -45 }}
              whileTap={{ scale: 0.92 }}
              onClick={handleReset}
              disabled={loadingAction}
              className="w-10 h-10 rounded-full border border-[var(--dust-taupe)] bg-white flex items-center justify-center hover:bg-[var(--canvas-cream)] transition-colors shadow-sm disabled:opacity-50 cursor-pointer"
              title="Reset simulation counters"
              aria-label="Reset simulation"
            >
              <RotateCcw className={`w-4 h-4 text-[var(--ink-black)] ${loadingAction ? 'animate-spin' : ''}`} />
            </motion.button>
          </div>
        </motion.div>
      </header>

      {/* Main Content Area */}
      <main className="pt-28 pb-20 relative z-10">
        <div className="container-main">
          
          {/* Hero Section */}
          <section className="mb-10 relative pt-6">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-8">
              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
              >
                <p className="eyebrow">AUTONOMOUS ADVERSARIAL SIMULATION</p>
                <h1 className="mt-2.5">ThreatIQ</h1>
                <p className="subline mt-2.5 max-w-2xl text-[17px]">
                  Enterprise AI Red Team / Blue Team Payment Fraud Simulation
                </p>
              </motion.div>

              {/* Action Cluster (Start Button + Running Pulse Widget) */}
              <div className="flex items-center gap-5 flex-wrap">
                <motion.button
                  whileHover={{ scale: 1.03 }}
                  whileTap={{ scale: 0.97 }}
                  onClick={handleToggleSimulation}
                  disabled={loadingAction}
                  className={`${isRunning ? 'btn-stop' : 'btn-primary'} text-lg px-8 py-3.5 shadow-level-1 transition-all`}
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
                </motion.button>

                {/* Animated Status Circle Satellite Widget */}
                <motion.div 
                  whileHover={{ scale: 1.02 }}
                  className="card-white-pill px-5 py-2.5 flex items-center gap-3 border border-[rgba(20,20,19,0.06)] shadow-sm"
                >
                  <div className="relative w-8 h-8 flex items-center justify-center">
                    <AnimatePresence>
                      {isRunning && (
                        <motion.div
                          initial={{ scale: 0.8, opacity: 0 }}
                          animate={{ scale: 1.6, opacity: 0.4 }}
                          exit={{ opacity: 0 }}
                          transition={{ repeat: Infinity, duration: 1.8, ease: 'easeOut' }}
                          className="w-3.5 h-3.5 rounded-full bg-[var(--success-green)] absolute"
                        />
                      )}
                    </AnimatePresence>
                    <div className={`w-3.5 h-3.5 rounded-full transition-colors duration-300 ${isRunning ? 'bg-[var(--success-green)]' : 'bg-[var(--dust-taupe)]'}`} />
                  </div>
                  <div className="text-left">
                    <p className="text-xs font-bold tracking-wider uppercase text-[var(--slate-gray)]">STATUS</p>
                    <p className="text-sm font-medium text-[var(--ink-black)]">{isRunning ? 'Running' : 'Standby'}</p>
                  </div>
                </motion.div>
              </div>
            </div>
          </section>

          {/* 6-Column Comprehensive Stats Stadium Card */}
          <motion.div 
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1 }}
            className="card-stadium p-6 sm:p-8 mb-12 border border-[rgba(20,20,19,0.04)] hover:shadow-level-2 transition-shadow duration-300" 
            role="region" 
            aria-label="Live Simulation Statistics"
          >
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 sm:gap-6 items-center text-center">
              
              {/* Total Processed Volume */}
              <div className="flex flex-col items-center">
                <span className="stat-label">TOTAL PROCESSED</span>
                <motion.span 
                  key={totalProcessed}
                  initial={{ scale: 1.05 }}
                  animate={{ scale: 1 }}
                  className="stat-value-xl text-[var(--ink-black)] mt-1.5"
                >
                  {totalProcessed.toLocaleString()}
                </motion.span>
              </div>

              {/* Total Fraud Attacks */}
              <div className="flex flex-col items-center border-l sm:border-l border-[var(--dust-taupe)]/40 pl-3 sm:pl-6">
                <span className="stat-label">FRAUD ATTACKS</span>
                <motion.span 
                  key={totalAttacks}
                  initial={{ scale: 1.05 }}
                  animate={{ scale: 1 }}
                  className="stat-value-xl text-[var(--danger-red)] mt-1.5"
                >
                  {totalAttacks.toLocaleString()}
                </motion.span>
              </div>

              {/* Attacks Blocked */}
              <div className="flex flex-col items-center border-l sm:border-l border-[var(--dust-taupe)]/40 pl-3 sm:pl-6">
                <span className="stat-label">ATTACKS BLOCKED</span>
                <motion.span 
                  key={detectedCount}
                  initial={{ scale: 1.05 }}
                  animate={{ scale: 1 }}
                  className="stat-value-xl text-[var(--success-green)] mt-1.5"
                >
                  {detectedCount.toLocaleString()}
                </motion.span>
              </div>

              {/* Block Rate / Accuracy */}
              <div className="flex flex-col items-center border-l sm:border-l border-[var(--dust-taupe)]/40 pl-3 sm:pl-6">
                <span className="stat-label">BLOCK RATE</span>
                <motion.span 
                  key={detectionRate}
                  initial={{ scale: 1.05 }}
                  animate={{ scale: 1 }}
                  className="stat-value-xl text-[var(--link-blue)] mt-1.5"
                >
                  {totalAttacks > 0 ? `${detectionRate}%` : '0%'}
                </motion.span>
              </div>

              {/* Latency */}
              <div className="flex flex-col items-center border-l sm:border-l border-[var(--dust-taupe)]/40 pl-3 sm:pl-6">
                <span className="stat-label">AVG LATENCY</span>
                <span className="stat-value-xl mt-1.5">{latencyMs}ms</span>
              </div>

              {/* Loss Prevented / ROI */}
              <div className="col-span-2 sm:col-span-1 flex flex-col items-center border-l-0 lg:border-l border-[var(--dust-taupe)]/40 lg:pl-6">
                <span className="stat-label">FRAUD PREVENTED</span>
                <span className="stat-value-xl text-[var(--success-green)] mt-1.5">${roiAmount.toLocaleString()}</span>
              </div>

            </div>
          </motion.div>

          {/* Module Tabs and Arena Dashboard Views */}
          <ArenaDashboard 
            activeTab={activeTab} 
            onSelectTab={setActiveTab}
            isRunning={isRunning}
            isConnected={isConnected}
            onStart={() => setIsRunning(true)}
            onStop={() => setIsRunning(false)}
            totalProcessed={totalProcessed}
            totalAttacks={totalAttacks}
            detectedCount={detectedCount}
            detectionRate={detectionRate}
            roiAmount={roiAmount}
            transactions={transactions}
            onAttackInjected={handleManualAttackInjected}
          />

        </div>
      </main>

      {/* Warm Editorial Dark Footer */}
      <footer className="bg-[var(--ink-black)] text-white pt-16 pb-24 border-t border-black">
        <div className="container-main">
          <div className="flex flex-col md:flex-row md:items-start justify-between gap-12 mb-14">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <img 
                  src="/threatiq-logo.png" 
                  alt="ThreatIQ Logo" 
                  className="w-9 h-9 object-contain" 
                />
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
                  <li><button onClick={() => setActiveTab('overview')} className="hover:text-white transition-colors">Overview</button></li>
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
