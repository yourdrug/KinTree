/**
 * components/tree/TreeCanvas.jsx
 *
 * Интегрирован хук useHighlight:
 *  - hoveredId — ID узла под курсором
 *  - getNodeRole(id) — роль узла при hover ("hovered"|"parent"|"child"|"spouse"|"sibling"|"dimmed"|null)
 *  - getEdgeHighlight(edge) — статус ребра ("active"|"dimmed"|null)
 *  - onNodeMouseEnter/onNodeMouseLeave — передаются в PersonNode
 *
 * PersonNode получает:
 *  - highlightRole={getNodeRole(node.id)}
 *  - onMouseEnter={onNodeMouseEnter}
 *  - onMouseLeave={onNodeMouseLeave}
 *
 * TreeConnections получает:
 *  - getEdgeHighlight={getEdgeHighlight}
 */

import { useRef, useState, useCallback, useEffect, useMemo } from "react";
import { ZoomIn, ZoomOut, Maximize2 } from "lucide-react";
import PersonNode      from "./PersonNode";
import TreeConnections from "./TreeConnections";
import { useHighlight } from "./useHighlight";

// ── Layout constants ──────────────────────────────────────────────────────────

const NODE_W   = 120;
const NODE_GAP = 36;
const GEN_H    = 180;

// ── computePositions ──────────────────────────────────────────────────────────

function computePositions(nodes, edges) {
  if (!nodes?.length) return {};

  const genGroups = {};
  for (const node of nodes) {
    const gen = node.generation ?? 0;
    if (!genGroups[gen]) genGroups[gen] = [];
    genGroups[gen].push(node);
  }

  const spouseOf = new Map();
  if (edges) {
    for (const e of edges) {
      if (e.type !== "spouse") continue;
      if (!spouseOf.has(e.source_id)) spouseOf.set(e.source_id, []);
      if (!spouseOf.has(e.target_id)) spouseOf.set(e.target_id, []);
      spouseOf.get(e.source_id).push(e.target_id);
      spouseOf.get(e.target_id).push(e.source_id);
    }
  }

  const positions  = {};
  const sortedGens = Object.keys(genGroups).map(Number).sort((a, b) => a - b);

  for (const gen of sortedGens) {
    const ordered = orderWithSpouses(genGroups[gen], spouseOf);
    const totalW  = ordered.length * NODE_W + (ordered.length - 1) * NODE_GAP;
    const startX  = -totalW / 2;
    ordered.forEach((node, i) => {
      positions[node.id] = { x: startX + i * (NODE_W + NODE_GAP), y: gen * GEN_H };
    });
  }

  return positions;
}

