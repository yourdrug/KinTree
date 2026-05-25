/**
 * components/tree/AddPersonModal.jsx
 *
 * Оркестратор модала добавления/редактирования персоны.
 * Содержит только: состояние, логику сохранения и обёртку (шапка + футер).
 *
 * Формы вынесены в отдельные компоненты:
 *   ConnectModeForm — режим «связать существующих»
 *   AddModeForm     — режим «добавить нового / редактировать»
 */

import { useState, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getPersonRelations } from "@/api";

import ConnectModeForm from "./ConnectModeForm";
import AddModeForm     from "./AddModeForm";

// ── Helpers ───────────────────────────────────────────────────────────────────

function buildEmptyForm() {
  return { first_name: "", last_name: "", birth_date: "", death_date: "", gender: "MALE" };
}

function formFromNode(node) {
  return {
    first_name: node.first_name || node.full_name?.split(" ")[0] || "",
    last_name:  node.last_name  || node.full_name?.split(" ").slice(1).join(" ") || "",
    gender:     node.gender     || "MALE",
    birth_date: node.birth_year ? String(node.birth_year) : "",
    death_date: node.death_year ? String(node.death_year) : "",
  };
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function AddPersonModal({
  open, onClose, onSave, onConnect,
  relativePerson, editPerson, relationMaps,
  initialConnectMode = false,
  nodes = [],
}) {
  const [relationType, setRelationType] = useState("child");
  const [form,         setForm]         = useState(buildEmptyForm());
  const [saving,       setSaving]       = useState(false);

  // Connect mode
  const [connectMode,    setConnectMode]    = useState(false);
  const [connectPersonA, setConnectPersonA] = useState(null);
  const [connectPersonB, setConnectPersonB] = useState(null);
  const [connectRelType, setConnectRelType] = useState("spouse");

  // Child + second parent
  const [parentsMarried, setParentsMarried] = useState(false);
  const [secondParentId, setSecondParentId] = useState(null);
  const [marriageDate,   setMarriageDate]   = useState("");
  const [divorceDate,    setDivorceDate]    = useState("");

  // Новый родитель + существующий со-родитель как супруги
  const [makeSpouseOfCoParent, setMakeSpouseOfCoParent] = useState(false);
  const [coParentMarriageDate, setCoParentMarriageDate] = useState("");
  const [coParentDivorceDate,  setCoParentDivorceDate]  = useState("");

  // Сиблинги
  const [siblingParentMode, setSiblingParentMode] = useState("same");
  const [siblingParentId,   setSiblingParentId]   = useState(null);

  const isEdit = !!editPerson;

  // ── Вычисляемые значения ───────────────────────────────────────────────────

  const existingParents = useMemo(() => {
    if (!relativePerson || !relationMaps || !nodes.length) return [];
    const rel = getPersonRelations(relationMaps, relativePerson.id);
    return rel.parentIds.map(id => nodes.find(n => n.id === id)).filter(Boolean);
  }, [relativePerson, relationMaps, nodes]);

  const showCoParentSpouseOffer = useMemo(() => (
    !isEdit && !connectMode && relationType === "parent" && existingParents.length === 1
  ), [isEdit, connectMode, relationType, existingParents]);

  const existingCoParent = showCoParentSpouseOffer ? existingParents[0] : null;

  const siblingNoParents = (
    !isEdit && relationType === "sibling" && relativePerson && relationMaps &&
    getPersonRelations(relationMaps, relativePerson.id).parentIds.length === 0
  );

  const canSave = connectMode
    ? (connectPersonA && connectPersonB && connectPersonA !== connectPersonB)
    : (form.first_name?.trim() && form.last_name?.trim() && !saving);

  // ── Сброс состояния при открытии ──────────────────────────────────────────

  useEffect(() => {
    if (!open) return;
    if (isEdit) {
      setForm(formFromNode(editPerson));
      setConnectMode(false);
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
      setMakeSpouseOfCoParent(false);
      setCoParentMarriageDate("");
      setCoParentDivorceDate("");
      setSiblingParentMode("same");
      setSiblingParentId(null);
    }
  }, [open, editPerson, isEdit, relativePerson]);

  useEffect(() => {
    if (open) setConnectMode(initialConnectMode);
  }, [open, initialConnectMode]);

  useEffect(() => {
    setMakeSpouseOfCoParent(false);
    setCoParentMarriageDate("");
    setCoParentDivorceDate("");
  }, [relationType]);

  // ── Сохранение ────────────────────────────────────────────────────────────

  const handleSave = async () => {
    if (saving) return;
    setSaving(true);
    try {
      if (connectMode) {
        if (!connectPersonA || !connectPersonB) return;
        await onConnect?.({
          personA: connectPersonA, personB: connectPersonB,
          relType: connectRelType, marriageDate, divorceDate,
        });
        onClose();
        return;
      }

      const extra = {};

      if (!isEdit && relationType === "child" && parentsMarried && secondParentId) {
        extra.secondParentId = secondParentId;
        extra.parentsMarried = true;
        extra.marriageDate   = marriageDate || null;
        extra.divorceDate    = divorceDate  || null;
      }

      if (!isEdit && relationType === "sibling") {
        extra.siblingParentMode = siblingParentMode;
        extra.siblingParentId   = siblingParentMode === "different" ? siblingParentId : null;
      }

      if (!isEdit && relationType === "parent" && makeSpouseOfCoParent && existingCoParent) {
        extra.makeSpouseOfCoParent = true;
        extra.coParentId           = existingCoParent.id;
        extra.coParentMarriageDate = coParentMarriageDate || null;
        extra.coParentDivorceDate  = coParentDivorceDate  || null;
      }

      await onSave(form, editPerson?.id, relationType, relativePerson, extra);
      onClose();
    } catch {
      // ошибки показываются через toast в TreeView
    } finally {
      setSaving(false);
    }
  };

  // ── Заголовок ─────────────────────────────────────────────────────────────

  const title = isEdit && connectMode ? "Связать с другим человеком"
    : isEdit        ? "Редактировать"
    : connectMode   ? "Связать родственников"
    : relativePerson ? `Добавить к: ${relativePerson.first_name || relativePerson.full_name}`
    : "Добавить человека";

  const subtitle = connectMode ? "Создать родственную связь между людьми"
    : (!isEdit && relativePerson) ? "Выберите тип связи"
    : "";

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
            {/* Шапка */}
            <div className="flex items-center justify-between px-6 pt-6 pb-4"
              style={{ borderBottom: "1px solid hsl(35,20%,90%)" }}>
              <div>
                <h2 className="font-serif text-xl font-semibold text-foreground">{title}</h2>
                {subtitle && <p className="text-xs text-muted-foreground mt-0.5">{subtitle}</p>}
              </div>
              {!saving && (
                <button onClick={onClose}
                  className="w-8 h-8 rounded-xl flex items-center justify-center hover:bg-muted transition-colors">
                  <X className="w-4 h-4 text-muted-foreground" />
                </button>
              )}
            </div>

            {/* Тело */}
            <div className="px-6 py-5 space-y-4 max-h-[72vh] overflow-y-auto">
              {connectMode ? (
                <ConnectModeForm
                  nodes={nodes}
                  personA={connectPersonA}  onChangeA={setConnectPersonA}
                  personB={connectPersonB}  onChangeB={setConnectPersonB}
                  relType={connectRelType}  onChangeRelType={setConnectRelType}
                  marriageDate={marriageDate} onChangeMarriageDate={setMarriageDate}
                  divorceDate={divorceDate}   onChangeDivorceDate={setDivorceDate}
                  saving={saving}
                />
              ) : (
                <AddModeForm
                  isEdit={isEdit}
                  relativePerson={relativePerson}
                  nodes={nodes}
                  saving={saving}

                  relationType={relationType}
                  onChangeRelationType={setRelationType}

                  form={form}
                  onChangeField={(key, val) => setForm(f => ({ ...f, [key]: val }))}

                  parentsMarried={parentsMarried} onChangeParentsMarried={setParentsMarried}
                  secondParentId={secondParentId} onChangeSecondParentId={setSecondParentId}
                  marriageDate={marriageDate}     onChangeMarriageDate={setMarriageDate}
                  divorceDate={divorceDate}       onChangeDivorceDate={setDivorceDate}

                  existingCoParent={existingCoParent}
                  showCoParentSpouseOffer={showCoParentSpouseOffer}
                  makeSpouseOfCoParent={makeSpouseOfCoParent}   onChangeMakeSpouseOfCoParent={setMakeSpouseOfCoParent}
                  coParentMarriageDate={coParentMarriageDate}   onChangeCoParentMarriageDate={setCoParentMarriageDate}
                  coParentDivorceDate={coParentDivorceDate}     onChangeCoParentDivorceDate={setCoParentDivorceDate}

                  siblingNoParents={siblingNoParents}
                  relativeParents={existingParents}
                  siblingParentMode={siblingParentMode} onChangeSiblingParentMode={setSiblingParentMode}
                  siblingParentId={siblingParentId}     onChangeSiblingParentId={setSiblingParentId}
                />
              )}
            </div>

            {/* Футер */}
            <div className="flex gap-3 px-6 py-4" style={{ borderTop: "1px solid hsl(35,20%,90%)" }}>
              <Button variant="outline" className="flex-1 rounded-xl" onClick={onClose} disabled={saving}>
                Отмена
              </Button>
              <Button
                className="flex-1 rounded-xl bg-primary text-primary-foreground hover:bg-primary/90"
                onClick={handleSave} disabled={!canSave}
              >
                {saving ? "Сохранение..." : connectMode ? "Создать связь" : isEdit ? "Сохранить" : "Добавить"}
              </Button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
