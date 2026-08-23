'use client';

import React, { useState, useCallback } from 'react';
import { Shield, Network, Brain, Bot, Lock, Layers, Settings, Zap, Gamepad2, Key, Search, Layers as LayersIcon } from 'lucide-react';
import RedBlueArena from './RedBlueArena';
import AttackMatrix from './AttackMatrix';
import DefenseMetrics from './DefenseMetrics';
import AttackInjection from './AttackInjection';
import TopologyGraph from './TopologyGraph';
import SARPanel from './SARPanel';
import ExplainabilityPanel from './ExplainabilityPanel';
import MARLStatus from './MARLStatus';
import SteeringPanel from './SteeringPanel';
import ConstraintPanel from './ConstraintPanel';
import FederatedLearningPanel from './FederatedLearningPanel';
import GameTheoryPanel from './GameTheoryPanel';
import ZKPPanel from './ZKPPanel';

const TABS = [
  { id: 'arena', label: 'Arena', icon: Shield },
  { id: 'topology', label: 'Topology', icon: Network },
  { id: 'xai', label: 'XAI', icon: Search },
  { id: 'marl', label: 'MARL', icon: Bot },
  { id: 'steering', label: 'Steering', icon: Layers },
  { id: 'constraints', label: 'Constraints', icon: Lock },
  { id: 'federated', label: 'Federated', icon: LayersIcon },
  { id: 'game', label: 'Game Theory', icon: Gamepad2 },
  { id: 'zkp', label: 'ZKP', icon: Key },
] as const;

type TabId = typeof TABS[number]['id'];

const tabComponents: Record<TabId, React.ComponentType<any>> = {
  arena: RedBlueArena,
  topology: TopologyGraph,
  xai: ExplainabilityPanel,
  marl: MARLStatus,
  steering: SteeringPanel,
  constraints: ConstraintPanel,
  federated: FederatedLearningPanel,
  game: GameTheoryPanel,
  zkp: ZKPPanel,
};

interface ArenaDashboardProps {
  isRunning: boolean;
  isConnected: boolean;
  onStart: () => void;
  onStop: () => void;
}

export default function ArenaDashboard({ isRunning, isConnected, onStart, onStop }: ArenaDashboardProps) {
  const [activeTab, setActiveTab] = useState<TabId>('arena');

  return (
    <div className="section-padding">
      {/* Tab Navigation */}
      <div className="mb-12">
        <div className="flex items-center gap-2 bg-[var(--lifted-cream)] rounded-full p-2 shadow-level-1 w-fit mx-auto" role="tablist" aria-label="Dashboard tabs">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              role="tab"
              aria-selected={activeTab === tab.id}
              aria-controls={`${tab.id}-panel`}
              id={`${tab.id}-tab`}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-full font-medium text-sm transition-all ${
                activeTab === tab.id
                  ? 'bg-[var(--ink-black)] text-white shadow-level-1'
                  : 'text-[var(--slate-gray)] hover:text-[var(--ink-black)]'
              }`}
            >
              <tab.icon className="w-4 h-4" aria-hidden="true" />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Tab Panels */}
      <div className="relative">
        {/* Orange arc connecting tabs to content */}
        <div className="absolute left-24 top-0 bottom-0 w-1.5 bg-gradient-to-b from-[var(--light-signal-orange)] to-transparent pointer-events-none" />
        
        <div className="container-main">
          {TABS.map((tab) => (
            <div
              key={tab.id}
              role="tabpanel"
              id={`${tab.id}-panel`}
              aria-labelledby={`${tab.id}-tab`}
              hidden={activeTab !== tab.id}
              className={activeTab === tab.id ? 'block' : 'hidden'}
            >
              {tab.id === 'arena' && (
                <RedBlueArena 
                  isRunning={isRunning} 
                  isConnected={isConnected}
                  onStart={onStart}
                  onStop={onStop}
                />
              )}
              {tab.id === 'topology' && <TopologyGraph />}
              {tab.id === 'xai' && <ExplainabilityPanel />}
              {tab.id === 'marl' && <MARLStatus />}
              {tab.id === 'steering' && <SteeringPanel />}
              {tab.id === 'constraints' && <ConstraintPanel />}
              {tab.id === 'federated' && <FederatedLearningPanel />}
              {tab.id === 'game' && <GameTheoryPanel />}
              {tab.id === 'zkp' && <ZKPPanel />}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}