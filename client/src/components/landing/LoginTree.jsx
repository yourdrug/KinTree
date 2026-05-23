/**
 * components/landing/LoginTree.jsx
 *
 * Красивое декоративное семейное дерево для левой панели страницы входа.
 */

import { motion } from "framer-motion";

/* ── Данные узлов ──────────────────────────────────────────────────────────── */

const NODES = [
  // gen 0 — прародители
  { id: "gf",  gen: 0, col: 0, label: "Дед",    init: "А", years: "1928",  ring: "#9FE1CB", dot: "#085041" },
  { id: "gm",  gen: 0, col: 1, label: "Баба",   init: "М", years: "1932",  ring: "#F4C0D1", dot: "#72243E" },
  // gen 1 — родители + дядя
  { id: "dad", gen: 1, col: 0, label: "Папа",   init: "В", years: "1958",  ring: "#B5D4F4", dot: "#0C447C" },
  { id: "mom", gen: 1, col: 1, label: "Мама",   init: "Е", years: "1961",  ring: "#F4C0D1", dot: "#72243E" },
  { id: "unc", gen: 1, col: 2, label: "Дядя",   init: "С", years: "1964",  ring: "#C0DD97", dot: "#27500A" },
  // gen 2 — братья/сёстры
  { id: "bro", gen: 2, col: 0, label: "Брат",   init: "Д", years: "1986",  ring: "#B5D4F4", dot: "#0C447C" },
  { id: "sis", gen: 2, col: 1, label: "Сестра", init: "А", years: "1989",  ring: "#F4C0D1", dot: "#72243E" },
  { id: "cuz", gen: 2, col: 2, label: "Кузен",  init: "И", years: "1991",  ring: "#C0DD97", dot: "#27500A" },
  // gen 3 — вы
  { id: "me",  gen: 3, col: 1, label: "Вы",     init: "Я", years: "н.в.", ring: "#5DCAA5", dot: "#04342C", isYou: true },
];

/* ── Рёбра ─────────────────────────────────────────────────────────────────── */

const EDGES = [
  ["gf",  "dad"], ["gf",  "mom"],
  ["gm",  "mom"], ["gm",  "unc"],
  ["dad", "bro"], ["dad", "sis"],
  ["mom", "sis"], ["mom", "me"],
  ["bro", "me"],
  ["unc", "cuz"],
];

/* Партнёрские линии (горизонтальные) */
const PARTNER_EDGES = [
  ["gf", "gm"],
  ["dad", "mom"],
];

/* ── Layout ─────────────────────────────────────────────────────────────────── */

const CARD_W   = 70;
const CARD_H   = 72;
const COL_GAP  = 26;         // горизонтальный зазор между карточками
const ROW_GAP  = 56;         // вертикальный зазор между поколениями
const PAD_Y    = 16;

// Количество колонок в каждом поколении
const GEN_COLS = [2, 3, 3, 1];

// X-начало первой карточки поколения (центрируем в viewBox 380px)
const VB_W = 380;

function genStartX(gen) {
  const cols  = GEN_COLS[gen];
  const total = cols * CARD_W + (cols - 1) * COL_GAP;
  return (VB_W - total) / 2;
}

// Позиция [x, y] левого верхнего угла карточки
function cardPos(node) {
  const sx = genStartX(node.gen);
  const x  = sx + node.col * (CARD_W + COL_GAP);
  const y  = PAD_Y + node.gen * (CARD_H + ROW_GAP);
  return { x, y };
}

const byId = Object.fromEntries(NODES.map((n) => [n.id, n]));

// Итоговая высота viewBox
const VB_H = PAD_Y + GEN_COLS.length * CARD_H + (GEN_COLS.length - 1) * ROW_GAP + PAD_Y + 8;

/* ── Кривая между двумя узлами ─────────────────────────────────────────────── */

function curvePath(n1, n2) {
  const p1 = cardPos(n1);
  const p2 = cardPos(n2);
  // выход из нижней середины n1, вход в верхнюю середину n2
  const x1 = p1.x + CARD_W / 2;
  const y1 = p1.y + CARD_H;
  const x2 = p2.x + CARD_W / 2;
  const y2 = p2.y;
  const mid = (y1 + y2) / 2;
  return `M ${x1} ${y1} C ${x1} ${mid}, ${x2} ${mid}, ${x2} ${y2}`;
}

/* ── Партнёрская линия между серединами правого края n1 и левого края n2 ───── */

function partnerPath(n1, n2) {
  const p1 = cardPos(n1);
  const p2 = cardPos(n2);
  const y  = p1.y + CARD_H / 2;
  return { x1: p1.x + CARD_W, y1: y, x2: p2.x, y2: y };
}

