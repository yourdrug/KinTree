import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

const emptyForm = {
  first_name: '',
  last_name: '',
  birth_date: '',
  death_date: '',
  gender: '',
  bio: '',
  birth_place: '',
  parent_ids: [],
  partner_id: '',
  generation: 0,
};

export default function MemberFormDialog({ open, onOpenChange, member, members, treeId, onSave, relativeContext }) {
  const [form, setForm] = useState(emptyForm);

  useEffect(() => {
    if (member) {
      setForm({
        first_name: member.first_name || '',
        last_name: member.last_name || '',
        birth_date: member.birth_date || '',
        death_date: member.death_date || '',
        gender: member.gender || '',
        bio: member.bio || '',
        birth_place: member.birth_place || '',
        parent_ids: member.parent_ids || [],
        partner_id: member.partner_id || '',
        generation: member.generation ?? 0,
      });
    } else if (relativeContext) {
      setForm({
        ...emptyForm,
        parent_ids: [relativeContext.id],
        generation: (relativeContext.generation || 0) + 1,
      });
    } else {
      setForm(emptyForm);
    }
  }, [member, relativeContext, open]);

  const handleSave = () => {
    onSave({
      ...form,
      tree_id: treeId,
    }, member?.id);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="font-serif text-xl">
            {member ? 'Редактировать' : 'Добавить члена семьи'}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-2">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Имя *</Label>
              <Input
                value={form.first_name}
                onChange={e => setForm({...form, first_name: e.target.value})}
                placeholder="Имя"
              />
            </div>
            <div className="space-y-2">
              <Label>Фамилия *</Label>
              <Input
                value={form.last_name}
                onChange={e => setForm({...form, last_name: e.target.value})}
                placeholder="Фамилия"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Пол</Label>
            <Select value={form.gender} onValueChange={v => setForm({...form, gender: v})}>
              <SelectTrigger>
                <SelectValue placeholder="Выберите пол" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="male">Мужской</SelectItem>
                <SelectItem value="female">Женский</SelectItem>
                <SelectItem value="other">Другой</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Дата рождения</Label>
              <Input
                type="date"
                value={form.birth_date}
                onChange={e => setForm({...form, birth_date: e.target.value})}
              />
            </div>
            <div className="space-y-2">
              <Label>Дата смерти</Label>
              <Input
                type="date"
                value={form.death_date}
                onChange={e => setForm({...form, death_date: e.target.value})}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Место рождения</Label>
            <Input
              value={form.birth_place}
              onChange={e => setForm({...form, birth_place: e.target.value})}
              placeholder="Город, страна"
            />
          </div>

          <div className="space-y-2">
            <Label>Поколение (0 = корень)</Label>
            <Input
              type="number"
              value={form.generation}
              onChange={e => setForm({...form, generation: parseInt(e.target.value) || 0})}
            />
          </div>

          {members.length > 0 && (
            <div className="space-y-2">
              <Label>Партнёр</Label>
              <Select value={form.partner_id || 'none'} onValueChange={v => setForm({...form, partner_id: v === 'none' ? '' : v})}>
                <SelectTrigger>
                  <SelectValue placeholder="Выберите партнёра" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Нет</SelectItem>
                  {members.filter(m => m.id !== member?.id).map(m => (
                    <SelectItem key={m.id} value={m.id}>{m.first_name} {m.last_name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          <div className="space-y-2">
            <Label>Биография</Label>
            <Textarea
              value={form.bio}
              onChange={e => setForm({...form, bio: e.target.value})}
              placeholder="Краткая биография..."
              className="h-24"
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" className="rounded-full" onClick={() => onOpenChange(false)}>
            Отмена
          </Button>
          <Button
            className="rounded-full"
            disabled={!form.first_name.trim() || !form.last_name.trim()}
            onClick={handleSave}
          >
            {member ? 'Сохранить' : 'Добавить'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}