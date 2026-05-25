/**
 * components/tree/AddModeForm.jsx
 *
 * Форма режима «Добавить нового человека» в AddPersonModal.
 * Содержит: выбор типа связи, поля имени/пола/дат,
 * блок второго родителя, блок со-родителя-супруга, блок сиблингов.
 */

import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, Heart, Check } from "lucide-react";
import { Input }  from "@/components/ui/input";
import { Label }  from "@/components/ui/label";
import {
  Select, SelectContent, SelectItem,
  SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { PersonPicker, ToggleCheckbox, RadioGroup, SectionCard } from "./modalAtoms";

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

// ── AddModeForm ───────────────────────────────────────────────────────────────

export default function AddModeForm({
  // Базовые пропсы
  isEdit,
  relativePerson,
  nodes,
  saving,

  // Тип связи
  relationType,
  onChangeRelationType,

  // Поля формы
  form,
  onChangeField,

  // Второй родитель (для child)
  parentsMarried, onChangeParentsMarried,
  secondParentId, onChangeSecondParentId,
  marriageDate,   onChangeMarriageDate,
  divorceDate,    onChangeDivorceDate,

  // Со-родитель как супруг (для parent)
  existingCoParent,
  showCoParentSpouseOffer,
  makeSpouseOfCoParent,    onChangeMakeSpouseOfCoParent,
  coParentMarriageDate,    onChangeCoParentMarriageDate,
  coParentDivorceDate,     onChangeCoParentDivorceDate,

  // Сиблинги
  siblingNoParents,
  relativeParents,
  siblingParentMode, onChangeSiblingParentMode,
  siblingParentId,   onChangeSiblingParentId,
}) {
  return (
    <>
      {/* ── Выбор типа связи ────────────────────────────────────────────── */}
      {!isEdit && relativePerson && (
        <div>
          <Label className="text-xs font-medium text-muted-foreground mb-2 block">
            Кем приходится {relativePerson.first_name || relativePerson.full_name}?
          </Label>
          <div className="grid grid-cols-2 gap-2">
            {RELATION_TYPES.map(r => (
              <button
                key={r.value}
                onClick={() => onChangeRelationType(r.value)}
                className="py-2 px-3 rounded-xl text-sm font-medium transition-all"
                style={{
                  background: relationType === r.value ? "hsl(145,35%,38%)" : "hsl(35,30%,95%)",
                  color:      relationType === r.value ? "white"             : "hsl(30,10%,30%)",
                  border:     relationType === r.value ? "none"              : "1px solid hsl(35,20%,88%)",
                }}
              >
                {r.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── Предупреждение: нет родителей для сиблинга ──────────────────── */}
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

      {/* ── Родители сиблинга ────────────────────────────────────────────── */}
      <AnimatePresence>
        {!isEdit && relationType === "sibling" && !siblingNoParents && relativeParents.length > 0 && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }}>
            <SectionCard title="Родители" icon={null} color="hsl(260,45%,50%)">
              <RadioGroup
                value={siblingParentMode}
                onChange={onChangeSiblingParentMode}
                options={[
                  {
                    value: "same",
                    label: `Общие родители (${relativeParents.map(p => p.first_name || p.full_name).join(", ")})`,
                  },
                  { value: "different", label: "Разные родители (другой родитель)" },
                ]}
              />
              <AnimatePresence>
                {siblingParentMode === "different" && (
                  <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} className="pt-2 space-y-2">
                    <Label className="text-xs text-muted-foreground block">Другой общий родитель (необязательно)</Label>
                    <PersonPicker
                      nodes={nodes}
                      value={siblingParentId}
                      onChange={onChangeSiblingParentId}
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

      {/* ── Имя и фамилия ───────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <Label className="text-xs text-muted-foreground mb-1 block">Имя *</Label>
          <Input
            value={form.first_name} onChange={e => onChangeField("first_name", e.target.value)}
            placeholder="Иван" className="rounded-xl" disabled={saving} autoFocus
          />
        </div>
        <div>
          <Label className="text-xs text-muted-foreground mb-1 block">Фамилия *</Label>
          <Input
            value={form.last_name} onChange={e => onChangeField("last_name", e.target.value)}
            placeholder="Иванов" className="rounded-xl" disabled={saving}
          />
        </div>
      </div>

      {/* ── Пол ─────────────────────────────────────────────────────────── */}
      <div>
        <Label className="text-xs text-muted-foreground mb-1 block">Пол</Label>
        <Select value={form.gender} onValueChange={v => onChangeField("gender", v)} disabled={saving}>
          <SelectTrigger className="rounded-xl"><SelectValue /></SelectTrigger>
          <SelectContent>
            {GENDERS.map(g => <SelectItem key={g.value} value={g.value}>{g.label}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      {/* ── Даты ────────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <Label className="text-xs text-muted-foreground mb-1 block">Год рождения</Label>
          <Input
            type="number" min="1" max="9999"
            value={form.birth_date} onChange={e => onChangeField("birth_date", e.target.value)}
            placeholder="1990" className="rounded-xl" disabled={saving}
          />
        </div>
        <div>
          <Label className="text-xs text-muted-foreground mb-1 block">Год смерти</Label>
          <Input
            type="number" min="1" max="9999"
            value={form.death_date} onChange={e => onChangeField("death_date", e.target.value)}
            placeholder="необязательно" className="rounded-xl" disabled={saving}
          />
        </div>
      </div>

      {/* ── Блок: новый родитель + существующий со-родитель как супруги ─── */}
      <AnimatePresence>
        {showCoParentSpouseOffer && existingCoParent && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }}>
            <div className="rounded-2xl p-4 space-y-3" style={{ background: "hsl(345,60%,98%)", border: "1px solid hsl(345,50%,88%)" }}>
              <div className="flex items-center gap-2 mb-1">
                <Heart className="w-3.5 h-3.5 flex-shrink-0" style={{ color: "hsl(345,60%,55%)" }} />
                <span className="text-xs font-semibold uppercase tracking-wide" style={{ color: "hsl(345,45%,40%)" }}>
                  Уже есть родитель
                </span>
              </div>

              <div className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm" style={{ background: "hsl(345,50%,94%)" }}>
                <div
                  className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0"
                  style={{ background: "hsl(345,55%,82%)", color: "hsl(345,55%,30%)" }}
                >
                  {(existingCoParent.first_name || existingCoParent.full_name || "?")[0].toUpperCase()}
                </div>
                <span className="font-medium" style={{ color: "hsl(345,45%,25%)" }}>
                  {[existingCoParent.first_name, existingCoParent.last_name].filter(Boolean).join(" ") || existingCoParent.full_name}
                </span>
                {existingCoParent.birth_year && (
                  <span className="text-xs ml-auto" style={{ color: "hsl(345,35%,55%)" }}>{existingCoParent.birth_year}</span>
                )}
              </div>

              <ToggleCheckbox
                checked={makeSpouseOfCoParent}
                onChange={onChangeMakeSpouseOfCoParent}
                label="Сделать их супругами"
                sublabel={`Новый родитель и ${existingCoParent.first_name || existingCoParent.full_name} будут связаны как партнёры`}
              />

              <AnimatePresence>
                {makeSpouseOfCoParent && (
                  <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} className="space-y-3 pt-1">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <Label className="text-xs text-muted-foreground mb-1 block">Год свадьбы</Label>
                        <Input type="number" min="1" max="9999" value={coParentMarriageDate} onChange={e => onChangeCoParentMarriageDate(e.target.value)} placeholder="необязательно" className="rounded-xl" disabled={saving} />
                      </div>
                      <div>
                        <Label className="text-xs text-muted-foreground mb-1 block">Год развода</Label>
                        <Input type="number" min="1" max="9999" value={coParentDivorceDate} onChange={e => onChangeCoParentDivorceDate(e.target.value)} placeholder="необязательно" className="rounded-xl" disabled={saving} />
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Блок: второй родитель у ребёнка ─────────────────────────────── */}
      <AnimatePresence>
        {!isEdit && relationType === "child" && relativePerson && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }}>
            <div className="rounded-2xl p-4 space-y-3" style={{ background: "hsl(35,40%,96%)", border: "1px solid hsl(35,25%,88%)" }}>
              <ToggleCheckbox
                checked={parentsMarried}
                onChange={onChangeParentsMarried}
                label="Есть второй родитель у этого ребёнка?"
              />

              <AnimatePresence>
                {parentsMarried && (
                  <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} className="space-y-3 pt-1">
                    <div>
                      <Label className="text-xs text-muted-foreground mb-1.5 block">Второй родитель (из существующих)</Label>
                      <PersonPicker
                        nodes={nodes}
                        value={secondParentId}
                        onChange={onChangeSecondParentId}
                        placeholder="Выбрать из списка"
                        exclude={[relativePerson?.id].filter(Boolean)}
                      />
                    </div>

                    {secondParentId && (
                      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
                        <div className="flex items-center gap-2 p-3 rounded-xl text-xs" style={{ background: "hsl(145,35%,94%)", border: "1px solid hsl(145,35%,82%)" }}>
                          <Check className="w-3.5 h-3.5 flex-shrink-0" style={{ color: "hsl(145,35%,38%)" }} />
                          <span style={{ color: "hsl(145,35%,28%)" }}>
                            Ребёнок будет связан с обоими родителями. Также создать связь «супруги» между ними?
                          </span>
                        </div>
                        <SectionCard title="Данные о браке (необязательно)" icon={null} color="hsl(30,50%,45%)">
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <Label className="text-xs text-muted-foreground mb-1 block">Год свадьбы</Label>
                              <Input type="number" min="1" max="9999" value={marriageDate} onChange={e => onChangeMarriageDate(e.target.value)} placeholder="необязательно" className="rounded-xl" disabled={saving} />
                            </div>
                            <div>
                              <Label className="text-xs text-muted-foreground mb-1 block">Год развода</Label>
                              <Input type="number" min="1" max="9999" value={divorceDate} onChange={e => onChangeDivorceDate(e.target.value)} placeholder="необязательно" className="rounded-xl" disabled={saving} />
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
  );
}
