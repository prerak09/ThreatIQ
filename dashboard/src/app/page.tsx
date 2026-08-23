'use client';

import { useState, useEffect } from 'react';
import { Play, Square, RotateCcw, Wifi, WifiOff } from 'lucide-react';
import ArenaDashboard from '@/components/ArenaDashboard';

const NAV_LINKS = [
  { id: 'arena', label: 'Arena' },
  { id: 'topology', label: 'Topology' },
  { id: 'xai', label: 'XAI' },
  { id: 'marl', label: 'MARL' },
  { id: 'steering', label: 'Steering' },
  { id: 'constraints', label: 'Constraints' },
  { id: 'federated', label: 'Federated' },
  { id: 'game', label: 'Game Theory' },
  { id: 'zkp', label: 'ZKP' },
];

export default function Page() {
  const [isRunning, setIsRunning] = useState(false);
  const [isConnected, setIsConnected] = useState(false);

  return (
    <div className="min-h-screen relative">
      {/* Ghost Watermark */}
      <div className="ghost-watermark" style={{ top: '120px', right: '-40%' }}>ARENA</div>

      {/* Floating Nav Pill */}
      <nav className="fixed top-6 left-1/2 -translate-x-1/2 z-50 w-full max-w-[1280px] px-10" aria-label="Main navigation">
        <div className="bg-white rounded-full shadow-[0_4px_24px_rgba(0,0,0,0.04)] px-10 py-4 flex items-center justify-between gap-8">
          {/* Logo */}
          <div className="flex items-center gap-3 flex-shrink-0">
            <div className="relative w-8 h-8">
              <div className="absolute left-0 top-0 w-8 h-8 rounded-full bg-[#EB001B]" />
              <div className="absolute left-[30%] top-0 w-8 h-8 rounded-full bg-[#F79E1B]" />
            </div>
            <span className="text-[var(--ink-black)] font-medium text-base">ThreatIQ</span>
          </div>

          {/* Nav Links */}
          <div className="flex items-center gap-8 flex-1 justify-center" role="navigation" aria-label="Main sections">
            {NAV_LINKS.map((link) => (
              <button
                key={link.id}
                className={`px-3 py-1.5 rounded-full font-medium text-sm transition-all ${link.id === 'arena'
                  ? 'bg-[var(--ink-black)] text-white'
                  : 'text-[var(--ink-black)] font-medium hover:text-[var(--slate-gray)]'}`}
                aria-current={link.id === 'arena' ? 'page' : undefined}
              >
                {link.label}
              </button>
            ))}
          </div>

          {/* Connection Chip + Reset */}
          <div className="flex items-center gap-3 flex-shrink-0">
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--success-tint)] text-[var(--success-green)] text-xs font-bold uppercase tracking-wider">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--success-green)]" aria-hidden="true"></span>
              LIVE
            </div>
            <button
              className="w-10 h-10 rounded-full border border-[var(--dust-taupe)] bg-white flex items-center justify-center hover:bg-[var(--canvas-cream)] transition-colors"
              aria-label="Reset simulation"
            >
              <RotateCcw className="w-5 h-5 text-[var(--ink-black)]" />
            </button>
          </div>
        </div>
      </nav>

      {/* Orange Arc from Nav to Stats Bar */}
      <div className="fixed top-6 left-24 w-1.5 h-[calc(100vh-6rem)] bg-gradient-to-b from-[var(--light-signal-orange)] to-transparent pointer-events-none z-10" />

      {/* Page Header + Stats Bar + Main Content */}
      <main className="pt-32 pb-20">
        <div className="container-main">
          {/* Page Header */}
          <header className="mb-16 relative">
            <div className="ghost-watermark" style={{ top: '0', right: '-30%', fontSize: '120px' }}>ARENA</div>
            
            <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-8 relative z-10">
              <div>
                <p className="eyebrow">AUTONOMOUS ADVERSARIAL SIMULATION</p>
                <h1 className="mt-2">ThreatIQ Arena</h1>
                <p className="subline mt-3 max-w-2xl">Enterprise AI Red Team / Blue Team Payment Fraud Simulation</p>
              </div>
              <div className="flex items-center gap-4 flex-wrap">
                <button
                  className={`btn-primary ${isRunning ? 'running' : ''} w-full lg:w-auto`}
                  onClick={() => setIsRunning(!isRunning)}
                >
                  {isRunning ? (
                    <>
                      <Square className="w-5 h-5" /> Stop
                    </>
                  ) : (
                    <>
                      <Play className="w-5 h-5" /> Start Simulation
                    </>
                  )}
                </button>
                <div className="w-12 h-12 rounded-full border border-[var(--dust-taupe)] bg-white flex items-center justify-center">
                  <span className={`w-2.5 h-2.5 rounded-full ${isConnected ? 'bg-[var(--success-green)]' : 'bg-[var(--dust-taupe)]'}`} />
                </div>
              </div>
            </div>
          </header>

          {/* Stats Bar */}
          <div className="card-stadium p-6 lg:px-8 mb-12 flex flex-wrap items-center gap-6 justify-between" role="region" aria-label="Simulation statistics">
            <div className="flex items-baseline gap-1">
              <span className="stat-label">TOTAL ATTACKS</span>
              <span className="stat-value text-[var(--danger-red)] ml-2">128</span>
            </div>
            <div className="w-px h-8 bg-[var(--dust-taupe)]" />
            <div className="flex items-baseline gap-1">
              <span className="stat-label">DETECTED</span>
              <span className="stat-value text-[var(--success-green)] ml-2">89</span>
            </div>
            <div className="w-px h-8 bg-[var(--dust-taupe)]" />
            <div className="flex items-baseline gap-1">
              <span className="stat-label">DETECTION RATE</span>
              <span className="stat-value text-[var(--link-blue)] ml-2">69.5%</span>
            </div>
            <div className="w-px h-8 bg-[var(--dust-taupe)]" />
            <div className="flex items-baseline gap-1">
              <span className="stat-label">LATENCY</span>
              <span className="stat-value ml-2">12.3ms</span>
            </div>
            <div className="w-px h-8 bg-[var(--dust-taupe)]" />
            <div className="flex items-baseline gap-1">
              <span className="stat-label">ROI</span>
              <span className="stat-value text-[var(--success-green)] ml-2">$2,723,200</span>
            </div>
          </div>
        </div>

        {/* Arena Dashboard */}
        <ArenaDashboard 
          isRunning={isRunning} 
          isConnected={isConnected}
          onStart={() => setIsRunning(true)}
          onStop={() => setIsRunning(false)}
        />
      </main>
    </div>
  );
}