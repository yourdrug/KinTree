import { motion } from "framer-motion";
import { Plus, User } from "lucide-react";

export default function PersonNode({ person, isSelected, onClick, canEdit, onAddChild, style = {} }) {
  const isAlive = !person.death_date;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.7 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ type: "spring", stiffness: 200, damping: 20 }}
      whileHover={{ scale: 1.04 }}
      onClick={() => onClick(person)}
      className="absolute cursor-pointer select-none"
      style={{ left: style.x || 0, top: style.y || 0, width: 110 }}
    >
      <div
        className="rounded-2xl p-3 text-center transition-all duration-300"
        style={{
          background: isSelected ? "hsl(145,35%,38%)" : "white",
          border: isSelected ? "2px solid hsl(145,35%,38%)" : "2px solid hsl(35,20%,88%)",
          boxShadow: isSelected
            ? "0 8px 30px hsla(145,35%,38%,0.3)"
            : "0 4px 16px hsla(30,10%,15%,0.08)",
        }}
      >
        {/* Photo */}
        <div className="mx-auto w-14 h-14 rounded-full overflow-hidden mb-2 border-2"
          style={{ borderColor: isSelected ? "hsla(255,255%,255%,0.3)" : "hsl(35,30%,90%)" }}>
          {person.photo_url ? (
            <img src={person.photo_url} alt={person.first_name} className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center"
              style={{ background: isSelected ? "hsla(255,255%,255%,0.2)" : "hsl(35,40%,92%)" }}>
              <User className="w-6 h-6" style={{ color: isSelected ? "white" : "hsl(30,8%,50%)" }} />
            </div>
          )}
        </div>

        {/* Name */}
        <div className="text-xs font-semibold leading-tight truncate"
          style={{ color: isSelected ? "white" : "hsl(30,10%,15%)" }}>
          {person.first_name}
        </div>
        <div className="text-xs font-semibold leading-tight truncate mb-1"
          style={{ color: isSelected ? "hsla(255,255%,255%,0.9)" : "hsl(30,10%,15%)" }}>
          {person.last_name}
        </div>

        {/* Years */}
        <div className="text-[10px]" style={{ color: isSelected ? "hsla(255,255%,255%,0.7)" : "hsl(30,8%,55%)" }}>
          {person.birth_date ? new Date(person.birth_date).getFullYear() : "?"} —{" "}
          {isAlive ? "наст." : person.death_date ? new Date(person.death_date).getFullYear() : "?"}
        </div>
      </div>

      {/* Add child button */}
      {canEdit && isSelected && (
        <motion.button
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          onClick={(e) => { e.stopPropagation(); onAddChild && onAddChild(person); }}
          className="absolute -bottom-3 left-1/2 -translate-x-1/2 w-6 h-6 rounded-full flex items-center justify-center text-white shadow-md hover:scale-110 transition-transform"
          style={{ background: "hsl(145,35%,38%)" }}
        >
          <Plus className="w-3 h-3" />
        </motion.button>
      )}
    </motion.div>
  );
}