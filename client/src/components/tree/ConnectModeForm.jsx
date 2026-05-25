/**
 * components/tree/ConnectModeForm.jsx
 *
 * Форма режима «Связать родственников» в AddPersonModal.
 * Позволяет выбрать двух людей из дерева и тип связи между ними.
 */

import { motion, AnimatePresence } from "framer-motion";
import { UserCheck } from "lucide-react";
import { Input }  from "@/components/ui/input";
import { Label }  from "@/components/ui/label";
import { PersonPicker, SectionCard } from "./modalAtoms";

const CONNECT_RELATION_TYPES = [
  { value: "parent_child_ab", labelFn: (a, b) => a && b ? `${a} — родитель ${b}` : "Первый — родитель второго" },
  { value: "parent_child_ba", labelFn: (a, b) => a && b ? `${b} — родитель ${a}` : "Второй — родитель первого" },
  { value: "spouse",          labelFn: ()      => "Супруги / Партнёры" },
  { value: "sibling",         labelFn: ()      => "Братья / Сёстры" },
];

export default function ConnectModeForm({
  nodes,
  personA, onChangeA,
  personB, onChangeB,
  relType, onChangeRelType,
  marriageDate, onChangeMarriageDate,
  divorceDate,  onChangeDivorceDate,
  saving,
}) {
  const nameA = personA ? (nodes.find(n => n.id === personA)?.first_name ?? "Первый")  : null;
  const nameB = personB ? (nodes.find(n => n.id === personB)?.first_name ?? "Второй") : null;

  return (
    <>
      <SectionCard title="Первый человек" icon={UserCheck} color="hsl(145,35%,38%)">
        <PersonPicker
          nodes={nodes} value={personA} onChange={onChangeA}
          placeholder="Выберите первого"
          exclude={personB ? [personB] : []}
        />
      </SectionCard>

      <SectionCard title="Второй человек" icon={UserCheck} color="hsl(210,60%,50%)">
        <PersonPicker
          nodes={nodes} value={personB} onChange={onChangeB}
          placeholder="Выберите второго"
          exclude={personA ? [personA] : []}
        />
      </SectionCard>

      {/* Разделитель */}
      <div className="flex items-center gap-3">
        <div className="flex-1 h-px" style={{ background: "hsl(35,20%,88%)" }} />
        <div className="px-3 py-1 rounded-xl text-xs font-semibold text-muted-foreground"
          style={{ background: "hsl(35,30%,94%)" }}>
          связь
        </div>
        <div className="flex-1 h-px" style={{ background: "hsl(35,20%,88%)" }} />
      </div>

      {/* Тип связи */}
      <div className="grid grid-cols-1 gap-2">
        {CONNECT_RELATION_TYPES.map(r => (
          <button
            key={r.value} type="button"
            onClick={() => onChangeRelType(r.value)}
            className="py-2.5 px-4 rounded-xl text-sm font-medium transition-all text-left"
            style={{
              background: relType === r.value ? "hsl(145,35%,38%)" : "hsl(35,30%,95%)",
              color:      relType === r.value ? "white"             : "hsl(30,10%,30%)",
              border:     relType === r.value ? "none"              : "1px solid hsl(35,20%,88%)",
            }}
          >
            {r.labelFn(nameA, nameB)}
          </button>
        ))}
      </div>

      {/* Данные о браке — только для spouse */}
      <AnimatePresence>
        {relType === "spouse" && (
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
                    value={marriageDate} onChange={e => onChangeMarriageDate(e.target.value)}
                    placeholder="необязательно" className="rounded-xl" disabled={saving}
                  />
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground mb-1 block">Год развода</Label>
                  <Input
                    type="number" min="1" max="9999"
                    value={divorceDate} onChange={e => onChangeDivorceDate(e.target.value)}
                    placeholder="необязательно" className="rounded-xl" disabled={saving}
                  />
                </div>
              </div>
            </SectionCard>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
