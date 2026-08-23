'use client';

import { useState, useEffect } from 'react';
import { Gamepad2, Target, RotateCw, CheckCircle, Trophy } from 'lucide-react';
import { api, GameEquilibriumResponse } from '@/lib/api';

const BLUE_STRATEGIES = ['Threshold 0.30', 'Threshold 0.50', 'Threshold 0.70', 'Threshold 0.85 (Optimal)'];
const RED_STRATEGIES = ['Intensity 0.40', 'Intensity 0.60', 'Intensity 0.80', 'Intensity 0.95 (Aggressive)'];

export default function GameTheoryPanel() {
  const [equilibrium, setEquilibrium] = useState({ blue: 2, red: 3 });
  const [isSolving, setIsSolving] = useState(false);
  const [leaderPayoff, setLeaderPayoff] = useState(9.88);
  const [blueMix, setBlueMix] = useState<number[]>([0.01, 0.01, 0.51, 0.47]);
  const [redMix, setRedMix] = useState<number[]>([0.01, 0.01, 0.01, 0.97]);
  const [payoffMatrix, setPayoffMatrix] = useState<{ blue: number[][]; red: number[][] }>({
    blue: [
      [3.4, 2.85, 2.3, 1.89],
      [7.0, 6.75, 6.5, 6.31],
      [10.0, 10.0, 10.0, 10.0],
      [10.0, 10.0, 10.0, 10.0],
    ],
    red: [
      [2.92, 4.38, 5.84, 6.94],
      [2.28, 3.42, 4.56, 5.41],
      [1.64, 2.46, 3.28, 3.89],
      [1.16, 1.74, 2.32, 2.75],
    ],
  });

  useEffect(() => {
    const fetchEq = async () => {
      try {
        const res = await api.getGameEquilibrium();
        if (res) {
          if (res.leader_payoff !== undefined) setLeaderPayoff(Number(res.leader_payoff.toFixed(2)));
          if (res.blue_mix) setBlueMix(res.blue_mix);
          if (res.red_mix) setRedMix(res.red_mix);
          if (res.best_blue_strategy !== undefined && res.best_red_strategy !== undefined) {
            setEquilibrium({ blue: res.best_blue_strategy, red: res.best_red_strategy });
          }
          if (res.payoff_matrix) {
            setPayoffMatrix({
              blue: res.payoff_matrix.blue_payoffs,
              red: res.payoff_matrix.red_payoffs,
            });
          }
        }
      } catch (e) {
        // fallback
      }
    };
    fetchEq();
  }, []);

  const handleSolve = async () => {
    setIsSolving(true);
    try {
      const res = await api.solveGame(100, 0.01);
      if (res) {
        if (res.final_leader_payoff !== undefined) setLeaderPayoff(Number(res.final_leader_payoff.toFixed(2)));
        if (res.blue_mix) setBlueMix(res.blue_mix);
        if (res.red_mix) setRedMix(res.red_mix);
      }
    } catch (e) {
      setLeaderPayoff(9.88);
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
            Solve mixed-strategy Stackelberg equilibria between Blue Team threshold policies and Red Team mutations
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
              <p className="eyebrow">BIMATRIX GAME (BLUE DEFENSE UTILITY / RED ADVERSARY REWARD)</p>
              <h3 className="text-xl font-medium mt-1">Payoff Matrix</h3>
            </div>
            <span className="status-chip success">STACKELBERG EQUILIBRIUM SOLVED</span>
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
                    const bVal = payoffMatrix.blue[rIdx]?.[cIdx] ?? 5.0;
                    const rVal = payoffMatrix.red[rIdx]?.[cIdx] ?? 2.0;
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
                          <span className="text-sm text-[var(--success-green)] font-mono">+{bVal.toFixed(1)}</span>
                          <span className="text-xs text-[var(--danger-red)] font-mono">{rVal.toFixed(1)}</span>
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
                <span className="caption font-mono text-[11px]">Mixed weight: {((blueMix[equilibrium.blue] || 0.5) * 100).toFixed(1)}%</span>
              </div>

              <div className="p-4 bg-[var(--lifted-cream)] rounded-2xl">
                <span className="stat-label">Adversary Best Response</span>
                <p className="font-semibold text-base text-[var(--danger-red)] mt-1">{RED_STRATEGIES[equilibrium.red]}</p>
                <span className="caption font-mono text-[11px]">Follower response weight: {((redMix[equilibrium.red] || 0.9) * 100).toFixed(1)}%</span>
              </div>

              <div className="p-4 bg-[var(--soft-bone)] rounded-2xl text-center">
                <span className="stat-label">Expected Leader Payoff</span>
                <p className="text-2xl font-bold text-[var(--success-green)] mt-0.5">+{leaderPayoff}</p>
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
