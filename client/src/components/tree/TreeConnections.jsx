/**
 * components/tree/TreeConnections.jsx
 *
 * Подсвечивает рёбра при hover через prop getEdgeHighlight(edge):
 *   "active" — ребро между hoveredId и его родственником → яркое, толстое
 *   "dimmed" — остальные рёбра → прозрачные
 *   null     — нет hover → обычный стиль
 *
 * Типы рёбер:
 *   parent_child → Безье-кривая (вертикальная)
 *   spouse       → горизонтальная линия (с годом)
 *   sibling      → горизонтальная линия (стиль по типу: FULL/HALF/STEP)
 */

const NODE_W  = 110;
const NODE_H  = 90;
const NODE_CX = 55;

// Базовые цвета рёбер по умолчанию
const EDGE_BASE = {
  parent_child_bio:  { stroke: "hsl(145,35%,55%)", dash: "none",  width: 2 },
  parent_child_adop: { stroke: "hsl(210,55%,55%)", dash: "5 4",   width: 2 },
  parent_child_step: { stroke: "hsl(30,50%,55%)",  dash: "5 4",   width: 2 },
  spouse_married:    { stroke: "hsl(30,65%,55%)",  dash: "none",  width: 2 },
  spouse_divorced:   { stroke: "hsl(0,55%,60%)",   dash: "6 4",   width: 1.5 },
  spouse_widowed:    { stroke: "hsl(240,10%,55%)", dash: "3 4",   width: 1.5 },
  sibling_full:      { stroke: "hsl(145,40%,50%)", dash: "none",  width: 1.5 },
  sibling_half:      { stroke: "hsl(145,30%,55%)", dash: "6 4",   width: 1.5 },
  sibling_step:      { stroke: "hsl(0,0%,60%)",    dash: "2 5",   width: 1.5 },
};

// Active-цвета (при hover) — насыщеннее и толще
const EDGE_ACTIVE = {
  parent_child_bio:  { stroke: "hsl(210,80%,50%)", width: 3 },
  parent_child_adop: { stroke: "hsl(210,80%,50%)", width: 3 },
  parent_child_step: { stroke: "hsl(30,70%,48%)",  width: 3 },
  spouse_married:    { stroke: "hsl(345,65%,52%)",  width: 3 },
  spouse_divorced:   { stroke: "hsl(0,65%,52%)",   width: 2.5 },
  spouse_widowed:    { stroke: "hsl(240,30%,52%)",  width: 2.5 },
  sibling_full:      { stroke: "hsl(260,55%,52%)",  width: 3 },
  sibling_half:      { stroke: "hsl(260,45%,58%)",  width: 2.5 },
  sibling_step:      { stroke: "hsl(260,25%,62%)",  width: 2 },
};

function edgeKey(edge) {
  if (edge.type === "parent_child") {
    const rt = edge.relation_type?.toLowerCase() ?? "bio";
    return rt === "biological" ? "parent_child_bio"
         : rt === "adopted"    ? "parent_child_adop"
         : "parent_child_step";
  }
  if (edge.type === "spouse") {
    const ms = edge.marriage_status?.toLowerCase() ?? "married";
    return ms === "divorced" ? "spouse_divorced"
         : ms === "widowed"  ? "spouse_widowed"
         : "spouse_married";
  }
  if (edge.type === "sibling") {
    const st = edge.sibling_type ?? "FULL";
    return st === "FULL" ? "sibling_full"
         : st === "HALF" ? "sibling_half"
         : "sibling_step";
  }
  return null;
}