/* ── Анимации ───────────────────────────────────────────────────────────────── */

const pathAnim = {
  hidden:  { pathLength: 0, opacity: 0 },
  visible: (i) => ({
    pathLength: 1,
    opacity:    1,
    transition: { delay: 0.1 + i * 0.06, duration: 0.65, ease: "easeOut" },
  }),
};

const cardAnim = {
  hidden:  { opacity: 0, scale: 0.5 },
  visible: (i) => ({
    opacity: 1,
    scale:   1,
    transition: { delay: 0.35 + i * 0.08, type: "spring", stiffness: 260, damping: 22 },
  }),
};

/* ── Component ──────────────────────────────────────────────────────────────── */

export default function LoginTree() {
  return (
    <div style={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <svg
        viewBox={`0 0 ${VB_W} ${VB_H}`}
        style={{ width: "100%", maxWidth: 320, overflow: "visible" }}
        aria-hidden="true"
      >
        {/* ── Партнёрские линии ── */}
        {PARTNER_EDGES.map(([aId, bId], i) => {
          const a  = byId[aId];
          const b  = byId[bId];
          const ln = partnerPath(a, b);
          return (
            <motion.line
              key={`p-${aId}-${bId}`}
              x1={ln.x1} y1={ln.y1} x2={ln.x2} y2={ln.y2}
              stroke="#FAC775"
              strokeWidth="1.5"
              strokeDasharray="5 3"
              strokeLinecap="round"
              initial={{ scaleX: 0, opacity: 0 }}
              animate={{ scaleX: 1, opacity: 0.7 }}
              transition={{ delay: 0.8 + i * 0.2, duration: 0.45 }}
              style={{ transformOrigin: `${(ln.x1 + ln.x2) / 2}px ${ln.y1}px` }}
            />
          );
        })}

        {/* ── Ветви ── */}
        {EDGES.map(([aId, bId], i) => {
          const a = byId[aId];
          const b = byId[bId];
          return (
            <motion.path
              key={`e-${aId}-${bId}`}
              d={curvePath(a, b)}
              fill="none"
              stroke="rgba(157,225,203,0.45)"
              strokeWidth="1.5"
              strokeLinecap="round"
              custom={i}
              variants={pathAnim}
              initial="hidden"
              animate="visible"
            />
          );
        })}

        {/* ── Карточки узлов ── */}
        {NODES.map((node, i) => {
          const { x, y }   = cardPos(node);
          const isYou       = node.isYou;
          const cx          = x + CARD_W / 2;
          const avatarY     = y + 20;
          const nameY       = y + CARD_H * 0.62;
          const yearY       = y + CARD_H * 0.82;

          return (
            <motion.g
              key={node.id}
              custom={i}
              variants={cardAnim}
              initial="hidden"
              animate="visible"
              style={{ transformOrigin: `${cx}px ${y + CARD_H / 2}px` }}
            >
              {/* Карточка-фон */}
              <rect
                x={x} y={y}
                width={CARD_W}
                height={CARD_H}
                rx={isYou ? 18 : 14}
                fill={isYou ? "rgba(8,80,65,0.85)" : "rgba(255,255,255,0.09)"}
                stroke={node.ring}
                strokeWidth={isYou ? 1.8 : 0.8}
              />

              {/* Аватар-круг */}
              <circle
                cx={cx}
                cy={avatarY}
                r={isYou ? 14 : 12}
                fill={node.ring}
                opacity={0.92}
              />

              {/* Инициал */}
              <text
                x={cx} y={avatarY + 4}
                textAnchor="middle"
                fontSize={isYou ? 11 : 10}
                fontWeight="600"
                fontFamily="system-ui, sans-serif"
                fill={node.dot}
              >
                {node.init}
              </text>

              {/* Имя */}
              <text
                x={cx} y={nameY}
                textAnchor="middle"
                fontSize={isYou ? 11 : 10}
                fontWeight={isYou ? "600" : "500"}
                fontFamily="system-ui, sans-serif"
                fill={isYou ? "white" : "rgba(255,255,255,0.88)"}
              >
                {node.label}
              </text>

              {/* Год */}
              <text
                x={cx} y={yearY}
                textAnchor="middle"
                fontSize="8.5"
                fontFamily="system-ui, sans-serif"
                fill={isYou ? node.ring : "rgba(255,255,255,0.4)"}
              >
                {node.years}
              </text>
            </motion.g>
          );
        })}
      </svg>
    </div>
  );
}
