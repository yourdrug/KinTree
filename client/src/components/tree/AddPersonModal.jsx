/**
 * components/tree/AddPersonModal.jsx
 *
 * ИСПРАВЛЕНИЯ:
 * 1. editPerson теперь NodeResponse (из graph.nodes), а не PersonResponse.
 *    Форма заполняется из birth_year (число), а не из birth_date (PartialDateSchema).
 *    При редактировании PATCH-запрос использует birth_date как PartialDateSchema.
 * 2. sibling-предупреждение: если у relativePerson нет родителей в relationMaps —
 *    показываем предупреждение что связь сиблингов будет неполной.
 * 3. handleSave: onClose только при успехе (ошибка оставляет модалку открытой).
 * 4. canSave проверяет !saving явно.
 * 5. Год рождения в форме — строка "YYYY" или "YYYY-MM-DD".
 */

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, AlertTriangle }  from "lucide-react";
import { Button }            from "@/components/ui/button";
import { Input }             from "@/components/ui/input";
import { Label }             from "@/components/ui/label";
import {
  Select, SelectContent, SelectItem,
  SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { getPersonRelations } from "@/api";

// ── Константы ─────────────────────────────────────────────────────────────────

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

/**
 * Заполняем форму из NodeResponse (editPerson).
 * NodeResponse содержит birth_year (число), не birth_date (PartialDateSchema).
 * Форма хранит строки вида "YYYY" или "YYYY-MM-DD" для input[type=date].
 */
function formFromNode(node) {
  return {
    first_name: node.first_name  || node.full_name?.split(" ")[0] || "",
    last_name:  node.last_name   || node.full_name?.split(" ").slice(1).join(" ") || "",
    gender:     node.gender      || "MALE",
    // birth_year → "YYYY" для input (не полная дата, нет month/day в NodeResponse)
    birth_date: node.birth_year  ? String(node.birth_year)  : "",
    death_date: node.death_year  ? String(node.death_year)  : "",
  };
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function AddPersonModal({
  open,
  onClose,
  onSave,
  relativePerson,
  editPerson,
  relationMaps,   // нужен для предупреждения sibling
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

  // Предупреждение для sibling: если у relativePerson нет родителей
  const showSiblingWarning =
    !isEdit &&
    relationType === "sibling" &&
    relativePerson &&
    relationMaps &&
    getPersonRelations(relationMaps, relativePerson.id).parentIds.length === 0;

  // FIX: onClose только при успехе
  const handleSave = async () => {
    if (saving) return;
    setSaving(true);
    try {
      await onSave(form, editPerson?.id, relationType, relativePerson);
      onClose();
    } catch {
      // Ошибка отображается через toast в TreeView — модалка остаётся открытой
    } finally {
      setSaving(false);
    }
  };

  const canSave = form.first_name?.trim() && form.last_name?.trim() && !saving;

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
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
            <ModalHeader
              title={
                isEdit
                  ? "Редактировать"
                  : relativePerson
                    ? `Добавить к: ${relativePerson.first_name || relativePerson.full_name}`
                    : "Добавить человека"
              }
              subtitle={!isEdit && relativePerson ? "Выберите тип связи" : undefined}
              onClose={saving ? undefined : onClose}
            />

            {/* Body */}
            <div className="px-6 py-5 space-y-4 max-h-[72vh] overflow-y-auto">
              {/* Тип связи */}
              {!isEdit && relativePerson && (
                <RelationSelector
                  relative={relativePerson}
                  value={relationType}
                  onChange={setRelationType}
                />
              )}

              {/* Предупреждение для sibling без родителей */}
              {showSiblingWarning && (
                <div
                  className="flex items-start gap-2 p-3 rounded-xl text-xs"
                  style={{ background: "hsl(45,90%,94%)", border: "1px solid hsl(45,70%,80%)" }}
                >
                  <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: "hsl(35,80%,45%)" }} />
                  <span style={{ color: "hsl(35,60%,30%)" }}>
                    У <strong>{relativePerson.first_name || relativePerson.full_name}</strong> нет родителей.
                    Добавьте сначала общего родителя, чтобы связь братьев/сестёр отобразилась корректно.
                    Персона будет создана без связи сиблинга.
                  </span>
                </div>
              )}

              {/* Имя и фамилия */}
              <div className="grid grid-cols-2 gap-3">
                <FormField label="Имя *">
                  <Input
                    value={form.first_name}
                    onChange={(e) => setField("first_name", e.target.value)}
                    placeholder="Иван"
                    className="rounded-xl"
                    disabled={saving}
                    autoFocus
                  />
                </FormField>
                <FormField label="Фамилия *">
                  <Input
                    value={form.last_name}
                    onChange={(e) => setField("last_name", e.target.value)}
                    placeholder="Иванов"
                    className="rounded-xl"
                    disabled={saving}
                  />
                </FormField>
              </div>

              {/* Пол */}
              <FormField label="Пол">
                <Select
                  value={form.gender}
                  onValueChange={(v) => setField("gender", v)}
                  disabled={saving}
                >
                  <SelectTrigger className="rounded-xl"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {GENDERS.map((g) => (
                      <SelectItem key={g.value} value={g.value}>{g.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </FormField>

              {/* Даты */}
              <div className="grid grid-cols-2 gap-3">
                <FormField label="Год рождения">
                  <Input
                    type="number"
                    min="1"
                    max="9999"
                    value={form.birth_date}
                    onChange={(e) => setField("birth_date", e.target.value)}
                    placeholder="1990"
                    className="rounded-xl"
                    disabled={saving}
                  />
                </FormField>
                <FormField label="Год смерти">
                  <Input
                    type="number"
                    min="1"
                    max="9999"
                    value={form.death_date}
                    onChange={(e) => setField("death_date", e.target.value)}
                    placeholder="необязательно"
                    className="rounded-xl"
                    disabled={saving}
                  />
                </FormField>
              </div>

              <p className="text-xs text-muted-foreground">* Обязательные поля</p>
            </div>

            {/* Footer */}
            <div
              className="flex gap-3 px-6 py-4"
              style={{ borderTop: "1px solid hsl(35,20%,90%)" }}
            >
              <Button
                variant="outline"
                className="flex-1 rounded-xl"
                onClick={onClose}
                disabled={saving}
              >
                Отмена
              </Button>
              <Button
                className="flex-1 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90"
                onClick={handleSave}
                disabled={!canSave}
              >
                {saving ? "Сохранение..." : isEdit ? "Сохранить" : "Добавить"}
              </Button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// ── Вспомогательные подкомпоненты ─────────────────────────────────────────────

function ModalHeader({ title, subtitle, onClose }) {
  return (
    <div
      className="flex items-center justify-between px-6 pt-6 pb-4"
      style={{ borderBottom: "1px solid hsl(35,20%,90%)" }}
    >
      <div>
        <h2 className="font-serif text-xl font-semibold text-foreground">{title}</h2>
        {subtitle && <p className="text-xs text-muted-foreground mt-0.5">{subtitle}</p>}
      </div>
      {onClose && (
        <button
          onClick={onClose}
          className="w-8 h-8 rounded-xl flex items-center justify-center hover:bg-muted transition-colors"
        >
          <X className="w-4 h-4 text-muted-foreground" />
        </button>
      )}
    </div>
  );
}

function RelationSelector({ relative, value, onChange }) {
  const name = relative.first_name || relative.full_name || "персоны";
  return (
    <div>
      <Label className="text-xs font-medium text-muted-foreground mb-2 block">
        Кем приходится {name}?
      </Label>
      <div className="grid grid-cols-2 gap-2">
        {RELATION_TYPES.map((r) => (
          <button
            key={r.value}
            onClick={() => onChange(r.value)}
            className="py-2 px-3 rounded-xl text-sm font-medium transition-all"
            style={{
              background: value === r.value ? "hsl(145,35%,38%)" : "hsl(35,30%,95%)",
              color:      value === r.value ? "white" : "hsl(30,10%,30%)",
              border:     value === r.value ? "none"  : "1px solid hsl(35,20%,88%)",
            }}
          >
            {r.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function FormField({ label, children }) {
  return (
    <div>
      <Label className="text-xs text-muted-foreground mb-1 block">{label}</Label>
      {children}
    </div>
  );
}
