import { motion, AnimatePresence } from "framer-motion";
import { X, Edit, UserPlus, User, Calendar, MapPin, Heart, FileText, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";

function RelativeChip({ person, label }) {
  return (
    <div className="flex items-center gap-2.5 p-2.5 rounded-xl transition-colors hover:bg-muted/60 cursor-default"
      style={{ background: "hsl(35,25%,95%)" }}>
      <div className="w-9 h-9 rounded-full overflow-hidden flex-shrink-0"
        style={{ background: "hsl(35,40%,88%)" }}>
        {person.photo_url
          ? <img src={person.photo_url} className="w-full h-full object-cover" alt="" />
          : <div className="w-full h-full flex items-center justify-center">
              <User className="w-4 h-4 text-muted-foreground" />
            </div>
        }
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-foreground truncate">{person.first_name} {person.last_name}</div>
        <div className="text-xs text-muted-foreground">{label}</div>
      </div>
    </div>
  );
}

export default function PersonSidebar({ person, members, onClose, canEdit, onEdit, onAddRelative }) {
  if (!person) return null;

  const parents = members.filter((m) => person.parent_ids?.includes(m.id));
  const children = members.filter((m) => m.parent_ids?.includes(person.id));
  const partner = members.find((m) => m.id === person.partner_id);
  const siblings = members.filter(
    (m) => m.id !== person.id && person.parent_ids?.length > 0 &&
    m.parent_ids?.some((pid) => person.parent_ids?.includes(pid))
  );

  const birthYear = person.birth_date ? new Date(person.birth_date).getFullYear() : null;
  const deathYear = person.death_date ? new Date(person.death_date).getFullYear() : null;
  const age = birthYear
    ? (deathYear ? deathYear - birthYear : new Date().getFullYear() - birthYear)
    : null;

  const formatDate = (d) =>
    d ? new Date(d).toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: "numeric" }) : null;

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

      {/* Scrollable body */}
      <div className="flex-1 overflow-y-auto">
        {/* Photo + Name */}
        <div className="flex flex-col items-center text-center px-5 py-6"
          style={{ background: "linear-gradient(to bottom, hsl(145,35%,96%), hsl(40,33%,98%))" }}>
          <div className="w-24 h-24 rounded-2xl overflow-hidden mb-4 shadow-md"
            style={{ border: "3px solid hsl(145,35%,80%)" }}>
            {person.photo_url
              ? <img src={person.photo_url} className="w-full h-full object-cover" alt="" />
              : <div className="w-full h-full flex items-center justify-center" style={{ background: "hsl(35,40%,90%)" }}>
                  <User className="w-10 h-10 text-muted-foreground/60" />
                </div>
            }
          </div>
          <h2 className="font-serif text-xl font-semibold text-foreground">
            {person.first_name} {person.last_name}
          </h2>
          <div className="flex items-center gap-2 mt-1 text-sm text-muted-foreground">
            {birthYear && <span>{birthYear}{deathYear ? ` — ${deathYear}` : ""}</span>}
            {age && <span>· {age} лет</span>}
          </div>
        </div>

        <div className="px-5 pb-5 space-y-5">
          {/* Details */}
          <div className="space-y-2.5">
            {formatDate(person.birth_date) && (
              <div className="flex items-start gap-3 text-sm">
                <Calendar className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: "hsl(145,35%,45%)" }} />
                <div>
                  <div className="text-xs text-muted-foreground">Дата рождения</div>
                  <div className="font-medium text-foreground">{formatDate(person.birth_date)}</div>
                </div>
              </div>
            )}
            {formatDate(person.death_date) && (
              <div className="flex items-start gap-3 text-sm">
                <Calendar className="w-4 h-4 mt-0.5 flex-shrink-0 text-muted-foreground" />
                <div>
                  <div className="text-xs text-muted-foreground">Дата смерти</div>
                  <div className="font-medium text-foreground">{formatDate(person.death_date)}</div>
                </div>
              </div>
            )}
            {person.birth_place && (
              <div className="flex items-start gap-3 text-sm">
                <MapPin className="w-4 h-4 mt-0.5 flex-shrink-0" style={{ color: "hsl(200,40%,50%)" }} />
                <div>
                  <div className="text-xs text-muted-foreground">Место рождения</div>
                  <div className="font-medium text-foreground">{person.birth_place}</div>
                </div>
              </div>
            )}
          </div>

          {/* Bio */}
          {person.bio && (
            <div>
              <div className="flex items-center gap-1.5 mb-2">
                <FileText className="w-3.5 h-3.5 text-muted-foreground" />
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">История</span>
              </div>
              <p className="text-sm text-foreground leading-relaxed p-3 rounded-xl"
                style={{ background: "hsl(35,30%,96%)" }}>{person.bio}</p>
            </div>
          )}

          {/* Relatives */}
          {(partner || parents.length > 0 || children.length > 0 || siblings.length > 0) && (
            <div>
              <div className="flex items-center gap-1.5 mb-3">
                <Heart className="w-3.5 h-3.5 text-muted-foreground" />
                <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Родственники</span>
              </div>
              <div className="space-y-2">
                {partner && <RelativeChip person={partner} label="Партнёр / Супруг(а)" />}
                {parents.map((p) => <RelativeChip key={p.id} person={p} label="Родитель" />)}
                {siblings.map((s) => <RelativeChip key={s.id} person={s} label="Брат / Сестра" />)}
                {children.map((c) => <RelativeChip key={c.id} person={c} label="Ребёнок" />)}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer actions */}
      <div className="flex-shrink-0 p-4 space-y-2.5" style={{ borderTop: "1px solid hsl(35,20%,90%)" }}>
        {canEdit ? (
          <>
            <Button
              className="w-full rounded-xl gap-2 bg-primary text-primary-foreground hover:bg-primary/90"
              onClick={() => onEdit && onEdit(person)}
            >
              <Edit className="w-4 h-4" /> Редактировать
            </Button>
            <Button
              variant="outline"
              className="w-full rounded-xl gap-2"
              onClick={() => onAddRelative && onAddRelative(person)}
            >
              <UserPlus className="w-4 h-4" /> Добавить родственника
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