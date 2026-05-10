/**
 * components/tree/TreeConnections.jsx
 *
 * ИСПРАВЛЕНИЯ:
 * 1. Линия супругов рисовалась с неправильной Y-координатой:
 *    y = childPos.y + 45 — использовала "childPos" что было текущей персоной,
 *    а не средним между двумя супругами. Теперь y берётся как среднее Y обоих.
 * 2. X-координаты линии между супругами: правильно берём правый край левого
 *    узла (x + 110) и левый край правого узла (x), независимо от порядка.
 * 3. Добавлена проверка что позиции обоих участников существуют.
 */

export default function TreeConnections({ members, positions }) {
  const paths = [];
  const drawnSpousePairs = new Set();

  members.forEach((member) => {
    const memberPos = positions[member.id];
    if (!memberPos) return;

    // Линии родитель → ребёнок
    (member.parent_ids || []).forEach((parentId) => {
      const parentPos = positions[parentId];
      if (!parentPos) return;

      const x1 = parentPos.x + 55;
      const y1 = parentPos.y + 90;
      const x2 = memberPos.x + 55;
      const y2 = memberPos.y;
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

      // FIX: определяем кто левее/правее и строим линию правильно
      const leftPos  = memberPos.x < spousePos.x ? memberPos : spousePos;
      const rightPos = memberPos.x < spousePos.x ? spousePos : memberPos;

      // Линия от правого края левого узла до левого края правого узла
      const x1 = leftPos.x + 110;
      const x2 = rightPos.x;
      // FIX: Y = середина между вертикальными центрами обоих узлов
      const y = (leftPos.y + rightPos.y) / 2 + 45;

      // Рисуем только если узлы не перекрываются
      if (x2 > x1) {
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
      }
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
