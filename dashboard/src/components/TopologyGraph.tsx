'use client';

import { useState, useEffect, useCallback } from 'react';
import { ChevronLeft, ChevronRight, Search, ZoomIn, ZoomOut, Target, ExternalLink, Network, RefreshCw } from 'lucide-react';
import { 
  ReactFlow, 
  Background, 
  Controls, 
  MiniMap, 
  addEdge, 
  Connection, 
  applyNodeChanges, 
  applyEdgeChanges 
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { api } from '@/lib/api';

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
  return 2 + (risk || 0) * 3;
}

const MOCK_NODES = [
  { id: 'user-1', type: 'graphNode', position: { x: 100, y: 150 }, data: { id: 'user-1', type: 'user', label: 'USR-001234', risk: 0.92, total_txn: 142, account_age: '2 days' } },
  { id: 'user-2', type: 'graphNode', position: { x: 450, y: 100 }, data: { id: 'user-2', type: 'user', label: 'USR-005678', risk: 0.87, total_txn: 89, account_age: '5 days' } },
  { id: 'device-1', type: 'graphNode', position: { x: 280, y: 280 }, data: { id: 'device-1', type: 'device', label: 'DEV-a3f2c1', risk: 0.95, os: 'Android 14', browser: 'Chrome' } },
  { id: 'card-1', type: 'graphNode', position: { x: 550, y: 260 }, data: { id: 'card-1', type: 'card', label: '****4521', risk: 0.88, issuer: 'Tier-1 Bank', bin: '541288' } },
  { id: 'ip-1', type: 'graphNode', position: { x: 120, y: 400 }, data: { id: 'ip-1', type: 'ip', label: '192.168.1.100', risk: 0.72, asn: 'AS12345 (Tor)', country: 'DE' } },
  { id: 'merchant-1', type: 'graphNode', position: { x: 620, y: 420 }, data: { id: 'merchant-1', type: 'merchant', label: 'MERCH-001', risk: 0.12, mcc: '5411', name: 'Global Mart' } },
];

const MOCK_EDGES = [
  { id: 'e1', source: 'user-1', target: 'device-1', type: 'graphEdge', data: { isFraud: true, amount: 4500 } },
  { id: 'e2', source: 'user-2', target: 'device-1', type: 'graphEdge', data: { isFraud: true, amount: 3200 } },
  { id: 'e3', source: 'user-1', target: 'card-1', type: 'graphEdge', data: { isFraud: true, amount: 4500 } },
  { id: 'e4', source: 'device-1', target: 'ip-1', type: 'graphEdge', data: { isFraud: true, amount: 0 } },
  { id: 'e5', source: 'user-1', target: 'merchant-1', type: 'graphEdge', data: { isFraud: true, amount: 4500 } },
  { id: 'e6', source: 'user-2', target: 'merchant-1', type: 'graphEdge', data: { isFraud: false, amount: 1200 } },
];

function GraphNodeComponent(props: any) {
  const { data } = props;
  const { id, type, label, risk } = data || {};
  const riskColor = getRiskColor(risk || 0);
  const ringWidth = getRingWidth(risk || 0);
  const isHighRisk = (risk || 0) > 0.7;

  return (
    <div className="relative group cursor-pointer">
      <div className="flex flex-col items-center" style={{ transform: 'translate(-50%, -50%)', width: '84px' }}>
        <div
          className="relative"
          style={{
            width: '78px',
            height: '78px',
            borderRadius: '50%',
            border: `${ringWidth}px solid ${riskColor}`,
            background: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 16px rgba(0,0,0,0.10)',
            transition: 'transform 0.2s ease',
          }}
        >
          <span className="text-3xl">{NODE_ICONS[type] || '👤'}</span>
          {isHighRisk && (
            <div className="absolute -top-1.5 -right-1.5 w-6 h-6 rounded-full bg-[var(--danger-red)] flex items-center justify-center shadow-sm">
              <span className="text-white text-[10px] font-bold">{Math.round((risk || 0) * 100)}%</span>
            </div>
          )}
        </div>
        <p className="text-[var(--ink-black)] font-semibold text-xs mt-2 text-center max-w-[90px] truncate bg-white/90 px-2 py-0.5 rounded-full shadow-sm">
          {label || id}
        </p>
      </div>
    </div>
  );
}

function GraphEdgeComponent(props: any) {
  const isFraud = props.data?.isFraud;
  return (
    <path
      stroke={isFraud ? '#F37338' : 'var(--dust-taupe)'}
      strokeWidth={isFraud ? 2.5 : 1.5}
      strokeDasharray={isFraud ? '5 5' : '0'}
      fill="none"
      style={{
        filter: isFraud ? 'drop-shadow(0 0 4px rgba(243,115,56,0.6))' : 'none',
        animation: isFraud ? 'dash 1.2s linear infinite' : 'none',
      }}
      d={props.path || ''}
    />
  );
}

const nodeTypes = { graphNode: GraphNodeComponent };
const edgeTypes = { graphEdge: GraphEdgeComponent };
const TIME_RANGES = ['1H', '6H', '24H', '7D'] as const;

