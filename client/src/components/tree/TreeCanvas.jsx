/**
 * components/tree/TreeCanvas.jsx
 *
 * Fixes:
 * 1. Container height — explicit style="height:100%;width:100%" on wrapper
 * 2. Focus person — wait for positions then fitView/setCenter properly
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

    if (!positions.has(e.source_id) || !positions.has(e.target_id)) continue;

    const hl    = getEdgeHighlight ? getEdgeHighlight(e) : null;
    const eType = e.type ?? "parent_child";
    const style = makeEdgeStyle(eType, hl);

    const srcPos = positions.get(e.source_id);
    const tgtPos = positions.get(e.target_id);

    let sourceHandle;
    let targetHandle;
    let edgeType = "smoothstep";

    if (eType === "parent_child") {
      sourceHandle = "bot";
      targetHandle = "top";
    } else if (eType === "spouse" && srcPos && tgtPos) {
      if (srcPos.x < tgtPos.x) {
        sourceHandle = "right";
        targetHandle = "left";
      } else {
        sourceHandle = "left";
        targetHandle = "right";
      }
      edgeType = "straight";
    } else if (eType === "sibling") {
      sourceHandle = "sib-top";
      targetHandle = "sib-top-t";
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

// ── Focus hook ────────────────────────────────────────────────────────────────
// Watches focusPersonId + positions. When both are ready, centres the view.
// Uses a ref to avoid re-running on unrelated re-renders.

function useFocusPerson({ focusPersonId, positions, setCenter, fitView }) {
  const initialDone  = useRef(false);
  const prevFocusId  = useRef(null);
  const rafRef       = useRef(null);

  useEffect(() => {
    if (!positions.size) return;

    const isInitial = !initialDone.current;
    const idChanged = focusPersonId && focusPersonId !== prevFocusId.current;

    if (!isInitial && !idChanged) return;

    // Cancel any pending animation frame
    if (rafRef.current) cancelAnimationFrame(rafRef.current);

    // Double rAF: first flush React, second flush ReactFlow internal layout
    rafRef.current = requestAnimationFrame(() => {
      rafRef.current = requestAnimationFrame(() => {
        if (isInitial) {
          fitView({ padding: 0.15, duration: 0 });
        } else {
          const pos = positions.get(focusPersonId);
          if (pos) {
            setCenter(
              pos.x + NODE_W / 2,
              pos.y + NODE_H / 2,
              { zoom: 1.2, duration: 500 }
            );
            prevFocusId.current = focusPersonId;
          } else {
            fitView({ padding: 0.15, duration: 500 });
          }
        }
        initialDone.current = true;
      });
    });

    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusPersonId, positions]);
}

function TreeCanvasInner({
  nodes: rawNodes,
  edges: rawEdges,
  selectedPerson,
  onSelectPerson,
  canEdit,
  onAddChild,
  focusPersonId,
}) {
  const { fitView, setCenter } = useReactFlow();

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

  useFocusPerson({ focusPersonId, positions, setCenter, fitView });

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
    // ── FIX 1: explicit 100% width+height so ReactFlow fills the flex cell ──
    <div style={{ width: "100%", height: "100%", position: "relative" }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        onNodeClick={onNodeClick}
        onNodeMouseEnter={onNodeMouseEnterCb}
        onNodeMouseLeave={onNodeMouseLeaveCb}
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
    // ── FIX 1: ReactFlowProvider must also be 100% height ──────────────────
    <ReactFlowProvider>
      <div style={{ width: "100%", height: "100%" }}>
        <TreeCanvasInner {...props} />
      </div>
    </ReactFlowProvider>
  );
}
