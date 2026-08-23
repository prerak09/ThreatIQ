'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Bolt, Shield, ChevronDown } from 'lucide-react';

interface Transaction {
  id: string;
  amount: number;
  attack_type: string;
  attack_vector: string;
  status: 'detected' | 'missed' | 'blocked';
  channel: string;
  timestamp: number;
}

const ATTACK_TYPES = [
  'Synthetic Identity',
  'Multi-Hop CNP',
  'Prompt Injection',
  'Voice Deepfake',
  'Merchant API Abuse',
  'Velocity Evasion',
];

const CHANNELS = ['Ecommerce', 'POS', 'Mobile Wallet', 'CNP', 'P2P'];

function formatAmount(amount: number): string {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0 }).format(amount);
}

function formatTime(ts: number): string {
  return new Date(ts).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function getStatusChip(status: Transaction['status']) {
  const configs = {
    detected: { label: 'DETECTED', className: 'status-chip success' },
    blocked: { label: 'BLOCKED', className: 'status-chip success' },
    missed: { label: 'MISSED', className: 'status-chip danger' },
  };
  const config = configs[status];
  return <span className={config.className}>{config.label}</span>;
}

function TransactionRow({ tx, isNewest }: { tx: Transaction; isNewest: boolean }) {
  const isRed = tx.status === 'missed' || tx.status === 'detected';
  const isBlue = tx.status === 'detected' || tx.status === 'blocked';
  
  return (
    <div className={`card-white-pill p-4 flex items-center gap-4 transition-all ${isNewest ? 'border-l-4 border-[var(--light-signal-orange)]' : ''}`}>
      <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${isRed ? 'bg-[var(--danger-tint)]' : 'bg-[var(--info-tint)]'}`}>
        {isRed ? (
          <Bolt className="w-5 h-5 text-[var(--danger-red)]" />
        ) : (
          <Shield className="w-5 h-5 text-[var(--link-blue)]" />
        )}
      </div>
      <div className="flex-1 min-w-0 flex items-center gap-3">
        <span className="font-medium text-[var(--ink-black)] whitespace-nowrap">{formatAmount(tx.amount)}</span>
        <span className="pill-btn inactive text-xs">{tx.attack_type}</span>
        <span className="px-2 py-0.5 rounded-full border border-[var(--dust-taupe)] text-[var(--slate-gray)] text-xs font-medium">{tx.channel}</span>
      </div>
      <span className="text-[var(--slate-gray)] text-xs font-medium whitespace-nowrap">{formatTime(tx.timestamp)}</span>
      {getStatusChip(tx.status)}
    </div>
  );
}

function FeedColumn({ 
  title, 
  eyebrow, 
  icon: Icon, 
  iconBgClass, 
  transactions, 
  isRed,
  emptyMessage 
}: {
  title: string;
  eyebrow: string;
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
  iconBgClass: string;
  transactions: Transaction[];
  isRed: boolean;
  emptyMessage: string;
}) {
  return (
    <div className="flex-1 min-w-0 flex flex-col">
      <div className="flex items-center gap-3 mb-6">
        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${iconBgClass}`}>
          <Icon className="w-5 h-5" style={{ color: isRed ? 'var(--danger-red)' : 'var(--link-blue)' }} />
        </div>
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h3 className="text-[var(--ink-black)] font-medium text-lg">{title}</h3>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto space-y-3 pr-2">
        {transactions.length === 0 ? (
          <div className="text-center py-12 text-[var(--slate-gray)]">{emptyMessage}</div>
        ) : (
          transactions.map((tx, idx) => (
            <TransactionRow key={tx.id} tx={tx} isNewest={idx === 0} />
          ))
        )}
      </div>
    </div>
  );
}

export interface RedBlueArenaProps {
  isRunning?: boolean;
  isConnected?: boolean;
  onStart?: () => void;
  onStop?: () => void;
}

