/**
 * components/tree/AddPersonModal.jsx
 */

import { useState, useEffect, useMemo, useRef, useCallback } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { X, AlertTriangle, Link2, UserCheck, Search, ChevronDown, Check } from "lucide-react";
import { Button }           from "@/components/ui/button";
import { Input }            from "@/components/ui/input";
import { Label }            from "@/components/ui/label";
import {
  Select, SelectContent, SelectItem,
  SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { getPersonRelations } from "@/api";

// ── Constants ─────────────────────────────────────────────────────────────────

const RELATION_TYPES = [
  { value: "child",   label: "Ребёнок" },
  { value: "parent",  label: "Родитель" },
  { value: "partner", label: "Партнёр / Супруг(а)" },
  { value: "sibling", label: "Брат / Сестра" },
];

// connect relation types — labels are built dynamically from selected person names
const CONNECT_RELATION_TYPES = [
  { value: "parent_child_ab", labelFn: (a, b) => a && b ? `${a} — родитель ${b}` : "Первый — родитель второго" },
  { value: "parent_child_ba", labelFn: (a, b) => a && b ? `${b} — родитель ${a}` : "Второй — родитель первого" },
  { value: "spouse",          labelFn: ()      => "Супруги / Партнёры" },
  { value: "sibling",         labelFn: ()      => "Братья / Сёстры" },
];

const GENDERS = [
  { value: "MALE",   label: "Мужской" },
  { value: "FEMALE", label: "Женский" },
  { value: "OTHER",  label: "Другой" },
];

// ── Helpers ───────────────────────────────────────────────────────────────────

function buildEmptyForm() {
  return { first_name: "", last_name: "", birth_date: "", death_date: "", gender: "MALE" };
}

function formFromNode(node) {
  return {
    first_name: node.first_name  || node.full_name?.split(" ")[0] || "",
    last_name:  node.last_name   || node.full_name?.split(" ").slice(1).join(" ") || "",
    gender:     node.gender      || "MALE",
    birth_date: node.birth_year  ? String(node.birth_year)  : "",
    death_date: node.death_year  ? String(node.death_year)  : "",
  };
}

function personLabel(p) {
  const name = [p.first_name, p.last_name].filter(Boolean).join(" ") || p.full_name || "—";
  const year = p.birth_year ? ` · ${p.birth_year}` : "";
  return name + year;
}

// ── PersonPicker — выпадающий список с порталом (не срезается overflow) ───────

function PersonPicker({ nodes, value, onChange, placeholder = "Выберите человека", exclude = [] }) {
  const [open, setOpen]         = useState(false);
  const [query, setQuery]       = useState("");
  const [dropPos, setDropPos]   = useState({ top: 0, left: 0, width: 0 });
  const triggerRef              = useRef(null);
  const dropdownRef             = useRef(null);

  const filtered = useMemo(() => {
    if (!nodes) return [];
    const q = query.toLowerCase();
    return nodes
      .filter(n => !exclude.includes(n.id))
      .filter(n => {
        const label = personLabel(n).toLowerCase();
        return !q || label.includes(q);
      });
  }, [nodes, query, exclude]);

  const selected = value ? nodes?.find(n => n.id === value) : null;

  // Calculate dropdown position relative to viewport
  const calcPos = useCallback(() => {
    if (!triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    setDropPos({
      top:   rect.bottom + window.scrollY + 4,
      left:  rect.left   + window.scrollX,
      width: rect.width,
    });
  }, []);

  const handleOpen = (e) => {
    e.stopPropagation();
    calcPos();
    setOpen(v => !v);
  };

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    const handler = (e) => {
      if (
        triggerRef.current && !triggerRef.current.contains(e.target) &&
        dropdownRef.current && !dropdownRef.current.contains(e.target)
      ) {
        setOpen(false);
        setQuery("");
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  // Reposition on scroll/resize
  useEffect(() => {
    if (!open) return;
    const handler = () => calcPos();
    window.addEventListener("scroll", handler, true);
    window.addEventListener("resize", handler);
    return () => {
      window.removeEventListener("scroll", handler, true);
      window.removeEventListener("resize", handler);
    };
  }, [open, calcPos]);

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        onClick={handleOpen}
        className="w-full flex items-center justify-between gap-2 h-10 px-3 rounded-xl text-sm transition-colors"
        style={{
          background:   "white",
          border:       `1.5px solid ${open ? "hsl(145,35%,52%)" : "hsl(35,20%,88%)"}`,
          color:        selected ? "hsl(30,10%,15%)" : "hsl(30,8%,55%)",
        }}
      >
        <span className="truncate">{selected ? personLabel(selected) : placeholder}</span>
        <ChevronDown className="w-3.5 h-3.5 flex-shrink-0 text-muted-foreground" style={{
          transform: open ? "rotate(180deg)" : "rotate(0deg)",
          transition: "transform 0.15s",
        }} />
      </button>

      {open && createPortal(
        <div
          ref={dropdownRef}
          style={{
            position: "fixed",
            top:      dropPos.top,
            left:     dropPos.left,
            width:    dropPos.width,
            zIndex:   9999,
          }}
        >
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
                  autoFocus
                  value={query}
                  onChange={e => setQuery(e.target.value)}
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
                  key={n.id}
                  type="button"
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

// ── Toggle Checkbox ───────────────────────────────────────────────────────────

function ToggleCheckbox({ checked, onChange, label }) {
  return (
    <button
      type="button"
      onClick={() => onChange(!checked)}
      className="flex items-center gap-2.5 text-sm font-medium transition-colors"
      style={{ color: checked ? "hsl(145,35%,38%)" : "hsl(30,10%,40%)" }}
    >
      <div
        className="w-5 h-5 rounded-md flex items-center justify-center flex-shrink-0 transition-all"
        style={{
          background:  checked ? "hsl(145,35%,38%)" : "white",
          border:      `2px solid ${checked ? "hsl(145,35%,38%)" : "hsl(35,20%,78%)"}`,
        }}
      >
        {checked && <Check className="w-3 h-3 text-white" />}
      </div>
      {label}
    </button>
  );
}

// ── RadioGroup ────────────────────────────────────────────────────────────────

function RadioGroup({ value, onChange, options }) {
  return (
    <div className="flex flex-col gap-2">
      {options.map(opt => (
        <button
          key={opt.value}
          type="button"
          onClick={() => onChange(opt.value)}
          className="flex items-center gap-2.5 text-sm transition-colors"
          style={{ color: value === opt.value ? "hsl(145,35%,30%)" : "hsl(30,10%,45%)" }}
        >
          <div
            className="w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 transition-all"
            style={{
              background:  value === opt.value ? "hsl(145,35%,38%)" : "white",
              border:      `2px solid ${value === opt.value ? "hsl(145,35%,38%)" : "hsl(35,20%,78%)"}`,
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

function SectionCard({ title, icon: Icon, color, children }) {
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

// ── Main component ─────────────────────────────────────────────────────────────

export default function AddPersonModal({
  open, onClose, onSave, onConnect,
  relativePerson, editPerson, relationMaps,
  nodes = [],
}) {
  const [relationType,       setRelationType]       = useState("child");
  const [form,               setForm]               = useState(buildEmptyForm());
  const [saving,             setSaving]             = useState(false);

  // Connect mode (связать двух существующих)
  const [connectMode,        setConnectMode]        = useState(false);
  const [connectPersonA,     setConnectPersonA]     = useState(null);
  const [connectPersonB,     setConnectPersonB]     = useState(null);
  const [connectRelType,     setConnectRelType]     = useState("spouse");

  // Child + parents married checkbox
  const [parentsMarried,     setParentsMarried]     = useState(false);
  const [secondParentId,     setSecondParentId]     = useState(null); // existing person
  const [marriageDate,       setMarriageDate]       = useState("");
  const [divorceDate,        setDivorceDate]        = useState("");

  // Sibling parents mode
  const [siblingParentMode,  setSiblingParentMode]  = useState("same"); // "same" | "different"
  const [siblingParentId,    setSiblingParentId]    = useState(null);   // additional parent for "different"

  const isEdit = !!editPerson;

  useEffect(() => {
    if (!open) return;
    if (isEdit) {
      setForm(formFromNode(editPerson));
      setConnectMode(false);
      // Pre-fill person A with the person being edited when switching to connect mode
      setConnectPersonA(editPerson.id);
      setConnectPersonB(null);
      setConnectRelType("spouse");
      setMarriageDate("");
      setDivorceDate("");
    } else {
      setRelationType("child");
      setForm(buildEmptyForm());
      setConnectMode(false);
      setConnectPersonA(relativePerson?.id ?? null);
      setConnectPersonB(null);
      setConnectRelType("spouse");
      setParentsMarried(false);
      setSecondParentId(null);
      setMarriageDate("");
      setDivorceDate("");
      setSiblingParentMode("same");
      setSiblingParentId(null);
    }
  }, [open, editPerson, isEdit, relativePerson]);

  const setField = (key, value) => setForm(f => ({ ...f, [key]: value }));

  // Siblings warning
  const siblingNoParents =
    !isEdit &&
    relationType === "sibling" &&
    relativePerson &&
    relationMaps &&
    getPersonRelations(relationMaps, relativePerson.id).parentIds.length === 0;

  // Relative's existing parents
  const relativeParents = useMemo(() => {
    if (!relativePerson || !relationMaps || !nodes.length) return [];
    const rel = getPersonRelations(relationMaps, relativePerson.id);
    return rel.parentIds.map(id => nodes.find(n => n.id === id)).filter(Boolean);
  }, [relativePerson, relationMaps, nodes]);

  // ── Save ──────────────────────────────────────────────────────────────────

  const handleSave = async () => {
    if (saving) return;
    setSaving(true);
    try {
      // Connect existing persons mode
      if (connectMode) {
        if (!connectPersonA || !connectPersonB) return;
        await onConnect?.({ personA: connectPersonA, personB: connectPersonB, relType: connectRelType, marriageDate, divorceDate });
        onClose();
        return;
      }

      // Extra data passed alongside the form
      const extra = {};

      if (!isEdit && relationType === "child" && parentsMarried && secondParentId) {
        extra.secondParentId  = secondParentId;
        extra.parentsMarried  = true;
        extra.marriageDate    = marriageDate || null;
        extra.divorceDate     = divorceDate  || null;
      }

      if (!isEdit && relationType === "sibling") {
        extra.siblingParentMode = siblingParentMode;
        extra.siblingParentId   = siblingParentMode === "different" ? siblingParentId : null;
      }

      await onSave(form, editPerson?.id, relationType, relativePerson, extra);
      onClose();
    } catch {
      // error shown via toast in TreeView
    } finally {
      setSaving(false);
    }
  };

  // Short first names for relation type labels
  const nameA = useMemo(() => {
    if (!connectPersonA) return null;
    const p = nodes.find(n => n.id === connectPersonA);
    return p ? (p.first_name || p.full_name?.split(" ")[0] || "Первый") : null;
  }, [connectPersonA, nodes]);

  const nameB = useMemo(() => {
    if (!connectPersonB) return null;
    const p = nodes.find(n => n.id === connectPersonB);
    return p ? (p.first_name || p.full_name?.split(" ")[0] || "Второй") : null;
  }, [connectPersonB, nodes]);

  const canSave = connectMode
    ? (connectPersonA && connectPersonB && connectPersonA !== connectPersonB)
    : (form.first_name?.trim() && form.last_name?.trim() && !saving);

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: "hsla(30,10%,15%,0.55)", backdropFilter: "blur(10px)" }}
          onClick={e => e.target === e.currentTarget && !saving && onClose()}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.93, y: 24 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.93, y: 24 }}
            transition={{ type: "spring", stiffness: 320, damping: 28 }}
            className="w-full max-w-md rounded-3xl shadow-2xl"
            style={{ background: "hsl(40,33%,98%)", border: "1px solid hsl(35,20%,88%)" }}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 pt-6 pb-4"
              style={{ borderBottom: "1px solid hsl(35,20%,90%)" }}>
              <div>
                <h2 className="font-serif text-xl font-semibold text-foreground">
                  {isEdit && connectMode
                    ? "Связать с другим человеком"
                    : isEdit
                      ? "Редактировать"
                      : connectMode
                        ? "Связать родственников"
                        : relativePerson
                          ? `Добавить к: ${relativePerson.first_name || relativePerson.full_name}`
                          : "Добавить человека"}
                </h2>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {connectMode
                    ? "Создать родственную связь между людьми"
                    : isEdit
                      ? ""
                      : relativePerson ? "Выберите тип связи" : ""}
                </p>
              </div>
              <div className="flex items-center gap-2">
                {/* Toggle connect mode — show when not already in add-relative flow, or when editing */}
                {(!relativePerson || isEdit) && nodes.length >= 2 && (
                  <button
                    type="button"
                    onClick={() => setConnectMode(v => !v)}
                    title={connectMode ? "Вернуться к редактированию" : "Связать с другим человеком"}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium transition-all"
                    style={{
                      background: connectMode ? "hsl(145,35%,92%)" : "hsl(35,30%,94%)",
                      color:      connectMode ? "hsl(145,35%,30%)" : "hsl(30,10%,45%)",
                      border:     `1px solid ${connectMode ? "hsl(145,35%,75%)" : "hsl(35,20%,85%)"}`,
                    }}
                  >
                    <Link2 className="w-3.5 h-3.5" />
                    {connectMode ? (isEdit ? "Редактировать" : "Создать нового") : "Связать"}
                  </button>
                )}
                {!saving && (
                  <button onClick={onClose}
                    className="w-8 h-8 rounded-xl flex items-center justify-center hover:bg-muted transition-colors">
                    <X className="w-4 h-4 text-muted-foreground" />
                  </button>
                )}
              </div>
            </div>

            {/* Body */}
            <div className="px-6 py-5 space-y-4 max-h-[72vh] overflow-y-auto">

              {/* ── CONNECT MODE ─────────────────────────────────────────── */}
              {connectMode ? (
                <>
                  <SectionCard title="Первый человек" icon={UserCheck} color="hsl(145,35%,38%)">
                    <PersonPicker
                      nodes={nodes}
                      value={connectPersonA}
                      onChange={setConnectPersonA}
                      placeholder="Выберите первого"
                      exclude={connectPersonB ? [connectPersonB] : []}
                    />
                  </SectionCard>

                  <SectionCard title="Второй человек" icon={UserCheck} color="hsl(210,60%,50%)">
                    <PersonPicker
                      nodes={nodes}
                      value={connectPersonB}
                      onChange={setConnectPersonB}
                      placeholder="Выберите второго"
                      exclude={connectPersonA ? [connectPersonA] : []}
                    />
                  </SectionCard>

                  <div className="flex items-center gap-3">
                    <div className="flex-1 h-px" style={{ background: "hsl(35,20%,88%)" }} />
                    <div className="px-3 py-1 rounded-xl text-xs font-semibold text-muted-foreground"
                      style={{ background: "hsl(35,30%,94%)" }}>
                      связь
                    </div>
                    <div className="flex-1 h-px" style={{ background: "hsl(35,20%,88%)" }} />
                  </div>

                  {/* Relation type */}
                  <div className="grid grid-cols-1 gap-2">
                    {CONNECT_RELATION_TYPES.map(r => (
                      <button
                        key={r.value}
                        type="button"
                        onClick={() => setConnectRelType(r.value)}
                        className="py-2.5 px-4 rounded-xl text-sm font-medium transition-all text-left"
                        style={{
                          background: connectRelType === r.value ? "hsl(145,35%,38%)" : "hsl(35,30%,95%)",
                          color:      connectRelType === r.value ? "white" : "hsl(30,10%,30%)",
                          border:     connectRelType === r.value ? "none" : "1px solid hsl(35,20%,88%)",
                        }}
                      >
                        {r.labelFn(nameA, nameB)}
                      </button>
                    ))}
                  </div>

                  {/* Marriage dates if spouse */}
                  <AnimatePresence>
                    {connectRelType === "spouse" && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                      >
                        <SectionCard title="Данные о браке" icon={null} color="hsl(30,50%,45%)">
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <Label className="text-xs text-muted-foreground mb-1 block">Год свадьбы</Label>
                              <Input
                                type="number" min="1" max="9999"
                                value={marriageDate} onChange={e => setMarriageDate(e.target.value)}
                                placeholder="необязательно" className="rounded-xl" disabled={saving}
                              />
                            </div>
                            <div>
                              <Label className="text-xs text-muted-foreground mb-1 block">Год развода</Label>
                              <Input
                                type="number" min="1" max="9999"
                                value={divorceDate} onChange={e => setDivorceDate(e.target.value)}
                                placeholder="необязательно" className="rounded-xl" disabled={saving}
                              />
                            </div>
                          </div>
                        </SectionCard>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </>
              ) : (
              /* ── ADD / EDIT MODE ──────────────────────────────────────── */
              <>
                {/* Relation type selector */}
                {!isEdit && relativePerson && (
                  <div>
                    <Label className="text-xs font-medium text-muted-foreground mb-2 block">
                      Кем приходится {relativePerson.first_name || relativePerson.full_name}?
                    </Label>
                    <div className="grid grid-cols-2 gap-2">
                      {RELATION_TYPES.map(r => (
                        <button key={r.value} onClick={() => setRelationType(r.value)}
                          className="py-2 px-3 rounded-xl text-sm font-medium transition-all"
                          style={{
                            background: relationType === r.value ? "hsl(145,35%,38%)" : "hsl(35,30%,95%)",
                            color:      relationType === r.value ? "white" : "hsl(30,10%,30%)",
                            border:     relationType === r.value ? "none" : "1px solid hsl(35,20%,88%)",
                          }}>
                          {r.label}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Sibling warning */}
                {siblingNoParents && (
                  <div className="flex items-start gap-2 p-3 rounded-xl text-xs"
                    style={{ background: "hsl(45,90%,94%)", border: "1px solid hsl(45,70%,80%)" }}>
                    <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: "hsl(35,80%,45%)" }} />
                    <span style={{ color: "hsl(35,60%,30%)" }}>
                      У <strong>{relativePerson.first_name || relativePerson.full_name}</strong> нет родителей.
                      Добавьте сначала общего родителя — персона будет создана без связи сиблинга.
                    </span>
                  </div>
                )}

                {/* ── SIBLING PARENTS MODE ─────────────────────────────── */}
                <AnimatePresence>
                  {!isEdit && relationType === "sibling" && !siblingNoParents && relativeParents.length > 0 && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                    >
                      <SectionCard title="Родители" icon={null} color="hsl(260,45%,50%)">
                        <RadioGroup
                          value={siblingParentMode}
                          onChange={setSiblingParentMode}
                          options={[
                            {
                              value: "same",
                              label: `Общие родители (${relativeParents.map(p => p.first_name || p.full_name).join(", ")})`,
                            },
                            {
                              value: "different",
                              label: "Разные родители (другой родитель)",
                            },
                          ]}
                        />
                        <AnimatePresence>
                          {siblingParentMode === "different" && (
                            <motion.div
                              initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}
                              exit={{ opacity: 0, height: 0 }}
                              className="pt-2 space-y-2"
                            >
                              <Label className="text-xs text-muted-foreground block">
                                Другой общий родитель (необязательно)
                              </Label>
                              <PersonPicker
                                nodes={nodes}
                                value={siblingParentId}
                                onChange={setSiblingParentId}
                                placeholder="Выбрать из существующих"
                                exclude={[relativePerson?.id, ...relativeParents.map(p => p.id)].filter(Boolean)}
                              />
                              <p className="text-xs" style={{ color: "hsl(30,8%,55%)" }}>
                                Если не выбрать, новый человек будет создан как отдельная персона без связи через родителя.
                              </p>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </SectionCard>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Name */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-xs text-muted-foreground mb-1 block">Имя *</Label>
                    <Input value={form.first_name} onChange={e => setField("first_name", e.target.value)}
                      placeholder="Иван" className="rounded-xl" disabled={saving} autoFocus />
                  </div>
                  <div>
                    <Label className="text-xs text-muted-foreground mb-1 block">Фамилия *</Label>
                    <Input value={form.last_name} onChange={e => setField("last_name", e.target.value)}
                      placeholder="Иванов" className="rounded-xl" disabled={saving} />
                  </div>
                </div>

                {/* Gender */}
                <div>
                  <Label className="text-xs text-muted-foreground mb-1 block">Пол</Label>
                  <Select value={form.gender} onValueChange={v => setField("gender", v)} disabled={saving}>
                    <SelectTrigger className="rounded-xl"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      {GENDERS.map(g => <SelectItem key={g.value} value={g.value}>{g.label}</SelectItem>)}
                    </SelectContent>
                  </Select>
                </div>

                {/* Dates */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label className="text-xs text-muted-foreground mb-1 block">Год рождения</Label>
                    <Input type="number" min="1" max="9999" value={form.birth_date}
                      onChange={e => setField("birth_date", e.target.value)}
                      placeholder="1990" className="rounded-xl" disabled={saving} />
                  </div>
                  <div>
                    <Label className="text-xs text-muted-foreground mb-1 block">Год смерти</Label>
                    <Input type="number" min="1" max="9999" value={form.death_date}
                      onChange={e => setField("death_date", e.target.value)}
                      placeholder="необязательно" className="rounded-xl" disabled={saving} />
                  </div>
                </div>

                {/* ── CHILD: parents married checkbox ─────────────────── */}
                <AnimatePresence>
                  {!isEdit && relationType === "child" && relativePerson && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                    >
                      <div
                        className="rounded-2xl p-4 space-y-3"
                        style={{ background: "hsl(35,40%,96%)", border: "1px solid hsl(35,25%,88%)" }}
                      >
                        <ToggleCheckbox
                          checked={parentsMarried}
                          onChange={setParentsMarried}
                          label={`Есть второй родитель у этого ребёнка?`}
                        />

                        <AnimatePresence>
                          {parentsMarried && (
                            <motion.div
                              initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}
                              exit={{ opacity: 0, height: 0 }}
                              className="space-y-3 pt-1"
                            >
                              <div>
                                <Label className="text-xs text-muted-foreground mb-1.5 block">
                                  Второй родитель (из существующих)
                                </Label>
                                <PersonPicker
                                  nodes={nodes}
                                  value={secondParentId}
                                  onChange={setSecondParentId}
                                  placeholder="Выбрать из списка"
                                  exclude={[relativePerson?.id].filter(Boolean)}
                                />
                              </div>

                              {secondParentId && (
                                <motion.div
                                  initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                                  className="space-y-3"
                                >
                                  <div
                                    className="flex items-center gap-2 p-3 rounded-xl text-xs"
                                    style={{ background: "hsl(145,35%,94%)", border: "1px solid hsl(145,35%,82%)" }}
                                  >
                                    <Check className="w-3.5 h-3.5 flex-shrink-0" style={{ color: "hsl(145,35%,38%)" }} />
                                    <span style={{ color: "hsl(145,35%,28%)" }}>
                                      Ребёнок будет связан с обоими родителями. Также создать связь «супруги» между ними?
                                    </span>
                                  </div>

                                  <SectionCard title="Данные о браке (необязательно)" icon={null} color="hsl(30,50%,45%)">
                                    <div className="grid grid-cols-2 gap-3">
                                      <div>
                                        <Label className="text-xs text-muted-foreground mb-1 block">Год свадьбы</Label>
                                        <Input
                                          type="number" min="1" max="9999"
                                          value={marriageDate} onChange={e => setMarriageDate(e.target.value)}
                                          placeholder="необязательно" className="rounded-xl" disabled={saving}
                                        />
                                      </div>
                                      <div>
                                        <Label className="text-xs text-muted-foreground mb-1 block">Год развода</Label>
                                        <Input
                                          type="number" min="1" max="9999"
                                          value={divorceDate} onChange={e => setDivorceDate(e.target.value)}
                                          placeholder="необязательно" className="rounded-xl" disabled={saving}
                                        />
                                      </div>
                                    </div>
                                  </SectionCard>
                                </motion.div>
                              )}
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                <p className="text-xs text-muted-foreground">* Обязательные поля</p>
              </>
              )}
            </div>

            {/* Footer */}
            <div className="flex gap-3 px-6 py-4" style={{ borderTop: "1px solid hsl(35,20%,90%)" }}>
              <Button variant="outline" className="flex-1 rounded-xl" onClick={onClose} disabled={saving}>
                Отмена
              </Button>
              <Button
                className="flex-1 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90"
                onClick={handleSave} disabled={!canSave}
              >
                {saving
                  ? "Сохранение..."
                  : connectMode
                    ? "Создать связь"
                    : isEdit ? "Сохранить" : "Добавить"}
              </Button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
