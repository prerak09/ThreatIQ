'use client';

import React from 'react';
import { 
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

export const TABS = [
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
}

export default function ArenaDashboard({ 
  activeTab, 
  onSelectTab, 
  isRunning, 
  isConnected, 
  onStart, 
  onStop 
}: ArenaDashboardProps) {
  return (
    <div className="w-full">
      {/* Tab Navigation Pill Bar */}
      <div className="mb-10 flex items-center justify-center">
        <div 
          className="flex items-center gap-1.5 bg-white p-2 rounded-full shadow-level-1 border border-[rgba(20,20,19,0.06)] overflow-x-auto max-w-full" 
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
                className={`flex items-center gap-2 px-4 py-2.5 rounded-full font-medium text-sm whitespace-nowrap transition-all duration-200 ${
                  isActive
                    ? 'bg-[var(--ink-black)] text-white shadow-level-1'
                    : 'text-[var(--slate-gray)] hover:text-[var(--ink-black)] hover:bg-[var(--lifted-cream)]'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-[var(--light-signal-orange)]' : 'text-current'}`} aria-hidden="true" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Tab Panel Viewports */}
      <div className="relative">
        <div
          role="tabpanel"
          id={`${activeTab}-panel`}
          aria-labelledby={`${activeTab}-tab`}
          className="animate-in fade-in duration-300"
        >
          {activeTab === 'arena' && (
            <RedBlueArena 
              isRunning={isRunning} 
              isConnected={isConnected}
              onStart={onStart}
              onStop={onStop}
            />
          )}
          {activeTab === 'topology' && <TopologyGraph />}
          {activeTab === 'marl' && <MARLStatus />}
          {activeTab === 'xai' && <ExplainabilityPanel />}
          {activeTab === 'steering' && <SteeringPanel />}
          {activeTab === 'constraints' && <ConstraintPanel />}
          {activeTab === 'federated' && <FederatedLearningPanel />}
          {activeTab === 'game' && <GameTheoryPanel />}
          {activeTab === 'zkp' && <ZKPPanel />}
          {activeTab === 'sar' && <SARPanel />}
        </div>
      </div>
    </div>
  );
}
