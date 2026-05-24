/**
 * components/tree/TreeCanvas.jsx
 *
 * ReactFlow + кастомный генеалогический layout (без Dagre).
 * Супруги всегда рядом, дети под парой, рёбра не наискосок.
 */

import { useCallback, useEffect, useMemo, useRef } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  useReactFlow,
  ReactFlowProvider,
  MarkerType,
} from "reactflow";
import "reactflow/dist/style.css";

import { computeGenealogyLayout } from "@/lib/genealogyLayout";
import { useHighlight } from "./useHighlight";
import PersonNodeRF from "./PersonNodeRF";

const NODE_W = 140;
const NODE_H = 100;
const nodeTypes = { person: PersonNodeRF };

const BASE_EDGE = {
  parent_child: { stroke: "hsl(145,35%,52%)", dash: undefined, width: 2   },
  spouse:       { stroke: "hsl(30,60%,58%)",  dash: "6 4",     width: 1.8 },
  sibling:      { stroke: "hsl(145,35%,60%)", dash: "4 4",     width: 1.5 },
};
const ACTIVE_EDGE = {
  parent_child: { stroke: "hsl(210,80%,50%)", width: 3   },
  spouse:       { stroke: "hsl(345,65%,52%)", width: 2.5 },
  sibling:      { stroke: "hsl(260,55%,52%)", width: 2.5 },
};

function makeEdgeStyle(edgeType, highlight) {
  const base   = BASE_EDGE[edgeType]   ?? BASE_EDGE.parent_child;
  const active = ACTIVE_EDGE[edgeType] ?? ACTIVE_EDGE.parent_child;
  const isActive = highlight === "active";
  const isDimmed = highlight === "dimmed";
  return {
    stroke:          isActive ? active.stroke : base.stroke,
    strokeWidth:     isActive ? active.width  : base.width,
    strokeDasharray: base.dash,
    opacity:         isDimmed ? 0.08 : isActive ? 1 : 0.5,
    transition:      "stroke 0.15s, stroke-width 0.15s, opacity 0.15s",
  };
}

function buildRFNodes(nodes, positions, selectedId, getNodeRole, canEdit, onSelectPerson, onAddChild, onMouseEnter, onMouseLeave) {
  return nodes.map(n => {
    const pos = positions.get(n.id) ?? { x: 0, y: 0 };
    return {
      id:       n.id,
      type:     "person",
      position: pos,
      width:    NODE_W,
      height:   NODE_H,
      data: {
        person:        n,
        isSelected:    n.id === selectedId,
        highlightRole: getNodeRole(n.id),
        canEdit,
        onAddChild,
        onClick:       onSelectPerson,
        onMouseEnter,
        onMouseLeave,
      },
    };
  });
}

function buildRFEdges(edges, positions, getEdgeHighlight) {
  const drawn  = new Set();
  const result = [];

  for (const e of edges) {
    const pairKey = [e.source_id, e.target_id].sort().join("|");
    const uniqKey = `${e.type}-${pairKey}`;
    if (drawn.has(uniqKey)) continue;
    drawn.add(uniqKey);

    const hl    = getEdgeHighlight ? getEdgeHighlight(e) : null;
    const eType = e.type ?? "parent_child";
    const style = makeEdgeStyle(eType, hl);

    const srcPos = positions.get(e.source_id);
    const tgtPos = positions.get(e.target_id);

    let sourceHandle = undefined;
    let targetHandle = undefined;
    let edgeType     = "smoothstep";

    if (eType === "spouse" && srcPos && tgtPos) {
      if (srcPos.x < tgtPos.x) {
        sourceHandle = "right";
        targetHandle = "left";
      } else {
        sourceHandle = "left";
        targetHandle = "right";
      }
      edgeType = "straight";
    }

    if (eType === "sibling" && srcPos && tgtPos) {
      edgeType = "straight";
      if (srcPos.x < tgtPos.x) {
        sourceHandle = "right";
        targetHandle = "left";
      } else {
        sourceHandle = "left";
        targetHandle = "right";
      }
    }

    result.push({
      id:           uniqKey,
      source:       e.source_id,
      target:       e.target_id,
      sourceHandle,
      targetHandle,
      type:         edgeType,
      animated:     false,
      data:         { type: eType, raw: e },
      style,
      markerEnd:    eType === "parent_child"
        ? { type: MarkerType.ArrowClosed, color: style.stroke, width: 14, height: 14 }
        : undefined,
    });
  }

  return result;
}

