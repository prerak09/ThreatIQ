'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  LayoutDashboard,
  Shield, 
  Network, 
  Search, 
  Bot, 
  Layers, 
  Lock, 
  Share2, 
  Gamepad2, 
  Key, 
  FileText 
} from 'lucide-react';
import OverviewPanel from './OverviewPanel';
import RedBlueArena from './RedBlueArena';
import TopologyGraph from './TopologyGraph';
import ExplainabilityPanel from './ExplainabilityPanel';
import MARLStatus from './MARLStatus';
import SteeringPanel from './SteeringPanel';
import ConstraintPanel from './ConstraintPanel';
import FederatedLearningPanel from './FederatedLearningPanel';
import GameTheoryPanel from './GameTheoryPanel';
import ZKPPanel from './ZKPPanel';
import SARPanel from './SARPanel';
import { Transaction } from '@/lib/api';

export const TABS = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard },
  { id: 'arena', label: 'Adversarial Arena', icon: Shield },
  { id: 'topology', label: 'Topology Graph', icon: Network },
  { id: 'marl', label: 'MARL Adversaries', icon: Bot },
  { id: 'xai', label: 'SHAP & XAI', icon: Search },
  { id: 'steering', label: 'Activation Steering', icon: Layers },
  { id: 'constraints', label: 'Diffusion Constraints', icon: Lock },
  { id: 'federated', label: 'Federated Intelligence', icon: Share2 },
  { id: 'game', label: 'Game Theory Solver', icon: Gamepad2 },
  { id: 'zkp', label: 'Zero-Knowledge Proofs', icon: Key },
  { id: 'sar', label: 'FinCEN SAR Queue', icon: FileText },
] as const;

export type TabId = typeof TABS[number]['id'];

interface ArenaDashboardProps {
  activeTab: TabId;
  onSelectTab: (tab: TabId) => void;
  isRunning: boolean;
  isConnected: boolean;
  onStart: () => void;
  onStop: () => void;
  totalProcessed?: number;
  totalAttacks?: number;
  detectedCount?: number;
  detectionRate?: number;
  roiAmount?: number;
  transactions?: Transaction[];
  onAttackInjected?: (injectedCount: number, detected: number, addedRoi: number, newTxs?: Transaction[]) => void;
}

export default function ArenaDashboard({ 
  activeTab, 
  onSelectTab, 
  isRunning, 
  isConnected, 
  onStart, 
  onStop,
  totalProcessed = 0,
  totalAttacks = 0,
  detectedCount = 0,
  detectionRate = 96.4,
  roiAmount = 0,
  transactions = [],
  onAttackInjected,
}: ArenaDashboardProps) {
  const [selectedTxId, setSelectedTxId] = useState<string | undefined>(undefined);

  return (
    <div className="w-full">
      {/* Tab Navigation Pill Bar with Apple Sliding Spring */}
      <div className="mb-10 flex items-center justify-center">
        <div 
          className="flex items-center gap-1 bg-white/95 backdrop-blur-md p-1.5 rounded-full shadow-level-1 border border-[rgba(20,20,19,0.06)] overflow-x-auto max-w-full" 
          role="tablist" 
          aria-label="Dashboard Modules"
        >
          {TABS.map((tab) => {
            const isActive = activeTab === tab.id;
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                role="tab"
                aria-selected={isActive}
                aria-controls={`${tab.id}-panel`}
                id={`${tab.id}-tab`}
                onClick={() => onSelectTab(tab.id)}
                className={`relative flex items-center gap-2 px-4 py-2.5 rounded-full font-medium text-sm whitespace-nowrap transition-colors duration-200 select-none z-10 ${
                  isActive
                    ? 'text-white'
                    : 'text-[var(--slate-gray)] hover:text-[var(--ink-black)]'
                }`}
              >
                {/* Apple Gliding Pill Indicator */}
                {isActive && (
                  <motion.div
                    layoutId="module-active-pill"
                    className="absolute inset-0 bg-[var(--ink-black)] rounded-full -z-10 shadow-sm"
                    transition={{ type: 'spring', stiffness: 420, damping: 32 }}
                  />
                )}

                <Icon 
                  className={`w-4 h-4 transition-colors ${
                    isActive ? 'text-[var(--light-signal-orange)]' : 'text-current'
                  }`} 
                  aria-hidden="true" 
                />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Tab Panel Viewports with Smooth Cross-Fade Animation */}
      <div className="relative">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            role="tabpanel"
            id={`${activeTab}-panel`}
            aria-labelledby={`${activeTab}-tab`}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.24, ease: [0.22, 1, 0.36, 1] }}
          >
            {activeTab === 'overview' && (
              <OverviewPanel
                onSelectTab={onSelectTab}
                isRunning={isRunning}
                isConnected={isConnected}
                totalProcessed={totalProcessed}
                totalAttacks={totalAttacks}
                detectedCount={detectedCount}
                detectionRate={detectionRate}
                roiAmount={roiAmount}
                transactions={transactions}
                onStartSimulation={onStart}
                onStopSimulation={onStop}
              />
            )}
            {activeTab === 'arena' && (
              <RedBlueArena 
                isRunning={isRunning} 
                isConnected={isConnected}
                onStart={onStart}
                onStop={onStop}
                transactions={transactions}
                onAttackInjected={onAttackInjected}
              />
            )}
            {activeTab === 'topology' && <TopologyGraph />}
            {activeTab === 'marl' && <MARLStatus />}
            {activeTab === 'xai' && (
              <ExplainabilityPanel 
                transactions={transactions}
                selectedTxId={selectedTxId}
                onSelectTxId={setSelectedTxId}
              />
            )}
            {activeTab === 'steering' && <SteeringPanel />}
            {activeTab === 'constraints' && <ConstraintPanel />}
            {activeTab === 'federated' && <FederatedLearningPanel />}
            {activeTab === 'game' && <GameTheoryPanel />}
            {activeTab === 'zkp' && <ZKPPanel />}
            {activeTab === 'sar' && <SARPanel />}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
