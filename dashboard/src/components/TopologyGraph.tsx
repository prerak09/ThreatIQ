'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { ChevronLeft, ChevronRight, Search, ZoomIn, ZoomOut, Target, ExternalLink } from 'lucide-react';
import { ReactFlow, Background, Controls, MiniMap, Node, Edge, addEdge, Connection, NodeProps, EdgeProps, XYPosition, OnNodesChange, OnEdgesChange, OnConnect, applyNodeChanges, applyEdgeChanges, getConnectedEdges } from 'reactflow';

import 'reactflow/dist/style.css';

interface GraphNode {
  id: string;
  type: 'card' | 'device' | 'ip' | 'merchant' | 'user';
  label: string;
  risk: number;
  data: Record<string, any>;
  position?: XYPosition;
}

interface GraphEdge {
  id: string;
  source: string;
  target: string;
  isFraud: boolean;
  amount: number;
}

const MOCK_NODES: GraphNode[] = [
  { id: 'user-1', type: 'user', label: 'USR-001234', risk: 0.92, data: { account_age: '2 days', total_txn: 142 }, position: { x: 100, y: 150 } },
  { id: 'user-2', type: 'user', label: 'USR-005678', risk: 0.87, data: { account_age: '5 days', total_txn: 89 }, position: { x: 400, y: 100 } },
  { id: 'device-1', type: 'device', label: 'DEV-a3f2c1', risk: 0.95, data: { os: 'Android 14', browser: 'Chrome' }, position: { x: 250, y: 300 } },
  { id: 'card-1', type: 'card', label: '****4521', risk: 0.88, data: { bin: '4111', issuer: 'Bank A' }, position: { x: 500, y: 250 } },
  { id: 'ip-1', type: 'ip', label: '192.168.1.100', risk: 0.72, data: { asn: 'AS12345', country: 'US' }, position: { x: 100, y: 400 } },
  { id: 'merchant-1', type: 'merchant', label: 'MERCH-001', risk: 0.1, data: { mcc: '5411', name: 'Quick Mart' }, position: { x: 600, y: 400 } },
];

const MOCK_EDGES: GraphEdge[] = [
  { id: 'e1', source: 'user-1', target: 'device-1', isFraud: true, amount: 4500 },
  { id: 'e2', source: 'user-2', target: 'device-1', isFraud: true, amount: 3200 },
  { id: 'e3', source: 'user-1', target: 'card-1', isFraud: true, amount: 4500 },
  { id: 'e4', source: 'device-1', target: 'ip-1', isFraud: true, amount: 0 },
  { id: 'e5', source: 'user-1', target: 'merchant-1', isFraud: true, amount: 4500 },
  { id: 'e6', source: 'user-2', target: 'merchant-1', isFraud: false, amount: 1200 },
];

const NODE_COLORS = {
  user: { low: '#2E7D32', mid: '#9A3A0A', high: '#B3261E' },
  device: { low: '#2E7D32', mid: '#9A3A0A', high: '#B3261E' },
  ip: { low: '#2E7D32', mid: '#9A3A0A', high: '#B3261E' },
  card: { low: '#2E7D32', mid: '#9A3A0A', high: '#B3261E' },
  merchant: { low: '#2E7D32', mid: '#9A3A0A', high: '#B3261E' },
};

const NODE_ICONS: Record<string, string> = {
  user: '👤',
  device: '📱',
  ip: '🌐',
  card: '💳',
  merchant: '🏪',
};

function getRiskColor(risk: number): string {
  if (risk < 0.3) return '#2E7D32';
  if (risk < 0.7) return '#9A3A0A';
  return '#B3261E';
}

function getRingWidth(risk: number): number {
  return 2 + risk * 3;
}

