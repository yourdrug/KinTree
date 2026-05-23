/**
 * components/tree/AddPersonModal.jsx
 */

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, AlertTriangle } from "lucide-react";
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

// ── Component ─────────────────────────────────────────────────────────────────

export default function AddPersonModal({
  open, onClose, onSave,
  relativePerson, editPerson, relationMaps,
}) {
  const [relationType, setRelationType] = useState("child");
  const [form,         setForm]         = useState(buildEmptyForm());
  const [saving,       setSaving]       = useState(false);

  const isEdit = !!editPerson;

  useEffect(() => {
    if (!open) return;
    if (isEdit) {
      setForm(formFromNode(editPerson));
    } else {
      setRelationType("child");
      setForm(buildEmptyForm());
    }
  }, [open, editPerson, isEdit]);

  const setField = (key, value) => setForm((f) => ({ ...f, [key]: value }));

  const showSiblingWarning =
    !isEdit &&
    relationType === "sibling" &&
    relativePerson &&
    relationMaps &&
    getPersonRelations(relationMaps, relativePerson.id).parentIds.length === 0;

  const handleSave = async () => {
    if (saving) return;
    setSaving(true);
    try {
      await onSave(form, editPerson?.id, relationType, relativePerson);
      onClose();
    } catch {
      // Ошибка показана через toast в TreeView — модалка остаётся открытой
    } finally {
      setSaving(false);
    }
  };

  const canSave = form.first_name?.trim() && form.last_name?.trim() && !saving;

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: "hsla(30,10%,15%,0.55)", backdropFilter: "blur(10px)" }}
          onClick={(e) => e.target === e.currentTarget && !saving && onClose()}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.93, y: 24 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.93, y: 24 }}
            transition={{ type: "spring", stiffness: 320, damping: 28 }}
            className="w-full max-w-md rounded-3xl shadow-2xl overflow-hidden"
            style={{ background: "hsl(40,33%,98%)", border: "1px solid hsl(35,20%,88%)" }}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 pt-6 pb-4"
              style={{ borderBottom: "1px solid hsl(35,20%,90%)" }}>
              <div>
                <h2 className="font-serif text-xl font-semibold text-foreground">
                  {isEdit
                    ? "Редактировать"
                    : relativePerson
                      ? `Добавить к: ${relativePerson.first_name || relativePerson.full_name}`
                      : "Добавить человека"}
                </h2>
                {!isEdit && relativePerson && (
                  <p className="text-xs text-muted-foreground mt-0.5">Выберите тип связи</p>
                )}
              </div>
              {!saving && (
                <button onClick={onClose}
                  className="w-8 h-8 rounded-xl flex items-center justify-center hover:bg-muted transition-colors">
                  <X className="w-4 h-4 text-muted-foreground" />
                </button>
              )}
            </div>

            {/* Body */}
            <div className="px-6 py-5 space-y-4 max-h-[72vh] overflow-y-auto">
              {/* Relation type selector */}
              {!isEdit && relativePerson && (
                <div>
                  <Label className="text-xs font-medium text-muted-foreground mb-2 block">
                    Кем приходится {relativePerson.first_name || relativePerson.full_name}?
                  </Label>
                  <div className="grid grid-cols-2 gap-2">
                    {RELATION_TYPES.map((r) => (
                      <button key={r.value} onClick={() => setRelationType(r.value)}
                        className="py-2 px-3 rounded-xl text-sm font-medium transition-all"
                        style={{
                          background: relationType === r.value ? "hsl(145,35%,38%)" : "hsl(35,30%,95%)",
                          color:      relationType === r.value ? "white" : "hsl(30,10%,30%)",
                          border:     relationType === r.value ? "none"  : "1px solid hsl(35,20%,88%)",
                        }}>
                        {r.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Sibling warning */}
              {showSiblingWarning && (
                <div className="flex items-start gap-2 p-3 rounded-xl text-xs"
                  style={{ background: "hsl(45,90%,94%)", border: "1px solid hsl(45,70%,80%)" }}>
                  <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: "hsl(35,80%,45%)" }} />
                  <span style={{ color: "hsl(35,60%,30%)" }}>
                    У <strong>{relativePerson.first_name || relativePerson.full_name}</strong> нет родителей.
                    Добавьте сначала общего родителя — персона будет создана без связи сиблинга.
                  </span>
                </div>
              )}

              {/* Name */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className="text-xs text-muted-foreground mb-1 block">Имя *</Label>
                  <Input value={form.first_name} onChange={(e) => setField("first_name", e.target.value)}
                    placeholder="Иван" className="rounded-xl" disabled={saving} autoFocus />
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground mb-1 block">Фамилия *</Label>
                  <Input value={form.last_name} onChange={(e) => setField("last_name", e.target.value)}
                    placeholder="Иванов" className="rounded-xl" disabled={saving} />
                </div>
              </div>

              {/* Gender */}
              <div>
                <Label className="text-xs text-muted-foreground mb-1 block">Пол</Label>
                <Select value={form.gender} onValueChange={(v) => setField("gender", v)} disabled={saving}>
                  <SelectTrigger className="rounded-xl"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {GENDERS.map((g) => <SelectItem key={g.value} value={g.value}>{g.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>

              {/* Dates */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className="text-xs text-muted-foreground mb-1 block">Год рождения</Label>
                  <Input type="number" min="1" max="9999" value={form.birth_date}
                    onChange={(e) => setField("birth_date", e.target.value)}
                    placeholder="1990" className="rounded-xl" disabled={saving} />
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground mb-1 block">Год смерти</Label>
                  <Input type="number" min="1" max="9999" value={form.death_date}
                    onChange={(e) => setField("death_date", e.target.value)}
                    placeholder="необязательно" className="rounded-xl" disabled={saving} />
                </div>
              </div>

              <p className="text-xs text-muted-foreground">* Обязательные поля</p>
            </div>

            {/* Footer */}
            <div className="flex gap-3 px-6 py-4" style={{ borderTop: "1px solid hsl(35,20%,90%)" }}>
              <Button variant="outline" className="flex-1 rounded-xl" onClick={onClose} disabled={saving}>
                Отмена
              </Button>
              <Button
                className="flex-1 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90"
                onClick={handleSave} disabled={!canSave}>
                {saving ? "Сохранение..." : isEdit ? "Сохранить" : "Добавить"}
              </Button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
