/**
 * components/tree/PersonNodeRF.jsx
 *
 * Кастомная нода для ReactFlow.
 * Принимает данные через props.data (стандарт ReactFlow).
 *
 * data shape:
 *   person        — объект персоны
 *   isSelected    — bool
 *   highlightRole — "hovered"|"parent"|"child"|"spouse"|"sibling"|"dimmed"|null
 *   canEdit       — bool
 *   onAddChild    — fn(person)
 *   onClick       — fn(person)   (дополнительно к onNodeClick ReactFlow)
 *   onMouseEnter  — fn(id)
 *   onMouseLeave  — fn()
 */

import { memo } from "react";
import { Handle, Position } from "reactflow";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, User } from "lucide-react";

// ── Role → visual config ──────────────────────────────────────────────────────

const ROLE_STYLES = {
  hovered: {
    bg: "hsl(145,35%,38%)",      border: "hsl(145,35%,38%)",
    shadow: "0 0 0 3px hsla(145,35%,38%,0.28), 0 8px 28px hsla(145,35%,38%,0.32)",
    text: "white",               sub: "rgba(255,255,255,0.85)",  year: "rgba(255,255,255,0.6)",
    avatarBg: "rgba(255,255,255,0.15)", avatarBorder: "rgba(255,255,255,0.3)", avatarIcon: "white",
    label: null,                 labelBg: null,
  },
  parent: {
    bg: "hsl(210,95%,98%)",      border: "hsl(210,70%,52%)",
    shadow: "0 0 0 2px hsla(210,70%,52%,0.28), 0 6px 18px hsla(210,70%,52%,0.18)",
    text: "hsl(210,60%,25%)",    sub: "hsl(210,50%,35%)",  year: "hsl(210,40%,55%)",
    avatarBg: "hsl(210,85%,94%)", avatarBorder: "hsl(210,70%,75%)", avatarIcon: "hsl(210,60%,45%)",
    label: "Родитель",           labelBg: "hsl(210,70%,52%)",
  },
  child: {
    bg: "hsl(175,80%,97%)",      border: "hsl(175,55%,42%)",
    shadow: "0 0 0 2px hsla(175,55%,42%,0.28), 0 6px 18px hsla(175,55%,42%,0.18)",
    text: "hsl(175,50%,20%)",    sub: "hsl(175,40%,30%)",  year: "hsl(175,35%,45%)",
    avatarBg: "hsl(175,80%,92%)", avatarBorder: "hsl(175,55%,70%)", avatarIcon: "hsl(175,50%,35%)",
    label: "Ребёнок",            labelBg: "hsl(175,55%,38%)",
  },
  spouse: {
    bg: "hsl(345,100%,98%)",     border: "hsl(345,60%,55%)",
    shadow: "0 0 0 2px hsla(345,60%,55%,0.28), 0 6px 18px hsla(345,60%,55%,0.18)",
    text: "hsl(345,55%,25%)",    sub: "hsl(345,45%,35%)",  year: "hsl(345,40%,55%)",
    avatarBg: "hsl(345,90%,95%)", avatarBorder: "hsl(345,60%,78%)", avatarIcon: "hsl(345,55%,50%)",
    label: "Супруг(а)",          labelBg: "hsl(345,60%,50%)",
  },
  sibling: {
    bg: "hsl(260,80%,98%)",      border: "hsl(260,50%,55%)",
    shadow: "0 0 0 2px hsla(260,50%,55%,0.28), 0 6px 18px hsla(260,50%,55%,0.18)",
    text: "hsl(260,45%,25%)",    sub: "hsl(260,35%,35%)",  year: "hsl(260,30%,55%)",
    avatarBg: "hsl(260,80%,94%)", avatarBorder: "hsl(260,50%,75%)", avatarIcon: "hsl(260,45%,50%)",
    label: "Брат/Сестра",        labelBg: "hsl(260,50%,50%)",
  },
};

// ── Component ─────────────────────────────────────────────────────────────────

