/**
 * components/tree/PersonNode.jsx
 *
 * Добавлена подсветка ближайших родственников при hover:
 *
 * highlightRole:
 *   null      — нормальное состояние (нет hover)
 *   "hovered" — узел под курсором
 *   "parent"  — родитель hoveredId    → синий
 *   "child"   — ребёнок hoveredId     → бирюзовый
 *   "spouse"  — супруг(а) hoveredId   → розово-красный
 *   "sibling" — брат/сестра hoveredId → фиолетовый
 *   "dimmed"  — не связан с hoveredId → прозрачный (opacity 0.3)
 */

import { motion } from "framer-motion";
import { Plus, User } from "lucide-react";

// ── Конфиг стилей по роли ─────────────────────────────────────────────────────

const ROLE_STYLES = {
  hovered: {
    bg: "hsl(145,35%,38%)", border: "hsl(145,35%,38%)",
    shadow: "0 0 0 3px hsla(145,35%,38%,0.25), 0 8px 30px hsla(145,35%,38%,0.3)",
    text: "white", sub: "hsla(255,255%,255%,0.85)", year: "hsla(255,255%,255%,0.65)",
    avatarBg: "hsla(255,255%,255%,0.15)", avatarBorder: "hsla(255,255%,255%,0.3)", avatarIcon: "white",
    label: null, labelBg: null, scale: 1.08,
  },
  parent: {
    bg: "hsl(210,95%,98%)", border: "hsl(210,70%,52%)",
    shadow: "0 0 0 2px hsla(210,70%,52%,0.3), 0 6px 20px hsla(210,70%,52%,0.2)",
    text: "hsl(210,60%,25%)", sub: "hsl(210,50%,35%)", year: "hsl(210,40%,55%)",
    avatarBg: "hsl(210,85%,94%)", avatarBorder: "hsl(210,70%,75%)", avatarIcon: "hsl(210,60%,45%)",
    label: "Родитель", labelBg: "hsl(210,70%,52%)", scale: 1.05,
  },
  child: {
    bg: "hsl(175,80%,97%)", border: "hsl(175,55%,42%)",
    shadow: "0 0 0 2px hsla(175,55%,42%,0.3), 0 6px 20px hsla(175,55%,42%,0.2)",
    text: "hsl(175,50%,20%)", sub: "hsl(175,40%,30%)", year: "hsl(175,35%,45%)",
    avatarBg: "hsl(175,80%,92%)", avatarBorder: "hsl(175,55%,70%)", avatarIcon: "hsl(175,50%,35%)",
    label: "Ребёнок", labelBg: "hsl(175,55%,38%)", scale: 1.05,
  },
  spouse: {
    bg: "hsl(345,100%,98%)", border: "hsl(345,60%,55%)",
    shadow: "0 0 0 2px hsla(345,60%,55%,0.3), 0 6px 20px hsla(345,60%,55%,0.2)",
    text: "hsl(345,55%,25%)", sub: "hsl(345,45%,35%)", year: "hsl(345,40%,55%)",
    avatarBg: "hsl(345,90%,95%)", avatarBorder: "hsl(345,60%,78%)", avatarIcon: "hsl(345,55%,50%)",
    label: "Супруг(а)", labelBg: "hsl(345,60%,50%)", scale: 1.05,
  },
  sibling: {
    bg: "hsl(260,80%,98%)", border: "hsl(260,50%,55%)",
    shadow: "0 0 0 2px hsla(260,50%,55%,0.3), 0 6px 20px hsla(260,50%,55%,0.2)",
    text: "hsl(260,45%,25%)", sub: "hsl(260,35%,35%)", year: "hsl(260,30%,55%)",
    avatarBg: "hsl(260,80%,94%)", avatarBorder: "hsl(260,50%,75%)", avatarIcon: "hsl(260,45%,50%)",
    label: "Брат/Сестра", labelBg: "hsl(260,50%,50%)", scale: 1.05,
  },
};

// ── Component ─────────────────────────────────────────────────────────────────

