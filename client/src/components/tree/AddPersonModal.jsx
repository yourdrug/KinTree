/**
 * components/tree/AddPersonModal.jsx
 *
 * Модалка добавления / редактирования члена семьи.
 */

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, User } from "lucide-react";
import { Button }   from "@/components/ui/button";
import { Input }    from "@/components/ui/input";
import { Label }    from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select, SelectContent, SelectItem,
  SelectTrigger, SelectValue,
} from "@/components/ui/select";

// ─── Константы ────────────────────────────────────────────────────────────────

const RELATION_TYPES = [
  { value: "child",   label: "Ребёнок" },
  { value: "parent",  label: "Родитель" },
  { value: "partner", label: "Партнёр / Супруг(а)" },
  { value: "sibling", label: "Брат / Сестра" },
];

const GENDERS = [
  { value: "male",   label: "Мужской" },
  { value: "female", label: "Женский" },
  { value: "other",  label: "Другой" },
];

// ─── Helpers ──────────────────────────────────────────────────────────────────

function buildEmptyForm(relativeId, relativeData, relationType) {
  const base = {
    first_name: "", last_name: "",
    birth_date: "", death_date: "",
    gender: "male", birth_place: "", bio: "", photo_url: "",
    parent_ids: [], partner_id: "", generation: 0,
  };

  if (!relativeId || !relativeData) return base;

  const relGen = relativeData.generation ?? 0;

  switch (relationType) {
    case "child":
      return { ...base, parent_ids: [relativeId], generation: relGen + 1 };
    case "parent":
      return { ...base, generation: relGen - 1 };
    case "partner":
      return { ...base, generation: relGen };
    case "sibling":
      return { ...base, parent_ids: relativeData.parent_ids || [], generation: relGen };
    default:
      return base;
  }
}

function formFromPerson(person) {
  return {
    first_name:  person.first_name  || "",
    last_name:   person.last_name   || "",
    birth_date:  person.birth_date  || "",
    death_date:  person.death_date  || "",
    gender:      person.gender      || "male",
    birth_place: person.birth_place || "",
    bio:         person.bio         || "",
    photo_url:   person.photo_url   || "",
    parent_ids:  person.parent_ids  || [],
    partner_id:  person.partner_id  || "",
    generation:  person.generation  ?? 0,
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
  const [form,         setForm]         = useState({});
  const [saving,       setSaving]       = useState(false);

  const isEdit = !!editPerson;

  // Инициализация формы при открытии
  useEffect(() => {
    if (!open) return;
    if (isEdit) {
      setForm(formFromPerson(editPerson));
    } else {
      setRelationType("child");
      setForm(buildEmptyForm(relativePerson?.id, relativePerson, "child"));
    }
  }, [open, relativePerson, editPerson]);

  const setField = (key, value) => setForm((f) => ({ ...f, [key]: value }));

  const handleRelationChange = (val) => {
    setRelationType(val);
    setForm(buildEmptyForm(relativePerson?.id, relativePerson, val));
  };

  const handleSave = async () => {
    setSaving(true);

    const data = { ...form };
    // Чистим пустые опциональные поля
    if (!data.death_date)  delete data.death_date;
    if (!data.partner_id)  delete data.partner_id;
    if (!data.birth_date)  delete data.birth_date;

    await onSave(data, editPerson?.id, relationType, relativePerson);
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

              {/* Тип связи — только для нового человека с относительным контекстом */}
              {!isEdit && relativePerson && (
                <RelationSelector
                  relative={relativePerson}
                  value={relationType}
                  onChange={handleRelationChange}
                />
              )}

              {/* Фото (только отображение, загрузка не реализована) */}
              <PhotoPreview url={form.photo_url} />

              {/* Имя и фамилия */}
              <div className="grid grid-cols-2 gap-3">
                <FormField label="Имя *">
                  <Input
                    value={form.first_name || ""}
                    onChange={(e) => setField("first_name", e.target.value)}
                    placeholder="Иван"
                    className="rounded-xl"
                  />
                </FormField>
                <FormField label="Фамилия *">
                  <Input
                    value={form.last_name || ""}
                    onChange={(e) => setField("last_name", e.target.value)}
                    placeholder="Иванов"
                    className="rounded-xl"
                  />
                </FormField>
              </div>

              {/* Пол */}
              <FormField label="Пол">
                <Select value={form.gender || "male"} onValueChange={(v) => setField("gender", v)}>
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
                    value={form.birth_date || ""}
                    onChange={(e) => setField("birth_date", e.target.value)}
                    className="rounded-xl"
                  />
                </FormField>
                <FormField label="Дата смерти">
                  <Input
                    type="date"
                    value={form.death_date || ""}
                    onChange={(e) => setField("death_date", e.target.value)}
                    className="rounded-xl"
                  />
                </FormField>
              </div>

              {/* Место рождения */}
              <FormField label="Место рождения">
                <Input
                  value={form.birth_place || ""}
                  onChange={(e) => setField("birth_place", e.target.value)}
                  placeholder="Москва, Россия"
                  className="rounded-xl"
                />
              </FormField>

              {/* Поколение — только в режиме редактирования */}
              {isEdit && (
                <FormField label="Поколение (0 = корень)">
                  <Input
                    type="number"
                    value={form.generation ?? 0}
                    onChange={(e) => setField("generation", Number(e.target.value))}
                    className="rounded-xl"
                  />
                </FormField>
              )}

              {/* Биография */}
              <FormField label="Биография">
                <Textarea
                  value={form.bio || ""}
                  onChange={(e) => setField("bio", e.target.value)}
                  placeholder="Краткая история жизни..."
                  className="rounded-xl h-20 resize-none"
                />
              </FormField>
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

function PhotoPreview({ url }) {
  return (
    <div
      className="w-16 h-16 rounded-2xl overflow-hidden flex items-center justify-center"
      style={{ background: "hsl(35,40%,92%)" }}
    >
      {url
        ? <img src={url} className="w-full h-full object-cover" alt="" />
        : <User className="w-7 h-7 text-muted-foreground" />
      }
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
