import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Upload, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const RELATION_TYPES = [
  { value: "child", label: "Ребёнок" },
  { value: "parent", label: "Родитель" },
  { value: "partner", label: "Партнёр / Супруг(а)" },
  { value: "sibling", label: "Брат / Сестра" },
];

function empty(relativeId, relativeData, relationType) {
  const base = {
    first_name: "", last_name: "", birth_date: "", death_date: "",
    gender: "male", birth_place: "", bio: "", photo_url: "",
    parent_ids: [], partner_id: "", generation: 0,
  };
  if (!relativeId || !relativeData) return base;
  const relGen = relativeData.generation ?? 0;
  if (relationType === "child") {
    return { ...base, parent_ids: [relativeId], generation: relGen + 1 };
  } else if (relationType === "parent") {
    return { ...base, generation: relGen - 1 };
  } else if (relationType === "partner") {
    return { ...base, generation: relGen };
  } else if (relationType === "sibling") {
    return { ...base, parent_ids: relativeData.parent_ids || [], generation: relGen };
  }
  return base;
}

export default function AddPersonModal({ open, onClose, onSave, treeId, relativePerson, editPerson }) {
  const [relationType, setRelationType] = useState("child");
  const [form, setForm] = useState({});
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) return;
    if (editPerson) {
      setForm({
        first_name: editPerson.first_name || "",
        last_name: editPerson.last_name || "",
        birth_date: editPerson.birth_date || "",
        death_date: editPerson.death_date || "",
        gender: editPerson.gender || "male",
        birth_place: editPerson.birth_place || "",
        bio: editPerson.bio || "",
        photo_url: editPerson.photo_url || "",
        parent_ids: editPerson.parent_ids || [],
        partner_id: editPerson.partner_id || "",
        generation: editPerson.generation ?? 0,
      });
    } else {
      setRelationType("child");
      setForm(empty(relativePerson?.id, relativePerson, "child"));
    }
  }, [open, relativePerson, editPerson]);

  const handleRelationChange = (val) => {
    setRelationType(val);
    setForm(empty(relativePerson?.id, relativePerson, val));
  };

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const handlePhoto = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      // Upload Photo (will implement in future)
      set("photo_url", file_url);
    } finally {
      setUploading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    const data = { ...form, tree_id: treeId };
    // Clean empty strings
    if (!data.death_date) delete data.death_date;
    if (!data.partner_id) delete data.partner_id;
    if (!data.birth_date) delete data.birth_date;

    await onSave(data, editPerson?.id, relationType, relativePerson);
    setSaving(false);
    onClose();
  };

  const isEdit = !!editPerson;

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
                  {isEdit ? "Редактировать" : relativePerson ? `Добавить к: ${relativePerson.first_name}` : "Добавить человека"}
                </h2>
                {!isEdit && relativePerson && (
                  <p className="text-xs text-muted-foreground mt-0.5">Выберите тип связи</p>
                )}
              </div>
              <button onClick={onClose}
                className="w-8 h-8 rounded-xl flex items-center justify-center hover:bg-muted transition-colors">
                <X className="w-4 h-4 text-muted-foreground" />
              </button>
            </div>

            <div className="px-6 py-5 space-y-4 max-h-[72vh] overflow-y-auto">

              {/* Relation type (only for new, when relative exists) */}
              {!isEdit && relativePerson && (
                <div>
                  <Label className="text-xs font-medium text-muted-foreground mb-2 block">Кем приходится {relativePerson.first_name}?</Label>
                  <div className="grid grid-cols-2 gap-2">
                    {RELATION_TYPES.map((r) => (
                      <button
                        key={r.value}
                        onClick={() => handleRelationChange(r.value)}
                        className="py-2 px-3 rounded-xl text-sm font-medium transition-all"
                        style={{
                          background: relationType === r.value ? "hsl(145,35%,38%)" : "hsl(35,30%,95%)",
                          color: relationType === r.value ? "white" : "hsl(30,10%,30%)",
                          border: relationType === r.value ? "none" : "1px solid hsl(35,20%,88%)",
                        }}
                      >
                        {r.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Photo */}
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-2xl overflow-hidden flex-shrink-0 flex items-center justify-center"
                  style={{ background: "hsl(35,40%,92%)" }}>
                  {form.photo_url
                    ? <img src={form.photo_url} className="w-full h-full object-cover" alt="" />
                    : <User className="w-7 h-7 text-muted-foreground" />
                  }
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground mb-1.5 block">Фотография</Label>
                  <label className="inline-flex items-center gap-2 cursor-pointer text-sm px-3 py-1.5 rounded-xl border transition-colors hover:bg-muted"
                    style={{ borderColor: "hsl(35,20%,88%)" }}>
                    <Upload className="w-3.5 h-3.5" />
                    {uploading ? "Загрузка..." : "Выбрать"}
                    <input type="file" accept="image/*" className="hidden" onChange={handlePhoto} disabled={uploading} />
                  </label>
                </div>
              </div>

              {/* Name */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className="text-xs text-muted-foreground mb-1 block">Имя *</Label>
                  <Input value={form.first_name || ""} onChange={(e) => set("first_name", e.target.value)}
                    placeholder="Иван" className="rounded-xl" />
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground mb-1 block">Фамилия *</Label>
                  <Input value={form.last_name || ""} onChange={(e) => set("last_name", e.target.value)}
                    placeholder="Иванов" className="rounded-xl" />
                </div>
              </div>

              {/* Gender */}
              <div>
                <Label className="text-xs text-muted-foreground mb-1 block">Пол</Label>
                <Select value={form.gender || "male"} onValueChange={(v) => set("gender", v)}>
                  <SelectTrigger className="rounded-xl"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="male">Мужской</SelectItem>
                    <SelectItem value="female">Женский</SelectItem>
                    <SelectItem value="other">Другой</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Dates */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label className="text-xs text-muted-foreground mb-1 block">Дата рождения</Label>
                  <Input type="date" value={form.birth_date || ""} onChange={(e) => set("birth_date", e.target.value)} className="rounded-xl" />
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground mb-1 block">Дата смерти</Label>
                  <Input type="date" value={form.death_date || ""} onChange={(e) => set("death_date", e.target.value)} className="rounded-xl" />
                </div>
              </div>

              {/* Birth place */}
              <div>
                <Label className="text-xs text-muted-foreground mb-1 block">Место рождения</Label>
                <Input value={form.birth_place || ""} onChange={(e) => set("birth_place", e.target.value)}
                  placeholder="Москва, Россия" className="rounded-xl" />
              </div>

              {/* Generation (hidden but editable) */}
              {isEdit && (
                <div>
                  <Label className="text-xs text-muted-foreground mb-1 block">Поколение (0 = корень)</Label>
                  <Input type="number" value={form.generation ?? 0}
                    onChange={(e) => set("generation", Number(e.target.value))} className="rounded-xl" />
                </div>
              )}

              {/* Bio */}
              <div>
                <Label className="text-xs text-muted-foreground mb-1 block">Биография</Label>
                <Textarea value={form.bio || ""} onChange={(e) => set("bio", e.target.value)}
                  placeholder="Краткая история жизни..." className="rounded-xl h-20 resize-none" />
              </div>
            </div>

            {/* Footer */}
            <div className="flex gap-3 px-6 py-4" style={{ borderTop: "1px solid hsl(35,20%,90%)" }}>
              <Button variant="outline" className="flex-1 rounded-xl" onClick={onClose}>Отмена</Button>
              <Button
                className="flex-1 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90"
                onClick={handleSave}
                disabled={!form.first_name?.trim() || !form.last_name?.trim() || saving}
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
