import React from 'react';
import { motion } from 'framer-motion';

const people = [
  { id: 1, name: 'Александр', years: '1935–2010', x: 200, y: 40, gen: 0 },
  { id: 2, name: 'Мария', years: '1938–2015', x: 340, y: 40, gen: 0 },
  { id: 3, name: 'Николай', years: '1960', x: 120, y: 160, gen: 1 },
  { id: 4, name: 'Елена', years: '1963', x: 270, y: 160, gen: 1 },
  { id: 5, name: 'Сергей', years: '1965', x: 420, y: 160, gen: 1 },
  { id: 6, name: 'Анна', years: '1988', x: 80, y: 280, gen: 2 },
  { id: 7, name: 'Дмитрий', years: '1990', x: 220, y: 280, gen: 2 },
  { id: 8, name: 'Ольга', years: '1992', x: 370, y: 280, gen: 2 },
  { id: 9, name: 'Максим', years: '2015', x: 150, y: 390, gen: 3 },
  { id: 10, name: 'София', years: '2018', x: 300, y: 390, gen: 3 },
];

const connections = [
  [1, 3], [1, 4], [2, 4], [2, 5],
  [3, 6], [4, 7], [4, 8], [5, 8],
  [7, 9], [7, 10], [8, 10],
];

const genColors = [
  'from-primary/20 to-primary/5',
  'from-accent/60 to-accent/20',
  'from-secondary to-secondary/40',
  'from-primary/10 to-accent/30',
];

export default function HeroTreeVisual() {
  const getNode = (id) => people.find(p => p.id === id);

  return (
    <div className="relative w-full aspect-square max-w-[520px] mx-auto">
      {/* Glow background */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-accent/10 to-secondary/20 rounded-3xl" />

      <svg className="absolute inset-0 w-full h-full" viewBox="0 0 520 450" fill="none">
        {connections.map(([fromId, toId], i) => {
          const from = getNode(fromId);
          const to = getNode(toId);
          if (!from || !to) return null;
          const midY = (from.y + 30 + to.y) / 2;
          return (
            <motion.path
              key={i}
              d={`M${from.x + 35} ${from.y + 50} C${from.x + 35} ${midY}, ${to.x + 35} ${midY}, ${to.x + 35} ${to.y}`}
              stroke="hsl(var(--primary))"
              strokeOpacity={0.2}
              strokeWidth={2}
              fill="none"
              initial={{ pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 1.2, delay: 0.3 + i * 0.08, ease: "easeOut" }}
            />
          );
        })}
      </svg>

      {people.map((person, i) => (
        <motion.div
          key={person.id}
          initial={{ opacity: 0, scale: 0.6 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, delay: 0.5 + i * 0.08, type: "spring", stiffness: 200 }}
          className="absolute group cursor-pointer"
          style={{ left: person.x, top: person.y }}
        >
          <div className={`
            w-[70px] h-[60px] rounded-2xl bg-gradient-to-br ${genColors[person.gen]}
            backdrop-blur-sm border border-white/40 shadow-sm
            flex flex-col items-center justify-center
            group-hover:shadow-lg group-hover:scale-110 group-hover:border-primary/30
            transition-all duration-300
          `}>
            <div className="w-6 h-6 rounded-full bg-primary/15 border border-primary/20 mb-1" />
            <span className="text-[9px] font-medium text-foreground/80 truncate max-w-[60px] text-center">{person.name}</span>
            <span className="text-[7px] text-muted-foreground">{person.years}</span>
          </div>
        </motion.div>
      ))}
    </div>
  );
}