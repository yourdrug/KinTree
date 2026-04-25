import { useRef, useState, useCallback, useEffect } from "react";
import { ZoomIn, ZoomOut, Maximize2 } from "lucide-react";
import PersonNode from "./PersonNode";
import TreeConnections from "./TreeConnections";

function computePositions(members) {
  const positions = {};
  const genGroups = {};

  members.forEach((m) => {
    const gen = m.generation ?? 0;
    if (!genGroups[gen]) genGroups[gen] = [];
    genGroups[gen].push(m);
  });

  const sortedGens = Object.keys(genGroups).map(Number).sort((a, b) => a - b);
  const NODE_W = 130;
  const GEN_H = 160;

  sortedGens.forEach((gen) => {
    const group = genGroups[gen];
    const totalW = group.length * NODE_W + (group.length - 1) * 30;
    const startX = -totalW / 2;
    group.forEach((m, i) => {
      positions[m.id] = {
        x: startX + i * (NODE_W + 30),
        y: gen * GEN_H,
      };
    });
  });

  return positions;
}

export default function TreeCanvas({ members, selectedPerson, onSelectPerson, canEdit, onAddChild }) {
  const containerRef = useRef(null);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [scale, setScale] = useState(0.9);
  const [dragging, setDragging] = useState(false);
  const dragStart = useRef(null);

  const positions = computePositions(members);

  // Center on load
  useEffect(() => {
    if (containerRef.current) {
      setOffset({ x: containerRef.current.clientWidth / 2, y: 80 });
    }
  }, []);

  const handleMouseDown = useCallback((e) => {
    if (e.target.closest("[data-node]")) return;
    setDragging(true);
    dragStart.current = { x: e.clientX - offset.x, y: e.clientY - offset.y };
  }, [offset]);

  const handleMouseMove = useCallback((e) => {
    if (!dragging || !dragStart.current) return;
    setOffset({ x: e.clientX - dragStart.current.x, y: e.clientY - dragStart.current.y });
  }, [dragging]);

  const handleMouseUp = useCallback(() => {
    setDragging(false);
    dragStart.current = null;
  }, []);

  const handleWheel = useCallback((e) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.08 : 0.08;
    setScale((s) => Math.max(0.3, Math.min(2, s + delta)));
  }, []);

  const zoom = (dir) => setScale((s) => Math.max(0.3, Math.min(2, s + dir * 0.15)));
  const reset = () => {
    setScale(0.9);
    if (containerRef.current) setOffset({ x: containerRef.current.clientWidth / 2, y: 80 });
  };

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full overflow-hidden select-none"
      style={{ cursor: dragging ? "grabbing" : "grab", background: "radial-gradient(ellipse at 50% 30%, hsl(145,35%,97%) 0%, hsl(40,33%,98%) 60%)" }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onWheel={handleWheel}
    >
      {/* Grid pattern */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-30">
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="hsl(145,35%,80%)" strokeWidth="0.5" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
      </svg>

      {/* Transform wrapper */}
      <div
        className="absolute"
        style={{ transform: `translate(${offset.x}px, ${offset.y}px) scale(${scale})`, transformOrigin: "0 0" }}
      >
        <div className="relative" style={{ width: "2px", height: "2px" }}>
          <TreeConnections members={members} positions={positions} />
          {members.map((m) => (
            <div key={m.id} data-node="true">
              <PersonNode
                person={m}
                isSelected={selectedPerson?.id === m.id}
                onClick={onSelectPerson}
                canEdit={canEdit}
                onAddChild={onAddChild}
                style={positions[m.id]}
              />
            </div>
          ))}
        </div>
      </div>

      {/* Zoom Controls */}
      <div className="absolute bottom-6 right-6 flex flex-col gap-2 z-10">
        <button onClick={() => zoom(1)} className="w-9 h-9 rounded-xl flex items-center justify-center shadow-md hover:scale-105 transition-transform"
          style={{ background: "white", border: "1px solid hsl(35,20%,88%)" }}>
          <ZoomIn className="w-4 h-4 text-foreground" />
        </button>
        <button onClick={() => zoom(-1)} className="w-9 h-9 rounded-xl flex items-center justify-center shadow-md hover:scale-105 transition-transform"
          style={{ background: "white", border: "1px solid hsl(35,20%,88%)" }}>
          <ZoomOut className="w-4 h-4 text-foreground" />
        </button>
        <button onClick={reset} className="w-9 h-9 rounded-xl flex items-center justify-center shadow-md hover:scale-105 transition-transform"
          style={{ background: "white", border: "1px solid hsl(35,20%,88%)" }}>
          <Maximize2 className="w-4 h-4 text-foreground" />
        </button>
      </div>

      {/* Scale indicator */}
      <div className="absolute bottom-6 left-6 px-3 py-1.5 rounded-lg text-xs text-muted-foreground"
        style={{ background: "hsla(40,33%,98%,0.8)", border: "1px solid hsl(35,20%,88%)" }}>
        {Math.round(scale * 100)}%
      </div>

      {members.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center">
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