export default function PersonNode({
  person,
  isSelected,
  onClick,
  canEdit,
  onAddChild,
  style = {},
  highlightRole,
  onMouseEnter,
  onMouseLeave,
}) {
  const birthYear = person.birth_year ?? null;
  const deathYear = person.death_year ?? null;
  const isAlive   = person.is_alive   ?? true;

  const yearsStr = birthYear
    ? `${birthYear} — ${isAlive ? "наст." : (deathYear ?? "?")}`
    : null;

  const displayFirst = person.first_name || person.full_name?.split(" ")[0] || "—";
  const displayLast  = person.last_name  || person.full_name?.split(" ").slice(1).join(" ") || "";

  const sel         = isSelected;
  const isDimmed    = highlightRole === "dimmed";
  const roleStyle   = !sel ? (ROLE_STYLES[highlightRole] ?? null) : null;
  const isLit       = !!roleStyle;

  // ── Visual vars ────────────────────────────────────────────────────────────
  const cardBg      = sel ? "hsl(145,35%,38%)" : (isLit ? roleStyle.bg      : "white");
  const borderColor = sel ? "hsl(145,35%,38%)" : (isLit ? roleStyle.border  : "hsl(35,20%,88%)");
  const shadow      = sel
    ? "0 8px 30px hsla(145,35%,38%,0.3)"
    : (isLit ? roleStyle.shadow : "0 4px 16px hsla(30,10%,15%,0.08)");

  const textColor     = sel ? "white"                          : (isLit ? roleStyle.text      : "hsl(30,10%,15%)");
  const subTextColor  = sel ? "hsla(255,255%,255%,0.9)"        : (isLit ? roleStyle.sub       : "hsl(30,10%,15%)");
  const yearColor     = sel ? "hsla(255,255%,255%,0.7)"        : (isLit ? roleStyle.year      : "hsl(30,8%,55%)");
  const avatarBg      = sel ? "hsla(255,255%,255%,0.15)"       : (isLit ? roleStyle.avatarBg  : "hsl(35,40%,92%)");
  const avatarBorder  = sel ? "hsla(255,255%,255%,0.3)"        : (isLit ? roleStyle.avatarBorder : "hsl(35,30%,90%)");
  const avatarIcon    = sel ? "white"                          : (isLit ? roleStyle.avatarIcon : "hsl(30,8%,50%)");

  const opacity    = isDimmed && !sel ? 0.28 : 1;
  const hoverScale = sel ? 1.0 : (roleStyle?.scale ?? 1.03);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.75 }}
      animate={{ opacity, scale: 1 }}
      transition={{
        opacity: { duration: 0.12 },
        scale:   { type: "spring", stiffness: 220, damping: 22 },
      }}
      whileHover={{ scale: hoverScale }}
      onClick={() => onClick(person)}
      onMouseEnter={() => onMouseEnter?.(person.id)}
      onMouseLeave={() => onMouseLeave?.()}
      className="absolute cursor-pointer select-none"
      style={{ left: style?.x ?? 0, top: style?.y ?? 0, width: 110 }}
    >
      <div
        style={{
          position:     "relative",
          background:   cardBg,
          border:       `2px solid ${borderColor}`,
          boxShadow:    shadow,
          borderRadius: "1rem",
          padding:      "0.75rem",
          textAlign:    "center",
          transition:   "background 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease",
        }}
      >
        {/* Плашка с ролью */}
        {isLit && !sel && roleStyle.label && (
          <div
            style={{
              position:      "absolute",
              top:           "-10px",
              left:          "50%",
              transform:     "translateX(-50%)",
              fontSize:      "8px",
              fontWeight:    700,
              letterSpacing: "0.05em",
              color:         "white",
              background:    roleStyle.labelBg,
              borderRadius:  "99px",
              padding:       "2px 8px",
              whiteSpace:    "nowrap",
              pointerEvents: "none",
              boxShadow:     "0 1px 4px rgba(0,0,0,0.15)",
            }}
          >
            {roleStyle.label}
          </div>
        )}

        {/* Avatar */}
        <div
          style={{
            margin:         "0 auto 0.5rem",
            width:          "3.5rem",
            height:         "3.5rem",
            borderRadius:   "50%",
            overflow:       "hidden",
            display:        "flex",
            alignItems:     "center",
            justifyContent: "center",
            border:         `2px solid ${avatarBorder}`,
            background:     avatarBg,
            transition:     "border-color 0.18s ease, background 0.18s ease",
          }}
        >
          <User className="w-6 h-6" style={{ color: avatarIcon, transition: "color 0.18s ease" }} />
        </div>

        {/* First name */}
        <div
          className="text-xs font-semibold leading-tight truncate"
          style={{ color: textColor, transition: "color 0.18s ease" }}
        >
          {displayFirst}
        </div>

        {/* Last name */}
        {displayLast && (
          <div
            className="text-xs font-semibold leading-tight truncate mb-1"
            style={{ color: subTextColor, transition: "color 0.18s ease" }}
          >
            {displayLast}
          </div>
        )}

        {/* Years */}
        {yearsStr && (
          <div
            className="text-[10px]"
            style={{ color: yearColor, transition: "color 0.18s ease" }}
          >
            {yearsStr}
          </div>
        )}

        {/* Dead marker */}
        {!isAlive && !deathYear && (
          <div className="text-[10px]" style={{ color: yearColor }}>†</div>
        )}
      </div>

      {/* Add child button */}
      {canEdit && sel && (
        <motion.button
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          onClick={(e) => { e.stopPropagation(); onAddChild?.(person); }}
          title="Добавить ребёнка"
          className="absolute -bottom-3 left-1/2 -translate-x-1/2 w-6 h-6 rounded-full flex items-center justify-center text-white shadow-md hover:scale-110 transition-transform z-10"
          style={{ background: "hsl(145,35%,38%)" }}
        >
          <Plus className="w-3 h-3" />
        </motion.button>
      )}
    </motion.div>
  );
}
