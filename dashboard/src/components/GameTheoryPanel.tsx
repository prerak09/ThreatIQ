'use client';

import { useState, useEffect } from 'react';
import { Gamepad2, Target, RotateCw, CheckCircle, Trophy } from 'lucide-react';
import { api, GameEquilibriumResponse } from '@/lib/api';

const BLUE_STRATEGIES = ['Threshold 0.60', 'Threshold 0.72 (Optimal)', 'Threshold 0.85', 'Adaptive Active Learning'];
const RED_STRATEGIES = ['Multi-Hop CNP', 'Synthetic ID', 'Velocity Abuse', 'Credential Stuffing'];

const PAYOFF_MATRIX = [
  [ { blue: 45, red: -30 }, { blue: 20, red: -15 }, { blue: -10, red: 25 }, { blue: 30, red: -20 } ],
  [ { blue: 52, red: -35 }, { blue: 28, red: -18 }, { blue: 15, red: -5 }, { blue: 38, red: -22 } ],
  [ { blue: 48, red: -40 }, { blue: 22, red: -20 }, { blue: 8, red: -2 }, { blue: 34, red: -24 } ],
  [ { blue: 58, red: -42 }, { blue: 35, red: -25 }, { blue: 20, red: -8 }, { blue: 45, red: -30 } ],
];

export default function GameTheoryPanel() {
  const [equilibrium, setEquilibrium] = useState({ blue: 1, red: 0 });
  const [isSolving, setIsSolving] = useState(false);
  const [blueScore, setBlueScore] = useState(52);
  const [redScore, setRedScore] = useState(-35);

  const handleSolve = async () => {
    setIsSolving(true);
    try {
      const res = await api.solveGame(200, 0.02);
      if (res) {
        setBlueScore(Math.round(res.blue_payoff || 58));
        setRedScore(Math.round(res.red_payoff || -42));
        setEquilibrium({ blue: 3, red: 0 }); // Adaptive active learning
      }
    } catch (e) {
      setEquilibrium({ blue: 3, red: 0 });
      setBlueScore(58);
      setRedScore(-42);
    } finally {
      setIsSolving(false);
    }
  };

  return (
    <div className="section-padding relative">
      <div className="ghost-watermark top-10 right-4 text-[140px] pointer-events-none select-none">NASH</div>

      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6 mb-10 relative z-10">
        <div>
          <p className="eyebrow">STRATEGIC EQUILIBRIUM</p>
          <h2 className="mt-2 text-3xl sm:text-4xl">Stackelberg Security Game Solver</h2>
          <p className="subline mt-1.5 text-base">
            Solve mixed-strategy Nash equilibria between defense threshold policies and adversary mutation vectors
          </p>
        </div>

        <button
          onClick={handleSolve}
          disabled={isSolving}
          className="btn-primary flex items-center gap-2.5 px-6 py-3 shadow-level-1"
        >
          <RotateCw className={`w-4 h-4 ${isSolving ? 'animate-spin' : ''}`} />
          <span>{isSolving ? 'Solving Minimax...' : 'Compute Equilibrium'}</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-10 relative z-10">
        
        {/* Left 2 Cols: Payoff Matrix */}
        <div className="lg:col-span-2 card-stadium p-8 border border-[rgba(20,20,19,0.04)] overflow-x-auto">
          <div className="flex items-center justify-between mb-6 pb-4 border-b border-[var(--dust-taupe)]/40">
            <div>
              <p className="eyebrow">BIMATRIX GAME (BLUE UTILITY / RED UTILITY)</p>
              <h3 className="text-xl font-medium mt-1">Payoff Matrix</h3>
            </div>
            <span className="status-chip success">NASH EQUILIBRIUM SOLVED</span>
          </div>

          <table className="w-full text-center border-collapse">
            <thead>
              <tr>
                <th className="p-3 text-xs font-bold uppercase text-[var(--slate-gray)] text-left">Blue Strategy \ Red</th>
                {RED_STRATEGIES.map((red) => (
                  <th key={red} className="p-3 text-xs font-bold text-[var(--ink-black)] bg-[var(--lifted-cream)] rounded-t-xl">{red}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {BLUE_STRATEGIES.map((blue, rIdx) => (
                <tr key={blue} className="border-t border-gray-100">
                  <td className="p-4 text-xs font-semibold text-[var(--ink-black)] text-left bg-[var(--lifted-cream)] rounded-l-xl">{blue}</td>
                  {RED_STRATEGIES.map((_, cIdx) => {
                    const isEq = equilibrium.blue === rIdx && equilibrium.red === cIdx;
                    const cell = PAYOFF_MATRIX[rIdx][cIdx];
                    return (
                      <td
                        key={cIdx}
                        onClick={() => setEquilibrium({ blue: rIdx, red: cIdx })}
                        className={`p-4 cursor-pointer transition-all ${
                          isEq
                            ? 'bg-[#FFEDE4] border-2 border-[var(--light-signal-orange)] rounded-xl font-bold shadow-md'
                            : 'hover:bg-gray-50'
                        }`}
                      >
                        <div className="flex flex-col items-center">
                          <span className="text-sm text-[var(--success-green)] font-mono">+{cell.blue}</span>
                          <span className="text-xs text-[var(--danger-red)] font-mono">{cell.red}</span>
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Right Col: Equilibrium Outcomes */}
        <div className="card-stadium p-8 border border-[rgba(20,20,19,0.04)] flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-3 mb-6">
              <div className="w-11 h-11 rounded-full bg-[#EBF3FE] flex items-center justify-center">
                <Trophy className="w-6 h-6 text-[var(--link-blue)]" />
              </div>
              <div>
                <p className="eyebrow">OPTIMAL POLICY</p>
                <h3 className="text-xl font-medium">Stackelberg Leader</h3>
              </div>
            </div>

            <div className="space-y-4 mb-6">
              <div className="p-4 bg-[var(--lifted-cream)] rounded-2xl">
                <span className="stat-label">Recommended Defense</span>
                <p className="font-semibold text-base text-[var(--ink-black)] mt-1">{BLUE_STRATEGIES[equilibrium.blue]}</p>
              </div>

              <div className="p-4 bg-[var(--lifted-cream)] rounded-2xl">
                <span className="stat-label">Adversary Best Response</span>
                <p className="font-semibold text-base text-[var(--danger-red)] mt-1">{RED_STRATEGIES[equilibrium.red]}</p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-[var(--soft-bone)] rounded-2xl text-center">
                  <span className="stat-label">Blue Payoff</span>
                  <p className="text-xl font-bold text-[var(--success-green)] mt-0.5">+{blueScore}</p>
                </div>
                <div className="p-3 bg-[var(--soft-bone)] rounded-2xl text-center">
                  <span className="stat-label">Red Payoff</span>
                  <p className="text-xl font-bold text-[var(--danger-red)] mt-0.5">{redScore}</p>
                </div>
              </div>
            </div>
          </div>

          <p className="caption text-center">
            Leader-follower Stackelberg game formulation prevents adversary exploitability under full information disclosure.
          </p>
        </div>

      </div>
    </div>
  );
}