function orderWithSpouses(group, spouseOf) {
  const placed  = new Set();
  const result  = [];
  const groupIds = new Set(group.map((n) => n.id));

  for (const node of group) {
    if (placed.has(node.id)) continue;
    const partners = (spouseOf.get(node.id) ?? [])
      .filter((id) => groupIds.has(id) && !placed.has(id));

    if (partners.length > 0) {
      const pair = [node, ...partners.map((pid) => group.find((n) => n.id === pid)).filter(Boolean)];
      pair.sort((a, b) => {
        if (a.gender === "MALE"   && b.gender !== "MALE")  return -1;
        if (a.gender === "FEMALE" && b.gender === "MALE")  return  1;
        return 0;
      });
      for (const p of pair) { placed.add(p.id); result.push(p); }
    } else {
      placed.add(node.id);
      result.push(node);
    }
  }
  return result;
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function TreeCanvas({
  nodes,
  edges,
  selectedPerson,
  onSelectPerson,
  canEdit,
  onAddChild,
}) {
  const containerRef = useRef(null);
  const dragStart    = useRef(null);

  const [offset,   setOffset]   = useState({ x: 0, y: 0 });
  const [scale,    setScale]    = useState(0.9);
  const [dragging, setDragging] = useState(false);

  const positions = useMemo(() => computePositions(nodes, edges), [nodes, edges]);

  // ── Hover highlight ────────────────────────────────────────────────────────
  const {
    getNodeRole,
    getEdgeHighlight,
    onNodeMouseEnter,
    onNodeMouseLeave,
  } = useHighlight(edges);

  // ── Canvas setup ───────────────────────────────────────────────────────────
  useEffect(() => {
    if (containerRef.current) {
      setOffset({ x: containerRef.current.clientWidth / 2, y: 80 });
    }
  }, []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const onWheel = (e) => {
      e.preventDefault();
      setScale((s) => Math.max(0.25, Math.min(2.5, s + (e.deltaY > 0 ? -0.08 : 0.08))));
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => el.removeEventListener("wheel", onWheel);
  }, []);

  const handleMouseDown = useCallback((e) => {
    if (e.button !== 0) return;
    if (e.target.closest("[data-node]")) return;
    setDragging(true);
    dragStart.current = { x: e.clientX - offset.x, y: e.clientY - offset.y };
  }, [offset]);

  const handleMouseMove = useCallback((e) => {
    if (!dragging || !dragStart.current) return;
    setOffset({ x: e.clientX - dragStart.current.x, y: e.clientY - dragStart.current.y });
  }, [dragging]);

  const stopDrag = useCallback(() => {
    setDragging(false);
    dragStart.current = null;
  }, []);

  const zoom  = (dir) => setScale((s) => Math.max(0.25, Math.min(2.5, s + dir * 0.15)));
  const reset = () => {
    setScale(0.9);
    if (containerRef.current) setOffset({ x: containerRef.current.clientWidth / 2, y: 80 });
  };

  const members = nodes ?? [];

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full overflow-hidden select-none"
      style={{
        cursor: dragging ? "grabbing" : "grab",
        background: "radial-gradient(ellipse at 50% 30%, hsl(145,35%,97%) 0%, hsl(40,33%,98%) 60%)",
      }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={stopDrag}
      onMouseLeave={stopDrag}
    >
      {/* Dot grid */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-25">
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <circle cx="1" cy="1" r="1" fill="hsl(145,35%,70%)" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
      </svg>

      {/* Transform wrapper */}
      <div
        className="absolute"
        style={{
          transform:       `translate(${offset.x}px, ${offset.y}px) scale(${scale})`,
          transformOrigin: "0 0",
        }}
      >
        <div className="relative" style={{ width: 0, height: 0 }}>
          {/* Connections — передаём getEdgeHighlight */}
          <TreeConnections
            positions={positions}
            edges={edges}
            getEdgeHighlight={getEdgeHighlight}
          />

          {members.map((node) => (
            <div key={node.id} data-node="true">
              <PersonNode
                person={node}
                isSelected={selectedPerson?.id === node.id}
                onClick={onSelectPerson}
                canEdit={canEdit}
                onAddChild={onAddChild}
                style={positions[node.id]}
                highlightRole={getNodeRole(node.id)}
                onMouseEnter={onNodeMouseEnter}
                onMouseLeave={onNodeMouseLeave}
              />
            </div>
          ))}
        </div>
      </div>

      {/* Zoom controls */}
      <div className="absolute bottom-6 right-6 flex flex-col gap-2 z-10">
        {[
          { icon: ZoomIn,    action: () => zoom(1),  title: "Увеличить" },
          { icon: ZoomOut,   action: () => zoom(-1), title: "Уменьшить" },
          { icon: Maximize2, action: reset,           title: "Сбросить" },
        ].map(({ icon: Icon, action, title }) => (
          <button
            key={title}
            title={title}
            onClick={action}
            className="w-9 h-9 rounded-xl flex items-center justify-center shadow-md hover:scale-105 transition-transform"
            style={{ background: "white", border: "1px solid hsl(35,20%,88%)" }}
          >
            <Icon className="w-4 h-4 text-foreground" />
          </button>
        ))}
      </div>

      {/* Scale indicator */}
      <div
        className="absolute bottom-6 left-6 px-3 py-1.5 rounded-lg text-xs text-muted-foreground pointer-events-none"
        style={{ background: "hsla(40,33%,98%,0.85)", border: "1px solid hsl(35,20%,88%)" }}
      >
        {Math.round(scale * 100)}%
      </div>

      {/* Empty state */}
      {members.length === 0 && (
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
