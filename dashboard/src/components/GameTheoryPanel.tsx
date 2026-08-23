'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Target, TrendingUp, TrendingDown } from 'lucide-react';

const BLUE_STRATEGIES = ['Threshold 0.6', 'Threshold 0.72', 'Threshold 0.85', 'Adaptive'];
const RED_STRATEGIES = ['Multi-Hop CNP', 'Synthetic ID', 'Velocity Abuse', 'Credential Stuffing'];

const PAYOFF_DATA = [
  { blue: 'Threshold 0.6', red: 'Multi-Hop CNP', bluePayoff: 45, redPayoff: -30 },
  { blue: 'Threshold 0.6', red: 'Synthetic ID', bluePayoff: 20, redPayoff: -15 },
  { blue: 'Threshold 0.6', red: 'Velocity Abuse', bluePayoff: -10, redPayoff: 25 },
  { blue: 'Threshold 0.6', red: 'Credential Stuffing', bluePayoff: 30, redPayoff: -20 },
  { blue: 'Threshold 0.72', red: 'Multi-Hop CNP', bluePayoff: 52, redPayoff: -35 },
  { blue: 'Threshold 0.72', red: 'Synthetic ID', bluePayoff: 28, redPayoff: -18 },
  { blue: 'Threshold 0.72', red: 'Velocity Abuse', bluePayoff: 15, redPayoff: -5 },
  { blue: 'Threshold 0.72', red: 'Credential Stuffing', bluePayoff: 38, redPayoff: -22 },
  { blue: 'Threshold 0.85', red: 'Multi-Hop CNP', bluePayoff: 48, redPayoff: -40 },
  { blue: 'Threshold 0.85', red: 'Synthetic ID', bluePayoff: 22, redPayoff: -20 },
  { blue: 'Threshold 0.85', red: 'Velocity Abuse', bluePayoff: 8, redPayoff: -2 },
  { blue: 'Threshold 0.85', red: 'Credential Stuffing', bluePayoff: 32, redPayoff: -18 },
  { blue: 'Adaptive', red: 'Multi-Hop CNP', bluePayoff: 40, redPayoff: -25 },
  { blue: 'Adaptive', red: 'Synthetic ID', bluePayoff: 18, redPayoff: -12 },
  { blue: 'Adaptive', red: 'Velocity Abuse', bluePayoff: -5, redPayoff: 10 },
  { blue: 'Adaptive', red: 'Credential Stuffing', bluePayoff: 25, redPayoff: -15 },
];

const CONVERGENCE_DATA = [
  { iteration: 1, blue: 20, red: -10 },
  { iteration: 2, blue: 23, red: -12 },
  { iteration: 3, blue: 26, red: -14 },
  { iteration: 4, blue: 28, red: -15 },
  { iteration: 5, blue: 29, red: -16 },
  { iteration: 6, blue: 30, red: -17 },
  { iteration: 7, blue: 31, red: -17 },
  { iteration: 8, blue: 31.5, red: -17.5 },
  { iteration: 9, blue: 32, red: -18 },
  { iteration: 10, blue: 32, red: -18 },
  { iteration: 11, blue: 32, red: -18 },
  { iteration: 12, blue: 32, red: -18 },
  { iteration: 13, blue: 32, red: -18 },
  { iteration: 14, blue: 32, red: -18 },
  { iteration: 15, blue: 32, red: -18 },
];

function PayoffCell({ value, isBlue, isEquilibrium }: { value: number; isBlue: boolean; isEquilibrium: boolean }) {
  const isPositive = value > 0;
  const bgColor = isEquilibrium 
    ? (isBlue ? 'rgba(56,96,190,0.4)' : 'rgba(207,69,0,0.4)')
    : (isPositive ? (isBlue ? 'rgba(56,96,190,0.2)' : 'rgba(207,69,0,0.2)') : (isBlue ? 'rgba(207,69,0,0.2)' : 'rgba(56,96,190,0.2)'));
  const textColor = (isBlue && isPositive) || (!isBlue && !isPositive) ? 'var(--ink-black)' : 'var(--ink-black)';
  
  return (
    <div 
      className={`relative rounded-[20px] h-[64px] w-full flex items-center justify-center font-medium text-sm ${isEquilibrium ? 'ring-1.5 ring-[var(--ink-black)]' : ''}`}
      style={{ backgroundColor: bgColor, color: textColor }}
    >
      {value > 0 ? '+' : ''}{value}
      {isEquilibrium && (
        <div className="absolute -top-2 -right-2 w-5 h-5 rounded-full bg-[var(--ink-black)] flex items-center justify-center">
          <Target className="w-3 h-3 text-white" />
        </div>
      )}
    </div>
  );
}