function GraphNodeComponent({ data }: NodeProps<GraphNode>) {
  const { id, type, label, risk, data: nodeData } = data;
  const riskColor = getRiskColor(risk);
  const ringWidth = getRingWidth(risk);
  const isHighRisk = risk > 0.7;

  return (
    <div className="relative group">
      <div 
        className="flex flex-col items-center"
        style={{ 
          transform: 'translate(-50%, -50%)',
          width: '88px'
        }}
      >
        <div 
          className="relative"
          style={{
            width: '88px',
            height: '88px',
            borderRadius: '50%',
            border: `${ringWidth}px solid ${riskColor}`,
            background: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 16px rgba(0,0,0,0.1)',
            transition: 'transform 0.2s ease',
          }}
        >
          <span className="text-3xl">{NODE_ICONS[type] || '❓'}</span>
          {isHighRisk && (
            <div className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-[var(--danger-red)] flex items-center justify-center">
              <span className="text-white text-xs font-bold">{Math.round(risk * 100)}%</span>
            </div>
          )}
        </div>
        <p className="text-[var(--ink-black)] font-medium text-xs mt-2 text-center max-w-[100px] truncate">{label}</p>
        {isHighRisk && (
          <button
            className="satellite-btn absolute -bottom-6 left-1/2 -translate-x-1/2 opacity-0 group-hover:opacity-100 transition-opacity z-10"
            aria-label={`Expand ${label} details`}
            onClick={(e) => { e.stopPropagation(); console.log('Expand', id); }}
          >
            <ExternalLink className="w-5 h-5 text-[var(--ink-black)]" />
          </button>
        )}
      </div>
    </div>
  );
}

function GraphEdgeComponent({ edge }: EdgeProps<GraphEdge>) {
  const isFraud = edge.data?.isFraud;
  return (
    <path
      stroke={isFraud ? '#F37338' : 'var(--dust-taupe)'}
      strokeWidth={isFraud ? 2 : 1.5}
      strokeDasharray={isFraud ? '4 4' : '0'}
      fill="none"
      style={{
        filter: isFraud ? 'drop-shadow(0 0 4px #F37338)' : 'none',
        animation: isFraud ? 'dash 1s linear infinite' : 'none',
      }}
      d={edge.path || ''}
    />
  );
}

const TIME_RANGES = ['1H', '6H', '24H', '7D'] as const;

