/**
 * components/tree/PersonSidebar.jsx
 */

import { X, Edit, UserPlus, User, Calendar, Heart, Link2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getPersonRelations } from "@/api";

// ── Helpers ───────────────────────────────────────────────────────────────────

const SIBLING_TYPE_LABEL = {
  FULL: "Брат/сестра",
  HALF: "Единокровный(ая) / единоутробный(ая)",
  STEP: "Сводный(ая) брат/сестра",
};

function computeAgeFromYears(birthYear, deathYear, isAlive) {
  if (!birthYear) return null;
  const endYear = (!isAlive && deathYear) ? deathYear : new Date().getFullYear();
  const age = endYear - birthYear;
  return age >= 0 ? age : null;
}

function RelativeChip({ node, label, badge }) {
  if (!node) return null;
  const name = node.full_name || [node.first_name, node.last_name].filter(Boolean).join(" ") || "—";

  return (
    <div className="flex items-center gap-2.5 p-2.5 rounded-xl" style={{ background: "hsl(35,25%,95%)" }}>
      <div className="w-9 h-9 rounded-full overflow-hidden flex-shrink-0 flex items-center justify-center"
        style={{ background: "hsl(35,40%,88%)" }}>
        <User className="w-4 h-4 text-muted-foreground" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-foreground truncate">{name}</div>
        <div className="text-xs text-muted-foreground">{label}</div>
      </div>
      {badge && (
        <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded-full flex-shrink-0"
          style={{
            background: badge === "FULL" ? "hsl(145,35%,90%)" : badge === "HALF" ? "hsl(210,50%,90%)" : "hsl(0,0%,90%)",
            color:      badge === "FULL" ? "hsl(145,40%,35%)" : badge === "HALF" ? "hsl(210,55%,40%)" : "hsl(0,0%,40%)",
          }}>
          {badge}
        </span>
      )}
    </div>
  );
}

