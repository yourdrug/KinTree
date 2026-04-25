export default function TreeConnections({ members, positions }) {
  const paths = [];

  members.forEach((member) => {
    if (!member.parent_ids || member.parent_ids.length === 0) return;
    const childPos = positions[member.id];
    if (!childPos) return;

    member.parent_ids.forEach((parentId) => {
      const parentPos = positions[parentId];
      if (!parentPos) return;

      const x1 = parentPos.x + 55;
      const y1 = parentPos.y + 90;
      const x2 = childPos.x + 55;
      const y2 = childPos.y;

      const midY = (y1 + y2) / 2;

      paths.push(
        <path
          key={`${parentId}-${member.id}`}
          d={`M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`}
          fill="none"
          stroke="hsl(145,35%,55%)"
          strokeWidth="2"
          strokeDasharray="5 4"
          opacity="0.5"
        />
      );
    });

    // Partner connection
    if (member.partner_id) {
      const partnerPos = positions[member.partner_id];
      if (partnerPos) {
        const x1 = Math.min(childPos.x, partnerPos.x) + 110;
        const x2 = Math.max(childPos.x, partnerPos.x);
        const y = childPos.y + 45;

        paths.push(
          <line
            key={`partner-${member.id}-${member.partner_id}`}
            x1={x1} y1={y} x2={x2} y2={y}
            stroke="hsl(30,50%,60%)"
            strokeWidth="2"
            strokeDasharray="4 3"
            opacity="0.45"
          />
        );
      }
    }
  });

  return (
    <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ overflow: "visible" }}>
      {paths}
    </svg>
  );
}