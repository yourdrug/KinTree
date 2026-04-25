import { motion } from "framer-motion";

const people = [
  { id: "gg1", name: "Иван", years: "1890–1965", x: 50, y: 5, photo: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&h=80&fit=crop&crop=face", gen: 0 },
  { id: "gg2", name: "Мария", years: "1893–1971", x: 155, y: 5, photo: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=80&h=80&fit=crop&crop=face", gen: 0 },
  { id: "g1", name: "Алексей", years: "1920–1988", x: 5, y: 115, photo: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=80&h=80&fit=crop&crop=face", gen: 1 },
  { id: "g2", name: "Ольга", years: "1922–1995", x: 105, y: 115, photo: "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=80&h=80&fit=crop&crop=face", gen: 1 },
  { id: "g3", name: "Надежда", years: "1925–2002", x: 205, y: 115, photo: "https://images.unsplash.com/photo-1531123897727-8f129e1688ce?w=80&h=80&fit=crop&crop=face", gen: 1 },
  { id: "p1", name: "Сергей", years: "1950–2018", x: 50, y: 225, photo: "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=80&h=80&fit=crop&crop=face", gen: 2 },
  { id: "p2", name: "Татьяна", years: "1953–", x: 155, y: 225, photo: "https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=80&h=80&fit=crop&crop=face", gen: 2 },
  { id: "c1", name: "Дмитрий", years: "1978–", x: 105, y: 335, photo: "https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?w=80&h=80&fit=crop&crop=face", gen: 3 },
];

const connections = [
  { from: "gg1", to: "g1", cx1: 86, cy1: 55, cx2: 41, cy2: 115 },
  { from: "gg1", to: "g2", cx1: 86, cy1: 55, cx2: 141, cy2: 115 },
  { from: "gg2", to: "g3", cx1: 191, cy1: 55, cx2: 241, cy2: 115 },
  { from: "g1", to: "p1", cx1: 41, cy1: 165, cx2: 86, cy2: 225 },
  { from: "g2", to: "p2", cx1: 141, cy1: 165, cx2: 191, cy2: 225 },
  { from: "p1", to: "c1", cx1: 86, cy1: 275, cx2: 141, cy2: 335 },
  { from: "p2", to: "c1", cx1: 191, cy1: 275, cx2: 141, cy2: 335 },
];

function TreeNode({ person, index }) {
  return (
    <motion.g
      initial={{ opacity: 0, scale: 0.5 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.12, duration: 0.5, type: "spring", stiffness: 120 }}
    >
      <defs>
        <clipPath id={`clip-${person.id}`}>
          <circle cx={person.x + 32} cy={person.y + 32} r={28} />
        </clipPath>
        <filter id={`shadow-${person.id}`}>
          <feDropShadow dx="0" dy="4" stdDeviation="6" floodOpacity="0.12" />
        </filter>
      </defs>

      {/* Card background */}
      <rect
        x={person.x}
        y={person.y}
        width={86}
        height={60}
        rx={16}
        fill="white"
        filter={`url(#shadow-${person.id})`}
        className="transition-all duration-300"
      />

      {/* Photo circle */}
      <circle cx={person.x + 32} cy={person.y + 30} r={22} fill="hsl(35,40%,92%)" />
      <image
        href={person.photo}
        x={person.x + 10}
        y={person.y + 8}
        width={44}
        height={44}
        clipPath={`url(#clip-${person.id})`}
        preserveAspectRatio="xMidYMid slice"
      />

      {/* Name */}
      <text x={person.x + 62} y={person.y + 26} fontSize="9" fontWeight="600" fill="hsl(30,10%,15%)" textAnchor="middle">
        {person.name}
      </text>
      <text x={person.x + 62} y={person.y + 38} fontSize="7.5" fill="hsl(30,8%,50%)" textAnchor="middle">
        {person.years}
      </text>
    </motion.g>
  );
}

export default function HeroTree() {
  return (
    <div className="w-full flex justify-center animate-float">
      <svg
        viewBox="-10 -10 310 415"
        className="w-full max-w-sm md:max-w-md drop-shadow-xl"
        style={{ filter: "drop-shadow(0 20px 60px hsla(145,35%,38%,0.12))" }}
      >
        {/* Background subtle glow */}
        <ellipse cx="145" cy="200" rx="130" ry="180" fill="hsla(145,35%,38%,0.04)" />

        {/* Connections */}
        {connections.map((c, i) => (
          <motion.path
            key={i}
            d={`M ${c.cx1} ${c.cy1} C ${c.cx1} ${(c.cy1 + c.cy2) / 2}, ${c.cx2} ${(c.cy1 + c.cy2) / 2}, ${c.cx2} ${c.cy2}`}
            fill="none"
            stroke="hsl(145,35%,38%)"
            strokeWidth="1.8"
            strokeDasharray="4 3"
            opacity="0.35"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 0.35 }}
            transition={{ delay: 0.3 + i * 0.1, duration: 0.8 }}
          />
        ))}

        {/* Partner lines */}
        <motion.line x1="91" y1="30" x2="155" y2="30" stroke="hsl(30,50%,65%)" strokeWidth="2" strokeDasharray="4 3" opacity="0.4"
          initial={{ scaleX: 0 }} animate={{ scaleX: 1 }} transition={{ delay: 1 }} />
        <motion.line x1="91" y1="250" x2="155" y2="250" stroke="hsl(30,50%,65%)" strokeWidth="2" strokeDasharray="4 3" opacity="0.4"
          initial={{ scaleX: 0 }} animate={{ scaleX: 1 }} transition={{ delay: 1.2 }} />

        {/* Nodes */}
        {people.map((p, i) => <TreeNode key={p.id} person={p} index={i} />)}

        {/* YOU label */}
        <motion.rect x={98} y={387} width={56} height={16} rx={8} fill="hsl(145,35%,38%)"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.5 }} />
        <motion.text x={126} y={399} fontSize="8" fontWeight="700" fill="white" textAnchor="middle"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.6 }}>
          ВЫ
        </motion.text>
      </svg>
    </div>
  );
}