export default function GameTheoryPanel() {
  const [equilibrium, setEquilibrium] = useState({ blue: 1, red: 0 });

  return (
    <div className="section-padding">
      <div className="mb-8">
        <p className="eyebrow">STRATEGIC EQUILIBRIUM</p>
        <h2 className="mt-1">Security Game Solver</h2>
        <p className="subline mt-2">Blue commits first · Red best-responds · payoffs in expected fraud loss ($k)</p>
      </div>

      <div className="grid-2 gap-8 mb-8">
        <div className="card-stadium p-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <p className="eyebrow">PAYOFF MATRIX</p>
              <h3 className="mt-1">Blue vs Red Strategies</h3>
            </div>
            <div className="flex items-center gap-2">
              <span className="pill-btn inactive text-xs" style={{ background: 'var(--soft-bone)' }}>LOW</span>
              <span className="pill-btn inactive text-xs" style={{ background: 'rgba(154,58,10,0.12)' }}>MED</span>
              <span className="pill-btn inactive text-xs" style={{ background: 'rgba(207,69,0,0.15)' }}>HIGH</span>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full border-collapse" role="table">
              <thead>
                <tr>
                  <th className="w-40 text-left py-2 px-0" aria-hidden="true"></th>
                  {RED_STRATEGIES.map((s, i) => (
                    <th key={i} className="text-center py-3 px-2 stat-label uppercase tracking-wider">{s}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {BLUE_STRATEGIES.map((blue, bi) => (
                  <tr key={bi}>
                    <td className="text-left py-3 px-0 font-medium text-[var(--ink-black)] text-sm pr-6 w-40">{blue}</td>
                    {RED_STRATEGIES.map((red, ri) => {
                      const data = PAYOFF_DATA.find(d => d.blue === blue && d.red === red);
                      const isEquil = equilibrium.blue === bi && equilibrium.red === ri;
                      return (
                        <td key={ri} className="relative">
                          <PayoffCell value={data?.bluePayoff || 0} isBlue={true} isEquilibrium={isEquil} />
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="caption mt-4">Equilibrium: Blue commits to Threshold 0.72, Red best-responds with Multi-Hop CNP.</p>
        </div>

        <div className="card-stadium p-8">
          <p className="eyebrow mb-4">PAYOFF TRAJECTORY</p>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={CONVERGENCE_DATA} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--dust-taupe)" />
                <XAxis dataKey="iteration" stroke="var(--slate-gray)" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis domain={[-25, 40]} stroke="var(--slate-gray)" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(v) => `${v}k`} />
                <Tooltip contentStyle={{ backgroundColor: 'var(--lifted-cream)', border: '1px solid var(--dust-taupe)', borderRadius: '12px' }} labelStyle={{ color: 'var(--ink-black)', fontWeight: 500 }} formatter={(v: number, name: string) => [`${v}k`, name === 'blue' ? 'Blue Payoff' : 'Red Payoff']} />
                <Line type="monotone" dataKey="blue" stroke="var(--ink-black)" strokeWidth={2} dot={{ r: 4, strokeWidth: 2 }} name="Blue Payoff" />
                <Line type="monotone" dataKey="red" stroke="var(--light-signal-orange)" strokeWidth={2} strokeDasharray="5 5" dot={{ r: 4, strokeWidth: 2 }} name="Red Payoff" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="card-stadium p-8">
        <p className="eyebrow mb-6">EQUILIBRIUM SUMMARY</p>
        <div className="grid-3 gap-4">
          <div className="flex items-center gap-4 p-4 bg-[var(--lifted-cream)] rounded-[20px]">
            <Target className="w-8 h-8 text-[var(--ink-black)]" />
            <div>
              <p className="stat-label">BLUE COMMITS</p>
              <p className="stat-value">Threshold 0.72</p>
            </div>
          </div>
          <div className="flex items-center gap-4 p-4 bg-[var(--lifted-cream)] rounded-[20px]">
            <TrendingUp className="w-8 h-8 text-[var(--light-signal-orange)]" />
            <div>
              <p className="stat-label">RED RESPONDS</p>
              <p className="stat-value text-[var(--light-signal-orange)]">Multi-Hop CNP</p>
            </div>
          </div>
          <div className="flex items-center gap-4 p-4 bg-[var(--lifted-cream)] rounded-[20px]">
            <TrendingDown className="w-8 h-8 text-[var(--ink-black)]" />
            <div>
              <p className="stat-label">EQUILIBRIUM VALUE</p>
              <p className="stat-value">B:+32 / R:-18</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}