export default function TopologyGraph() {
  const [nodes, setNodes] = useState(MOCK_NODES);
  const [edges, setEdges] = useState(MOCK_EDGES);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [timeRange, setTimeRange] = useState<TIME_RANGES[number]>('24H');
  const [viewport, setViewport] = useState({ x: 0, y: 0, zoom: 1 });

  const onNodesChange = useCallback((changes: any) => setNodes((nds) => applyNodeChanges(changes, nds)), []);
  const onEdgesChange = useCallback((changes: any) => setEdges((eds) => applyEdgeChanges(changes, eds)), []);
  const onConnect = useCallback((params: Connection) => setEdges((eds) => addEdge(params, eds)), []);
  const onNodeClick = useCallback((_: any, node: Node<GraphNode>) => setSelectedNode(node.data), []);
  const onPaneClick = useCallback(() => setSelectedNode(null), []);

  const onZoom = useCallback((_, v: any) => setViewport(v), []);
  const onMove = useCallback((_, v: any) => setViewport(v), []);

  return (
    <div className="card-stadium p-8 relative overflow-hidden">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-6">
        <div>
          <p className="eyebrow">PAYMENT NETWORK</p>
          <h2 className="mt-1">Fraud Topology</h2>
          <p className="subline mt-1">Accounts, devices, cards, IPs and merchants connected by live transaction flow</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {TIME_RANGES.map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                timeRange === range
                  ? 'bg-[var(--ink-black)] text-white'
                  : 'text-[var(--slate-gray)] hover:text-[var(--ink-black)]'
              }`}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      <div className="relative h-[640px] w-full">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          onPaneClick={onPaneClick}
          onViewportChange={({ x, y, zoom }) => setViewport({ x, y, zoom })}
          viewport={viewport}
          fitView={false}
          attributionPosition="bottom-right"
          nodeTypes={{
            graphNode: GraphNodeComponent,
          }}
          edgeTypes={{
            graphEdge: GraphEdgeComponent,
          }}
        >
          <Background 
            color="var(--dust-taupe)" 
            gap={24} 
            style={{ opacity: 0.3 }} 
          />
          <Controls 
            position="bottom-right" 
            showZoom={true}
            showFitView={true}
            showInteractive={true}
          />
          <MiniMap 
            nodeColor={(node) => getRiskColor(node.data.risk)} 
            maskColor="rgba(20,20,19,0.1)" 
          />
        </ReactFlow>

        {/* Legend */}
        <div className="absolute bottom-4 left-4 bg-[var(--lifted-cream)] rounded-[20px] p-4 shadow-level-1 flex items-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full border-2 border-[#2E7D32] flex items-center justify-center bg-white" />
            <span className="text-[var(--slate-gray)]">Low Risk (<0.3)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full border-2 border-[#9A3A0A] flex items-center justify-center bg-white" />
            <span className="text-[var(--slate-gray)]">Med Risk (0.3-0.7)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full border-2 border-[#B3261E] flex items-center justify-center bg-white" />
            <span className="text-[var(--slate-gray)]">High Risk (>0.7)</span>
          </div>
          <div className="flex items-center gap-2 ml-4 border-l border-[var(--dust-taupe)] pl-4">
            <div className="w-6 h-1 rounded-full bg-[#F37338] border-t-2 border-dashed" />
            <span className="text-[var(--slate-gray)]">Fraud Flow</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-1 rounded-full bg-[var(--dust-taupe)]" />
            <span className="text-[var(--slate-gray)]">Legit Flow</span>
          </div>
        </div>

        {/* Side Detail Card */}
        {selectedNode && (
          <div className="absolute right-4 top-4 bottom-4 w-80 bg-white rounded-[40px] p-6 shadow-level-2 overflow-y-auto">
            <div className="flex items-center gap-3 mb-4">
              <div className={`w-16 h-16 rounded-full border-3 flex items-center justify-center bg-white`} style={{ borderColor: getRiskColor(selectedNode.risk) }}>
                <span className="text-4xl">{NODE_ICONS[selectedNode.type] || '❓'}</span>
              </div>
              <div>
                <p className="text-[var(--ink-black)] font-medium text-lg">{selectedNode.label}</p>
                <p className="text-[var(--slate-gray)] text-sm capitalize">{selectedNode.type}</p>
              </div>
            </div>
            
            <div className="mb-4">
              <div className="relative w-full h-16 mb-4">
                <svg viewBox="0 0 100 100" className="w-full h-full">
                  <circle 
                    cx="50" cy="50" r="40" 
                    stroke="#E8E2DA" strokeWidth="8" fill="none" 
                  />
                  <circle 
                    cx="50" cy="50" r="40" 
                    stroke={getRiskColor(selectedNode.risk)} 
                    strokeWidth="8" 
                    fill="none" 
                    strokeDasharray={`${selectedNode.risk * 251.2} 251.2`}
                    strokeLinecap="round"
                    transform="rotate(-90 50 50)"
                    className="transition-all duration-500"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-2xl font-medium text-[var(--ink-black)]">{Math.round(selectedNode.risk * 100)}%</span>
                </div>
              </div>
              <p className="text-[var(--slate-gray)] text-xs uppercase tracking-wider text-center">RISK SCORE</p>
            </div>

            <div className="space-y-3 mb-6">
              {Object.entries(selectedNode.data).map(([key, value]) => (
                <div key={key} className="flex justify-between py-2 border-b border-[var(--dust-taupe)]">
                  <span className="text-[var(--slate-gray)] text-sm capitalize">{key.replace(/_/g, ' ')}</span>
                  <span className="font-medium text-[var(--ink-black)] text-sm">{value}</span>
                </div>
              ))}
            </div>

            <button className="btn-secondary w-full">
              <ExternalLink className="w-4 h-4" /> View Transactions
            </button>
          </div>
        )}
      </div>
    </div>
  );
}