function TreeCanvasInner({
  nodes: rawNodes,
  edges: rawEdges,
  selectedPerson,
  onSelectPerson,
  canEdit,
  onAddChild,
}) {
  const { fitView } = useReactFlow();
  const fitDone = useRef(false);

  const { getNodeRole, getEdgeHighlight, onNodeMouseEnter, onNodeMouseLeave } =
    useHighlight(rawEdges);

  const positions = useMemo(
    () => computeGenealogyLayout(rawNodes, rawEdges),
    [rawNodes, rawEdges]
  );

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // Sync layout when source data changes
  useEffect(() => {
    setNodes(
      buildRFNodes(
        rawNodes, positions,
        selectedPerson?.id, getNodeRole,
        canEdit, onSelectPerson, onAddChild,
        onNodeMouseEnter, onNodeMouseLeave
      )
    );
    setEdges(buildRFEdges(rawEdges, positions, getEdgeHighlight));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rawNodes, rawEdges, positions]);

  // Sync edge highlight on hover
  useEffect(() => {
    setEdges(eds =>
      eds.map(e => {
        const rawEdge = e.data?.raw;
        if (!rawEdge) return e;
        return { ...e, style: makeEdgeStyle(rawEdge.type ?? "parent_child", getEdgeHighlight(rawEdge)) };
      })
    );
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [getEdgeHighlight]);

  // Sync selection + highlight into node data
  useEffect(() => {
    setNodes(nds =>
      nds.map(n => ({
        ...n,
        data: {
          ...n.data,
          isSelected:    n.id === selectedPerson?.id,
          highlightRole: getNodeRole(n.id),
          canEdit,
          onAddChild,
          onClick:       onSelectPerson,
          onMouseEnter:  onNodeMouseEnter,
          onMouseLeave:  onNodeMouseLeave,
        },
      }))
    );
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedPerson?.id, getNodeRole, canEdit]);

  // Fit view on first load
  useEffect(() => {
    if (rawNodes.length && !fitDone.current) {
      fitDone.current = true;
      setTimeout(() => fitView({ padding: 0.15, duration: 500 }), 120);
    }
  }, [rawNodes.length, fitView]);

  const onNodeClick = useCallback(
    (_, node) => onSelectPerson?.(node.data.person),
    [onSelectPerson]
  );
  const onNodeMouseEnterCb = useCallback(
    (_, node) => onNodeMouseEnter(node.id),
    [onNodeMouseEnter]
  );
  const onNodeMouseLeaveCb = useCallback(
    () => onNodeMouseLeave(),
    [onNodeMouseLeave]
  );

  return (
    <div className="w-full h-full relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        onNodeClick={onNodeClick}
        onNodeMouseEnter={onNodeMouseEnterCb}
        onNodeMouseLeave={onNodeMouseLeaveCb}
        fitView
        minZoom={0.1}
        maxZoom={2.5}
        proOptions={{ hideAttribution: true }}
        nodesDraggable={canEdit}
        nodesConnectable={false}
        elementsSelectable={true}
        panOnScroll={false}
        zoomOnScroll={true}
        style={{
          background: "radial-gradient(ellipse at 50% 30%, hsl(145,35%,97%) 0%, hsl(40,33%,98%) 65%)",
        }}
      >
        <Background
          variant="dots"
          gap={32}
          size={1.2}
          color="hsl(145,35%,78%)"
          style={{ opacity: 0.35 }}
        />
        <Controls
          showInteractive={false}
          style={{
            display: "flex", flexDirection: "column", gap: 4,
            background: "transparent", border: "none", boxShadow: "none",
            bottom: 24, right: 24,
          }}
        />
        {rawNodes.length > 8 && (
          <MiniMap
            nodeColor={n => n.data?.isSelected ? "hsl(145,35%,38%)" : "hsl(35,40%,88%)"}
            maskColor="hsla(40,33%,98%,0.75)"
            style={{
              background: "hsla(40,33%,96%,0.92)",
              border: "1px solid hsl(35,20%,88%)",
              borderRadius: 12, bottom: 24, left: 55, width: 200,
            }}
          />
        )}
      </ReactFlow>

      {rawNodes.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="text-center">
            <div className="text-5xl mb-4">🌱</div>
            <p className="font-serif text-xl text-foreground mb-2">Дерево пока пусто</p>
            <p className="text-sm text-muted-foreground">Добавьте первого члена семьи, чтобы начать</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default function TreeCanvas(props) {
  return (
    <ReactFlowProvider>
      <TreeCanvasInner {...props} />
    </ReactFlowProvider>
  );
}
