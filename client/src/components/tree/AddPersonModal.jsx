/**
 * components/tree/AddPersonModal.jsx
 *
 * Модалка добавления / редактирования члена семьи.
 *
 * Исправления:
 * - Убраны поля bio, birth_place, photo_url, generation — их нет в API
 * - gender приведён к значениям сервера: MALE | FEMALE | OTHER
 * - birth_date / death_date хранятся как строки "YYYY-MM-DD" в форме,
 *   преобразование в PartialDateSchema происходит в personsApi
 */

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, User } from "lucide-react";
import { Button }   from "@/components/ui/button";
import { Input }    from "@/components/ui/input";
import { Label }    from "@/components/ui/label";
import {
  Select, SelectContent, SelectItem,
  SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { fromPartialDate } from "@/api";

// ─── Константы ────────────────────────────────────────────────────────────────

const RELATION_TYPES = [
  { value: "child",   label: "Ребёнок" },
  { value: "parent",  label: "Родитель" },
  { value: "partner", label: "Партнёр / Супруг(а)" },
  { value: "sibling", label: "Брат / Сестра" },
];

// Значения совпадают с PersonGender на сервере
const GENDERS = [
  { value: "MALE",   label: "Мужской" },
  { value: "FEMALE", label: "Женский" },
  { value: "OTHER",  label: "Другой" },
];

// ─── Helpers ──────────────────────────────────────────────────────────────────

function buildEmptyForm() {
  return {
    first_name: "",
    last_name: "",
    birth_date: "",
    death_date: "",
    gender: "MALE",
  };
}

function formFromPerson(person) {
  return {
    first_name: person.first_name  || "",
    last_name:  person.last_name   || "",
    birth_date: fromPartialDate(person.birth_date),
    death_date: fromPartialDate(person.death_date),
    // Нормализуем gender — сервер может вернуть MALE/FEMALE/OTHER
    gender:     person.gender || "MALE",
  };
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function AddPersonModal({
  open,
  onClose,
  onSave,
  relativePerson,
  editPerson,
}) {
  const [relationType, setRelationType] = useState("child");
  const [form,         setForm]         = useState(buildEmptyForm());
  const [saving,       setSaving]       = useState(false);

  const isEdit = !!editPerson;

  useEffect(() => {
    if (!open) return;
    if (isEdit) {
      setForm(formFromPerson(editPerson));
    } else {
      setRelationType("child");
      setForm(buildEmptyForm());
    }
  }, [open, editPerson, isEdit]);

  const setField = (key, value) => setForm((f) => ({ ...f, [key]: value }));

  const handleSave = async () => {
    setSaving(true);
    // Передаём форму как есть — нормализация дат происходит в personsApi
    await onSave(form, editPerson?.id, relationType, relativePerson);
    setSaving(false);
    onClose();
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
          onClick={(e) => e.target === e.currentTarget && onClose()}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.93, y: 24 }}
            animate={{ opacity: 1, scale: 1,    y: 0  }}
            exit={{    opacity: 0, scale: 0.93, y: 24 }}
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
                    ? `Добавить к: ${relativePerson.first_name}`
                    : "Добавить человека"
              }
              subtitle={!isEdit && relativePerson ? "Выберите тип связи" : undefined}
              onClose={onClose}
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

              {/* Имя и фамилия */}
              <div className="grid grid-cols-2 gap-3">
                <FormField label="Имя *">
                  <Input
                    value={form.first_name}
                    onChange={(e) => setField("first_name", e.target.value)}
                    placeholder="Иван"
                    className="rounded-xl"
                  />
                </FormField>
                <FormField label="Фамилия *">
                  <Input
                    value={form.last_name}
                    onChange={(e) => setField("last_name", e.target.value)}
                    placeholder="Иванов"
                    className="rounded-xl"
                  />
                </FormField>
              </div>

              {/* Пол */}
              <FormField label="Пол">
                <Select value={form.gender} onValueChange={(v) => setField("gender", v)}>
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
                <FormField label="Дата рождения">
                  <Input
                    type="date"
                    value={form.birth_date}
                    onChange={(e) => setField("birth_date", e.target.value)}
                    className="rounded-xl"
                  />
                </FormField>
                <FormField label="Дата смерти">
                  <Input
                    type="date"
                    value={form.death_date}
                    onChange={(e) => setField("death_date", e.target.value)}
                    className="rounded-xl"
                  />
                </FormField>
              </div>

              <p className="text-xs text-muted-foreground">
                * Обязательные поля
              </p>
            </div>

            {/* Footer */}
            <div className="flex gap-3 px-6 py-4" style={{ borderTop: "1px solid hsl(35,20%,90%)" }}>
              <Button variant="outline" className="flex-1 rounded-xl" onClick={onClose}>
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

// ─── Вспомогательные подкомпоненты ────────────────────────────────────────────

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
      <button
        onClick={onClose}
        className="w-8 h-8 rounded-xl flex items-center justify-center hover:bg-muted transition-colors"
      >
        <X className="w-4 h-4 text-muted-foreground" />
      </button>
    </div>
  );
}

function RelationSelector({ relative, value, onChange }) {
  return (
    <div>
      <Label className="text-xs font-medium text-muted-foreground mb-2 block">
        Кем приходится {relative.first_name}?
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
              border:     value === r.value ? "none" : "1px solid hsl(35,20%,88%)",
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
