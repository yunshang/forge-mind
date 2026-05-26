"use client";

import { useCallback, useMemo, useRef, useEffect } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
  NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

// Custom node: Contract
function ContractNode({ data }: NodeProps) {
  const isInherited = data.type === "inherited";
  return (
    <div
      className={`px-4 py-3 rounded-lg border-2 font-mono text-sm ${
        isInherited
          ? "bg-gray-800 border-gray-600 text-gray-400"
          : "bg-indigo-950 border-indigo-500 text-indigo-200"
      }`}
    >
      <Handle type="target" position={Position.Top} />
      <div className="font-bold">{String(data.label)}</div>
      <div className="text-xs text-gray-500">{isInherited ? "inherited" : "contract"}</div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}

// Custom node: Function
function FunctionNode({ data }: NodeProps) {
  const isRead = data.node_type === "functionRead";
  return (
    <div
      className={`px-3 py-2 rounded-lg border font-mono text-xs ${
        isRead
          ? "bg-emerald-950/50 border-emerald-500/50 text-emerald-300"
          : "bg-orange-950/50 border-orange-500/50 text-orange-300"
      }`}
    >
      <Handle type="target" position={Position.Top} />
      <div className="font-bold text-sm">{String(data.label)}</div>
      <div className="text-gray-500 mt-1">
        {String(data.visibility)} {data.mutability ? String(data.mutability) : ""}
      </div>
      {Array.isArray(data.params) && data.params.length > 0 && (
        <div className="mt-1 text-gray-600">
          {(data.params as Array<{ type: string; name: string }>).map((p, i) => (
            <div key={i}>{p.type} {p.name}</div>
          ))}
        </div>
      )}
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}

// Custom node: State variable
function StateVarNode({ data }: NodeProps) {
  return (
    <div className="px-3 py-2 rounded-lg border bg-purple-950/50 border-purple-500/50 text-purple-300 font-mono text-xs">
      <Handle type="target" position={Position.Left} />
      <div className="font-bold">{String(data.label)}</div>
      <div className="text-gray-500">{String(data.var_type)} ({String(data.visibility)})</div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

// Custom node: Modifier
function ModifierNode({ data }: NodeProps) {
  return (
    <div className="px-3 py-2 rounded-lg border bg-amber-950/50 border-amber-500/50 text-amber-300 font-mono text-xs">
      <Handle type="target" position={Position.Right} />
      <div className="font-bold">🔒 {String(data.label)}</div>
      <div className="text-gray-500">modifier</div>
      <Handle type="source" position={Position.Left} />
    </div>
  );
}

const nodeTypes = {
  contractNode: ContractNode,
  functionNode: FunctionNode,
  stateVarNode: StateVarNode,
  modifierNode: ModifierNode,
};

interface FlowCanvasProps {
  graphData: {
    nodes: Array<{
      id: string;
      type: string;
      position: { x: number; y: number };
      data: Record<string, unknown>;
    }>;
    edges: Array<{
      id: string;
      source: string;
      target: string;
      type?: string;
      label?: string;
      animated?: boolean;
      style?: Record<string, unknown>;
    }>;
  };
  onExportImage?: (element: HTMLElement | null) => void;
}

export default function FlowCanvas({ graphData, onExportImage }: FlowCanvasProps) {
  const flowRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    if (onExportImage && flowRef.current) {
      onExportImage(flowRef.current);
    }
  }, [graphData, onExportImage]);
  
  const initialNodes: Node[] = useMemo(
    () =>
      (graphData?.nodes || []).map((n) => ({
        id: n.id,
        type: n.type,
        position: n.position,
        data: n.data,
      })),
    [graphData]
  );

  const initialEdges: Edge[] = useMemo(
    () =>
      (graphData?.edges || []).map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        type: (e.type as string) || "smoothstep",
        label: e.label as string,
        animated: e.animated || false,
        style: (e.style as React.CSSProperties) || { stroke: "#6366f1" },
      })),
    [graphData]
  );

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  if (!graphData?.nodes?.length) {
    return (
      <div className="h-full flex items-center justify-center text-gray-600 font-mono text-sm">
        Contract topology will appear here
      </div>
    );
  }

  return (
    <div className="h-full" ref={flowRef}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        proOptions={{ hideAttribution: true }}
        className="bg-gray-950"
      >
        <Background color="#1f2937" gap={20} />
        <Controls className="!bg-gray-800 !border-gray-700 !text-gray-300" />
        <MiniMap
          nodeColor={(node) => {
            switch (node.type) {
              case "contractNode":
                return "#6366f1";
              case "functionNode":
                return "#10b981";
              case "stateVarNode":
                return "#a855f7";
              case "modifierNode":
                return "#f59e0b";
              default:
                return "#6b7280";
            }
          }}
          className="!bg-gray-900 !border-gray-700"
        />
      </ReactFlow>
    </div>
  );
}
