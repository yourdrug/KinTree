import React from 'react';
import { Button } from '@/components/ui/button';
import { X, User, Calendar, MapPin, Pencil, UserPlus, Paperclip, Heart } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

export default function MemberSidePanel({ member, members, isOpen, onClose, canEdit, onEdit, onAddRelative }) {
  const parents = members.filter(m => member?.parent_ids?.includes(m.id));
  const children = members.filter(m => m.parent_ids?.includes(member?.id));
  const partner = members.find(m => m.id === member?.partner_id);

  const formatDate = (dateStr) => {
    if (!dateStr) return null;
    return format(new Date(dateStr), 'd MMMM yyyy', { locale: ru });
  };

  return (
    <AnimatePresence>
      {isOpen && member && (
        <motion.div
          initial={{ x: 400, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          exit={{ x: 400, opacity: 0 }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          className="absolute top-0 right-0 h-full w-96 max-w-full bg-card/95 backdrop-blur-xl border-l border-border/50 z-20 overflow-y-auto"
        >
          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wide">Профиль</h3>
              <Button variant="ghost" size="icon" className="w-8 h-8 rounded-full" onClick={onClose}>
                <X className="w-4 h-4" />
              </Button>
            </div>

            {/* Photo & Name */}
            <div className="flex flex-col items-center text-center mb-8">
              <div className={`w-24 h-24 rounded-2xl flex items-center justify-center mb-4 ${
                member.photo_url ? '' : 'bg-gradient-to-br from-primary/15 to-accent/30'
              }`}>
                {member.photo_url ? (
                  <img src={member.photo_url} alt="" className="w-full h-full rounded-2xl object-cover" />
                ) : (
                  <User className="w-10 h-10 text-primary/50" />
                )}
              </div>
              <h2 className="text-xl font-serif font-bold">{member.first_name} {member.last_name}</h2>
              {member.birth_date && (
                <p className="text-sm text-muted-foreground mt-1">
                  {new Date(member.birth_date).getFullYear()}
                  {member.death_date && ` – ${new Date(member.death_date).getFullYear()}`}
                </p>
              )}
            </div>

            {/* Details */}
            <div className="space-y-4 mb-8">
              {member.birth_date && (
                <div className="flex items-center gap-3 text-sm">
                  <Calendar className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                  <div>
                    <span className="text-muted-foreground">Дата рождения: </span>
                    <span className="font-medium">{formatDate(member.birth_date)}</span>
                  </div>
                </div>
              )}
              {member.death_date && (
                <div className="flex items-center gap-3 text-sm">
                  <Calendar className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                  <div>
                    <span className="text-muted-foreground">Дата смерти: </span>
                    <span className="font-medium">{formatDate(member.death_date)}</span>
                  </div>
                </div>
              )}
              {member.birth_place && (
                <div className="flex items-center gap-3 text-sm">
                  <MapPin className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                  <div>
                    <span className="text-muted-foreground">Место рождения: </span>
                    <span className="font-medium">{member.birth_place}</span>
                  </div>
                </div>
              )}
            </div>

            {/* Bio */}
            {member.bio && (
              <div className="mb-8">
                <h4 className="text-sm font-medium text-muted-foreground mb-2">О человеке</h4>
                <p className="text-sm leading-relaxed bg-muted/50 rounded-xl p-4">{member.bio}</p>
              </div>
            )}

            {/* Relatives */}
            <div className="space-y-4 mb-8">
              {partner && (
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground mb-2 flex items-center gap-1.5">
                    <Heart className="w-3.5 h-3.5" />
                    Партнёр
                  </h4>
                  <div className="bg-muted/50 rounded-xl p-3 flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                      <User className="w-4 h-4 text-primary/60" />
                    </div>
                    <span className="text-sm font-medium">{partner.first_name} {partner.last_name}</span>
                  </div>
                </div>
              )}
              {parents.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground mb-2">Родители</h4>
                  <div className="space-y-2">
                    {parents.map(p => (
                      <div key={p.id} className="bg-muted/50 rounded-xl p-3 flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                          <User className="w-4 h-4 text-primary/60" />
                        </div>
                        <span className="text-sm font-medium">{p.first_name} {p.last_name}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {children.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground mb-2">Дети</h4>
                  <div className="space-y-2">
                    {children.map(c => (
                      <div key={c.id} className="bg-muted/50 rounded-xl p-3 flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                          <User className="w-4 h-4 text-primary/60" />
                        </div>
                        <span className="text-sm font-medium">{c.first_name} {c.last_name}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Actions */}
            {canEdit && (
              <div className="space-y-2">
                <Button className="w-full rounded-xl gap-2" onClick={() => onEdit(member)}>
                  <Pencil className="w-4 h-4" />
                  Редактировать
                </Button>
                <Button variant="outline" className="w-full rounded-xl gap-2" onClick={() => onAddRelative(member)}>
                  <UserPlus className="w-4 h-4" />
                  Добавить родственника
                </Button>
              </div>
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}