export default function RedBlueArena({ 
  isRunning = false, 
  isConnected = false,
  onStart,
  onStop 
}: RedBlueArenaProps) {
  const [redTransactions, setRedTransactions] = useState<Transaction[]>([]);
  const [blueTransactions, setBlueTransactions] = useState<Transaction[]>([]);
  const [totalAttacks, setTotalAttacks] = useState(0);
  const [totalDetected, setTotalDetected] = useState(0);
  const [totalBlocked, setTotalBlocked] = useState(0);
  const [avgResponse, setAvgResponse] = useState(11.8);

  // Simulate live transactions
  useEffect(() => {
    if (!isRunning) return;

    const interval = setInterval(() => {
      const isFraud = Math.random() < 0.6;
      const attackType = ATTACK_TYPES[Math.floor(Math.random() * ATTACK_TYPES.length)];
      const channel = CHANNELS[Math.floor(Math.random() * CHANNELS.length)];
      const amount = Math.random() * 50000 + 5;
      
      let status: Transaction['status'];
      if (isFraud) {
        const detected = Math.random() < 0.69;
        status = detected ? 'detected' : 'missed';
      } else {
        status = 'blocked';
      }

      const tx: Transaction = {
        id: `TXN-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`,
        amount,
        attack_type: attackType,
        attack_vector: attackType,
        status,
        channel,
        timestamp: Date.now(),
      };

      if (isFraud || status !== 'blocked') {
        setRedTransactions(prev => [tx, ...prev].slice(0, 20));
      }
      if (status === 'detected' || status === 'blocked') {
        setBlueTransactions(prev => [tx, ...prev].slice(0, 20));
      }

      setTotalAttacks(prev => prev + 1);
      if (status === 'detected') setTotalDetected(prev => prev + 1);
      if (status === 'blocked') setTotalBlocked(prev => prev + 1);
      
      // Simulate response time variation
      setAvgResponse(prev => Math.max(5, Math.min(25, prev + (Math.random() - 0.5) * 2)));
    }, 1500);

    return () => clearInterval(interval);
  }, [isRunning]);

  return (
    <div className="card-stadium p-8 relative overflow-hidden">
      {/* Orange arc connecting headers */}
      <div className="absolute top-8 left-1/2 -translate-x-1/2 w-1.5 h-[calc(100%-2rem)] bg-gradient-to-b from-[var(--light-signal-orange)] to-transparent pointer-events-none" />
      
      <div className="flex flex-col lg:flex-row gap-8 relative z-10">
        {/* Red Team Column */}
        <FeedColumn
          title="Attack Stream"
          eyebrow="RED TEAM"
          icon={Bolt}
          iconBgClass="bg-[var(--danger-tint)]"
          transactions={redTransactions}
          isRed={true}
          emptyMessage="No attack transactions yet"
        />

        {/* VS Divider */}
        <div className="hidden lg:flex flex-col items-center justify-center px-4 relative">
          <div className="w-px h-full bg-[var(--dust-taupe)]" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
            <div className="w-14 h-14 rounded-full bg-white border-2 border-[var(--ink-black)] flex items-center justify-center shadow-level-2 z-10">
              <span className="text-[var(--ink-black)] font-medium text-sm">VS</span>
            </div>
          </div>
        </div>

        {/* Blue Team Column */}
        <FeedColumn
          title="Defense Stream"
          eyebrow="BLUE TEAM"
          icon={Shield}
          iconBgClass="bg-[var(--info-tint)]"
          transactions={blueTransactions}
          isRed={false}
          emptyMessage="No defense actions yet"
        />

        {/* Footer Stats */}
        <div className="lg:col-span-3 mt-8 pt-6 border-t border-[var(--dust-taupe)] flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-1">
            <span className="stat-label">Attacks/min</span>
            <span className="stat-value ml-2">{totalAttacks}</span>
          </div>
          <div className="w-px h-8 bg-[var(--dust-taupe)]" />
          <div className="flex items-center gap-1">
            <span className="stat-label">Block rate</span>
            <span className="stat-value text-[var(--success-green)] ml-2">
              {totalAttacks > 0 ? Math.round(((totalDetected + totalBlocked) / totalAttacks) * 100) : 0}%
            </span>
          </div>
          <div className="w-px h-8 bg-[var(--dust-taupe)]" />
          <div className="flex items-center gap-1">
            <span className="stat-label">Avg response</span>
            <span className="stat-value ml-2">{avgResponse.toFixed(1)}ms</span>
          </div>
        </div>
      </div>
    </div>
  );
}