export default function TopologyGraph() {
  const [nodes, setNodes] = useState<any[]>(MOCK_NODES);
  const [edges, setEdges] = useState<any[]>(MOCK_EDGES);
  const [selectedNode, setSelectedNode] = useState<any | null>(MOCK_NODES[0].data);
  const [timeRange, setTimeRange] = useState<(typeof TIME_RANGES)[number]>('24H');
  const [isLoading, setIsLoading] = useState(false);

  const fetchGraph = async () => {
    setIsLoading(true);
    try {
      const res = await api.getTopologyGraph();
      if (res && res.nodes && res.nodes.length > 0) {
        setNodes(
          res.nodes.map((n: any, idx: number) => ({
            id: n.id,
            type: 'graphNode',
            position: n.position || { x: 100 + (idx % 3) * 220, y: 120 + Math.floor(idx / 3) * 160 },
            data: n,
          }))
        );
      }
      if (res && res.edges && res.edges.length > 0) {
        setEdges(
          res.edges.map((e: any) => ({
            id: e.id,
            source: e.source,
            target: e.target,
            type: 'graphEdge',
            data: { isFraud: e.is_fraud ?? true, amount: e.amount || 1000 },
          }))
        );
      }
    } catch (e) {
      // fallback to mock graph
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchGraph();
  }, []);

  const onNodesChange = useCallback((changes: any) => setNodes((nds) => applyNodeChanges(changes, nds)), []);
  const onEdgesChange = useCallback((changes: any) => setEdges((eds) => applyEdgeChanges(changes, eds)), []);
  const onConnect = useCallback((params: Connection) => setEdges((eds) => addEdge(params, eds)), []);
  const onNodeClick = useCallback((_: any, node: any) => setSelectedNode(node.data), []);

  return (
    <div className="section-padding relative">
      <div className="ghost-watermark top-10 right-4 text-[140px] pointer-events-none select-none">GRAPH</div>

      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6 mb-10 relative z-10">
        <div>
          <p className="eyebrow">PAYMENT GRAPH TOPOLOGY</p>
          <h2 className="mt-2 text-3xl sm:text-4xl">Fraud Ring Topology</h2>
          <p className="subline mt-1.5 text-base">
            Accounts, devices, cards, IPs, and merchants connected by live transaction edges
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 p-1.5 bg-white rounded-full border border-[var(--dust-taupe)] shadow-sm">
            {TIME_RANGES.map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`pill-btn ${timeRange === range ? 'active' : 'inactive'}`}
              >
                {range}
              </button>
            ))}
          </div>

          <button
            onClick={fetchGraph}
            disabled={isLoading}
            className="w-10 h-10 rounded-full bg-white border border-[var(--dust-taupe)] flex items-center justify-center text-[var(--ink-black)] shadow-sm hover:bg-[var(--canvas-cream)]"
            title="Refresh graph"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Graph Viewport Card */}
      <div className="card-stadium p-6 sm:p-8 border border-[rgba(20,20,19,0.04)] relative overflow-hidden">
        <div className="relative h-[560px] w-full rounded-[28px] overflow-hidden bg-[var(--lifted-cream)]">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            edgeTypes={edgeTypes}
            fitView
          >
            <Background color="var(--dust-taupe)" gap={24} style={{ opacity: 0.3 }} />
            <Controls position="bottom-left" />
            <MiniMap nodeColor={(n: any) => getRiskColor(n.data?.risk || 0)} maskColor="rgba(20,20,19,0.08)" />
          </ReactFlow>

          {/* Legend Pill at Bottom Right */}
          <div className="absolute bottom-5 right-5 bg-white/95 backdrop-blur-md rounded-full px-5 py-2.5 shadow-level-1 flex items-center gap-4 text-xs z-10 border border-[var(--dust-taupe)]/40">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#2E7D32]" />
              <span className="text-[var(--slate-gray)]">Low (&lt;0.3)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#9A3A0A]" />
              <span className="text-[var(--slate-gray)]">Med (0.3–0.7)</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#B3261E]" />
              <span className="text-[var(--slate-gray)]">High (&gt;0.7)</span>
            </div>
            <div className="flex items-center gap-1.5 border-l border-gray-200 pl-3">
              <span className="w-4 h-0.5 bg-[#F37338] inline-block" />
              <span className="text-[var(--slate-gray)]">Fraud Flow</span>
            </div>
          </div>
        </div>

        {/* Selected Entity Details Drawer */}
        {selectedNode && (
          <div className="mt-6 p-6 bg-[var(--lifted-cream)] rounded-3xl border border-[var(--dust-taupe)]/40 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <div
                className="w-14 h-14 rounded-full bg-white flex items-center justify-center text-3xl shadow-sm border-2"
                style={{ borderColor: getRiskColor(selectedNode.risk) }}
              >
                {NODE_ICONS[selectedNode.type] || '👤'}
              </div>
              <div>
                <div className="flex items-center gap-2.5">
                  <span className="text-lg font-bold text-[var(--ink-black)]">{selectedNode.label || selectedNode.id}</span>
                  <span className="status-chip danger text-[10px]">
                    Risk {Math.round((selectedNode.risk || 0.85) * 100)}%
                  </span>
                </div>
                <p className="caption text-xs mt-1">
                  Type: {selectedNode.type} · Connected Fraud Subgraph Cluster
                </p>
              </div>
            </div>

            <div className="flex items-center gap-6 text-xs">
              <div className="bg-white px-4 py-2 rounded-xl border border-[var(--dust-taupe)]/40">
                <span className="text-[var(--slate-gray)]">Attributes:</span>
                <span className="font-semibold ml-2">{JSON.stringify(selectedNode).slice(0, 45)}...</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
