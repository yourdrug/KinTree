import React from 'react';
import { User } from 'lucide-react';

export default function TreeNode({ member, isSelected, onClick }) {
  const fullName = `${member.first_name} ${member.last_name}`;
  const years = [
    member.birth_date ? new Date(member.birth_date).getFullYear() : null,
    member.death_date ? new Date(member.death_date).getFullYear() : null,
  ].filter(Boolean).join('–');

  return (
    <button
      onClick={onClick}
      className={`
        w-44 p-4 rounded-2xl border-2 backdrop-blur-sm
        flex flex-col items-center text-center
        transition-all duration-300 hover:shadow-xl hover:scale-105
        ${isSelected
          ? 'border-primary bg-primary/5 shadow-lg shadow-primary/10'
          : 'border-border/60 bg-card/90 hover:border-primary/30 shadow-sm'
        }
      `}
    >
      <div className={`
        w-14 h-14 rounded-full flex items-center justify-center mb-3
        ${member.photo_url ? '' : 'bg-gradient-to-br from-primary/15 to-accent/30'}
        ${isSelected ? 'ring-2 ring-primary ring-offset-2 ring-offset-card' : ''}
      `}>
        {member.photo_url ? (
          <img src={member.photo_url} alt={fullName} className="w-full h-full rounded-full object-cover" />
        ) : (
          <User className="w-6 h-6 text-primary/60" />
        )}
      </div>

      <span className="text-sm font-semibold truncate max-w-full">{fullName}</span>
      {years && (
        <span className="text-xs text-muted-foreground mt-0.5">{years}</span>
      )}
      {member.birth_place && (
        <span className="text-xs text-muted-foreground/70 mt-0.5 truncate max-w-full">{member.birth_place}</span>
      )}
    </button>
  );
}