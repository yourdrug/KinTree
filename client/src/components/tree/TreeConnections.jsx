/**
 * components/tree/TreeConnections.jsx
 *
 * Исправления:
 * - parent_ids и spouse_ids берутся из enriched persons (из графа)
 * - Дедублируем линии супругов чтобы не рисовать дважды
 */

export default function TreeConnections({ members, positions }) {
  const paths = [];
  const drawnSpousePairs = new Set();

  members.forEach((member) => {
    const childPos = positions[member.id];
    if (!childPos) return;

    // Линии родитель → ребёнок
    (member.parent_ids || []).forEach((parentId) => {
      const parentPos = positions[parentId];
      if (!parentPos) return;

      const x1 = parentPos.x + 55;
      const y1 = parentPos.y + 90;
      const x2 = childPos.x + 55;
      const y2 = childPos.y;
      const midY = (y1 + y2) / 2;

      paths.push(
        <path
          key={`pc-${parentId}-${member.id}`}
          d={`M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`}
          fill="none"
          stroke="hsl(145,35%,55%)"
          strokeWidth="2"
          strokeDasharray="5 4"
          opacity="0.5"
        />
      );
    });

    // Линии супругов (рисуем один раз на пару)
    (member.spouse_ids || []).forEach((spouseId) => {
      const pairKey = [member.id, spouseId].sort().join("-");
      if (drawnSpousePairs.has(pairKey)) return;
      drawnSpousePairs.add(pairKey);

      const spousePos = positions[spouseId];
      if (!spousePos) return;

      const x1 = Math.min(childPos.x, spousePos.x) + 110;
      const x2 = Math.max(childPos.x, spousePos.x);
      const y  = childPos.y + 45;

      paths.push(
        <line
          key={`sp-${pairKey}`}
          x1={x1} y1={y} x2={x2} y2={y}
          stroke="hsl(30,50%,60%)"
          strokeWidth="2"
          strokeDasharray="4 3"
          opacity="0.45"
        />
      );
    });
  });

  return (
    <svg
      className="absolute inset-0 w-full h-full pointer-events-none"
      style={{ overflow: "visible" }}
    >
      {paths}
    </svg>
  );
}