export default function PersonSidebar({
  person, nodes, relationMaps, onClose,
  canEdit, onEdit, onAddRelative, onConnect, onDelete,
}) {
  if (!person) return null;

  const nodesById = new Map((nodes ?? []).map((n) => [n.id, n]));
  const rel = getPersonRelations(relationMaps, person.id);

  const parents  = rel.parentIds .map((id) => nodesById.get(id)).filter(Boolean);
  const children = rel.childIds  .map((id) => nodesById.get(id)).filter(Boolean);
  const spouses  = rel.spouseIds .map((id) => nodesById.get(id)).filter(Boolean);
  const siblings = rel.siblingIds.map((id) => {
    const node = nodesById.get(id);
    if (!node) return null;
    return { node, type: rel.siblingTypeMap.get(id) ?? "FULL" };
  }).filter(Boolean);

  const birthYear = person.birth_year ?? null;
  const deathYear = person.death_year ?? null;
  const isAlive   = person.is_alive   ?? true;
  const age       = computeAgeFromYears(birthYear, deathYear, isAlive);

  const genderLabel =
    person.gender === "MALE"   ? "Мужской"  :
    person.gender === "FEMALE" ? "Женский"  : "Другой";

  const hasRelatives = spouses.length + parents.length + children.length + siblings.length > 0;

  return (
    <div className="h-full flex flex-col"
      style={{ background: "hsl(40,33%,98%)", borderLeft: "1px solid hsl(35,20%,88%)" }}>

      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 flex-shrink-0"
        style={{ borderBottom: "1px solid hsl(35,20%,90%)" }}>
        <span className="text-xs font-semibold text-muted-foreground uppercase tracking-widest">Профиль</span>
        <button onClick={onClose}
          className="w-7 h-7 rounded-lg flex items-center justify-center hover:bg-muted transition-colors">
          <X className="w-4 h-4 text-muted-foreground" />
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto">
        <div className="flex flex-col items-center text-center px-5 py-6"
          style={{ background: "linear-gradient(to bottom, hsl(145,35%,96%), hsl(40,33%,98%))" }}>
          <div className="w-24 h-24 rounded-2xl overflow-hidden mb-4 shadow-md flex items-center justify-center"
            style={{ border: "3px solid hsl(145,35%,80%)", background: "hsl(35,40%,90%)" }}>
            <User className="w-10 h-10 text-muted-foreground/60" />
          </div>

          <h2 className="font-serif text-xl font-semibold text-foreground">
            {person.full_name || [person.first_name, person.last_name].filter(Boolean).join(" ") || "—"}
          </h2>

          <div className="flex items-center gap-2 mt-1 text-sm text-muted-foreground">
            {birthYear && (
              <span>{birthYear}{!isAlive && deathYear ? ` — ${deathYear}` : ""}</span>
            )}
            {age !== null && <span>· {age} лет</span>}
          </div>

          <div className="mt-1 text-xs text-muted-foreground">{genderLabel}</div>
          {!isAlive && <div className="mt-1 text-xs text-muted-foreground/60">† Умер(ла)</div>}
        </div>

        <div className="px-5 pb-5 space-y-5">
          {(person.birth_date_raw || birthYear) && (
            <div className="space-y-2.5">
              <div className="flex items-start gap-3 text-sm">
                <Calendar className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: "hsl(145,35%,45%)" }} />
                <div>
                  <div className="text-xs text-muted-foreground">Дата рождения</div>
                  <div className="font-medium text-foreground">{person.birth_date_raw || birthYear}</div>
                </div>
              </div>
              {!isAlive && (person.birth_date_raw || deathYear) && (
                <div className="flex items-start gap-3 text-sm">
                  <Calendar className="w-4 h-4 mt-0.5 flex-shrink-0 text-muted-foreground" />
                  <div>
                    <div className="text-xs text-muted-foreground">Дата смерти</div>
                    <div className="font-medium text-foreground">{deathYear || "неизвестно"}</div>
                  </div>
                </div>
              )}
            </div>
          )}

          {hasRelatives && (
            <div>
              <div className="flex items-center gap-1.5 mb-3">
                <Heart className="w-3.5 h-3.5 text-muted-foreground" />
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                  Родственники
                </span>
              </div>
              <div className="space-y-2">
                {spouses.map((n)  => <RelativeChip key={n.id} node={n} label="Партнёр / Супруг(а)" />)}
                {parents.map((n)  => <RelativeChip key={n.id} node={n} label="Родитель" />)}
                {siblings.map(({ node, type }) => (
                  <RelativeChip key={node.id} node={node}
                    label={SIBLING_TYPE_LABEL[type] ?? "Брат / Сестра"} badge={type} />
                ))}
                {children.map((n) => <RelativeChip key={n.id} node={n} label="Ребёнок" />)}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="flex-shrink-0 p-4 space-y-2.5" style={{ borderTop: "1px solid hsl(35,20%,90%)" }}>
        {canEdit ? (
          <>
            <Button className="w-full rounded-xl gap-2 bg-primary text-primary-foreground hover:bg-primary/90"
              onClick={() => onEdit?.(person)}>
              <Edit className="w-4 h-4" /> Редактировать
            </Button>
            <Button variant="outline" className="w-full rounded-xl gap-2"
              onClick={() => onAddRelative?.(person)}>
              <UserPlus className="w-4 h-4" /> Добавить родственника
            </Button>
            {nodes?.length >= 2 && (
              <Button variant="outline" className="w-full rounded-xl gap-2"
                onClick={() => onConnect?.(person)}>
                <Link2 className="w-4 h-4" /> Связать с другим
              </Button>
            )}
            <Button variant="outline"
              className="w-full rounded-xl gap-2 text-destructive border-destructive/30 hover:bg-destructive/5"
              onClick={() => onDelete?.(person.id)}>
              Удалить
            </Button>
          </>
        ) : (
          <div className="text-center py-2">
            <p className="text-xs text-muted-foreground">Войдите, чтобы редактировать дерево</p>
          </div>
        )}
      </div>
    </div>
  );
}
