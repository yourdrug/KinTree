/**
 * components/tree/modalAtoms.jsx
 *
 * Атомарные компоненты модала добавления персоны:
 *   PersonPicker   — выпадающий список выбора человека
 *   ToggleCheckbox — переключатель-чекбокс
 *   RadioGroup     — группа радиокнопок
 *   SectionCard    — секция с заголовком
 */

import { useState, useMemo, useRef, useCallback, useEffect } from "react";
import { createPortal } from "react-dom";
import { motion } from "framer-motion";
import { Search, ChevronDown, Check } from "lucide-react";

// ── Helpers ───────────────────────────────────────────────────────────────────

export function personLabel(p) {
  const name = [p.first_name, p.last_name].filter(Boolean).join(" ") || p.full_name || "—";
  const year = p.birth_year ? ` · ${p.birth_year}` : "";
  return name + year;
}

// ── PersonPicker ──────────────────────────────────────────────────────────────

export function PersonPicker({ nodes, value, onChange, placeholder = "Выберите человека", exclude = [] }) {
  const [open, setOpen]       = useState(false);
  const [query, setQuery]     = useState("");
  const [dropPos, setDropPos] = useState({ top: 0, left: 0, width: 0 });
  const triggerRef            = useRef(null);
  const dropdownRef           = useRef(null);

  const filtered = useMemo(() => {
    if (!nodes) return [];
    const q = query.toLowerCase();
    return nodes
      .filter(n => !exclude.includes(n.id))
      .filter(n => !q || personLabel(n).toLowerCase().includes(q));
  }, [nodes, query, exclude]);

  const selected = value ? nodes?.find(n => n.id === value) : null;

  const calcPos = useCallback(() => {
    if (!triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    setDropPos({ top: rect.bottom + window.scrollY + 4, left: rect.left + window.scrollX, width: rect.width });
  }, []);

  const handleOpen = (e) => { e.stopPropagation(); calcPos(); setOpen(v => !v); };

  useEffect(() => {
    if (!open) return;
    const handler = (e) => {
      if (
        triggerRef.current && !triggerRef.current.contains(e.target) &&
        dropdownRef.current && !dropdownRef.current.contains(e.target)
      ) { setOpen(false); setQuery(""); }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const handler = () => calcPos();
    window.addEventListener("scroll", handler, true);
    window.addEventListener("resize", handler);
    return () => { window.removeEventListener("scroll", handler, true); window.removeEventListener("resize", handler); };
  }, [open, calcPos]);

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        onClick={handleOpen}
        className="w-full flex items-center justify-between gap-2 h-10 px-3 rounded-xl text-sm transition-colors"
        style={{
          background: "white",
          border:     `1.5px solid ${open ? "hsl(145,35%,52%)" : "hsl(35,20%,88%)"}`,
          color:      selected ? "hsl(30,10%,15%)" : "hsl(30,8%,55%)",
        }}
      >
        <span className="truncate">{selected ? personLabel(selected) : placeholder}</span>
        <ChevronDown className="w-3.5 h-3.5 flex-shrink-0 text-muted-foreground" style={{
          transform: open ? "rotate(180deg)" : "rotate(0deg)", transition: "transform 0.15s",
        }} />
      </button>

      {open && createPortal(
        <div ref={dropdownRef} style={{ position: "fixed", top: dropPos.top, left: dropPos.left, width: dropPos.width, zIndex: 9999 }}>
          <motion.div
            initial={{ opacity: 0, y: -6, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.13 }}
            className="rounded-2xl shadow-2xl overflow-hidden"
            style={{ background: "white", border: "1px solid hsl(35,20%,88%)" }}
          >
            <div className="p-2" style={{ borderBottom: "1px solid hsl(35,20%,92%)" }}>
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
                <input
                  autoFocus value={query} onChange={e => setQuery(e.target.value)}
                  placeholder="Поиск..."
                  className="w-full pl-8 pr-3 h-8 text-sm rounded-lg outline-none"
                  style={{ background: "hsl(35,25%,95%)", border: "none" }}
                />
              </div>
            </div>
            <div className="max-h-52 overflow-y-auto">
              <button
                type="button"
                onClick={() => { onChange(null); setOpen(false); setQuery(""); }}
                className="w-full flex items-center gap-2 px-3 py-2.5 text-sm hover:bg-muted/50 transition-colors text-muted-foreground"
              >
                — Не выбрано
              </button>
              {filtered.map(n => (
                <button
                  key={n.id} type="button"
                  onClick={() => { onChange(n.id); setOpen(false); setQuery(""); }}
                  className="w-full flex items-center justify-between gap-2 px-3 py-2.5 text-sm hover:bg-muted/50 transition-colors"
                  style={{ color: "hsl(30,10%,15%)" }}
                >
                  <span className="truncate">{personLabel(n)}</span>
                  {n.id === value && <Check className="w-3.5 h-3.5 flex-shrink-0 text-primary" />}
                </button>
              ))}
              {filtered.length === 0 && (
                <div className="px-3 py-4 text-center text-sm text-muted-foreground">Никого не найдено</div>
              )}
            </div>
          </motion.div>
        </div>,
        document.body
      )}
    </>
  );
}

// ── ToggleCheckbox ────────────────────────────────────────────────────────────

export function ToggleCheckbox({ checked, onChange, label, sublabel }) {
  return (
    <button type="button" onClick={() => onChange(!checked)} className="flex items-start gap-2.5 text-left w-full">
      <div
        className="w-5 h-5 rounded-md flex items-center justify-center flex-shrink-0 transition-all mt-0.5"
        style={{
          background: checked ? "hsl(145,35%,38%)" : "white",
          border:     `2px solid ${checked ? "hsl(145,35%,38%)" : "hsl(35,20%,78%)"}`,
        }}
      >
        {checked && <Check className="w-3 h-3 text-white" />}
      </div>
      <div>
        <span className="text-sm font-medium transition-colors" style={{ color: checked ? "hsl(145,35%,38%)" : "hsl(30,10%,40%)" }}>
          {label}
        </span>
        {sublabel && <p className="text-xs text-muted-foreground mt-0.5">{sublabel}</p>}
      </div>
    </button>
  );
}

// ── RadioGroup ────────────────────────────────────────────────────────────────

export function RadioGroup({ value, onChange, options }) {
  return (
    <div className="flex flex-col gap-2">
      {options.map(opt => (
        <button
          key={opt.value} type="button" onClick={() => onChange(opt.value)}
          className="flex items-center gap-2.5 text-sm transition-colors"
          style={{ color: value === opt.value ? "hsl(145,35%,30%)" : "hsl(30,10%,45%)" }}
        >
          <div
            className="w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 transition-all"
            style={{
              background: value === opt.value ? "hsl(145,35%,38%)" : "white",
              border:     `2px solid ${value === opt.value ? "hsl(145,35%,38%)" : "hsl(35,20%,78%)"}`,
            }}
          >
            {value === opt.value && <div className="w-1.5 h-1.5 rounded-full bg-white" />}
          </div>
          <span className="leading-snug">{opt.label}</span>
        </button>
      ))}
    </div>
  );
}

// ── SectionCard ───────────────────────────────────────────────────────────────

export function SectionCard({ title, icon: Icon, color, children }) {
  return (
    <div className="rounded-2xl" style={{ border: "1px solid hsl(35,20%,90%)" }}>
      <div className="flex items-center gap-2 px-4 py-3 rounded-t-2xl" style={{ background: "hsl(35,30%,96%)" }}>
        {Icon && <Icon className="w-3.5 h-3.5" style={{ color }} />}
        <span className="text-xs font-semibold uppercase tracking-wide" style={{ color }}>{title}</span>
      </div>
      <div className="px-4 py-4 space-y-3 rounded-b-2xl" style={{ background: "white" }}>
        {children}
      </div>
    </div>
  );
}