function PersonNodeRF({ data }) {
  const {
    person,
    isSelected,
    highlightRole,
    canEdit,
    onAddChild,
    onMouseEnter,
    onMouseLeave,
  } = data;

  if (!person) return null;

  const birthYear = person.birth_year ?? null;
  const deathYear = person.death_year ?? null;
  const isAlive   = person.is_alive   ?? true;

  const yearsStr = birthYear
    ? `${birthYear} — ${isAlive ? "наст." : (deathYear ?? "?")}`
    : null;

  const displayFirst = person.first_name || person.full_name?.split(" ")[0] || "—";
  const displayLast  = person.last_name  || person.full_name?.split(" ").slice(1).join(" ") || "";

  const isDimmed  = highlightRole === "dimmed";
  const roleStyle = !isSelected ? (ROLE_STYLES[highlightRole] ?? null) : null;
  const isLit     = !!roleStyle;

  // Visual vars
  const cardBg      = isSelected ? "hsl(145,35%,38%)" : (isLit ? roleStyle.bg      : "white");
  const borderColor = isSelected ? "hsl(145,35%,38%)" : (isLit ? roleStyle.border  : "hsl(35,20%,88%)");
  const shadow      = isSelected
    ? "0 8px 30px hsla(145,35%,38%,0.3)"
    : (isLit ? roleStyle.shadow : "0 2px 12px hsla(30,10%,15%,0.07)");

  const textColor    = isSelected ? "white"                    : (isLit ? roleStyle.text      : "hsl(30,10%,15%)");
  const subColor     = isSelected ? "rgba(255,255,255,0.9)"    : (isLit ? roleStyle.sub       : "hsl(30,10%,15%)");
  const yearColor    = isSelected ? "rgba(255,255,255,0.65)"   : (isLit ? roleStyle.year      : "hsl(30,8%,55%)");
  const avatarBg     = isSelected ? "rgba(255,255,255,0.15)"   : (isLit ? roleStyle.avatarBg  : "hsl(35,40%,92%)");
  const avatarBorder = isSelected ? "rgba(255,255,255,0.3)"    : (isLit ? roleStyle.avatarBorder : "hsl(35,30%,90%)");
  const avatarIcon   = isSelected ? "white"                    : (isLit ? roleStyle.avatarIcon : "hsl(30,8%,50%)");

  const opacity = isDimmed && !isSelected ? 0.25 : 1;

  return (
    <>
      {/* ReactFlow handles — невидимые, нужны для рёбер */}
      <Handle type="target" position={Position.Top}    id="top"   style={{ opacity: 0, pointerEvents: "none" }} />
      <Handle type="source" position={Position.Bottom} id="bot"   style={{ opacity: 0, pointerEvents: "none" }} />
      <Handle type="source" position={Position.Left}   id="left"  style={{ opacity: 0, pointerEvents: "none" }} />
      <Handle type="target" position={Position.Right}  id="right" style={{ opacity: 0, pointerEvents: "none" }} />
      {/* Spouse edge handles: source on right side, target on left side */}
      <Handle type="source" position={Position.Right} id="right-src" style={{ opacity: 0, pointerEvents: "none" }} />
      <Handle type="target" position={Position.Left}  id="left-tgt"  style={{ opacity: 0, pointerEvents: "none" }} />
      <Handle type="source" position={Position.Top} id="sib-top"
        style={{ opacity: 0, pointerEvents: "none", left: "30%" }}
      />
      <Handle type="target" position={Position.Top} id="sib-top-t"
        style={{ opacity: 0, pointerEvents: "none", left: "30%" }}
      />

      <motion.div
        initial={{ opacity: 0, scale: 0.7 }}
        animate={{ opacity, scale: 1 }}
        transition={{ type: "spring", stiffness: 220, damping: 22 }}
        onMouseEnter={() => onMouseEnter?.(person.id)}
        onMouseLeave={() => onMouseLeave?.()}
        style={{ width: 140, cursor: "pointer", userSelect: "none" }}
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
            transition:   "background 0.18s, border-color 0.18s, box-shadow 0.18s",
          }}
        >
          {/* Плашка роли */}
          {isLit && !isSelected && roleStyle.label && (
            <div style={{
              position:      "absolute",
              top:           -11,
              left:          "50%",
              transform:     "translateX(-50%)",
              fontSize:      8,
              fontWeight:    700,
              letterSpacing: "0.05em",
              color:         "white",
              background:    roleStyle.labelBg,
              borderRadius:  99,
              padding:       "2px 8px",
              whiteSpace:    "nowrap",
              pointerEvents: "none",
              boxShadow:     "0 1px 4px rgba(0,0,0,0.15)",
            }}>
              {roleStyle.label}
            </div>
          )}

          {/* Avatar */}
          {person.photo_url ? (
            <img
              src={person.photo_url}
              alt={displayFirst}
              style={{
                width:        52,
                height:       52,
                borderRadius: "50%",
                objectFit:    "cover",
                margin:       "0 auto 8px",
                border:       `2px solid ${avatarBorder}`,
                display:      "block",
              }}
            />
          ) : (
            <div style={{
              width:          52,
              height:         52,
              borderRadius:   "50%",
              display:        "flex",
              alignItems:     "center",
              justifyContent: "center",
              margin:         "0 auto 8px",
              background:     avatarBg,
              border:         `2px solid ${avatarBorder}`,
              transition:     "background 0.18s, border-color 0.18s",
            }}>
              <User style={{ width: 22, height: 22, color: avatarIcon, transition: "color 0.18s" }} />
            </div>
          )}

          {/* First name */}
          <div style={{
            fontSize:     11,
            fontWeight:   600,
            color:        textColor,
            lineHeight:   1.3,
            overflow:     "hidden",
            textOverflow: "ellipsis",
            whiteSpace:   "nowrap",
            transition:   "color 0.18s",
          }}>
            {displayFirst}
          </div>

          {/* Last name */}
          {displayLast && (
            <div style={{
              fontSize:     11,
              fontWeight:   600,
              color:        subColor,
              lineHeight:   1.3,
              overflow:     "hidden",
              textOverflow: "ellipsis",
              whiteSpace:   "nowrap",
              marginBottom: 2,
              transition:   "color 0.18s",
            }}>
              {displayLast}
            </div>
          )}

          {/* Years */}
          <div style={{ fontSize: 9, color: yearColor, minHeight: 12, transition: "color 0.18s" }}>
            {yearsStr || (!isAlive ? "†" : "\u00A0")}
          </div>
        </div>

        {/* Add child button */}
        <AnimatePresence>
          {canEdit && isSelected && (
            <motion.button
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              onClick={(e) => { e.stopPropagation(); onAddChild?.(person); }}
              title="Добавить ребёнка"
              style={{
                position:       "absolute",
                bottom:         -14,
                left:           "70%",
                transform:      "translateX(-50%)",
                width:          24,
                height:         24,
                borderRadius:   "50%",
                background:     "hsl(145,35%,38%)",
                border:         "none",
                cursor:         "pointer",
                display:        "flex",
                alignItems:     "center",
                justifyContent: "center",
                boxShadow:      "0 2px 8px hsla(145,35%,38%,0.4)",
                zIndex:         10,
              }}
            >
              <Plus style={{ width: 12, height: 12, color: "white" }} />
            </motion.button>
          )}
        </AnimatePresence>
      </motion.div>
    </>
  );
}

export default memo(PersonNodeRF);