export default function TreeConnections({ positions, edges, getEdgeHighlight }) {
  if (!edges?.length || !positions) return null;

  const paths        = [];
  const drawnSpouse  = new Set();
  const drawnSibling = new Set();

  for (const edge of edges) {
    const srcPos = positions[edge.source_id];
    const tgtPos = positions[edge.target_id];
    if (!srcPos || !tgtPos) continue;

    const highlight = getEdgeHighlight ? getEdgeHighlight(edge) : null;
    const key       = edgeKey(edge);
    if (!key) continue;

    const base   = EDGE_BASE[key]   ?? { stroke: "hsl(0,0%,60%)", dash: "none", width: 1.5 };
    const active = EDGE_ACTIVE[key] ?? { stroke: base.stroke,     width: base.width + 1 };

    const isActive  = highlight === "active";
    const isDimmed  = highlight === "dimmed";
    const hasHover  = highlight !== null;

    const stroke      = isActive ? active.stroke : base.stroke;
    const strokeWidth = isActive ? active.width  : base.width;
    const dash        = isActive ? "none"         : base.dash;
    const opacity     = isDimmed ? 0.1 : (isActive ? 0.95 : (hasHover ? 0.45 : 0.5));

    // ── parent_child ───────────────────────────────────────────────────────
    if (edge.type === "parent_child") {
      const x1   = srcPos.x + NODE_CX;
      const y1   = srcPos.y + NODE_H;
      const x2   = tgtPos.x + NODE_CX;
      const y2   = tgtPos.y;
      const midY = (y1 + y2) / 2;

      paths.push(
        <path
          key={`pc-${edge.source_id}-${edge.target_id}`}
          d={`M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`}
          fill="none"
          stroke={stroke}
          strokeWidth={strokeWidth}
          strokeDasharray={dash}
          opacity={opacity}
          style={{ transition: "opacity 0.15s, stroke 0.15s, stroke-width 0.15s" }}
        />
      );
      continue;
    }

    // ── spouse ────────────────────────────────────────────────────────────
    if (edge.type === "spouse") {
      const pairKey = [edge.source_id, edge.target_id].sort().join("|");
      if (drawnSpouse.has(pairKey)) continue;
      drawnSpouse.add(pairKey);

      const leftPos  = srcPos.x <= tgtPos.x ? srcPos : tgtPos;
      const rightPos = srcPos.x <= tgtPos.x ? tgtPos : srcPos;
      const x1 = leftPos.x  + NODE_W;
      const x2 = rightPos.x;
      const y  = (leftPos.y + rightPos.y) / 2 + NODE_H / 2;

      if (x2 <= x1) continue;

      paths.push(
        <line
          key={`sp-${pairKey}`}
          x1={x1} y1={y} x2={x2} y2={y}
          stroke={stroke}
          strokeWidth={strokeWidth}
          strokeDasharray={dash}
          opacity={opacity}
          style={{ transition: "opacity 0.15s, stroke 0.15s, stroke-width 0.15s" }}
        />
      );

      if (edge.marriage_year) {
        const midX = (x1 + x2) / 2;
        const label = edge.divorce_year
          ? `${edge.marriage_year}–${edge.divorce_year}`
          : `${edge.marriage_year}`;
        paths.push(
          <text
            key={`sp-lbl-${pairKey}`}
            x={midX} y={y - 5}
            textAnchor="middle"
            fontSize="9"
            fill={isActive ? stroke : "hsl(30,40%,50%)"}
            opacity={isDimmed ? 0.1 : (isActive ? 0.9 : 0.7)}
            style={{ transition: "opacity 0.15s, fill 0.15s" }}
          >
            {label}
          </text>
        );
      }
      continue;
    }

    // ── sibling ──────────────────────────────────────────────────────────
    if (edge.type === "sibling") {
      const pairKey = [edge.source_id, edge.target_id].sort().join("|");
      if (drawnSibling.has(pairKey)) continue;
      drawnSibling.add(pairKey);

      const leftPos  = srcPos.x <= tgtPos.x ? srcPos : tgtPos;
      const rightPos = srcPos.x <= tgtPos.x ? tgtPos : srcPos;
      const x1 = leftPos.x  + NODE_W;
      const x2 = rightPos.x;
      const y  = (leftPos.y + rightPos.y) / 2 + NODE_H * 0.35;

      if (x2 <= x1) continue;

      paths.push(
        <line
          key={`sib-${pairKey}`}
          x1={x1} y1={y} x2={x2} y2={y}
          stroke={stroke}
          strokeWidth={strokeWidth}
          strokeDasharray={dash}
          opacity={opacity}
          style={{ transition: "opacity 0.15s, stroke 0.15s, stroke-width 0.15s" }}
        />
      );
      continue;
    }
  }

  return (
    <svg
      className="absolute inset-0 pointer-events-none"
      style={{ overflow: "visible", width: "1px", height: "1px" }}
    >
      {paths}
    </svg>
  );
}
